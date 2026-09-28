"""Business logic for GET /health: freshness of the last successful scan
(brief §4.1, §5.1)."""

from __future__ import annotations

from datetime import datetime, timezone

from src.freep_pipeline.storage.repository import JobRepository


class HealthService:
    def __init__(self, repository: JobRepository | None = None) -> None:
        self._repository = repository or JobRepository()

    def get_health(self) -> dict:
        scan = self._repository.get_last_published_scan()
        if scan is None:
            return {
                "status": "no_successful_scan_yet",
                "last_successful_scan_id": None,
                "last_successful_scan_ended_at": None,
                "seconds_since_last_successful_scan": None,
            }

        now = datetime.now(timezone.utc)
        ended_at = scan.ended_at if scan.ended_at.tzinfo else scan.ended_at.replace(tzinfo=timezone.utc)
        age_seconds = (now - ended_at).total_seconds()

        return {
            "status": "ok",
            "last_successful_scan_id": scan.scan_id,
            "last_successful_scan_ended_at": ended_at.isoformat(),
            "seconds_since_last_successful_scan": age_seconds,
        }
