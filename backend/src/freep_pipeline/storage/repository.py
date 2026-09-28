"""Repository: persists job observations and maintains the jobs_current
projection in PostgreSQL.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config.logging_config import get_logger
from config.settings import DATABASE_URL
from freep_pipeline.models.job import ParsedJob
from freep_pipeline.storage.models import Base, JobCurrent, JobObservation
from freep_pipeline.tracking.change_tracker import ChangeTracker

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

    def upsert_current(self, job: ParsedJob, content_hash: str) -> None:
        """Update the jobs_current projection from a new observation,
        deriving change_type by comparing against the previous state."""
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
