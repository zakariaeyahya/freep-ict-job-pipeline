"""Verifies the scan advisory lock (storage/scan_lock.py) actually
prevents two concurrent scans (brief §9.2, Scheduler: "prevents
conflicting runs").

Requires a reachable Postgres server — pg_try_advisory_lock is Postgres-
specific, so this can't be exercised against SQLite. Skipped automatically
if no server is reachable, same pattern as test_migrations.py. Uses the
real DATABASE_URL directly (not a scratch database): an advisory lock is
session-scoped, not tied to any table or data, so this never touches
actual pipeline data.
"""

from __future__ import annotations

import threading

import pytest
from sqlalchemy import create_engine

from config.settings import DATABASE_URL
from src.freep_pipeline.storage.scan_lock import ScanAlreadyRunningError, scan_lock


def _postgres_reachable() -> bool:
    try:
        engine = create_engine(DATABASE_URL)
        engine.connect().close()
        engine.dispose()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _postgres_reachable(),
    reason="Postgres is not reachable — start it (see README.md) to run scan lock tests.",
)


@pytest.fixture()
def engine():
    eng = create_engine(DATABASE_URL)
    try:
        yield eng
    finally:
        eng.dispose()


def test_a_second_lock_attempt_is_rejected_while_the_first_is_held(engine) -> None:
    with scan_lock(engine):
        with pytest.raises(ScanAlreadyRunningError):
            with scan_lock(engine):
                pass  # never reached


def test_the_lock_is_released_after_the_with_block_exits(engine) -> None:
    with scan_lock(engine):
        pass  # first scan finishes normally

    with scan_lock(engine):
        pass  # a second, later scan must be able to acquire it


def test_the_lock_is_released_even_if_the_block_raises(engine) -> None:
    class _SimulatedScanFailure(Exception):
        pass

    with pytest.raises(_SimulatedScanFailure):
        with scan_lock(engine):
            raise _SimulatedScanFailure("scan crashed mid-run")

    # The crash above must not leave the lock stuck held.
    with scan_lock(engine):
        pass


def test_two_threads_racing_for_the_lock_only_one_succeeds(engine) -> None:
    """Closer to the real scenario the lock exists for: two independent
    scan triggers (e.g. the manual "run scan" button and a scheduled run)
    firing at nearly the same time."""
    second_engine = create_engine(DATABASE_URL)
    results: dict[str, bool] = {}
    first_holds_lock = threading.Event()
    second_may_release = threading.Event()

    def _hold_lock_until_released():
        with scan_lock(engine):
            first_holds_lock.set()
            second_may_release.wait(timeout=5)
        results["first"] = True

    def _try_to_acquire_while_held():
        first_holds_lock.wait(timeout=5)
        try:
            with scan_lock(second_engine):
                results["second_acquired"] = True
        except ScanAlreadyRunningError:
            results["second_acquired"] = False
        finally:
            second_may_release.set()

    try:
        t1 = threading.Thread(target=_hold_lock_until_released)
        t2 = threading.Thread(target=_try_to_acquire_while_held)
        t1.start()
        t2.start()
        t1.join(timeout=10)
        t2.join(timeout=10)

        assert results.get("first") is True
        assert results.get("second_acquired") is False
    finally:
        second_engine.dispose()


def test_lock_is_a_no_op_on_a_non_postgres_engine() -> None:
    """SQLite-backed tests (test_scan_recovery.py, test_publish_blocking.py)
    must never fail just because pg_try_advisory_lock doesn't exist there
    — the lock silently does nothing on a non-Postgres engine."""
    sqlite_engine = create_engine("sqlite:///:memory:")
    try:
        with scan_lock(sqlite_engine):
            with scan_lock(sqlite_engine):  # "nested" acquisition must not raise
                pass
    finally:
        sqlite_engine.dispose()
