// GET /api/v1/scans, GET /api/v1/scans/{scan_id}. Response shapes mirror
// the backend's ScanListResponse/ScanRunResponse (src/freep_pipeline/api/
// schemas.py) exactly.

import { apiFetch } from "@/api/client";
import type { ScanRun } from "@/lib/contracts/scan";

type ScanListResponse = {
  items: ScanRun[];
  limit: number;
  offset: number;
};

export async function fetchScans(params: { limit?: number; offset?: number } = {}): Promise<ScanRun[]> {
  const query = new URLSearchParams();
  if (params.limit !== undefined) query.set("limit", String(params.limit));
  if (params.offset !== undefined) query.set("offset", String(params.offset));

  const queryString = query.toString();
  const response = await apiFetch<ScanListResponse>(`/api/v1/scans${queryString ? `?${queryString}` : ""}`);
  return response.items;
}

export async function fetchScan(scanId: string): Promise<ScanRun> {
  return apiFetch<ScanRun>(`/api/v1/scans/${encodeURIComponent(scanId)}`);
}

export async function fetchLatestScan(): Promise<ScanRun | null> {
  const scans = await fetchScans({ limit: 1 });
  return scans[0] ?? null;
}

// POST /api/v1/scans/trigger — starts a scan on the backend's side and
// returns immediately (202); the scan itself can take minutes. Callers
// poll fetchLatestScan()/fetchScans() to see it appear once finished.
// Throws ApiError with status 409 (via apiFetch) if a scan is already
// running.
export async function triggerScan(): Promise<void> {
  await apiFetch<{ status: string }>("/api/v1/scans/trigger", { method: "POST" });
}
