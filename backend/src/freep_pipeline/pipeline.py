"""Orchestrates one full scan run: discover, fetch, parse, validate, store,
and record a scan report (AC01, AC10, AC11, AC12, AC14).

Migrated from the notebook's orchestration cell (cell 27: loop over all
discovered URLs, fetch + parse each one).
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from config.logging_config import get_logger
from config.settings import FREEP_START_URL, HTTP_REQUEST_DELAY_SECONDS
from src.freep_pipeline.contracts.job_record_mapper import JobRecordMapper
from src.freep_pipeline.contracts.schema_validator import SchemaValidator, job_record_validator
from src.freep_pipeline.discovery.freep_discovery import FreepDiscovery
from src.freep_pipeline.extraction.llm_field_extractor import LlmFieldExtractor
from src.freep_pipeline.fetching.http_client import FreepHttpClient
from src.freep_pipeline.models.job import ParsedJob, RawJobLink
from src.freep_pipeline.models.scan import RouteVisit, ScanReport
from src.freep_pipeline.parsing.job_parser import JobParser
from src.freep_pipeline.storage.repository import JobRepository
from src.freep_pipeline.storage.scan_lock import scan_lock
from src.freep_pipeline.validation.validator import JobValidator

logger = get_logger(__name__)

DEDUP_RULE = "unique by Freep job slug"
DISCOVERY_CONFIG = "freep-ict-nuxt-data-v1"


class NullProgressReporter:
    """Default no-op progress reporter — ScanPipeline never needs to know
    whether anything is actually listening. The real listener
    (api/services/scan_progress.py's ScanProgressTracker) lives in the API
    layer and is injected only when a scan is started through the API's
    "run scan now" trigger; the CLI (scripts/scrape.py) and every test use
    this no-op instead, keeping the pipeline itself free of any API-layer
    import."""

    def start(self) -> None:
        pass

    def report_discovery_finished(self, jobs_total: int) -> None:
        pass

    def report_job_processed(self, index: int, total: int, title: str | None) -> None:
        pass

    def report_storing(self) -> None:
        pass

    def finish(self) -> None:
        pass


class ScanPipeline:
    """Runs one discovery-to-storage pass over Freep's ICT jobs."""

    def __init__(
        self,
        discovery: FreepDiscovery | None = None,
        http_client: FreepHttpClient | None = None,
        parser: JobParser | None = None,
        validator: JobValidator | None = None,
        repository: JobRepository | None = None,
        schema_validator: SchemaValidator | None = None,
        record_mapper: JobRecordMapper | None = None,
        field_extractor: LlmFieldExtractor | None = None,
        # Any, not NullProgressReporter: ScanProgressTracker (api layer) is
        # passed here too and only shares this class's method signatures
        # by duck typing, not inheritance — keeps ScanPipeline free of any
        # api-layer import.
        progress_reporter: Any | None = None,
    ) -> None:
        self._discovery = discovery or FreepDiscovery()
        self._http_client = http_client or FreepHttpClient()
        self._parser = parser or JobParser()
        self._validator = validator or JobValidator()
        self._repository = repository or JobRepository()
        self._schema_validator = schema_validator or job_record_validator()
        self._record_mapper = record_mapper or JobRecordMapper()
        self._field_extractor = field_extractor or LlmFieldExtractor()
        self._progress = progress_reporter or NullProgressReporter()

    def run(self) -> str:
        """Run one full scan: discover links, fetch+parse each job, validate,
        store, and persist a scan report. Returns the scan_id.

        Raises ScanAlreadyRunningError immediately (before doing any work)
        if another scan already holds the lock on this database (brief
        §9.2: "prevents conflicting runs") — two concurrent scans writing
        to the same jobs_current projection is exactly the kind of
        conflict AC10's recovery guarantees assume can't happen."""
        with scan_lock(self._repository.engine):
            return self._run_locked()

    def _run_locked(self) -> str:
        self._progress.start()
        try:
            return self._run_locked_and_tracked()
        finally:
            self._progress.finish()

    def _run_locked_and_tracked(self) -> str:
        report = ScanReport(
            scan_id=self._generate_scan_id(),
            started_at=datetime.now(timezone.utc),
            config=DISCOVERY_CONFIG,
            dedup_rule=DEDUP_RULE,
        )
        logger.info("Starting scan %s", report.scan_id)

        self._repository.create_schema()

        links = self._discover(report)
        self._progress.report_discovery_finished(len(links))
        parsed_jobs = self._fetch_and_parse_all(links, report)
        discovery_route_succeeded = any(route.result != "failed" for route in report.routes)

        results = self._validator.validate_batch(parsed_jobs)
        valid_jobs = [r.job for r in results if r.is_valid]
        for r in results:
            if not r.is_valid:
                report.add_error(r.job.source_job_id, "; ".join(r.errors))

        report.counts.discovered = len(links)
        report.counts.processed = len(parsed_jobs)

        self._progress.report_storing()

        schema_violation_count = 0
        for job in valid_jobs:
            content_hash = self._compute_content_hash(job)
            source_hash = self._compute_source_hash(job)
            self._repository.save_observation(job, scan_id=report.scan_id, content_hash=content_hash)
            change_type, current = self._repository.upsert_current(
                job, content_hash=content_hash, source_hash=source_hash
            )
            self._count_change(report, change_type)

            schema_result = self._schema_validator.validate(self._record_mapper.to_job_record(current))
            if not schema_result.is_valid:
                schema_violation_count += 1
                report.add_error(
                    job.source_job_id,
                    f"published record failed schema validation: {'; '.join(schema_result.errors)}",
                )

        # Only mark jobs absent when discovery actually ran — a failed
        # discovery route must never be mistaken for jobs having closed
        # (brief §3.3: a source problem must not silently cause data loss).
        if discovery_route_succeeded:
            seen_ids = {job.source_job_id for job in valid_jobs}
            absence_counts = self._repository.mark_absent_jobs(seen_ids)
            report.counts.temporarily_not_found = absence_counts["temporarily_not_found"]
            report.counts.closed = absence_counts["closed"]

        report.ended_at = datetime.now(timezone.utc)
        report.scan_status = self._determine_scan_status(report, expected_route_count=1)

        # AC14: never publish a new production version when a critical
        # validation fails, even if the scan itself otherwise completed
        # (brief §6.2 FAILED row: "Do not publish a new production
        # version"). A schema violation on a published record is exactly
        # that critical failure — it means the contract every downstream
        # consumer (API, UI, matching tool) relies on was broken.
        if schema_violation_count > 0:
            report.published = False
            report.published_reason = (
                f"{schema_violation_count} published record(s) failed schema validation "
                f"(AC12/AC14) - see errors for detail"
            )
        else:
            report.published = report.scan_status == "COMPLETE_WITHIN_SCAN_WINDOW"
            if not report.published:
                report.published_reason = f"scan_status was {report.scan_status}, not COMPLETE_WITHIN_SCAN_WINDOW"

        self._repository.save_scan_run(report)

        logger.info(
            "Scan %s finished: status=%s discovered=%d processed=%d valid=%d errors=%d",
            report.scan_id,
            report.scan_status,
            report.counts.discovered,
            report.counts.processed,
            len(valid_jobs),
            report.counts.errors,
        )
        return report.scan_id

    def _discover(self, report: ScanReport) -> list[RawJobLink]:
        """Fetch the one known source route (Freep's homepage __NUXT_DATA__
        payload) and record its outcome, per AC01/AC02.

        A route only counts as "success" when coverage is confirmed — i.e.
        the number of jobs found matches what Freep itself displays for the
        ICT filter (AC03). If the fetch worked but coverage could not be
        confirmed, the route is "partial", not "success": we cannot
        demonstrate we found everything."""
        try:
            result = self._discovery.discover_job_links()
            route_result = "success" if result.coverage_confirmed else "partial"
            error = (
                None
                if result.coverage_confirmed
                else f"coverage not confirmed: found {len(result.links)}, site displays {result.displayed_count}"
            )
            report.routes.append(
                RouteVisit(url=FREEP_START_URL, pages_visited=1, result=route_result, error=error)
            )
            if not result.coverage_confirmed:
                report.add_error(FREEP_START_URL, error)
            return result.links
        except Exception as exc:
            logger.exception("Discovery failed")
            report.routes.append(
                RouteVisit(url=FREEP_START_URL, pages_visited=0, result="failed", error=str(exc))
            )
            report.add_error(FREEP_START_URL, str(exc))
            return []

    def _fetch_and_parse_all(self, links: list[RawJobLink], report: ScanReport) -> list[ParsedJob]:
        parsed_jobs: list[ParsedJob] = []
        total = len(links)

        for index, link in enumerate(links, start=1):
            logger.info("[%d/%d] fetching %s", index, total, link.source_url)
            title: str | None = None
            try:
                soup = self._http_client.get_detail_soup(link.source_url)
                job = self._parser.parse(soup, link.source_url)
                title = job.title
                self._enrich_with_llm_fields_unless_source_unchanged(job)
                parsed_jobs.append(job)
            except Exception as exc:
                logger.exception("Failed to fetch/parse %s", link.source_url)
                report.add_error(link.source_job_path, str(exc))

            self._progress.report_job_processed(index, total, title)
            time.sleep(HTTP_REQUEST_DELAY_SECONDS)

        return parsed_jobs

    def _enrich_with_llm_fields_unless_source_unchanged(self, job: ParsedJob) -> None:
        """Skips the LLM call entirely when this job's HTML-parsed content
        is byte-for-byte identical to the last scan's — re-running
        extraction on unchanged text would always produce the same
        grounded result anyway (temperature=0), so it's pure wasted time
        (OpenAI/Groq latency). Reuses the previous observation's
        LLM-derived fields instead of leaving them empty."""
        source_hash = self._compute_source_hash(job)
        existing = self._repository.get_current_job(job.source_job_id)

        if existing is not None and existing.source_hash == source_hash:
            logger.info("Source unchanged for %s, reusing previous LLM extraction", job.source_job_id)
            job.education = existing.education
            job.experience = existing.experience
            job.skills = existing.skills
            job.methods = existing.methods
            job.certifications = existing.certifications
            job.languages = existing.languages
            job.contract_type = job.contract_type or existing.contract_type
            job.zzp_allowed = existing.zzp_allowed
            job.screening = existing.screening
            job.vog = existing.vog
            job.positions = existing.positions
            job.max_candidates = existing.max_candidates
            return

        self._enrich_with_llm_fields(job)

    def _enrich_with_llm_fields(self, job: ParsedJob) -> None:
        """Best-effort: never blocks or fails the scan if the LLM is down
        or returns something ungrounded (LlmFieldExtractor already
        verifies every value against the source text)."""
        extracted = self._field_extractor.extract(
            title=job.title or "", hard_requirements=job.hard_requirements, wishes=job.wishes
        )
        job.education = extracted.education
        job.experience = extracted.experience
        job.skills = extracted.skills
        job.methods = extracted.methods
        job.certifications = extracted.certifications
        job.languages = extracted.languages
        # contract_type: the parser's HTML badge extraction (a real
        # structured field, not a guess) takes priority over the LLM's
        # text-based inference — only fall back to the LLM's finding if
        # the parser found no badge on the page.
        job.contract_type = job.contract_type or extracted.contract_type
        job.zzp_allowed = extracted.zzp_allowed
        job.screening = extracted.screening
        job.vog = extracted.vog
        job.positions = extracted.positions
        job.max_candidates = extracted.max_candidates

    @staticmethod
    def _count_change(report: ScanReport, change_type: str) -> None:
        if change_type == "new":
            report.counts.new += 1
        elif change_type == "changed":
            report.counts.changed += 1
        # "unchanged" is not tracked as a separate counter in ScanCounts —
        # only transitions that matter operationally are counted.

    @staticmethod
    def _determine_scan_status(report: ScanReport, expected_route_count: int) -> str:
        """AC11: complete only if every known route succeeded and processing
        covered every discovered job without unexplained gaps."""
        all_routes_succeeded = (
            len(report.routes) == expected_route_count
            and all(route.result == "success" for route in report.routes)
        )
        all_discovered_processed = report.counts.processed >= report.counts.discovered

        if not report.routes or all(route.result == "failed" for route in report.routes):
            return "FAILED"
        if all_routes_succeeded and all_discovered_processed and report.counts.errors == 0:
            return "COMPLETE_WITHIN_SCAN_WINDOW"
        return "INCOMPLETE"

    @staticmethod
    def _compute_content_hash(job: ParsedJob) -> str:
        payload = job.model_dump_json()
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _compute_source_hash(job: ParsedJob) -> str:
        """Hashes only the fields JobParser extracts directly from HTML —
        never the LLM-derived fields (education/skills/etc.), which don't
        exist yet at the point this is called (before
        _enrich_with_llm_fields_unless_source_unchanged runs). This is
        what "has this job's source content changed since last scan?"
        means for the LLM-skip decision — distinct from content_hash,
        which hashes the full ParsedJob (including LLM output) for AC09's
        change_type classification."""
        source_fields = {
            "title": job.title,
            "company": job.company,
            "rate": job.rate,
            "province": job.province,
            "segment": job.segment,
            "hours_per_week": job.hours_per_week,
            "start_date": job.start_date,
            "end_date": job.end_date,
            "description_original": job.description_original,
            "hard_requirements": job.hard_requirements,
            "wishes": job.wishes,
            "contract_type": job.contract_type,
        }
        payload = json.dumps(source_fields, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _generate_scan_id() -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
        return f"scan_{timestamp}_{uuid.uuid4().hex[:6]}"


if __name__ == "__main__":
    pipeline = ScanPipeline()
    scan_id = pipeline.run()
    print(f"Scan complete: {scan_id}")
