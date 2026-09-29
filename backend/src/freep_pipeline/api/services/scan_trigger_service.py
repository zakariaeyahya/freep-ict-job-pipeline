"""Business logic for POST /api/v1/scans/trigger — the manual "run scan
now" action (brief §9.2, Scheduler responsibility: "starts scheduled and
manual scans"). Routes call this; it never talks HTTP directly.

A scan can take minutes (route discovery + one fetch per job with a
self-imposed delay, plus LLM-assisted extraction) — far too long for an
HTTP request/response cycle. The scan therefore runs on a background
thread; this endpoint only starts it and returns immediately. Callers
poll GET /api/v1/scans (or /health) to see the new scan appear once it
finishes — there is no separate "scan status" endpoint, since a scan's
own record in scan_runs already carries its status once it exists.
"""

from __future__ import annotations

import threading

from sqlalchemy import create_engine, text

from config.logging_config import get_logger
from config.settings import DATABASE_URL
from src.freep_pipeline.api.services.scan_progress import ScanProgressTracker, get_scan_progress_tracker
from src.freep_pipeline.pipeline import ScanPipeline
from src.freep_pipeline.storage.scan_lock import SCAN_LOCK_KEY

logger = get_logger(__name__)


class ScanAlreadyRunningError(Exception):
    """Raised when a scan is requested while another one already holds the
    lock — surfaced as 409, not 500: the caller did nothing wrong, they
    just need to wait or check the in-progress scan."""


class ScanTriggerService:
    def __init__(self, progress_tracker: ScanProgressTracker | None = None) -> None:
        self._progress_tracker = progress_tracker or get_scan_progress_tracker()

    def trigger_scan(self) -> None:
        """Best-effort, non-blocking check for a scan already in progress,
        so a caller clicking "run scan" gets immediate feedback instead of
        silently starting a run that will fail once it actually tries to
        acquire the lock. This check-then-start has a small race window
        (the real, authoritative lock is the one ScanPipeline.run() takes
        on its own connection inside the background thread) — acceptable
        here because the cost of losing the race is just a background
        thread that logs ScanAlreadyRunningError and exits, not corrupted
        data."""
        if self._scan_appears_to_be_running():
            raise ScanAlreadyRunningError("A scan is already running")

        thread = threading.Thread(target=self._run_scan_in_background, daemon=True)
        thread.start()

    @staticmethod
    def _scan_appears_to_be_running() -> bool:
        engine = create_engine(DATABASE_URL)
        try:
            with engine.connect() as connection:
                acquired = connection.execute(
                    text("SELECT pg_try_advisory_lock(:key)"), {"key": SCAN_LOCK_KEY}
                ).scalar()
                if acquired:
                    connection.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": SCAN_LOCK_KEY})
                return not acquired
        finally:
            engine.dispose()

    def _run_scan_in_background(self) -> None:
        try:
            scan_id = ScanPipeline(progress_reporter=self._progress_tracker).run()
            logger.info("Manually triggered scan finished: %s", scan_id)
        except Exception:
            # Never let a background-thread exception vanish silently —
            # log it with a full traceback. The caller already got a 202
            # and has no request left to receive an error on; GET /scans
            # not showing a new scan is the caller-visible signal.
            logger.exception("Manually triggered scan failed")
