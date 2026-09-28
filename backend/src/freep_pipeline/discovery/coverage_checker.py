"""Measures discovery coverage against Freep's own displayed filter count.

Per brief §3.2/AC02/AC03: the engineer must propose a measurable, testable
coverage method, not just assume the crawl found everything. Freep's
listing page shows a segment filter with a count in parentheses, e.g.
<label for="ICT Informatievoorziening">ICT Informatievoorziening (87)</label>.
This reads that displayed count from the raw HTML and compares it against
the number of unique ICT jobs actually discovered, in the SAME response —
no extra request, no dependency on timing between separate scans.

Per brief §1.4, this displayed count is "diagnostic metadata only" and
never determines completeness by itself — it is one input alongside route
coverage and detail-retrieval success (§6.3), not a replacement for them.
"""

from __future__ import annotations

from bs4 import BeautifulSoup

from config.logging_config import get_logger
from config.settings import ICT_FILTER_LABEL

logger = get_logger(__name__)


class CoverageChecker:
    """Compares Freep's displayed filter count to the number of jobs
    actually discovered, as a measurable coverage signal for one scan."""

    def extract_displayed_count(self, html: str) -> int | None:
        """Read the job count Freep itself displays next to the ICT filter
        checkbox. Returns None if the label could not be found (the site's
        markup may have changed)."""
        soup = BeautifulSoup(html, "html.parser")
        label = soup.select_one(f'label[for="{ICT_FILTER_LABEL}"]')

        if not label:
            logger.warning("Could not find the ICT filter label in the page HTML")
            return None

        text = label.get_text(strip=True)
        count = self._parse_count(text)

        if count is None:
            logger.warning("Could not parse a count out of filter label text: %r", text)

        return count

    def check_coverage(self, displayed_count: int | None, discovered_count: int) -> bool:
        """True if the number of jobs discovered matches what Freep itself
        displays for the ICT filter. Logs the comparison either way."""
        if displayed_count is None:
            logger.warning(
                "Coverage check inconclusive: no displayed count available "
                "(discovered=%d)",
                discovered_count,
            )
            return False

        matches = discovered_count == displayed_count
        logger.info(
            "Coverage check: discovered=%d displayed=%d match=%s",
            discovered_count,
            displayed_count,
            matches,
        )
        return matches

    @staticmethod
    def _parse_count(label_text: str) -> int | None:
        start = label_text.rfind("(")
        end = label_text.rfind(")")
        if start == -1 or end == -1 or end < start:
            return None

        digits = label_text[start + 1 : end]
        return int(digits) if digits.isdigit() else None
