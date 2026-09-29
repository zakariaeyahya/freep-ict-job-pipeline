"""AC12: the published JobRecord/ScanRun shapes validate against a
versioned JSON Schema (contracts/job_record.schema.json,
contracts/scan_run.schema.json).

Covers three things:
1. Every required fixture (contracts/fixtures/) validates cleanly — these
   are the same fixtures the frontend UI is built against (CLAUDE.md
   "Fixtures in contracts/fixtures/ must include at least: one complete
   open job, one job with unknown fields, one closed job, one COMPLETE
   scan and one INCOMPLETE scan").
2. JobRecordMapper's real output (from an actual JobCurrent row) validates
   against the schema, proving the schema matches what the pipeline
   actually produces, not just hand-written fixtures.
3. A record that violates the contract (wrong enum value, missing
   required field) is correctly rejected — proving the schema is strict,
   not a rubber stamp.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.freep_pipeline.contracts.job_record_mapper import JobRecordMapper
from src.freep_pipeline.contracts.scan_run_mapper import ScanRunMapper
from src.freep_pipeline.contracts.schema_validator import job_record_validator, scan_run_validator

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "contracts" / "fixtures"

JOB_FIXTURES = [
    "job_complete_open.json",
    "job_unknown_fields.json",
    "job_closed.json",
]
SCAN_FIXTURES = [
    "scan_complete.json",
    "scan_incomplete.json",
]


def _load_fixture(name: str) -> dict:
    with open(FIXTURES_DIR / name, encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.parametrize("fixture_name", JOB_FIXTURES)
def test_job_fixture_validates_against_schema(fixture_name: str) -> None:
    record = _load_fixture(fixture_name)
    result = job_record_validator().validate(record)
    assert result.is_valid, f"{fixture_name} failed schema validation: {result.errors}"


@pytest.mark.parametrize("fixture_name", SCAN_FIXTURES)
def test_scan_fixture_validates_against_schema(fixture_name: str) -> None:
    report = _load_fixture(fixture_name)
    result = scan_run_validator().validate(report)
    assert result.is_valid, f"{fixture_name} failed schema validation: {result.errors}"


def test_all_required_fixture_categories_exist() -> None:
    """CLAUDE.md requires at least these 5 fixture categories to exist."""
    for name in JOB_FIXTURES + SCAN_FIXTURES:
        assert (FIXTURES_DIR / name).exists(), f"missing required fixture: {name}"


class _FakeJobCurrent:
    """Stand-in for storage.models.JobCurrent with the fields the mapper
    reads, avoiding a DB round-trip for this contract test."""

    def __init__(self, **overrides) -> None:
        defaults = dict(
            source_job_id="freep-99001",
            source_url="https://www.freep.nl/opdracht/99001",
            title="Cloud Engineer",
            company="Acme Consulting",
            rate="80-100",
            province="Utrecht",
            segment="ICT Informatievoorziening",
            hours_per_week="32 - 40 uur per week",
            start_date=None,
            end_date=None,
            description_original="Build and maintain cloud infrastructure.",
            hard_requirements=["Minimaal 5 jaar ervaring met Java"],
            wishes=["Kennis van Kubernetes is een pre"],
            education=[],
            experience=[],
            skills=[],
            methods=[],
            certifications=[],
            languages=[],
            contract_type=None,
            zzp_allowed=None,
            screening=None,
            vog=None,
            positions=None,
            max_candidates=None,
            rate_min=80,
            rate_max=100,
            hours_min=32,
            hours_max=40,
            status="open",
            change_type="new",
            consecutive_absences=0,
            content_hash="abc123",
            record_version=1,
            first_seen_at=datetime(2026, 9, 27, 10, 0, tzinfo=timezone.utc),
            last_seen_at=datetime(2026, 9, 27, 10, 0, tzinfo=timezone.utc),
        )
        defaults.update(overrides)
        for key, value in defaults.items():
            setattr(self, key, value)


def test_mapper_output_validates_against_schema() -> None:
    job = _FakeJobCurrent()
    record = JobRecordMapper().to_job_record(job)

    result = job_record_validator().validate(record)
    assert result.is_valid, f"mapper output failed schema validation: {result.errors}"


def test_mapper_output_for_closed_job_validates_against_schema() -> None:
    job = _FakeJobCurrent(status="closed", change_type="closed", consecutive_absences=2, record_version=3)
    record = JobRecordMapper().to_job_record(job)

    result = job_record_validator().validate(record)
    assert result.is_valid, f"mapper output failed schema validation: {result.errors}"
    assert record["version"]["observation_state"] == "closed"


def test_mapper_output_with_populated_profile_engagement_procedure_validates_against_schema() -> None:
    """AC's profile/engagement/procedure groups, once LlmFieldExtractor
    populates them, must still validate — proves the schema's shape for
    these groups matches what the mapper actually emits, not just the
    empty-defaults case covered above."""
    job = _FakeJobCurrent(
        education=["HBO werk- en denkniveau"],
        experience=["5 jaar ervaring als architect"],
        skills=["Azure", "Kubernetes"],
        methods=["Scrum"],
        certifications=["AZ-900"],
        languages=["Nederlands", "Engels"],
        contract_type="detachering",
        zzp_allowed=False,
        screening="VOG vereist",
        vog=True,
        positions=2,
        max_candidates=5,
    )
    record = JobRecordMapper().to_job_record(job)

    result = job_record_validator().validate(record)
    assert result.is_valid, f"mapper output failed schema validation: {result.errors}"
    assert record["profile"]["skills"] == ["Azure", "Kubernetes"]
    assert record["engagement"]["zzp_allowed"] is False
    assert record["procedure"]["positions"] == 2


def test_schema_rejects_invalid_change_type() -> None:
    record = _load_fixture("job_complete_open.json")
    record["change_type"] = "deleted"  # not in the allowed enum

    result = job_record_validator().validate(record)
    assert not result.is_valid
    assert any("change_type" in error for error in result.errors)


def test_schema_rejects_missing_required_group() -> None:
    record = _load_fixture("job_complete_open.json")
    del record["quality"]

    result = job_record_validator().validate(record)
    assert not result.is_valid


def test_schema_rejects_scan_with_invalid_status() -> None:
    report = _load_fixture("scan_complete.json")
    report["scan_status"] = "DONE"  # not in the allowed enum

    result = scan_run_validator().validate(report)
    assert not result.is_valid


class _FakeRoute:
    def __init__(self, **overrides) -> None:
        defaults = dict(url="https://www.freep.nl/opdrachten", pages_visited=3, result="success", error=None)
        defaults.update(overrides)
        for key, value in defaults.items():
            setattr(self, key, value)


class _FakeScanError:
    def __init__(self, **overrides) -> None:
        defaults = dict(reference="freep-1", reason="HTTP 500", retry_count=1, recovery_status="recovered")
        defaults.update(overrides)
        for key, value in defaults.items():
            setattr(self, key, value)


class _FakeScanRun:
    """Stand-in for storage.scan_models.ScanRun with the fields
    ScanRunMapper reads, avoiding a DB round-trip for this contract test."""

    def __init__(self, **overrides) -> None:
        defaults = dict(
            scan_id="scan_20260927_1000",
            started_at=datetime(2026, 9, 27, 10, 0, tzinfo=timezone.utc),
            ended_at=datetime(2026, 9, 27, 10, 12, tzinfo=timezone.utc),
            config="freep-ict-daily-v3",
            dedup_rule="unique by Freep job slug",
            scan_status="COMPLETE_WITHIN_SCAN_WINDOW",
            published=True,
            published_reason=None,
            count_discovered=10,
            count_processed=10,
            count_duplicates=0,
            count_new=3,
            count_changed=2,
            count_closed=1,
            count_temporarily_not_found=0,
            count_errors=1,
            routes=[_FakeRoute()],
            errors=[_FakeScanError()],
        )
        defaults.update(overrides)
        for key, value in defaults.items():
            setattr(self, key, value)


def test_scan_mapper_output_validates_against_schema() -> None:
    scan = _FakeScanRun()
    report = ScanRunMapper().to_scan_run(scan)

    result = scan_run_validator().validate(report)
    assert result.is_valid, f"scan mapper output failed schema validation: {result.errors}"
    assert report["convergence_rounds"] == []


def test_scan_mapper_output_for_unpublished_scan_validates_against_schema() -> None:
    scan = _FakeScanRun(
        scan_status="INCOMPLETE",
        published=False,
        published_reason="scan_status was INCOMPLETE, not COMPLETE_WITHIN_SCAN_WINDOW",
    )
    report = ScanRunMapper().to_scan_run(scan)

    result = scan_run_validator().validate(report)
    assert result.is_valid, f"scan mapper output failed schema validation: {result.errors}"
    assert report["published"] == {"value": False, "reason": "scan_status was INCOMPLETE, not COMPLETE_WITHIN_SCAN_WINDOW"}
