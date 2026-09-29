"""In-memory, thread-safe state of the currently running scan, if any —
backs GET /api/v1/scans/trigger's companion read endpoint,
GET /api/v1/scans/current, so the review UI can show live progress
(jobs processed/total, current phase, a short activity feed) instead of
only learning a scan finished once it appears in scan_runs.

Deliberately in-memory, not persisted: this is UI-facing progress, not
part of the durable scan record (scan_runs already captures the final,
authoritative result — see ScanRunModel). If the API process restarts
mid-scan, progress simply resets; the scan itself (running in its own
thread) is unaffected and still writes its real result to the database
when it finishes.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone

MAX_ACTIVITY_EVENTS = 5


@dataclass
class ScanActivityEvent:
    message: str
    at: str  # ISO 8601


@dataclass
class ScanProgress:
    phase: str  # "discovering" | "processing" | "storing"
    jobs_total: int | None
    jobs_processed: int
    activity: list[ScanActivityEvent] = field(default_factory=list)
    started_at: str = ""


class ScanProgressTracker:
    """One process-wide instance (_tracker below) shared between the
    background scan thread (which calls the `report_*` methods) and HTTP
    request threads (which call `current`). A single lock is enough here —
    updates are infrequent (once per job, not per HTTP request) so there's
    no contention worth optimizing away."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._progress: ScanProgress | None = None

    def start(self) -> None:
        with self._lock:
            self._progress = ScanProgress(
                phase="discovering",
                jobs_total=None,
                jobs_processed=0,
                activity=[self._event("Discovering job routes…")],
                started_at=datetime.now(timezone.utc).isoformat(),
            )

    def report_discovery_finished(self, jobs_total: int) -> None:
        with self._lock:
            if self._progress is None:
                return
            self._progress.phase = "processing"
            self._progress.jobs_total = jobs_total
            self._add_event(f"Found {jobs_total} job(s) — fetching details…")

    def report_job_processed(self, index: int, total: int, title: str | None) -> None:
        with self._lock:
            if self._progress is None:
                return
            self._progress.jobs_processed = index
            label = title or "job"
            self._add_event(f"Processed {index}/{total}: {label}")

    def report_storing(self) -> None:
        with self._lock:
            if self._progress is None:
                return
            self._progress.phase = "storing"
            self._add_event("Validating and storing results…")

    def finish(self) -> None:
        with self._lock:
            self._progress = None

    def current(self) -> ScanProgress | None:
        with self._lock:
            return self._progress

    def _add_event(self, message: str) -> None:
        # Caller already holds self._lock — never call this directly from
        # outside this class.
        assert self._progress is not None
        self._progress.activity.append(self._event(message))
        self._progress.activity = self._progress.activity[-MAX_ACTIVITY_EVENTS:]

    @staticmethod
    def _event(message: str) -> ScanActivityEvent:
        return ScanActivityEvent(message=message, at=datetime.now(timezone.utc).isoformat())


_tracker = ScanProgressTracker()


def get_scan_progress_tracker() -> ScanProgressTracker:
    """The single process-wide tracker. Not injected via FastAPI's DI
    (unlike services elsewhere) because it must be the SAME instance the
    background scan thread and every request thread all share — a fresh
    instance per request would defeat the entire point."""
    return _tracker
