// Version history entry, per CLAUDE.md "Job detail > Version history"
// and the GET /jobs/{internal_job_id}/versions endpoint. Each entry is an
// immutable past observation, never an edit of a prior one.

import type { ChangeType } from "@/lib/contracts/job";

export type JobVersionEntry = {
  record_version: number;
  observed_at: string;
  change_type: ChangeType;
  content_hash: string;
  summary: string;
};
