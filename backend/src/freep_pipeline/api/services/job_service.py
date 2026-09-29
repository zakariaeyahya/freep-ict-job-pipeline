"""Business logic for job endpoints. Routes call this; it never talks HTTP
directly (CLAUDE.md: "Never put business logic in FastAPI route handlers.
Routes call services, services hold the logic.").
"""

from __future__ import annotations

from src.freep_pipeline.contracts.job_record_mapper import JobRecordMapper
from src.freep_pipeline.contracts.schema_validator import SchemaValidator, job_record_validator
from src.freep_pipeline.storage.repository import JobRepository
from src.freep_pipeline.tracking.change_tracker import ChangeTracker


class JobNotFoundError(Exception):
    def __init__(self, source_job_id: str) -> None:
        self.source_job_id = source_job_id
        super().__init__(f"Job not found: {source_job_id}")


class JobService:
    """Reads jobs_current and serves it in the published JobRecord shape.

    Every record is schema-validated before being handed to a route
    (AC12) — the API must never serve a record it cannot itself prove
    conforms to the published contract."""

    def __init__(
        self,
        repository: JobRepository | None = None,
        mapper: JobRecordMapper | None = None,
        validator: SchemaValidator | None = None,
        change_tracker: ChangeTracker | None = None,
    ) -> None:
        self._repository = repository or JobRepository()
        self._mapper = mapper or JobRecordMapper()
        self._validator = validator or job_record_validator()
        self._change_tracker = change_tracker or ChangeTracker()

    def list_jobs(self, status: str | None, change_type: str | None, limit: int, offset: int) -> list[dict]:
        rows = self._repository.list_current_jobs(status=status, change_type=change_type, limit=limit, offset=offset)
        return [self._to_validated_record(row) for row in rows]

    def get_job(self, source_job_id: str) -> dict:
        row = self._repository.get_current_job(source_job_id)
        if row is None:
            raise JobNotFoundError(source_job_id)
        return self._to_validated_record(row)

    def get_versions(self, source_job_id: str) -> list[dict]:
        """Past observations of one job (GET /jobs/{id}/versions,
        brief §5.1) — every observation except the most recent, which is
        the current state already served by GET /jobs/{id}. Each entry's
        change_type is derived the same way the pipeline derives it live
        (ChangeTracker), by comparing each observation's content_hash to
        the one before it; observation history itself never stores
        change_type, only jobs_current does."""
        observations = self._repository.list_observations(source_job_id)
        if not observations:
            raise JobNotFoundError(source_job_id)

        past_observations = observations[:-1]
        entries: list[dict] = []
        previous_hash: str | None = None
        for observation in past_observations:
            change_type = self._change_tracker.derive_change_type(
                previous_hash=previous_hash, new_hash=observation.content_hash
            )
            entries.append(
                {
                    "record_version": len(entries) + 1,
                    "observed_at": observation.observed_at.isoformat(),
                    "change_type": change_type,
                    "content_hash": f"sha256:{observation.content_hash}",
                    "summary": f"{observation.title or 'Untitled'} at {observation.company or 'unknown company'}",
                }
            )
            previous_hash = observation.content_hash
        return entries

    def _to_validated_record(self, row) -> dict:
        record = self._mapper.to_job_record(row)
        result = self._validator.validate(record)
        if not result.is_valid:
            # A record that fails its own published contract must never
            # reach a caller (AC12/AC14) — surfacing it as a 500 is
            # correct here: this is an unexpected server-side data
            # integrity failure, not a client error.
            raise ValueError(f"Stored job {row.source_job_id} failed schema validation: {result.errors}")
        return record
