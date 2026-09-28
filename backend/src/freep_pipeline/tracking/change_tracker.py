"""Derives a job's change_type and status across scans.

Per CLAUDE.md/AC09: change_type is one of new, changed, unchanged, closed,
temporarily_not_found, uncertain. Per brief §3.3, a single missed
observation is never a deletion — it becomes temporarily_not_found and
only turns into closed after CLOSURE_AFTER_CONSECUTIVE_ABSENCES
consecutive scans without seeing the job again.
"""

from __future__ import annotations

from config.logging_config import get_logger
from config.settings import CLOSURE_AFTER_CONSECUTIVE_ABSENCES

logger = get_logger(__name__)


class ChangeTracker:
    """Compares content hashes and presence across scans to classify a
    job's change_type and status."""

    def derive_change_type(self, previous_hash: str | None, new_hash: str) -> str:
        """For a job that WAS seen in the current scan."""
        if previous_hash is None:
            return "new"
        if previous_hash != new_hash:
            return "changed"
        return "unchanged"

    def derive_absence_state(self, previous_consecutive_absences: int) -> tuple[str, str, int]:
        """For a job that was open but was NOT seen in the current scan.

        Returns (status, change_type, new_consecutive_absences)."""
        absences = previous_consecutive_absences + 1

        if absences >= CLOSURE_AFTER_CONSECUTIVE_ABSENCES:
            return "closed", "closed", absences

        return "unknown", "temporarily_not_found", absences
