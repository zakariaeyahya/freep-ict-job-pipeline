"""Discovery: fetch Freep's homepage and extract every currently listed
ICT job link.

Freep server-renders a Nuxt app and embeds its full job list — every
segment, not just ICT — as a devalue-encoded JSON payload in
<script id="__NUXT_DATA__">. This reads that payload directly instead of
driving a headless browser: no filter checkbox to click, no scrolling, and
no dependency on client-side rendering behaving a particular way.
"""

from __future__ import annotations

import json
import re
import time

import requests

from config.logging_config import get_logger
from config.settings import (
    FREEP_START_URL,
    HOMEPAGE_COVERAGE_RETRY_ATTEMPTS,
    HOMEPAGE_COVERAGE_RETRY_DELAY_SECONDS,
    HTTP_TIMEOUT_SECONDS,
    HTTP_USER_AGENT,
    ICT_FILTER_LABEL,
)
from src.freep_pipeline.discovery.coverage_checker import CoverageChecker
from src.freep_pipeline.discovery.nuxt_data_decoder import NuxtDataDecoder
from src.freep_pipeline.models.job import RawJobLink

logger = get_logger(__name__)

_NUXT_DATA_SCRIPT_PATTERN = re.compile(
    r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>',
    re.DOTALL,
)


class DiscoveryResult:
    """Discovered links plus the coverage signal for that discovery run
    (AC02/AC03: a measurable, testable coverage check, not an assumption)."""

    def __init__(self, links: list[RawJobLink], coverage_confirmed: bool, displayed_count: int | None) -> None:
        self.links = links
        self.coverage_confirmed = coverage_confirmed
        self.displayed_count = displayed_count


class FreepDiscovery:
    """Discovers every ICT job link currently listed on Freep."""

    def __init__(self) -> None:
        self._decoder = NuxtDataDecoder()
        self._coverage_checker = CoverageChecker()

    def discover_job_links(self) -> DiscoveryResult:
        """Fetch Freep's homepage and return every unique ICT job link,
        plus whether the count found matches what the site itself displays."""
        html = self._fetch_homepage_html()
        raw_array = self._extract_nuxt_data(html)
        decoded = self._decoder.decode(raw_array)

        jobs_by_slug = self._collect_unique_jobs(decoded)
        ict_jobs = [job for job in jobs_by_slug.values() if job.get("segment") == ICT_FILTER_LABEL]

        links = [
            RawJobLink(source_url=self._job_url(job["slug"]), source_job_path=job["slug"])
            for job in ict_jobs
        ]

        displayed_count = self._coverage_checker.extract_displayed_count(html)
        if displayed_count is None:
            displayed_count = self._retry_for_displayed_count()
        coverage_confirmed = self._coverage_checker.check_coverage(
            displayed_count=displayed_count, discovered_count=len(links)
        )

        logger.info(
            "Discovery finished: %d unique ICT job links found (of %d total listed jobs), "
            "coverage_confirmed=%s",
            len(links),
            len(jobs_by_slug),
            coverage_confirmed,
        )
        return DiscoveryResult(links=links, coverage_confirmed=coverage_confirmed, displayed_count=displayed_count)

    def _retry_for_displayed_count(self) -> int | None:
        """Re-fetches the homepage (a fresh request, not a re-parse of the
        same HTML) a few times when the coverage label is missing from a
        response — observed to be a transient Freep rendering issue, not a
        parsing bug (see settings.HOMEPAGE_COVERAGE_RETRY_ATTEMPTS)."""
        for attempt in range(1, HOMEPAGE_COVERAGE_RETRY_ATTEMPTS + 1):
            time.sleep(HOMEPAGE_COVERAGE_RETRY_DELAY_SECONDS)
            logger.info(
                "ICT filter label missing, retrying homepage fetch for coverage count (attempt %d/%d)",
                attempt,
                HOMEPAGE_COVERAGE_RETRY_ATTEMPTS,
            )
            retry_html = self._fetch_homepage_html()
            displayed_count = self._coverage_checker.extract_displayed_count(retry_html)
            if displayed_count is not None:
                return displayed_count
        return None

    def _fetch_homepage_html(self) -> str:
        response = requests.get(
            FREEP_START_URL,
            headers={"User-Agent": HTTP_USER_AGENT},
            timeout=HTTP_TIMEOUT_SECONDS,
        )
        logger.info("HTTP %s -> %s", response.status_code, FREEP_START_URL)
        response.raise_for_status()
        return response.text

    def _extract_nuxt_data(self, html: str) -> list:
        match = _NUXT_DATA_SCRIPT_PATTERN.search(html)
        if not match:
            raise RuntimeError(
                "Could not find <script id=\"__NUXT_DATA__\"> in Freep's homepage response. "
                "The site's rendering may have changed."
            )
        return json.loads(match.group(1))

    def _collect_unique_jobs(self, decoded: object) -> dict[str, dict]:
        """Walk the decoded tree, collect every job-like record, deduped by
        slug (the same job can be referenced from more than one place in
        the tree, e.g. a "featured" list plus the full list)."""
        jobs_by_slug: dict[str, dict] = {}

        def walk(node: object) -> None:
            if isinstance(node, dict):
                if "segment" in node and "slug" in node and "title" in node:
                    jobs_by_slug[node["slug"]] = node
                for value in node.values():
                    walk(value)
            elif isinstance(node, list):
                for value in node:
                    walk(value)

        walk(decoded)
        return jobs_by_slug

    @staticmethod
    def _job_url(slug: str) -> str:
        return f"https://www.freep.nl/opdracht/{slug}"


if __name__ == "__main__":
    discovery = FreepDiscovery()
    result = discovery.discover_job_links()

    print(f"{len(result.links)} ICT job links found (site displays {result.displayed_count})")
    print(f"Coverage confirmed: {result.coverage_confirmed}\n")
    for link in result.links:
        print(" -", link.source_url)
