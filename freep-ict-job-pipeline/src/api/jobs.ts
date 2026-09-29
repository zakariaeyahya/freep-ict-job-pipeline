// GET /api/v1/jobs, GET /api/v1/jobs/{id}, GET /api/v1/jobs/{id}/versions.
// Response shapes mirror the backend's JobListResponse/JobRecordResponse/
// JobVersionsResponse (src/freep_pipeline/api/schemas.py) exactly.

import { apiFetch } from "@/api/client";
import type { JobRecord } from "@/lib/contracts/job";
import type { JobVersionEntry } from "@/lib/contracts/job-version";

type JobListResponse = {
  items: JobRecord[];
  limit: number;
  offset: number;
};

type JobVersionsResponse = {
  items: JobVersionEntry[];
};

export type JobListParams = {
  status?: string;
  change_type?: string;
  limit?: number;
  offset?: number;
};

export async function fetchJobs(params: JobListParams = {}): Promise<JobListResponse> {
  const query = new URLSearchParams();
  if (params.status) query.set("status", params.status);
  if (params.change_type) query.set("change_type", params.change_type);
  if (params.limit !== undefined) query.set("limit", String(params.limit));
  if (params.offset !== undefined) query.set("offset", String(params.offset));

  const queryString = query.toString();
  return apiFetch<JobListResponse>(`/api/v1/jobs${queryString ? `?${queryString}` : ""}`);
}

export async function fetchJob(internalJobId: string): Promise<JobRecord> {
  return apiFetch<JobRecord>(`/api/v1/jobs/${encodeURIComponent(internalJobId)}`);
}

export async function fetchJobVersions(internalJobId: string): Promise<JobVersionEntry[]> {
  const response = await apiFetch<JobVersionsResponse>(
    `/api/v1/jobs/${encodeURIComponent(internalJobId)}/versions`
  );
  return response.items;
}
