"""Discovery: open Freep, select the ICT filter, scroll to load every job,
extract and deduplicate job detail links.

Migrated from the exploration notebook (cells checking the ICT filter
checkbox via JS and extracting `/opdracht/` links). The notebook never
finished the listing pagination — Freep loads more jobs on scroll rather
than through numbered pages, so this scrolls until the discovered job
count stops growing.
"""

from __future__ import annotations

from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

from config.logging_config import get_logger
from config.settings import (
    BROWSER_HEADLESS,
    BROWSER_WAIT_FOR_TIMEOUT_MS,
    FREEP_BASE_URL,
    FREEP_START_URL,
    ICT_FILTER_LABEL,
    JOB_LINK_MARKER,
)
from freep_pipeline.models.job import RawJobLink

logger = get_logger(__name__)

MAX_SCROLL_ATTEMPTS = 20
SCROLL_PAUSE_MS = 1200


class FreepDiscovery:
    """Discovers every ICT job link currently listed on Freep."""

    def __init__(self, max_scroll_attempts: int = MAX_SCROLL_ATTEMPTS) -> None:
        self._max_scroll_attempts = max_scroll_attempts

    async def discover_job_links(self) -> list[RawJobLink]:
        """Select the ICT filter, scroll to load all jobs, return unique links."""
        browser_config = BrowserConfig(headless=BROWSER_HEADLESS, verbose=False)

        async with AsyncWebCrawler(config=browser_config) as crawler:
            config = CrawlerRunConfig(
                js_code=self._select_ict_filter_and_scroll_js(),
                wait_for="body",
            )

            result = await crawler.arun(url=FREEP_START_URL, config=config)

            if not result.success:
                logger.error("Discovery crawl failed: %s", result.error_message)
                raise RuntimeError(f"Freep discovery crawl failed: {result.error_message}")

            links = self._extract_job_links(result.html)
            logger.info("Discovery finished: %d unique ICT job links found", len(links))
            return links

    def _extract_job_links(self, html: str) -> list[RawJobLink]:
        """Parse the rendered listing HTML into unique job links."""
        soup = BeautifulSoup(html, "html.parser")

        seen: dict[str, RawJobLink] = {}
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]
            if JOB_LINK_MARKER not in href:
                continue

            path = href if href.startswith("/") else href.replace(FREEP_BASE_URL, "", 1)
            url = href if href.startswith("http") else FREEP_BASE_URL + href

            if path not in seen:
                seen[path] = RawJobLink(source_url=url, source_job_path=path)

        return list(seen.values())

    @staticmethod
    def _select_ict_filter_and_scroll_js() -> str:
        """JS run in-page: check the ICT filter, then scroll until the job
        count stops growing (Freep loads more jobs on scroll, not via
        numbered pages)."""
        return f"""
            const checkbox = document.querySelector(
                'input[value="{ICT_FILTER_LABEL}"]'
            );
            if (!checkbox) {{
                throw new Error("ICT filter checkbox not found");
            }}
            if (!checkbox.checked) {{
                checkbox.click();
            }}
            await new Promise(resolve => setTimeout(resolve, {SCROLL_PAUSE_MS}));

            let previousCount = -1;
            let attempts = 0;

            while (attempts < {MAX_SCROLL_ATTEMPTS}) {{
                const currentCount = document.querySelectorAll(
                    'a[href*="{JOB_LINK_MARKER}"]'
                ).length;

                console.log("scroll attempt", attempts, "jobs visible:", currentCount);

                if (currentCount === previousCount) {{
                    break;
                }}

                previousCount = currentCount;
                window.scrollTo(0, document.body.scrollHeight);
                await new Promise(resolve => setTimeout(resolve, {SCROLL_PAUSE_MS}));
                attempts += 1;
            }}
        """
