import type { ScanRun } from "@/lib/contracts/scan";
import { INCOMPLETE_SCAN_WARNING } from "@/lib/contracts/scan";
import { formatDateTime } from "@/lib/format";

// Mirrors the mandatory scan banner from CLAUDE.md "Status vocabulary" and
// §6.2 of the brief.
export function ScanStatusBanner({ scan }: { scan: ScanRun }) {
  const isComplete = scan.scan_status === "COMPLETE_WITHIN_SCAN_WINDOW";
  const routesCompleted = scan.routes.filter((route) => route.result === "success").length;

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
          Last scan: {formatDateTime(scan.ended_at)} · {routesCompleted}/{scan.routes.length} routes ·{" "}
          {scan.counts.processed}/{scan.counts.discovered} jobs
        </p>
        {!isComplete ? (
          <p className="mt-1 font-medium text-amber-800 dark:text-amber-300">{INCOMPLETE_SCAN_WARNING}</p>
        ) : null}
      </div>
    </div>
  );
}
