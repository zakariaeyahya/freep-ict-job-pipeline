"""Parses a Freep job detail page (BeautifulSoup tree) into a ParsedJob.

Migrated from the notebook's `parse_job_detail` (cell 25), the most
complete version of the parser explored there.
"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup, Tag

from config.logging_config import get_logger
from config.settings import KNOWN_PROVINCES
from freep_pipeline.models.job import ParsedJob

logger = get_logger(__name__)

_DATE_PATTERN = re.compile(r"^\d{1,2} [A-Za-z]+ \d{4}$")


class JobParser:
    """Extracts structured job data from a Freep job detail page."""

    def parse(self, soup: BeautifulSoup, url: str) -> ParsedJob:
        title, company = self._extract_title_and_company(soup)
        rate, province, hours_per_week, segment = self._extract_info_items(soup)
        start_date, end_date = self._extract_dates(soup)
        description = self._extract_description(soup)
        requirements = self._extract_labeled_list(soup, "de eisen")
        wishes = self._extract_labeled_list(soup, "de wensen")

        job = ParsedJob(
            source_job_id=self._extract_source_job_id(url),
            source_url=url,
            title=title,
            company=company,
            rate=rate,
            province=province,
            segment=segment,
            hours_per_week=hours_per_week,
            start_date=start_date,
            end_date=end_date,
            description_original=description,
            hard_requirements=requirements,
            wishes=wishes,
        )

        logger.debug("Parsed job %s: %s", job.source_job_id, job.title)
        return job

    @staticmethod
    def _clean_text(element: Tag | None) -> str | None:
        if not element:
            return None
        return element.get_text(" ", strip=True) or None

    def _extract_list_items(self, elements: list[Tag]) -> list[str]:
        return [text for e in elements if (text := self._clean_text(e))]

    def _extract_title_and_company(self, soup: BeautifulSoup) -> tuple[str | None, str | None]:
        title_element = soup.select_one("h1")
        title = self._clean_text(title_element)

        company = None
        if title_element and title_element.parent:
            company_element = title_element.parent.select_one("p")
            company = self._clean_text(company_element)

        return title, company

    def _extract_info_items(
        self, soup: BeautifulSoup
    ) -> tuple[str | None, str | None, str | None, str | None]:
        info_items = soup.select("ul.mt-8 > li")

        rate = province = hours_per_week = segment = None

        for item in info_items:
            text = self._clean_text(item)
            if not text:
                continue

            if "€" in text and "uur" in text:
                rate = text
            elif "uur per week" in text:
                hours_per_week = text
            elif item.select_one("a[href^='/opdrachten/']"):
                segment = self._clean_text(item.select_one("a"))
            elif text in KNOWN_PROVINCES:
                province = text

        return rate, province, hours_per_week, segment

    def _extract_dates(self, soup: BeautifulSoup) -> tuple[str | None, str | None]:
        info_items = soup.select("ul.mt-8 > li")

        dates = [
            text
            for item in info_items
            if (text := self._clean_text(item)) and _DATE_PATTERN.match(text)
        ]

        start_date = dates[0] if len(dates) >= 1 else None
        end_date = dates[1] if len(dates) >= 2 else None
        return start_date, end_date

    def _extract_description(self, soup: BeautifulSoup) -> str | None:
        heading = soup.find(
            lambda tag: tag.name in ("h2", "h3") and "opdracht" in tag.get_text(" ", strip=True).lower()
        )
        if not heading:
            return None

        container = heading.find_next("div", class_=lambda x: x and "prose-base" in x)
        return self._clean_text(container) if container else None

    def _extract_labeled_list(self, soup: BeautifulSoup, label: str) -> list[str]:
        heading = soup.find(
            lambda tag: tag.name == "h4" and tag.get_text(" ", strip=True).lower() == label
        )
        if not heading:
            return []

        ul = heading.find_next("ul")
        if not ul:
            return []

        return self._extract_list_items(ul.find_all("li", recursive=False))

    @staticmethod
    def _extract_source_job_id(url: str) -> str:
        return url.rstrip("/").split("/")[-1]
