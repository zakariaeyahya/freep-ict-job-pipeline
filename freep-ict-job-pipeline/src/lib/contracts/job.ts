// Job record contract, per CLAUDE.md "Final output > 1. Data contract"
// and brief §4.2 (Desired Job Content).
//
// The UI and the future API are both built against this shape. When the
// real API exists, fetched responses should be typed with this same
// contract instead of a re-declared/duplicated shape.

export type JobStatus = "open" | "closed" | "unknown";

export type ChangeType =
  | "new"
  | "changed"
  | "unchanged"
  | "closed"
  | "temporarily_not_found"
  | "uncertain";

export type CompletenessStatus =
  | "complete_within_scan_window"
  | "incomplete"
  | "failed";

export type ObservationState =
  | "active"
  | "temporarily_not_found"
  | "closed";

export type RetrievalStatus = "retrieved" | "failed" | "not_attempted";

// A list item that keeps the exact source text plus its evidence pointer.
// Used for hard_requirements, wishes, award_criteria, competencies (AC07).
export type EvidencedText = {
  text: string;
  evidence_ref: string | null;
};

export type Attachment = {
  url: string;
  name: string;
  type: string;
  hash: string | null;
  retrieval_status: RetrievalStatus;
};

export type JobRecord = {
  schema_version: string;

  identity: {
    internal_job_id: string;
    source_job_id: string;
    canonical_url: string;
    source: string;
  };

  core: {
    title: string;
    client_name: string | null;
    description_original: string | null;
    description_clean: string | null;
  };

  publication: {
    publication_datetime: string | null;
    closing_datetime: string | null;
    timezone: string;
    status: JobStatus;
  };

  delivery: {
    location: string | null;
    remote_policy: string | null;
    hours_min: number | null;
    hours_max: number | null;
    start_date: string | null;
    end_date: string | null;
    extension_options: string | null;
  };

  selection: {
    hard_requirements: EvidencedText[];
    wishes: EvidencedText[];
    award_criteria: EvidencedText[];
    competencies: EvidencedText[];
  };

  profile: {
    education: string[];
    experience: string[];
    skills: string[];
    methods: string[];
    certifications: string[];
    languages: string[];
  };

  commercial: {
    rate_min: number | null;
    rate_max: number | null;
    currency: string | null;
    vat_basis: string | null;
    travel_cost_policy: string | null;
  };

  engagement: {
    contract_type: string | null;
    zzp_allowed: boolean | null;
    screening: string | null;
    vog: boolean | null;
    nationality_constraints: string | null;
    supplier_conditions: string | null;
  };

  procedure: {
    positions: number | null;
    max_candidates: number | null;
    interview_window: string | null;
    submission_instructions: string | null;
  };

  quality: {
    completeness_status: CompletenessStatus;
    validation_errors: string[];
    source_evidence: string[];
    confidence_per_field: Record<string, number> | null;
  };

  version: {
    first_seen_at: string;
    last_seen_at: string;
    changed_at: string | null;
    content_hash: string;
    record_version: number;
    observation_state: ObservationState;
  };

  attachments: Attachment[];

  // Not part of the stored record; derived by comparing versions (AC09).
  // Kept alongside the record here so the mock data can drive the Jobs
  // table without a separate join.
  change_type: ChangeType;
};
