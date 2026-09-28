import type { ScanStatus } from "@/lib/contracts/scan";

const LABEL: Record<ScanStatus, string> = {
  COMPLETE_WITHIN_SCAN_WINDOW: "Complete within scan window",
  INCOMPLETE: "Incomplete",
  FAILED: "Failed",
};

const CLASS: Record<ScanStatus, string> = {
  COMPLETE_WITHIN_SCAN_WINDOW:
    "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-500/10 dark:text-emerald-300 dark:border-emerald-500/30",
  INCOMPLETE: "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-500/10 dark:text-amber-300 dark:border-amber-500/30",
  FAILED: "bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-500/10 dark:text-rose-300 dark:border-rose-500/30",
};

const ICON: Record<ScanStatus, string> = {
  COMPLETE_WITHIN_SCAN_WINDOW: "✓",
  INCOMPLETE: "!",
  FAILED: "✕",
};

export function ScanStatusBadge({ status }: { status: ScanStatus }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wide ${CLASS[status]}`}
    >
      <span aria-hidden="true">{ICON[status]}</span>
      {LABEL[status]}
    </span>
  );
}
