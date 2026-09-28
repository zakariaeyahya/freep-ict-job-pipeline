"""Derives a job's change_type by comparing content hashes across scans.

Per CLAUDE.md: change_type is one of new, changed, unchanged, closed,
temporarily_not_found, uncertain (AC09). This module only derives the
comparable cases (new/changed/unchanged); closed and
temporarily_not_found are decided by the pipeline once it knows whether a
previously-seen job was absent from the current scan.
"""

from __future__ import annotations

from config.logging_config import get_logger

logger = get_logger(__name__)


class ChangeTracker:
    """Compares content hashes across observations to classify a change."""

    def derive_change_type(self, previous_hash: str | None, new_hash: str) -> str:
        if previous_hash is None:
            return "new"
        if previous_hash != new_hash:
            return "changed"
        return "unchanged"
