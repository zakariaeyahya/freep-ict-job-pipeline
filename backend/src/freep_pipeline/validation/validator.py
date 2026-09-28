"""Validates parsed jobs before they are stored.

Migrated from the notebook's ad-hoc pandas checks (cells 28-30: missing
values, duplicate source_job_id, segment counts) into explicit rules.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from config.logging_config import get_logger
from src.freep_pipeline.models.job import ParsedJob

logger = get_logger(__name__)

REQUIRED_FIELDS = ("source_job_id", "source_url", "title", "company", "description_original", "segment")
_DATE_PATTERN_HINT = "expected format like '18 September 2026'"


@dataclass
class ValidationResult:
    job: ParsedJob
    errors: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors


class JobValidator:
    """Runs quality checks on a batch of parsed jobs."""

    def validate_batch(self, jobs: list[ParsedJob]) -> list[ValidationResult]:
        seen_ids: set[str] = set()
        results: list[ValidationResult] = []

        for job in jobs:
            errors = self._validate_required_fields(job)
            errors += self._validate_duplicate_id(job, seen_ids)
            seen_ids.add(job.source_job_id)

            result = ValidationResult(job=job, errors=errors)
            if not result.is_valid:
                logger.warning("Job %s failed validation: %s", job.source_job_id, errors)
            results.append(result)

        valid_count = sum(1 for r in results if r.is_valid)
        logger.info("Validation: %d/%d jobs valid", valid_count, len(results))
        return results

    def _validate_required_fields(self, job: ParsedJob) -> list[str]:
        errors = []
        for field_name in REQUIRED_FIELDS:
            if not getattr(job, field_name):
                errors.append(f"missing required field: {field_name}")
        return errors

    def _validate_duplicate_id(self, job: ParsedJob, seen_ids: set[str]) -> list[str]:
        if job.source_job_id in seen_ids:
            return [f"duplicate source_job_id: {job.source_job_id}"]
        return []
