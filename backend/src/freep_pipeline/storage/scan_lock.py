"""Prevents two scans from running concurrently against the same database
(brief §9.2, Scheduler responsibility: "prevents conflicting runs").

Uses a PostgreSQL session-level advisory lock rather than a row in a
table: it requires no cleanup on crash (Postgres releases it automatically
when the holding connection closes, so a killed process never leaves a
stale lock behind) and it doesn't touch the append-only scan_runs/
job_observations write pattern that AC10's recovery guarantees rely on.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import text
from sqlalchemy.engine import Engine

from config.logging_config import get_logger

logger = get_logger(__name__)

# Arbitrary but fixed 64-bit key identifying "a Freep scan is running" —
# any int works as long as it's stable across the codebase; picked by
# hashing the string "freep_scan" down to a value pg_advisory_lock accepts.
SCAN_LOCK_KEY = 84_621_907_331_402_551 % (2**63)


class ScanAlreadyRunningError(Exception):
    """Raised when a scan is requested while another one already holds the
    lock. Never a reason to run anyway — two concurrent scans writing to
    the same jobs_current projection is exactly the conflict AC10's
    recovery guarantees assume can't happen."""


@contextmanager
def scan_lock(engine: Engine) -> Iterator[None]:
    """Acquires the scan advisory lock for the duration of the `with`
    block, on a dedicated connection held open for that whole time (an
    advisory lock is tied to the session that took it — releasing early
    or on a different connection would be a no-op). Raises
    ScanAlreadyRunningError immediately if another scan already holds it,
    rather than blocking and queueing.

    A no-op on any non-PostgreSQL engine (e.g. the SQLite databases
    test_scan_recovery.py/test_publish_blocking.py use for fast,
    Postgres-free tests) — pg_try_advisory_lock doesn't exist there, and
    SQLite's own file-level locking is a different mechanism entirely.
    Concurrency protection is a production (Postgres) concern only; it is
    never silently claimed on an engine that can't actually provide it."""
    if engine.dialect.name != "postgresql":
        yield
        return

    connection = engine.connect()
    try:
        acquired = connection.execute(
            text("SELECT pg_try_advisory_lock(:key)"), {"key": SCAN_LOCK_KEY}
        ).scalar()
        if not acquired:
            raise ScanAlreadyRunningError("A scan is already running")

        logger.info("Scan lock acquired")
        try:
            yield
        finally:
            connection.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": SCAN_LOCK_KEY})
            logger.info("Scan lock released")
    finally:
        connection.close()
