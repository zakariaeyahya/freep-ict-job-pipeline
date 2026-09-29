"""Maps a persisted ScanRun (+ its routes/errors) onto the published
ScanRun contract shape (scan_run.schema.json, mirroring
freep-ict-job-pipeline/src/lib/contracts/scan.ts).

convergence_rounds is always emitted empty: the pipeline does not model
convergence rounds yet (only one known route today — see CLAUDE.md "Not
done yet"), so there is nothing real to report. Emitting [] keeps the
contract's required field present without fabricating data.
"""

from __future__ import annotations

from typing import Any


class ScanRunMapper:
    def to_scan_run(self, scan: Any) -> dict:
        return {
            "scan_id": scan.scan_id,
            "started_at": scan.started_at.isoformat(),
            "ended_at": scan.ended_at.isoformat() if scan.ended_at is not None else None,
            "config": scan.config,
            "routes": [self._route(route) for route in scan.routes],
            "convergence_rounds": [],
            "counts": self._counts(scan),
            "dedup_rule": scan.dedup_rule,
            "scan_status": scan.scan_status,
            "published": {"value": scan.published, "reason": scan.published_reason},
            "errors": [self._error(error) for error in scan.errors],
        }

    @staticmethod
    def _route(route: Any) -> dict:
        return {
            "url": route.url,
            "pages_visited": route.pages_visited,
            "result": route.result,
            "error": route.error,
        }

    @staticmethod
    def _error(error: Any) -> dict:
        return {
            "reference": error.reference,
            "reason": error.reason,
            "retry_count": error.retry_count,
            "recovery_status": error.recovery_status,
        }

    @staticmethod
    def _counts(scan: Any) -> dict:
        return {
            "discovered": scan.count_discovered,
            "processed": scan.count_processed,
            "duplicates": scan.count_duplicates,
            "new": scan.count_new,
            "changed": scan.count_changed,
            "closed": scan.count_closed,
            "temporarily_not_found": scan.count_temporarily_not_found,
            "errors": scan.count_errors,
        }
