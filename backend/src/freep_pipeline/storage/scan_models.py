"""SQLAlchemy table definitions for scan runs.

Mirrors the ScanRun contract already defined and used by the frontend
(freep-ict-job-pipeline/src/lib/contracts/scan.ts), so the future API can
serve this table's data without reshaping it.

Per brief §4.3: scan_run is a distinct concept from job_observation — one
row per scan, holding the scan window, route inventory, convergence and
final status. route_visit is its own concept too (§4.1/§4.3): each source
route's outcome for that scan. Both are append-only, like job_observations.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.freep_pipeline.storage.models import Base


class ScanRun(Base):
    """One scan run: window, configuration, counts and final status."""

    __tablename__ = "scan_runs"

    scan_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    config: Mapped[str] = mapped_column(String(128))
    dedup_rule: Mapped[str] = mapped_column(String(128))

    scan_status: Mapped[str] = mapped_column(String(32), default="INCOMPLETE")
    published: Mapped[bool] = mapped_column(Boolean, default=False)
    published_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    count_discovered: Mapped[int] = mapped_column(Integer, default=0)
    count_processed: Mapped[int] = mapped_column(Integer, default=0)
    count_duplicates: Mapped[int] = mapped_column(Integer, default=0)
    count_new: Mapped[int] = mapped_column(Integer, default=0)
    count_changed: Mapped[int] = mapped_column(Integer, default=0)
    count_closed: Mapped[int] = mapped_column(Integer, default=0)
    count_temporarily_not_found: Mapped[int] = mapped_column(Integer, default=0)
    count_errors: Mapped[int] = mapped_column(Integer, default=0)

    routes: Mapped[list[ScanRoute]] = relationship(back_populates="scan", cascade="all, delete-orphan")
    errors: Mapped[list[ScanError]] = relationship(back_populates="scan", cascade="all, delete-orphan")


class ScanRoute(Base):
    """One known ICT source route's outcome for one scan.

    The complete inventory of known routes for a scan lives here — this is
    what AC01 ("complete inventory of known ICT source routes") and AC02
    ("all known routes demonstrably traversed") are checked against.
    """

    __tablename__ = "scan_routes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scan_id: Mapped[str] = mapped_column(ForeignKey("scan_runs.scan_id"), index=True)

    url: Mapped[str] = mapped_column(Text)
    pages_visited: Mapped[int] = mapped_column(Integer, default=0)
    result: Mapped[str] = mapped_column(String(16))  # success | partial | failed
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    scan: Mapped[ScanRun] = relationship(back_populates="routes")


class ScanError(Base):
    """One error recorded during a scan (a job or a route), with recovery
    status, per AC10 ("errors remain visible in the scan report")."""

    __tablename__ = "scan_errors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scan_id: Mapped[str] = mapped_column(ForeignKey("scan_runs.scan_id"), index=True)

    reference: Mapped[str] = mapped_column(Text)  # job id or route url
    reason: Mapped[str] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    recovery_status: Mapped[str] = mapped_column(String(16), default="unresolved")

    scan: Mapped[ScanRun] = relationship(back_populates="errors")
