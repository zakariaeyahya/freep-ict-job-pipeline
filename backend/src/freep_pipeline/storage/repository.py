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

    def create_schema(self) -> None:
        """Create tables if they do not exist yet. Use Alembic migrations
        for schema changes after the first deploy."""
        Base.metadata.create_all(self._engine)
        logger.info("Database schema ensured")

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

    def upsert_current(self, job: ParsedJob, content_hash: str) -> str:
        """Update the jobs_current projection from a new observation,
        deriving change_type by comparing against the previous state.
        Returns the derived change_type."""
        with self._session_factory() as session:
            existing = session.get(JobCurrent, job.source_job_id)
            now = datetime.now(timezone.utc)

            change_type = self._change_tracker.derive_change_type(
                previous_hash=existing.content_hash if existing else None,
                new_hash=content_hash,
            )

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
                existing.content_hash = content_hash
                existing.change_type = change_type
                existing.record_version += 1
                existing.last_seen_at = now
            else:
                session.add(
                    JobCurrent(
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
                        status="open",
                        change_type="new",
                        content_hash=content_hash,
                        record_version=1,
                        first_seen_at=now,
                        last_seen_at=now,
                    )
                )

            session.commit()
            logger.info("Upserted jobs_current for %s (%s)", job.source_job_id, change_type)
            return change_type

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
