"""Maps the flat JobCurrent row the pipeline stores today onto the grouped
JobRecord shape the data contract publishes (job_record.schema.json,
mirroring freep-ict-job-pipeline/src/lib/contracts/job.ts and brief §4.2).

The pipeline does not populate profile/commercial/engagement/procedure or
attachments yet (see CLAUDE.md "Not done yet") — those groups are emitted
with their null/empty defaults rather than fabricated, per the
never-fabricate-content rule. As the parser grows to extract more fields,
extend the mapping here; the schema already expects the full shape.
"""

from __future__ import annotations

from typing import Any

SCHEMA_VERSION = "1.0"


class JobRecordMapper:
    """Builds a schema-shaped JobRecord dict from a JobCurrent row."""

    def to_job_record(self, job: Any) -> dict:
        return {
            "schema_version": SCHEMA_VERSION,
            "identity": self._identity(job),
            "core": self._core(job),
            "publication": self._publication(job),
            "delivery": self._delivery(job),
            "selection": self._selection(job),
            "profile": self._empty_profile(),
            "commercial": self._commercial(job),
            "engagement": self._empty_engagement(),
            "procedure": self._empty_procedure(),
            "quality": self._quality(job),
            "version": self._version(job),
            "attachments": [],
            "change_type": job.change_type,
        }

    @staticmethod
    def _identity(job: Any) -> dict:
        return {
            "internal_job_id": job.source_job_id,
            "source_job_id": job.source_job_id,
            "canonical_url": job.source_url,
            "source": "freep",
        }

    @staticmethod
    def _core(job: Any) -> dict:
        return {
            "title": job.title,
            "client_name": job.company,
            "description_original": job.description_original,
            "description_clean": None,
        }

    @staticmethod
    def _publication(job: Any) -> dict:
        return {
            "publication_datetime": None,
            "closing_datetime": None,
            "timezone": "Europe/Amsterdam",
            "status": job.status,
        }

    @staticmethod
    def _delivery(job: Any) -> dict:
        return {
            "location": job.province,
            "remote_policy": None,
            "hours_min": job.hours_min,
            "hours_max": job.hours_max,
            "start_date": job.start_date,
            "end_date": job.end_date,
            "extension_options": None,
        }

    @staticmethod
    def _selection(job: Any) -> dict:
        return {
            "hard_requirements": [
                {"text": text, "evidence_ref": None} for text in (job.hard_requirements or [])
            ],
            "wishes": [{"text": text, "evidence_ref": None} for text in (job.wishes or [])],
            "award_criteria": [],
            "competencies": [],
        }

    @staticmethod
    def _empty_profile() -> dict:
        return {
            "education": [],
            "experience": [],
            "skills": [],
            "methods": [],
            "certifications": [],
            "languages": [],
        }

    @staticmethod
    def _commercial(job: Any) -> dict:
        return {
            "rate_min": job.rate_min,
            "rate_max": job.rate_max,
            "currency": "EUR" if job.rate else None,
            "vat_basis": None,
            "travel_cost_policy": None,
        }

    @staticmethod
    def _empty_engagement() -> dict:
        return {
            "contract_type": None,
            "zzp_allowed": None,
            "screening": None,
            "vog": None,
            "nationality_constraints": None,
            "supplier_conditions": None,
        }

    @staticmethod
    def _empty_procedure() -> dict:
        return {
            "positions": None,
            "max_candidates": None,
            "interview_window": None,
            "submission_instructions": None,
        }

    @staticmethod
    def _quality(job: Any) -> dict:
        return {
            "completeness_status": "complete_within_scan_window",
            "validation_errors": [],
            "source_evidence": [],
            "confidence_per_field": None,
        }

    @staticmethod
    def _version(job: Any) -> dict:
        observation_state = "closed" if job.status == "closed" else (
            "temporarily_not_found" if job.change_type == "temporarily_not_found" else "active"
        )
        return {
            "first_seen_at": job.first_seen_at.isoformat(),
            "last_seen_at": job.last_seen_at.isoformat(),
            "changed_at": job.last_seen_at.isoformat() if job.change_type == "changed" else None,
            "content_hash": f"sha256:{job.content_hash}",
            "record_version": job.record_version,
            "observation_state": observation_state,
        }
