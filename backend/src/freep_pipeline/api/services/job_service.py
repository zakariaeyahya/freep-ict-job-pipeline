"""Business logic for job endpoints. Routes call this; it never talks HTTP
directly (CLAUDE.md: "Never put business logic in FastAPI route handlers.
Routes call services, services hold the logic.").
"""

from __future__ import annotations

from src.freep_pipeline.contracts.job_record_mapper import JobRecordMapper
from src.freep_pipeline.contracts.schema_validator import SchemaValidator, job_record_validator
from src.freep_pipeline.storage.repository import JobRepository


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
    ) -> None:
        self._repository = repository or JobRepository()
        self._mapper = mapper or JobRecordMapper()
        self._validator = validator or job_record_validator()

    def list_jobs(self, status: str | None, change_type: str | None, limit: int, offset: int) -> list[dict]:
        rows = self._repository.list_current_jobs(status=status, change_type=change_type, limit=limit, offset=offset)
        return [self._to_validated_record(row) for row in rows]

    def get_job(self, source_job_id: str) -> dict:
        row = self._repository.get_current_job(source_job_id)
        if row is None:
            raise JobNotFoundError(source_job_id)
        return self._to_validated_record(row)

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
