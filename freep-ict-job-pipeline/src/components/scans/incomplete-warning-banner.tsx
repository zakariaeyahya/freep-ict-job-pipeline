import { INCOMPLETE_SCAN_WARNING } from "@/lib/contracts/scan";

export function IncompleteWarningBanner() {
  return (
    <div
      role="alert"
      className="flex items-start gap-3 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 dark:border-amber-500/30 dark:bg-amber-500/10"
    >
      <span
        aria-hidden="true"
        className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-amber-500 text-white"
      >
        !
      </span>
      <p className="text-sm font-medium text-amber-800 dark:text-amber-300">{INCOMPLETE_SCAN_WARNING}</p>
    </div>
  );
}
