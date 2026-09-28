"""Domain model for a scraped Freep ICT job."""

from __future__ import annotations

from pydantic import BaseModel


class RawJobLink(BaseModel):
    """A job link discovered on a listing page, before the detail fetch."""

    source_url: str
    source_job_path: str


class ParsedJob(BaseModel):
    """A job as parsed from its Freep detail page."""

    source: str = "freep.nl"
    source_job_id: str
    source_url: str

    title: str | None = None
    company: str | None = None
    rate: str | None = None
    province: str | None = None
    segment: str | None = None
    hours_per_week: str | None = None

    publication_date: str | None = None
    start_date: str | None = None
    end_date: str | None = None

    description_original: str | None = None
    hard_requirements: list[str] = []
    wishes: list[str] = []
