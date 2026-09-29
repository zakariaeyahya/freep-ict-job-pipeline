"""Pydantic response models for the API. Mirrors the JobRecord contract
(contracts/job_record.schema.json) field-for-field so the OpenAPI docs and
the actual JSON body never diverge (CLAUDE.md: "Use DTOs to separate API
contracts from entities. Never expose JPA/ORM entities directly in
responses" — same rule applies to FastAPI + SQLAlchemy).
"""

from __future__ import annotations

from pydantic import BaseModel


class EvidencedText(BaseModel):
    text: str
    evidence_ref: str | None


class Identity(BaseModel):
    internal_job_id: str
    source_job_id: str
    canonical_url: str
    source: str


class Core(BaseModel):
    title: str
    client_name: str | None
    description_original: str | None
    description_clean: str | None


class Publication(BaseModel):
    publication_datetime: str | None
    closing_datetime: str | None
    timezone: str
    status: str


class Delivery(BaseModel):
    location: str | None
    remote_policy: str | None
    hours_min: float | None
    hours_max: float | None
    start_date: str | None
    end_date: str | None
    extension_options: str | None


class Selection(BaseModel):
    hard_requirements: list[EvidencedText]
    wishes: list[EvidencedText]
    award_criteria: list[EvidencedText]
    competencies: list[EvidencedText]


class Profile(BaseModel):
    education: list[str]
    experience: list[str]
    skills: list[str]
    methods: list[str]
    certifications: list[str]
    languages: list[str]


class Commercial(BaseModel):
    rate_min: float | None
    rate_max: float | None
    currency: str | None
    vat_basis: str | None
    travel_cost_policy: str | None


class Engagement(BaseModel):
    contract_type: str | None
    zzp_allowed: bool | None
    screening: str | None
    vog: bool | None
    nationality_constraints: str | None
    supplier_conditions: str | None


class Procedure(BaseModel):
    positions: int | None
    max_candidates: int | None
    interview_window: str | None
    submission_instructions: str | None


class Quality(BaseModel):
    completeness_status: str
    validation_errors: list[str]
    source_evidence: list[str]
    confidence_per_field: dict[str, float] | None


class Version(BaseModel):
    first_seen_at: str
    last_seen_at: str
    changed_at: str | None
    content_hash: str
    record_version: int
    observation_state: str


class Attachment(BaseModel):
    url: str
    name: str
    type: str
    hash: str | None
    retrieval_status: str


class JobRecordResponse(BaseModel):
    schema_version: str
    identity: Identity
    core: Core
    publication: Publication
    delivery: Delivery
    selection: Selection
    profile: Profile
    commercial: Commercial
    engagement: Engagement
    procedure: Procedure
    quality: Quality
    version: Version
    attachments: list[Attachment]
    change_type: str


class JobListResponse(BaseModel):
    items: list[JobRecordResponse]
    limit: int
    offset: int


class JobVersionEntry(BaseModel):
    record_version: int
    observed_at: str
    change_type: str
    content_hash: str
    summary: str


class JobVersionsResponse(BaseModel):
    items: list[JobVersionEntry]


class RouteVisit(BaseModel):
    url: str
    pages_visited: int
    result: str
    error: str | None


class ConvergenceRound(BaseModel):
    round: int
    new_routes_discovered: int
    converged: bool
    observed_at: str


class ScanCounts(BaseModel):
    discovered: int
    processed: int
    duplicates: int
    new: int
    changed: int
    closed: int
    temporarily_not_found: int
    errors: int


class ScanErrorEntry(BaseModel):
    reference: str
    reason: str
    retry_count: int
    recovery_status: str


class PublishedStatus(BaseModel):
    value: bool
    reason: str | None


class ScanRunResponse(BaseModel):
    scan_id: str
    started_at: str
    ended_at: str
    config: str
    routes: list[RouteVisit]
    convergence_rounds: list[ConvergenceRound]
    counts: ScanCounts
    dedup_rule: str
    scan_status: str
    published: PublishedStatus
    errors: list[ScanErrorEntry]


class ScanListResponse(BaseModel):
    items: list[ScanRunResponse]
    limit: int
    offset: int


class ScanTriggerResponse(BaseModel):
    status: str


class ScanActivityEventResponse(BaseModel):
    message: str
    at: str


class ScanProgressResponse(BaseModel):
    phase: str
    jobs_total: int | None
    jobs_processed: int
    activity: list[ScanActivityEventResponse]
    started_at: str


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    expires_in: int
    refresh_token: str | None
    refresh_expires_in: int | None


class HealthResponse(BaseModel):
    status: str
    last_successful_scan_id: str | None
    last_successful_scan_ended_at: str | None
    seconds_since_last_successful_scan: float | None


class ErrorResponse(BaseModel):
    """Uniform error body (CLAUDE.md: "Return a uniform error body...
    never leak stack traces or internals to the client")."""

    timestamp: str
    status: int
    error: str
    message: str
    path: str
