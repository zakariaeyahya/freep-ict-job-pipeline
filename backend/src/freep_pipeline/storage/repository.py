"""Repository: persists job observations and maintains the jobs_current
projection in PostgreSQL.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config.logging_config import get_logger
from config.settings import DATABASE_URL
from src.freep_pipeline.models.job import ParsedJob
from src.freep_pipeline.models.scan import ScanReport
from src.freep_pipeline.normalization.normalizer import JobNormalizer
from src.freep_pipeline.storage.models import Base, JobCurrent, JobObservation
from src.freep_pipeline.storage.scan_models import ScanError, ScanRoute
from src.freep_pipeline.storage.scan_models import ScanRun as ScanRunModel
from src.freep_pipeline.tracking.change_tracker import ChangeTracker

logger = get_logger(__name__)


class JobRepository:
    """Owns the database connection and read/write access to job data."""

    def __init__(self, database_url: str = DATABASE_URL) -> None:
        self._engine = create_engine(database_url)
        self._session_factory: sessionmaker[Session] = sessionmaker(bind=self._engine)
        self._change_tracker = ChangeTracker()
        self._normalizer = JobNormalizer()

    def create_schema(self) -> None:
        """Create tables if they do not exist yet — used for disposable
        test databases (SQLite, see tests/test_scan_recovery.py) where a
        fresh schema is created and thrown away per test. For the real
        Postgres database, schema changes go through Alembic migrations
        (migrations/) instead; this method is a no-op there once the
        initial migration has been stamped, since the tables already
        exist."""
        Base.metadata.create_all(self._engine)
        logger.info("Database schema ensured")

    def get_current_job(self, source_job_id: str) -> JobCurrent | None:
        """Reads one job's current projection. Returns None if it does not
        exist (the API maps that to 404, not this layer's concern)."""
        with self._session_factory() as session:
            job = session.get(JobCurrent, source_job_id)
            if job is not None:
                session.expunge(job)
            return job

    def list_current_jobs(
        self,
        status: str | None = None,
        change_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[JobCurrent]:
        """Reads the current projection, optionally filtered, for the
        API's GET /jobs (brief §5.1: filter by status/change_type)."""
        with self._session_factory() as session:
            query = session.query(JobCurrent)
            if status is not None:
                query = query.filter(JobCurrent.status == status)
            if change_type is not None:
                query = query.filter(JobCurrent.change_type == change_type)
            jobs = query.order_by(JobCurrent.source_job_id).offset(offset).limit(limit).all()
            for job in jobs:
                session.expunge(job)
            return jobs

    def save_observation(self, job: ParsedJob, scan_id: str, content_hash: str) -> None:
        """Insert one immutable observation row. Never updates existing rows."""
        with self._session_factory() as session:
            observation = JobObservation(
                scan_id=scan_id,
                source_job_id=job.source_job_id,
                source_url=job.source_url,
                title=job.title,
                company=job.company,
                rate=job.rate,
                province=job.province,
                segment=job.segment,
                hours_per_week=job.hours_per_week,
                start_date=job.start_date,
                end_date=job.end_date,
                description_original=job.description_original,
                hard_requirements=job.hard_requirements,
                wishes=job.wishes,
                content_hash=content_hash,
                observed_at=datetime.now(timezone.utc),
            )
            session.add(observation)
            session.commit()

    def upsert_current(self, job: ParsedJob, content_hash: str) -> tuple[str, JobCurrent]:
        """Update the jobs_current projection from a new observation,
        deriving change_type by comparing against the previous state.
        Returns (change_type, the resulting JobCurrent row, detached from
        the session so the caller can read it after this method returns —
        e.g. to schema-validate what was just published, AC12/AC14)."""
        with self._session_factory() as session:
            existing = session.get(JobCurrent, job.source_job_id)
            now = datetime.now(timezone.utc)

            change_type = self._change_tracker.derive_change_type(
                previous_hash=existing.content_hash if existing else None,
                new_hash=content_hash,
            )
            rate_min, rate_max = self._normalizer.normalize_rate(job.rate)
            hours_min, hours_max = self._normalizer.normalize_hours(job.hours_per_week)

            if existing:
                existing.title = job.title
                existing.company = job.company
                existing.rate = job.rate
                existing.province = job.province
                existing.segment = job.segment
                existing.hours_per_week = job.hours_per_week
                existing.start_date = job.start_date
                existing.end_date = job.end_date
                existing.description_original = job.description_original
                existing.hard_requirements = job.hard_requirements
                existing.wishes = job.wishes
                existing.rate_min = rate_min
                existing.rate_max = rate_max
                existing.hours_min = hours_min
                existing.hours_max = hours_max
                existing.content_hash = content_hash
                existing.change_type = change_type
                existing.status = "open"
                existing.consecutive_absences = 0
                existing.record_version += 1
                existing.last_seen_at = now
                current = existing
            else:
                current = JobCurrent(
                    source_job_id=job.source_job_id,
                    source_url=job.source_url,
                    title=job.title,
                    company=job.company,
                    rate=job.rate,
                    province=job.province,
                    segment=job.segment,
                    hours_per_week=job.hours_per_week,
                    start_date=job.start_date,
                    end_date=job.end_date,
                    description_original=job.description_original,
                    hard_requirements=job.hard_requirements,
                    wishes=job.wishes,
                    rate_min=rate_min,
                    rate_max=rate_max,
                    hours_min=hours_min,
                    hours_max=hours_max,
                    status="open",
                    change_type="new",
                    consecutive_absences=0,
                    content_hash=content_hash,
                    record_version=1,
                    first_seen_at=now,
                    last_seen_at=now,
                )
                session.add(current)

            session.commit()
            session.refresh(current)
            session.expunge(current)
            logger.info("Upserted jobs_current for %s (%s)", job.source_job_id, change_type)
            return change_type, current

    def mark_absent_jobs(self, seen_source_job_ids: set[str]) -> dict[str, int]:
        """Mark every currently-open-or-unknown job NOT in
        seen_source_job_ids as temporarily_not_found or closed, per
        CLOSURE_AFTER_CONSECUTIVE_ABSENCES (AC09, brief §3.3). Never
        touches jobs already closed. Returns counts by change_type."""
        counts = {"temporarily_not_found": 0, "closed": 0}

        with self._session_factory() as session:
            candidates = (
                session.query(JobCurrent)
                .filter(JobCurrent.status != "closed")
                .filter(JobCurrent.source_job_id.notin_(seen_source_job_ids))
                .all()
            )

            for job in candidates:
                status, change_type, absences = self._change_tracker.derive_absence_state(
                    job.consecutive_absences
                )
                job.status = status
                job.change_type = change_type
                job.consecutive_absences = absences
                job.record_version += 1
                counts[change_type] += 1
                logger.info(
                    "Marked %s as %s (consecutive_absences=%d)",
                    job.source_job_id,
                    change_type,
                    absences,
                )

            session.commit()

        return counts

    def list_observations(self, source_job_id: str) -> list[JobObservation]:
        """All immutable observations of one job, oldest first — the raw
        material for GET /jobs/{id}/versions (brief §5.1)."""
        with self._session_factory() as session:
            observations = (
                session.query(JobObservation)
                .filter(JobObservation.source_job_id == source_job_id)
                .order_by(JobObservation.observed_at.asc())
                .all()
            )
            for observation in observations:
                session.expunge(observation)
            return observations

    def list_scan_runs(self, limit: int = 50, offset: int = 0) -> list[ScanRunModel]:
        """Most recent scan runs first, for GET /scans (brief §5.1)."""
        with self._session_factory() as session:
            scans = (
                session.query(ScanRunModel)
                .order_by(ScanRunModel.started_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )
            for scan in scans:
                self._load_scan_children(session, scan)
                session.expunge(scan)
            return scans

    def get_scan_run(self, scan_id: str) -> ScanRunModel | None:
        """One scan run by id, with its routes/errors, for GET
        /scans/{scan_id} and the JSONL export (brief §5.1, §5.2)."""
        with self._session_factory() as session:
            scan = session.get(ScanRunModel, scan_id)
            if scan is None:
                return None
            self._load_scan_children(session, scan)
            session.expunge(scan)
            return scan

    @staticmethod
    def _load_scan_children(session: Session, scan: ScanRunModel) -> None:
        # Force-load relationships before expunge — accessing them after
        # the session closes would raise DetachedInstanceError.
        _ = list(scan.routes)
        _ = list(scan.errors)

    def list_observed_source_job_ids(self, scan_id: str) -> list[str]:
        """Distinct source_job_ids observed during one scan, in first-seen
        order — drives the per-scan JSONL export (brief §5.2: 'one job per
        line')."""
        with self._session_factory() as session:
            rows = (
                session.query(JobObservation.source_job_id)
                .filter(JobObservation.scan_id == scan_id)
                .distinct()
                .order_by(JobObservation.source_job_id.asc())
                .all()
            )
            return [row[0] for row in rows]

    def get_last_published_scan(self) -> ScanRunModel | None:
        """The most recently published (successful) scan, for GET /health's
        freshness signal (brief §4.1 "Freshness and audit"). Deliberately
        ignores unpublished scans — a FAILED or INCOMPLETE run must never
        make the dataset look fresher than it is."""
        with self._session_factory() as session:
            scan = (
                session.query(ScanRunModel)
                .filter(ScanRunModel.published.is_(True))
                .order_by(ScanRunModel.ended_at.desc())
                .first()
            )
            if scan is not None:
                session.expunge(scan)
            return scan

    def save_scan_run(self, report: ScanReport) -> None:
        """Persist a finished scan run: window, routes, counts, errors and
        final status (AC01, AC10)."""
        with self._session_factory() as session:
            scan_run = ScanRunModel(
                scan_id=report.scan_id,
                started_at=report.started_at,
                ended_at=report.ended_at,
                config=report.config,
                dedup_rule=report.dedup_rule,
                scan_status=report.scan_status,
                published=report.published,
                published_reason=report.published_reason,
                count_discovered=report.counts.discovered,
                count_processed=report.counts.processed,
                count_duplicates=report.counts.duplicates,
                count_new=report.counts.new,
                count_changed=report.counts.changed,
                count_closed=report.counts.closed,
                count_temporarily_not_found=report.counts.temporarily_not_found,
                count_errors=report.counts.errors,
            )

            scan_run.routes = [
                ScanRoute(
                    url=route.url,
                    pages_visited=route.pages_visited,
                    result=route.result,
                    error=route.error,
                )
                for route in report.routes
            ]

            scan_run.errors = [
                ScanError(
                    reference=error.reference,
                    reason=error.reason,
                    retry_count=error.retry_count,
                    recovery_status=error.recovery_status,
                )
                for error in report.errors
            ]

            session.add(scan_run)
            session.commit()
            logger.info("Saved scan run %s (%s)", report.scan_id, report.scan_status)
