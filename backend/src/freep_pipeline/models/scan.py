"""In-memory scan run report, built up during a pipeline run and then
persisted as-is. Mirrors the ScanRun contract used by the frontend."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RouteVisit(BaseModel):
    url: str
    pages_visited: int = 0
    result: str = "success"  # success | partial | failed
    error: str | None = None


class ScanErrorEntry(BaseModel):
    reference: str  # job id or route url
    reason: str
    retry_count: int = 0
    recovery_status: str = "unresolved"  # recovered | unresolved


class ScanCounts(BaseModel):
    discovered: int = 0
    processed: int = 0
    duplicates: int = 0
    new: int = 0
    changed: int = 0
    closed: int = 0
    temporarily_not_found: int = 0
    errors: int = 0


class ScanReport(BaseModel):
    """Accumulates everything about one scan run as the pipeline executes.
    Passed to JobRepository.save_scan_run() at the end to persist it."""

    scan_id: str
    started_at: datetime
    ended_at: datetime | None = None
    config: str
    dedup_rule: str

    scan_status: str = "INCOMPLETE"  # COMPLETE_WITHIN_SCAN_WINDOW | INCOMPLETE | FAILED
    published: bool = False
    published_reason: str | None = None

    routes: list[RouteVisit] = Field(default_factory=list)
    errors: list[ScanErrorEntry] = Field(default_factory=list)
    counts: ScanCounts = Field(default_factory=ScanCounts)

    def add_error(self, reference: str, reason: str, retry_count: int = 0) -> None:
        self.errors.append(ScanErrorEntry(reference=reference, reason=reason, retry_count=retry_count))
        self.counts.errors += 1
