"""SQLAlchemy table definitions for the pipeline's PostgreSQL store.

Two tables, matching CLAUDE.md's immutability rule: `job_observations` is
append-only (one row per scan observation of a job, never edited),
`jobs_current` is the derived projection of the latest observation per job.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class JobObservation(Base):
    """One immutable observation of a job during one scan. Never updated."""

    __tablename__ = "job_observations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scan_id: Mapped[str] = mapped_column(String(64), index=True)
    source_job_id: Mapped[str] = mapped_column(String(255), index=True)
    source_url: Mapped[str] = mapped_column(Text)

    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    company: Mapped[str | None] = mapped_column(Text, nullable=True)
    rate: Mapped[str | None] = mapped_column(Text, nullable=True)
    province: Mapped[str | None] = mapped_column(Text, nullable=True)
    segment: Mapped[str | None] = mapped_column(Text, nullable=True)
    hours_per_week: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[str | None] = mapped_column(Text, nullable=True)
    end_date: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_original: Mapped[str | None] = mapped_column(Text, nullable=True)

    hard_requirements: Mapped[list] = mapped_column(JSON, default=list)
    wishes: Mapped[list] = mapped_column(JSON, default=list)

    # Profile/engagement/procedure signals (brief §4.2), extracted by
    # LlmFieldExtractor from the free-text fields above — Freep does not
    # expose these as separate HTML fields. Every value is a verified
    # exact substring of the source text (see llm_field_extractor.py);
    # empty/null when nothing could be grounded in the source, never a
    # fabricated guess.
    education: Mapped[list] = mapped_column(JSON, default=list)
    experience: Mapped[list] = mapped_column(JSON, default=list)
    skills: Mapped[list] = mapped_column(JSON, default=list)
    methods: Mapped[list] = mapped_column(JSON, default=list)
    certifications: Mapped[list] = mapped_column(JSON, default=list)
    languages: Mapped[list] = mapped_column(JSON, default=list)
    contract_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    zzp_allowed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    screening: Mapped[str | None] = mapped_column(Text, nullable=True)
    vog: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    positions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_candidates: Mapped[int | None] = mapped_column(Integer, nullable=True)

    content_hash: Mapped[str] = mapped_column(String(64))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class JobCurrent(Base):
    """Derived projection: the latest reliable state of each job.

    Rebuilt from job_observations, never edited directly (CLAUDE.md rule:
    "job_current is a derived projection and is never edited in place").
    """

    __tablename__ = "jobs_current"

    source_job_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    source_url: Mapped[str] = mapped_column(Text)

    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    company: Mapped[str | None] = mapped_column(Text, nullable=True)
    rate: Mapped[str | None] = mapped_column(Text, nullable=True)
    province: Mapped[str | None] = mapped_column(Text, nullable=True)
    segment: Mapped[str | None] = mapped_column(Text, nullable=True)
    hours_per_week: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[str | None] = mapped_column(Text, nullable=True)
    end_date: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_original: Mapped[str | None] = mapped_column(Text, nullable=True)

    hard_requirements: Mapped[list] = mapped_column(JSON, default=list)
    wishes: Mapped[list] = mapped_column(JSON, default=list)

    # Profile/engagement/procedure signals (brief §4.2) from the most
    # recent observation's LlmFieldExtractor pass — see JobObservation for
    # the extraction/anti-fabrication rationale. Overwritten on every
    # upsert like the other flat fields above; the immutable history lives
    # in job_observations, not here.
    education: Mapped[list] = mapped_column(JSON, default=list)
    experience: Mapped[list] = mapped_column(JSON, default=list)
    skills: Mapped[list] = mapped_column(JSON, default=list)
    methods: Mapped[list] = mapped_column(JSON, default=list)
    certifications: Mapped[list] = mapped_column(JSON, default=list)
    languages: Mapped[list] = mapped_column(JSON, default=list)
    contract_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    zzp_allowed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    screening: Mapped[str | None] = mapped_column(Text, nullable=True)
    vog: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    positions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_candidates: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Structured values derived from the free-text rate/hours_per_week
    # fields (JobNormalizer). Never replaces the original text — brief
    # §4.4: "retain the original text alongside each normalised value".
    # Null when the source text didn't match a recognisable pattern.
    rate_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rate_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hours_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hours_max: Mapped[int | None] = mapped_column(Integer, nullable=True)

    status: Mapped[str] = mapped_column(String(32), default="open")
    change_type: Mapped[str] = mapped_column(String(32), default="new")

    # Consecutive scans in which this job was NOT seen. A single miss
    # never means deletion (brief §3.3) — it becomes temporarily_not_found
    # and only turns into closed after CLOSURE_AFTER_CONSECUTIVE_ABSENCES
    # consecutive misses (config.settings).
    consecutive_absences: Mapped[int] = mapped_column(Integer, default=0)

    content_hash: Mapped[str] = mapped_column(String(64))
    record_version: Mapped[int] = mapped_column(Integer, default=1)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
