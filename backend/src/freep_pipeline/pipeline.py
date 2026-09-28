"""Orchestrates one full scan run: discover, fetch, parse, validate, store.

Migrated from the notebook's orchestration cell (cell 27: loop over all
discovered URLs, fetch + parse each one).
"""

from __future__ import annotations

import hashlib
import time
import uuid
from datetime import datetime, timezone

from config.logging_config import get_logger
from config.settings import HTTP_REQUEST_DELAY_SECONDS
from src.freep_pipeline.discovery.freep_discovery import FreepDiscovery
from freep_pipeline.fetching.http_client import FreepHttpClient
from freep_pipeline.models.job import ParsedJob
from freep_pipeline.parsing.job_parser import JobParser
from freep_pipeline.storage.repository import JobRepository
from freep_pipeline.validation.validator import JobValidator

logger = get_logger(__name__)


class ScanPipeline:
    """Runs one discovery-to-storage pass over Freep's ICT jobs."""

    def __init__(
        self,
        discovery: FreepDiscovery | None = None,
        http_client: FreepHttpClient | None = None,
        parser: JobParser | None = None,
        validator: JobValidator | None = None,
        repository: JobRepository | None = None,
    ) -> None:
        self._discovery = discovery or FreepDiscovery()
        self._http_client = http_client or FreepHttpClient()
        self._parser = parser or JobParser()
        self._validator = validator or JobValidator()
        self._repository = repository or JobRepository()

    async def run(self) -> str:
        """Run one full scan: discover links, fetch+parse each job, validate,
        store. Returns the scan_id."""
        scan_id = self._generate_scan_id()
        logger.info("Starting scan %s", scan_id)

        links = await self._discovery.discover_job_links()
        parsed_jobs = self._fetch_and_parse_all(links)

        results = self._validator.validate_batch(parsed_jobs)
        valid_jobs = [r.job for r in results if r.is_valid]

        self._repository.create_schema()
        for job in valid_jobs:
            content_hash = self._compute_content_hash(job)
            self._repository.save_observation(job, scan_id=scan_id, content_hash=content_hash)
            self._repository.upsert_current(job, content_hash=content_hash)

        logger.info(
            "Scan %s finished: %d discovered, %d parsed, %d valid, %d stored",
            scan_id,
            len(links),
            len(parsed_jobs),
            len(valid_jobs),
            len(valid_jobs),
        )
        return scan_id

    def _fetch_and_parse_all(self, links: list) -> list[ParsedJob]:
        parsed_jobs: list[ParsedJob] = []

        for index, link in enumerate(links, start=1):
            logger.info("[%d/%d] fetching %s", index, len(links), link.source_url)
            try:
                soup = self._http_client.get_detail_soup(link.source_url)
                job = self._parser.parse(soup, link.source_url)
                parsed_jobs.append(job)
            except Exception:
                logger.exception("Failed to fetch/parse %s", link.source_url)

            time.sleep(HTTP_REQUEST_DELAY_SECONDS)

        return parsed_jobs

    @staticmethod
    def _compute_content_hash(job: ParsedJob) -> str:
        payload = job.model_dump_json()
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _generate_scan_id() -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
        return f"scan_{timestamp}_{uuid.uuid4().hex[:6]}"
