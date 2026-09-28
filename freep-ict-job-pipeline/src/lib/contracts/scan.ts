// Scan run contract, per CLAUDE.md "Final output > 1. Data contract"
// (Scan run paragraph) and brief §6.2 (Minimum Status Distinctions).

export type ScanStatus = "COMPLETE_WITHIN_SCAN_WINDOW" | "INCOMPLETE" | "FAILED";

export type RouteResult = "success" | "partial" | "failed";

export type RouteVisit = {
  url: string;
  pages_visited: number;
  result: RouteResult;
  error: string | null;
};

export type ConvergenceRound = {
  round: number;
  new_routes_discovered: number;
  converged: boolean;
  observed_at: string;
};

export type ScanCounts = {
  discovered: number;
  processed: number;
  duplicates: number;
  new: number;
  changed: number;
  closed: number;
  temporarily_not_found: number;
  errors: number;
};

export type RecoveryStatus = "recovered" | "unresolved";

export type ScanError = {
  reference: string; // job id or route
  reason: string;
  retry_count: number;
  recovery_status: RecoveryStatus;
};

export type ScanRun = {
  scan_id: string;
  started_at: string;
  ended_at: string;
  config: string;
  routes: RouteVisit[];
  convergence_rounds: ConvergenceRound[];
  counts: ScanCounts;
  dedup_rule: string;
  scan_status: ScanStatus;
  published: {
    value: boolean;
    reason: string | null;
  };
  errors: ScanError[];
};

export const INCOMPLETE_SCAN_WARNING =
  "FREEP SCAN INCOMPLETE. Not all known ICT source routes, discovered assignments or convergence checks could be processed reliably within the scan window. The scan report states what was observed and what could not be verified.";
