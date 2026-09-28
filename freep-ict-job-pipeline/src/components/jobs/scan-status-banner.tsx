import { formatDateTime } from "@/lib/format";

// Mirrors the mandatory scan banner from CLAUDE.md "Status vocabulary" and
// §6.2 of the brief. Backed by mock data until /scans exists.
const MOCK_SCAN = {
  scan_status: "COMPLETE_WITHIN_SCAN_WINDOW" as const,
  ended_at: "2025-09-28T17:14:00+02:00",
  routes_total: 8,
  routes_completed: 8,
  jobs_processed: 13,
  jobs_discovered: 13,
};

const INCOMPLETE_WARNING =
  "FREEP SCAN INCOMPLETE. Not all known ICT source routes, discovered assignments or convergence checks could be processed reliably within the scan window. The scan report states what was observed and what could not be verified.";

export function ScanStatusBanner() {
  const isComplete = MOCK_SCAN.scan_status === "COMPLETE_WITHIN_SCAN_WINDOW";

  return (
    <div
      className={
        isComplete
          ? "flex items-center gap-3 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 dark:border-emerald-500/30 dark:bg-emerald-500/10"
          : "flex items-center gap-3 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 dark:border-amber-500/30 dark:bg-amber-500/10"
      }
      role="status"
    >
      <span
        aria-hidden="true"
        className={
          isComplete
            ? "flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-emerald-500 text-white"
            : "flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-amber-500 text-white"
        }
      >
        {isComplete ? "✓" : "!"}
      </span>
      <div className="text-sm">
        <p className={isComplete ? "font-medium text-emerald-800 dark:text-emerald-300" : "font-medium text-amber-800 dark:text-amber-300"}>
          {isComplete ? "Scan completed within window" : "Scan incomplete"}
        </p>
        <p className="text-zinc-600 dark:text-zinc-400">
          Last scan: {formatDateTime(MOCK_SCAN.ended_at)} · {MOCK_SCAN.routes_completed}/{MOCK_SCAN.routes_total}{" "}
          routes · {MOCK_SCAN.jobs_processed}/{MOCK_SCAN.jobs_discovered} jobs
        </p>
        {!isComplete ? (
          <p className="mt-1 font-medium text-amber-800 dark:text-amber-300">{INCOMPLETE_WARNING}</p>
        ) : null}
      </div>
    </div>
  );
}
