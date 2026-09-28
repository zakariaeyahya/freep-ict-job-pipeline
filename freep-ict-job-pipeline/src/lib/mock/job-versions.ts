import type { JobVersionEntry } from "@/lib/contracts/job-version";

// Mock version history, keyed by internal_job_id. Simulates what a future
// GET /jobs/{internal_job_id}/versions would return.
//
// IMPORTANT: only PAST versions go here (record_version strictly less than
// the job's current version.record_version in its fixture). The current
// observation is rendered separately by VersionHistory from the job's own
// `version` block, so it must never be duplicated here — jobs.json's
// record_version and job-versions.ts's most recent entry are also compared
// to keep record_version numbering contiguous.
const VERSIONS: Record<string, JobVersionEntry[]> = {
  "job-1246": [
    {
      record_version: 1,
      observed_at: "2025-09-20T09:00:00+02:00",
      change_type: "new",
      content_hash: "sha256:1246a0b1c2",
      summary: "First observed: Data Engineer at Capgemini, rate 65-90 EUR/hour.",
    },
    // record_version 2 is the job's current observation (see job-1246.json).
  ],
  "job-1242": [
    {
      record_version: 1,
      observed_at: "2025-09-15T09:00:00+02:00",
      change_type: "new",
      content_hash: "sha256:1242e5f6a7",
      summary: "First observed: Business Analyst at Sopra Steria.",
    },
    // record_version 2 is the job's current observation (see job-1242.json).
  ],
  "job-1244": [
    {
      record_version: 1,
      observed_at: "2025-09-10T09:00:00+02:00",
      change_type: "new",
      content_hash: "sha256:1244c3d4e5",
      summary: "First observed: Data Scientist at BNP Paribas.",
    },
    {
      record_version: 2,
      observed_at: "2025-09-20T10:00:00+02:00",
      change_type: "unchanged",
      content_hash: "sha256:1244c3d4e5",
      summary: "No changes detected during this scan.",
    },
    // record_version 3 is the job's current observation (see job-1244.json).
  ],
};

export function getJobVersions(internalJobId: string): JobVersionEntry[] {
  return VERSIONS[internalJobId] ?? [];
}
