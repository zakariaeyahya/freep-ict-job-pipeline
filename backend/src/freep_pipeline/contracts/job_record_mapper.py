"""Maps the flat JobCurrent row the pipeline stores today onto the grouped
JobRecord shape the data contract publishes (job_record.schema.json,
mirroring freep-ict-job-pipeline/src/lib/contracts/job.ts and brief §4.2).

profile/engagement/procedure are populated from LlmFieldExtractor's output
(stored on JobCurrent — see storage/models.py), which only ever contains
values verified as exact substrings of the source text. Fields with no
reliable signal on Freep's pages at all (nationality_constraints,
supplier_conditions, interview_window, submission_instructions) stay null
rather than fabricated, per the never-fabricate-content rule. attachments
stays empty — no attachment mechanism was found on Freep's job pages.
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
            "profile": self._profile(job),
            "commercial": self._commercial(job),
            "engagement": self._engagement(job),
            "procedure": self._procedure(job),
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
    def _profile(job: Any) -> dict:
        return {
            "education": job.education or [],
            "experience": job.experience or [],
            "skills": job.skills or [],
            "methods": job.methods or [],
            "certifications": job.certifications or [],
            "languages": job.languages or [],
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
    def _engagement(job: Any) -> dict:
        return {
            "contract_type": job.contract_type,
            "zzp_allowed": job.zzp_allowed,
            "screening": job.screening,
            "vog": job.vog,
            # No reliable per-offer signal found on Freep's pages for
            # these two (see ../docs/DISCOVERY_REPORT.md) — never fabricated.
            "nationality_constraints": None,
            "supplier_conditions": None,
        }

    @staticmethod
    def _procedure(job: Any) -> dict:
        return {
            "positions": job.positions,
            "max_candidates": job.max_candidates,
            # No reliable per-offer signal found on Freep's pages for
            # these two (see ../docs/DISCOVERY_REPORT.md) — never fabricated.
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
