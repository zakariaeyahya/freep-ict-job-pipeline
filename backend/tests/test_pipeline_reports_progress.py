"""Verifies ScanPipeline actually calls into a progress reporter at the
right points during a real run (discovery -> per-job -> storing -> done),
using the same fake-discovery/fake-http SQLite setup as
test_scan_recovery.py. The reporter itself (ScanProgressTracker) is
tested in isolation in test_scan_progress.py — this is the wiring between
the two.
"""

from __future__ import annotations

import pytest

from src.freep_pipeline.discovery.freep_discovery import DiscoveryResult
from src.freep_pipeline.extraction.llm_field_extractor import ExtractedFields
from src.freep_pipeline.models.job import ParsedJob, RawJobLink
from src.freep_pipeline.pipeline import ScanPipeline
from src.freep_pipeline.storage.repository import JobRepository
from src.freep_pipeline.validation.validator import JobValidator

JOB_SLUGS = ["job-a", "job-b", "job-c"]


class _NoOpFieldExtractor:
    def extract(self, title, hard_requirements, wishes) -> ExtractedFields:
        return ExtractedFields()


def _job_url(slug: str) -> str:
    return f"https://www.freep.nl/opdracht/{slug}"


class _FakeDiscovery:
    def discover_job_links(self) -> DiscoveryResult:
        links = [RawJobLink(source_url=_job_url(slug), source_job_path=slug) for slug in JOB_SLUGS]
        return DiscoveryResult(links=links, coverage_confirmed=True, displayed_count=len(links))


class _FakeHttpClient:
    def get_detail_soup(self, url: str):
        return url


class _FakeParser:
    def parse(self, soup, url: str) -> ParsedJob:
        slug = url.rstrip("/").rsplit("/", 1)[-1]
        return ParsedJob(source_job_id=slug, source_url=url, title=f"Title for {slug}")


class _RecordingProgressReporter:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def start(self) -> None:
        self.calls.append(("start",))

    def report_discovery_finished(self, jobs_total: int) -> None:
        self.calls.append(("discovery_finished", jobs_total))

    def report_job_processed(self, index: int, total: int, title: str | None) -> None:
        self.calls.append(("job_processed", index, total, title))

    def report_storing(self) -> None:
        self.calls.append(("storing",))

    def finish(self) -> None:
        self.calls.append(("finish",))


@pytest.fixture()
def sqlite_url(tmp_path) -> str:
    db_path = tmp_path / "progress_test.db"
    return f"sqlite:///{db_path}"


def test_pipeline_reports_progress_through_a_full_run(sqlite_url: str) -> None:
    reporter = _RecordingProgressReporter()
    pipeline = ScanPipeline(
        discovery=_FakeDiscovery(),
        http_client=_FakeHttpClient(),
        parser=_FakeParser(),
        validator=JobValidator(),
        repository=JobRepository(database_url=sqlite_url),
        field_extractor=_NoOpFieldExtractor(),
        progress_reporter=reporter,
    )

    pipeline.run()

    kinds = [call[0] for call in reporter.calls]
    assert kinds[0] == "start"
    assert kinds[-1] == "finish"
    assert ("discovery_finished", 3) in reporter.calls
    assert ("storing",) in reporter.calls
    job_processed_calls = [call for call in reporter.calls if call[0] == "job_processed"]
    assert len(job_processed_calls) == 3
    assert job_processed_calls[0] == ("job_processed", 1, 3, "Title for job-a")
    assert job_processed_calls[-1] == ("job_processed", 3, 3, "Title for job-c")


def test_finish_is_reported_even_when_discovery_raises(sqlite_url: str) -> None:
    class _BrokenDiscovery:
        def discover_job_links(self):
            raise ConnectionError("simulated discovery failure")

    reporter = _RecordingProgressReporter()
    pipeline = ScanPipeline(
        discovery=_BrokenDiscovery(),
        http_client=_FakeHttpClient(),
        parser=_FakeParser(),
        validator=JobValidator(),
        repository=JobRepository(database_url=sqlite_url),
        field_extractor=_NoOpFieldExtractor(),
        progress_reporter=reporter,
    )

    # _discover() catches the exception internally (per pipeline.py) and
    # records a failed route rather than propagating — the scan still
    # completes (with zero jobs), so finish() is reached normally.
    pipeline.run()

    assert reporter.calls[0] == ("start",)
    assert reporter.calls[-1] == ("finish",)


def test_default_null_progress_reporter_does_not_break_a_normal_run(sqlite_url: str) -> None:
    """No progress_reporter passed (the CLI/test-suite-default case) must
    behave exactly as before this feature existed."""
    pipeline = ScanPipeline(
        discovery=_FakeDiscovery(),
        http_client=_FakeHttpClient(),
        parser=_FakeParser(),
        validator=JobValidator(),
        repository=JobRepository(database_url=sqlite_url),
        field_extractor=_NoOpFieldExtractor(),
    )

    scan_id = pipeline.run()

    assert scan_id is not None
