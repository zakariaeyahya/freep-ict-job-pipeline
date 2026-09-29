"""API surface beyond the AC15 minimum (brief §2/§5):
GET /jobs/{id}/versions and GET /exports/{scan_id}.jsonl.

Both services take an optional repository, so these tests inject a fake
in-memory repository instead of hitting Postgres — consistent with
test_contracts.py's _FakeJobCurrent pattern.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.freep_pipeline.api.services.export_service import ExportService
from src.freep_pipeline.api.services.job_service import JobNotFoundError, JobService
from src.freep_pipeline.api.services.scan_service import ScanNotFoundError


class _FakeObservation:
    def __init__(self, **overrides) -> None:
        defaults = dict(
            source_job_id="freep-1246",
            title="Data Engineer",
            company="Capgemini",
            content_hash="hash-v1",
            observed_at=datetime(2026, 9, 20, 9, 0, tzinfo=timezone.utc),
        )
        defaults.update(overrides)
        for key, value in defaults.items():
            setattr(self, key, value)


class _FakeCurrentJob:
    def __init__(self, **overrides) -> None:
        defaults = dict(
            source_job_id="freep-1246",
            source_url="https://www.freep.nl/opdracht/1246",
            title="Data Engineer",
            company="Capgemini",
            rate="65-90",
            province="Utrecht",
            segment="ICT Informatievoorziening",
            hours_per_week="32-40",
            start_date=None,
            end_date=None,
            description_original="Build data pipelines.",
            hard_requirements=[],
            wishes=[],
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
            rate_min=65,
            rate_max=90,
            hours_min=32,
            hours_max=40,
            status="open",
            change_type="changed",
            consecutive_absences=0,
            content_hash="hash-v3",
            record_version=3,
            first_seen_at=datetime(2026, 9, 20, 9, 0, tzinfo=timezone.utc),
            last_seen_at=datetime(2026, 9, 27, 9, 0, tzinfo=timezone.utc),
        )
        defaults.update(overrides)
        for key, value in defaults.items():
            setattr(self, key, value)


class _FakeRepository:
    def __init__(self, observations=None, current_jobs=None, scan_exists=True, observed_ids=None) -> None:
        self._observations = observations or []
        self._current_jobs = current_jobs or {}
        self._scan_exists = scan_exists
        self._observed_ids = observed_ids or []

    def list_observations(self, source_job_id: str):
        return [obs for obs in self._observations if obs.source_job_id == source_job_id]

    def get_current_job(self, source_job_id: str):
        return self._current_jobs.get(source_job_id)

    def get_scan_run(self, scan_id: str):
        return object() if self._scan_exists else None

    def list_observed_source_job_ids(self, scan_id: str):
        return self._observed_ids


def test_get_versions_excludes_the_current_observation_and_derives_change_type() -> None:
    """Three observations (new -> unchanged -> changed): only the first two
    are 'past' versions (record_version 1 and 2); the third is the current
    state, already served by GET /jobs/{id}, so it must not be duplicated
    here — matching the frontend mock's documented contract."""
    observations = [
        _FakeObservation(content_hash="hash-v1", observed_at=datetime(2026, 9, 10, 9, 0, tzinfo=timezone.utc)),
        _FakeObservation(content_hash="hash-v1", observed_at=datetime(2026, 9, 17, 9, 0, tzinfo=timezone.utc)),
        _FakeObservation(content_hash="hash-v3", observed_at=datetime(2026, 9, 24, 9, 0, tzinfo=timezone.utc)),
    ]
    service = JobService(repository=_FakeRepository(observations=observations))

    versions = service.get_versions("freep-1246")

    assert len(versions) == 2
    assert versions[0]["change_type"] == "new"
    assert versions[0]["record_version"] == 1
    assert versions[1]["change_type"] == "unchanged"
    assert versions[1]["record_version"] == 2
    assert all(v["content_hash"].startswith("sha256:") for v in versions)


def test_get_versions_raises_not_found_for_unknown_job() -> None:
    service = JobService(repository=_FakeRepository(observations=[]))

    with pytest.raises(JobNotFoundError):
        service.get_versions("freep-does-not-exist")


def test_get_versions_for_job_observed_only_once_returns_empty_list() -> None:
    """A job seen in exactly one scan has no PAST version yet — its single
    observation IS the current state, so the version history is empty
    (not an error)."""
    observations = [_FakeObservation()]
    service = JobService(repository=_FakeRepository(observations=observations))

    versions = service.get_versions("freep-1246")

    assert versions == []


def test_export_scan_returns_one_validated_record_per_observed_job() -> None:
    current_jobs = {"freep-1246": _FakeCurrentJob()}
    repository = _FakeRepository(current_jobs=current_jobs, observed_ids=["freep-1246"])
    service = ExportService(repository=repository, job_service=JobService(repository=repository))

    records = service.export_scan_as_jsonl_lines("scan_20260927_1000")

    assert len(records) == 1
    assert records[0]["identity"]["source_job_id"] == "freep-1246"
    assert records[0]["schema_version"] == "1.0"


def test_export_raises_not_found_for_unknown_scan() -> None:
    repository = _FakeRepository(scan_exists=False)
    service = ExportService(repository=repository, job_service=JobService(repository=repository))

    with pytest.raises(ScanNotFoundError):
        service.export_scan_as_jsonl_lines("scan_does_not_exist")


def test_export_for_scan_with_no_observed_jobs_returns_empty_list() -> None:
    repository = _FakeRepository(scan_exists=True, observed_ids=[])
    service = ExportService(repository=repository, job_service=JobService(repository=repository))

    records = service.export_scan_as_jsonl_lines("scan_with_zero_jobs")

    assert records == []
