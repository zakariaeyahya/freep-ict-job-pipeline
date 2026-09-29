"""AC14: the pipeline must never publish a new production version when a
critical validation fails, even if the scan otherwise completed cleanly
(brief §6.2 FAILED row: "Do not publish a new production version"; §7
Quality Goals: schema validation of every published record in CI).

Uses the same real-pipeline-against-SQLite setup as test_scan_recovery.py,
but injects a JobRecordMapper that produces schema-invalid records (an
illegal change_type) to prove the block actually triggers on a genuine
schema violation, not just on discovery/fetch failures already covered by
AC10/AC11 tests.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.freep_pipeline.contracts.job_record_mapper import JobRecordMapper
from src.freep_pipeline.contracts.schema_validator import job_record_validator
from src.freep_pipeline.discovery.freep_discovery import DiscoveryResult
from src.freep_pipeline.extraction.llm_field_extractor import ExtractedFields
from src.freep_pipeline.models.job import ParsedJob, RawJobLink
from src.freep_pipeline.pipeline import ScanPipeline
from src.freep_pipeline.storage.repository import JobRepository
from src.freep_pipeline.storage.scan_models import ScanRun
from src.freep_pipeline.validation.validator import JobValidator

JOB_SLUGS = ["job-a", "job-b"]


class _NoOpFieldExtractor:
    """Stands in for LlmFieldExtractor so this suite never makes a real
    network call to Ollama — it tests publish-blocking, not extraction."""

    def extract(self, title, hard_requirements, wishes) -> ExtractedFields:
        return ExtractedFields()


def _job_url(slug: str) -> str:
    return f"https://www.freep.nl/opdracht/{slug}"


def _make_job(slug: str) -> ParsedJob:
    return ParsedJob(
        source_job_id=slug,
        source_url=_job_url(slug),
        title="AI Developer",
        company="Acme Consulting",
        description_original="Build and maintain tooling.",
        segment="ICT Informatievoorziening",
        province="Utrecht",
    )


class FakeDiscovery:
    def discover_job_links(self) -> DiscoveryResult:
        links = [RawJobLink(source_url=_job_url(slug), source_job_path=slug) for slug in JOB_SLUGS]
        return DiscoveryResult(links=links, coverage_confirmed=True, displayed_count=len(links))


class FakeHttpClient:
    def get_detail_soup(self, url: str):
        return url


class FakeParser:
    def parse(self, soup, url: str) -> ParsedJob:
        slug = url.rstrip("/").rsplit("/", 1)[-1]
        return _make_job(slug)


class SchemaBreakingMapper(JobRecordMapper):
    """Same mapping as production, except it emits an illegal change_type
    not in the schema's enum — simulating a mapping bug that would
    otherwise silently corrupt what gets published."""

    def to_job_record(self, job) -> dict:
        record = super().to_job_record(job)
        record["change_type"] = "deleted"  # not a valid ChangeType value
        return record


@pytest.fixture()
def sqlite_url(tmp_path) -> str:
    db_path = tmp_path / "publish_blocking_test.db"
    return f"sqlite:///{db_path}"


def _make_pipeline(sqlite_url: str, record_mapper) -> ScanPipeline:
    return ScanPipeline(
        discovery=FakeDiscovery(),
        http_client=FakeHttpClient(),
        parser=FakeParser(),
        validator=JobValidator(),
        repository=JobRepository(database_url=sqlite_url),
        schema_validator=job_record_validator(),
        record_mapper=record_mapper,
        field_extractor=_NoOpFieldExtractor(),
    )


def test_schema_violation_blocks_publication_even_when_scan_otherwise_complete(sqlite_url: str) -> None:
    scan_id = _make_pipeline(sqlite_url, SchemaBreakingMapper()).run()

    engine = create_engine(sqlite_url)
    with sessionmaker(bind=engine)() as session:
        scan = session.get(ScanRun, scan_id)

        # Coverage succeeded, both jobs fetched and parsed without error —
        # by AC11 alone this would have been COMPLETE_WITHIN_SCAN_WINDOW.
        # The schema violation must override that and block publication.
        assert scan.published is False
        assert "schema validation" in scan.published_reason
        assert scan.count_errors == len(JOB_SLUGS)
        assert all("schema validation" in e.reason for e in scan.errors)


def test_valid_mapper_publishes_normally_for_comparison(sqlite_url: str) -> None:
    """Control case: with the real (non-breaking) mapper, the same scan
    publishes normally — proving the block above is specific to the
    schema violation, not a side effect of the test setup."""
    scan_id = _make_pipeline(sqlite_url, JobRecordMapper()).run()

    engine = create_engine(sqlite_url)
    with sessionmaker(bind=engine)() as session:
        scan = session.get(ScanRun, scan_id)

        assert scan.scan_status == "COMPLETE_WITHIN_SCAN_WINDOW"
        assert scan.published is True
        assert scan.count_errors == 0
