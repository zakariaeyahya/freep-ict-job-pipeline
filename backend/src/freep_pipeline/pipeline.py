"""Orchestrates one full scan run: discover, fetch, parse, validate, store,
and record a scan report (AC01, AC10, AC11, AC12, AC14).

Migrated from the notebook's orchestration cell (cell 27: loop over all
discovered URLs, fetch + parse each one).
"""

from __future__ import annotations

import hashlib
import time
import uuid
from datetime import datetime, timezone

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
from src.freep_pipeline.validation.validator import JobValidator

logger = get_logger(__name__)

DEDUP_RULE = "unique by Freep job slug"
DISCOVERY_CONFIG = "freep-ict-nuxt-data-v1"


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
    ) -> None:
        self._discovery = discovery or FreepDiscovery()
        self._http_client = http_client or FreepHttpClient()
        self._parser = parser or JobParser()
        self._validator = validator or JobValidator()
        self._repository = repository or JobRepository()
        self._schema_validator = schema_validator or job_record_validator()
        self._record_mapper = record_mapper or JobRecordMapper()
        self._field_extractor = field_extractor or LlmFieldExtractor()

    def run(self) -> str:
        """Run one full scan: discover links, fetch+parse each job, validate,
        store, and persist a scan report. Returns the scan_id."""
        report = ScanReport(
            scan_id=self._generate_scan_id(),
            started_at=datetime.now(timezone.utc),
            config=DISCOVERY_CONFIG,
            dedup_rule=DEDUP_RULE,
        )
        logger.info("Starting scan %s", report.scan_id)

        self._repository.create_schema()

        links = self._discover(report)
        parsed_jobs = self._fetch_and_parse_all(links, report)
        discovery_route_succeeded = any(route.result != "failed" for route in report.routes)

        results = self._validator.validate_batch(parsed_jobs)
        valid_jobs = [r.job for r in results if r.is_valid]
        for r in results:
            if not r.is_valid:
                report.add_error(r.job.source_job_id, "; ".join(r.errors))

        report.counts.discovered = len(links)
        report.counts.processed = len(parsed_jobs)

        schema_violation_count = 0
        for job in valid_jobs:
            content_hash = self._compute_content_hash(job)
            self._repository.save_observation(job, scan_id=report.scan_id, content_hash=content_hash)
            change_type, current = self._repository.upsert_current(job, content_hash=content_hash)
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

        for index, link in enumerate(links, start=1):
            logger.info("[%d/%d] fetching %s", index, len(links), link.source_url)
            try:
                soup = self._http_client.get_detail_soup(link.source_url)
                job = self._parser.parse(soup, link.source_url)
                self._enrich_with_llm_fields(job)
                parsed_jobs.append(job)
            except Exception as exc:
                logger.exception("Failed to fetch/parse %s", link.source_url)
                report.add_error(link.source_job_path, str(exc))

            time.sleep(HTTP_REQUEST_DELAY_SECONDS)

        return parsed_jobs

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
    def _generate_scan_id() -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
        return f"scan_{timestamp}_{uuid.uuid4().hex[:6]}"


if __name__ == "__main__":
    pipeline = ScanPipeline()
    scan_id = pipeline.run()
    print(f"Scan complete: {scan_id}")
