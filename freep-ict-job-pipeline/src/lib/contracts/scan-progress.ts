// GET /api/v1/scans/current response shape, mirrors the backend's
// ScanProgressResponse (src/freep_pipeline/api/schemas.py) exactly.
// null (204 from the API) means no scan is currently running.

export type ScanPhase = "discovering" | "processing" | "storing";

export type ScanActivityEvent = {
  message: string;
  at: string;
};

export type ScanProgress = {
  phase: ScanPhase;
  jobs_total: number | null;
  jobs_processed: number;
  activity: ScanActivityEvent[];
  started_at: string;
};
