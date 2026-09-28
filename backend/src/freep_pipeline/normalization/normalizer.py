"""Normalizes free-text fields into structured values.

Per CLAUDE.md: "Normalised values always sit next to their original text"
— this never replaces the original text, only derives additional fields
from it.
"""

from __future__ import annotations

import re

from config.logging_config import get_logger

logger = get_logger(__name__)

_RATE_PATTERN = re.compile(r"(\d+)\s*-\s*(\d+)")
_HOURS_PATTERN = re.compile(r"(\d+)\s*-\s*(\d+)\s*uur per week")
_SINGLE_HOURS_PATTERN = re.compile(r"(\d+)\s*uur per week")


class JobNormalizer:
    """Derives structured min/max values from Freep's free-text fields."""

    def normalize_rate(self, rate_text: str | None) -> tuple[int | None, int | None]:
        if not rate_text:
            return None, None

        match = _RATE_PATTERN.search(rate_text)
        if not match:
            return None, None

        return int(match.group(1)), int(match.group(2))

    def normalize_hours(self, hours_text: str | None) -> tuple[int | None, int | None]:
        if not hours_text:
            return None, None

        range_match = _HOURS_PATTERN.search(hours_text)
        if range_match:
            return int(range_match.group(1)), int(range_match.group(2))

        single_match = _SINGLE_HOURS_PATTERN.search(hours_text)
        if single_match:
            hours = int(single_match.group(1))
            return hours, hours

        return None, None
