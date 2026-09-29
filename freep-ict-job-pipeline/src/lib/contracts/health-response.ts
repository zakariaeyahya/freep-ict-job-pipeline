// GET /api/v1/health response shape, mirrors the backend's HealthResponse
// (src/freep_pipeline/api/schemas.py) exactly. Distinct from
// lib/contracts/health.ts, which only holds the agreed scan frequency
// constant used to judge freshness against this response.

export type HealthResponse = {
  status: string;
  last_successful_scan_id: string | null;
  last_successful_scan_ended_at: string | null;
  seconds_since_last_successful_scan: number | null;
};
