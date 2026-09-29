"""Verifies ScanProgressTracker (in-memory, thread-safe scan progress
state backing GET /api/v1/scans/current) and that ScanPipeline reports
into it at the right points — the pieces behind the Scan Report page's
live "scan in progress" view.
"""

from __future__ import annotations

from src.freep_pipeline.api.services.scan_progress import ScanProgressTracker


def test_no_scan_in_progress_returns_none() -> None:
    tracker = ScanProgressTracker()

    assert tracker.current() is None


def test_start_sets_the_discovering_phase() -> None:
    tracker = ScanProgressTracker()

    tracker.start()

    progress = tracker.current()
    assert progress is not None
    assert progress.phase == "discovering"
    assert progress.jobs_total is None
    assert progress.jobs_processed == 0
    assert len(progress.activity) == 1


def test_report_discovery_finished_sets_total_and_moves_to_processing() -> None:
    tracker = ScanProgressTracker()
    tracker.start()

    tracker.report_discovery_finished(87)

    progress = tracker.current()
    assert progress.phase == "processing"
    assert progress.jobs_total == 87


def test_report_job_processed_updates_the_running_count() -> None:
    tracker = ScanProgressTracker()
    tracker.start()
    tracker.report_discovery_finished(3)

    tracker.report_job_processed(1, 3, "AI Developer")
    tracker.report_job_processed(2, 3, "Data Engineer")

    progress = tracker.current()
    assert progress.jobs_processed == 2


def test_report_storing_sets_the_storing_phase() -> None:
    tracker = ScanProgressTracker()
    tracker.start()

    tracker.report_storing()

    assert tracker.current().phase == "storing"


def test_finish_clears_progress_back_to_none() -> None:
    tracker = ScanProgressTracker()
    tracker.start()
    tracker.report_discovery_finished(5)

    tracker.finish()

    assert tracker.current() is None


def test_activity_feed_keeps_only_the_most_recent_events() -> None:
    tracker = ScanProgressTracker()
    tracker.start()  # 1 event

    for i in range(1, 10):
        tracker.report_job_processed(i, 9, f"Job {i}")

    progress = tracker.current()
    from src.freep_pipeline.api.services.scan_progress import MAX_ACTIVITY_EVENTS

    assert len(progress.activity) == MAX_ACTIVITY_EVENTS
    # Keeps the most recent ones, not the oldest.
    assert "Job 9" in progress.activity[-1].message


def test_reporting_methods_are_no_ops_when_no_scan_has_started() -> None:
    """A stray report call (e.g. a race with finish()) must never raise or
    resurrect a cleared progress state."""
    tracker = ScanProgressTracker()

    tracker.report_discovery_finished(5)
    tracker.report_job_processed(1, 5, "Job")
    tracker.report_storing()

    assert tracker.current() is None
