"""Business logic for scan endpoints. Routes call this; it never talks
HTTP directly (CLAUDE.md: "Never put business logic in FastAPI route
handlers. Routes call services, services hold the logic.").
"""

from __future__ import annotations

from src.freep_pipeline.contracts.schema_validator import SchemaValidator, scan_run_validator
from src.freep_pipeline.contracts.scan_run_mapper import ScanRunMapper
from src.freep_pipeline.storage.repository import JobRepository


class ScanNotFoundError(Exception):
    def __init__(self, scan_id: str) -> None:
        self.scan_id = scan_id
        super().__init__(f"Scan not found: {scan_id}")


class ScanService:
    """Reads scan_runs and serves it in the published ScanRun shape.

    Every scan report is schema-validated before being handed to a route
    (AC12), same guarantee as JobService applies to job records."""

    def __init__(
        self,
        repository: JobRepository | None = None,
        mapper: ScanRunMapper | None = None,
        validator: SchemaValidator | None = None,
    ) -> None:
        self._repository = repository or JobRepository()
        self._mapper = mapper or ScanRunMapper()
        self._validator = validator or scan_run_validator()

    def list_scans(self, limit: int, offset: int) -> list[dict]:
        scans = self._repository.list_scan_runs(limit=limit, offset=offset)
        return [self._to_validated_scan(scan) for scan in scans]

    def get_scan(self, scan_id: str) -> dict:
        scan = self._repository.get_scan_run(scan_id)
        if scan is None:
            raise ScanNotFoundError(scan_id)
        return self._to_validated_scan(scan)

    def _to_validated_scan(self, scan) -> dict:
        record = self._mapper.to_scan_run(scan)
        result = self._validator.validate(record)
        if not result.is_valid:
            # A stored scan report failing its own published contract is a
            # server-side data integrity fault (CLAUDE.md: 500 only for
            # real unexpected server failures).
            raise ValueError(f"Stored scan {scan.scan_id} failed schema validation: {result.errors}")
        return record
