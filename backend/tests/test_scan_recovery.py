"""Demonstrates AC10 recovery: interrupting a scan and re-running it must
not duplicate or silently lose data.

Uses a real ScanPipeline wired to a real JobRepository against an in-memory
SQLite database (swapped in via the same database_url constructor param
used for Postgres in production) so the assertions exercise the actual
persistence path, not a mock of it. Discovery and fetching are faked so the
"interruption" (one job's fetch blowing up mid-scan) is deterministic.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from src.freep_pipeline.discovery.freep_discovery import DiscoveryResult
from src.freep_pipeline.extraction.llm_field_extractor import ExtractedFields
from src.freep_pipeline.models.job import ParsedJob, RawJobLink
from src.freep_pipeline.pipeline import ScanPipeline
from src.freep_pipeline.storage.models import JobCurrent, JobObservation
from src.freep_pipeline.storage.repository import JobRepository
from src.freep_pipeline.storage.scan_models import ScanRun
from src.freep_pipeline.validation.validator import JobValidator

JOB_SLUGS = ["job-a", "job-b", "job-c"]


class _NoOpFieldExtractor:
    """Stands in for LlmFieldExtractor so this suite never makes a real
    network call to Ollama — it tests scan recovery, not LLM extraction."""

    def extract(self, title, hard_requirements, wishes) -> ExtractedFields:
        return ExtractedFields()


def _job_url(slug: str) -> str:
    return f"https://www.freep.nl/opdracht/{slug}"


def _make_job(slug: str, title: str = "AI Developer") -> ParsedJob:
    return ParsedJob(
        source_job_id=slug,
        source_url=_job_url(slug),
        title=title,
        company="Acme Consulting",
        description_original="Build and maintain tooling.",
        segment="ICT Informatievoorziening",
        province="Utrecht",
    )


class FakeDiscovery:
    """Always finds the same 3 jobs, with confirmed coverage."""

    def discover_job_links(self) -> DiscoveryResult:
        links = [RawJobLink(source_url=_job_url(slug), source_job_path=slug) for slug in JOB_SLUGS]
        return DiscoveryResult(links=links, coverage_confirmed=True, displayed_count=len(links))


class FakeHttpClient:
    """Returns a canned BeautifulSoup-like object per URL; raises for URLs
    listed in `failing_urls` to simulate a mid-scan interruption."""

    def __init__(self, failing_urls: set[str] | None = None) -> None:
        self.failing_urls = failing_urls or set()

    def get_detail_soup(self, url: str):
        if url in self.failing_urls:
            raise ConnectionError(f"simulated network failure fetching {url}")
        return url  # opaque token; FakeParser only cares about the URL


class FakeParser:
    """Turns the opaque token from FakeHttpClient back into a ParsedJob."""

    def parse(self, soup, url: str) -> ParsedJob:
        slug = url.rstrip("/").rsplit("/", 1)[-1]
        return _make_job(slug)


@pytest.fixture()
def sqlite_url(tmp_path) -> str:
    # A file-backed SQLite DB (not :memory:) so every new engine/connection
    # created by JobRepository.__init__ sees the same persisted data,
    # exactly like separate scan runs reconnecting to the same Postgres DB.
    db_path = tmp_path / "recovery_test.db"
    return f"sqlite:///{db_path}"


def _make_pipeline(sqlite_url: str, http_client: FakeHttpClient) -> ScanPipeline:
    return ScanPipeline(
        discovery=FakeDiscovery(),
        http_client=http_client,
        parser=FakeParser(),
        validator=JobValidator(),
        repository=JobRepository(database_url=sqlite_url),
        field_extractor=_NoOpFieldExtractor(),
    )


def _session_factory(sqlite_url: str):
    engine = create_engine(sqlite_url)
    return sessionmaker(bind=engine)


def test_interrupted_scan_then_resume_causes_no_duplicates_or_loss(sqlite_url: str) -> None:
    # --- Scan 1: full success, establishes baseline -----------------------
    scan1_id = _make_pipeline(sqlite_url, FakeHttpClient()).run()

    Session = _session_factory(sqlite_url)
    with Session() as session:
        scan1 = session.get(ScanRun, scan1_id)
        assert scan1.scan_status == "COMPLETE_WITHIN_SCAN_WINDOW"
        assert scan1.published is True
        assert session.scalar(select(func.count()).select_from(JobCurrent)) == 3
        assert session.scalar(select(func.count()).select_from(JobObservation)) == 3

    # --- Scan 2: interrupted mid-scan (job-b's fetch fails) ----------------
    failing = {_job_url("job-b")}
    scan2_id = _make_pipeline(sqlite_url, FakeHttpClient(failing_urls=failing)).run()

    with Session() as session:
        scan2 = session.get(ScanRun, scan2_id)
        # An incomplete scan must be reported as such, never as success
        # (CLAUDE.md: "An incomplete scan is never shown or published as a
        # success").
        assert scan2.scan_status == "INCOMPLETE"
        assert scan2.published is False
        assert scan2.count_errors == 1
        assert len(scan2.errors) == 1
        assert scan2.errors[0].reference == "job-b"

        # job-a and job-c succeeded and must still be persisted even though
        # the scan as a whole was interrupted.
        current_jobs = {j.source_job_id: j for j in session.query(JobCurrent).all()}
        assert set(current_jobs) == {"job-a", "job-b", "job-c"}
        # job-b was not re-observed this scan; a single miss is never a
        # deletion (brief §3.3) — it must become temporarily_not_found, not
        # be dropped from jobs_current or silently marked closed.
        assert current_jobs["job-b"].change_type == "temporarily_not_found"
        assert current_jobs["job-b"].status == "unknown"
        assert current_jobs["job-b"].consecutive_absences == 1
        # job-a/job-c were re-observed and correctly classified unchanged
        # (identical content), not duplicated as spurious "new" rows.
        assert current_jobs["job-a"].change_type == "unchanged"
        assert current_jobs["job-c"].change_type == "unchanged"

        # No duplicate observation rows: job-a and job-c each got exactly
        # one new observation row for scan 2; job-b got none (its fetch
        # never completed).
        obs_counts = dict(
            session.query(JobObservation.source_job_id, func.count())
            .group_by(JobObservation.source_job_id)
            .all()
        )
        assert obs_counts == {"job-a": 2, "job-b": 1, "job-c": 2}

    # --- Scan 3: resume/re-run, job-b's fetch now succeeds -----------------
    scan3_id = _make_pipeline(sqlite_url, FakeHttpClient()).run()

    with Session() as session:
        scan3 = session.get(ScanRun, scan3_id)
        assert scan3.scan_status == "COMPLETE_WITHIN_SCAN_WINDOW"
        assert scan3.published is True
        assert scan3.count_errors == 0

        # Still exactly 3 jobs in the current projection: no duplicate rows
        # were created for job-b (or anyone else) by the interruption.
        current_jobs = {j.source_job_id: j for j in session.query(JobCurrent).all()}
        assert len(current_jobs) == 3

        # job-b recovered: seen again, absence counter reset, no longer
        # temporarily_not_found.
        assert current_jobs["job-b"].status == "open"
        assert current_jobs["job-b"].change_type == "unchanged"
        assert current_jobs["job-b"].consecutive_absences == 0

        # Total observations after 3 scans: job-a/job-c observed all 3
        # times, job-b observed in scans 1 and 3 only (missed in scan 2) —
        # proves no silent loss (job-b still has history) and no
        # duplication (counts match exactly, nothing double-counted).
        obs_counts = dict(
            session.query(JobObservation.source_job_id, func.count())
            .group_by(JobObservation.source_job_id)
            .all()
        )
        assert obs_counts == {"job-a": 3, "job-b": 2, "job-c": 3}

        # Record versions: job-b's version incremented on both the scan-2
        # absence-marking and the scan-3 recovery, exactly twice — not
        # skipped (loss) and not double-bumped (duplication).
        assert current_jobs["job-b"].record_version == 3  # 1 (new) + 1 (absent) + 1 (recovered)
        assert current_jobs["job-a"].record_version == 3  # new, unchanged, unchanged
