"""Business logic for GET /exports/{scan_id}.jsonl (brief §5.2: 'One job
per line, UTF-8, with schema version' — for batch matching/embeddings).

Reuses JobService for the mapping + AC12 schema validation, so an exported
line and a GET /jobs/{id} response for the same job are always identical
in shape and never diverge.
"""

from __future__ import annotations

from src.freep_pipeline.api.services.job_service import JobNotFoundError, JobService
from src.freep_pipeline.api.services.scan_service import ScanNotFoundError
from src.freep_pipeline.storage.repository import JobRepository


class ExportService:
    def __init__(
        self,
        repository: JobRepository | None = None,
        job_service: JobService | None = None,
    ) -> None:
        self._repository = repository or JobRepository()
        self._job_service = job_service or JobService(repository=self._repository)

    def export_scan_as_jsonl_lines(self, scan_id: str) -> list[dict]:
        """One validated JobRecord dict per job observed during scan_id, in
        the order observed. Raises ScanNotFoundError if the scan itself
        does not exist — an empty scan (no jobs observed) is valid and
        returns an empty list."""
        scan = self._repository.get_scan_run(scan_id)
        if scan is None:
            raise ScanNotFoundError(scan_id)

        source_job_ids = self._repository.list_observed_source_job_ids(scan_id)
        records = []
        for source_job_id in source_job_ids:
            try:
                records.append(self._job_service.get_job(source_job_id))
            except JobNotFoundError:
                # The job was observed during this scan but has since been
                # removed from jobs_current entirely — cannot happen under
                # the current pipeline (jobs_current rows are never
                # deleted, only marked closed), but skipping rather than
                # crashing the whole export keeps one stale reference from
                # blocking every other job's export.
                continue
        return records
