import type { RecoveryStatus, RouteResult } from "@/lib/contracts/scan";

const RESULT_LABEL: Record<RouteResult, string> = {
  success: "Success",
  partial: "Partial",
  failed: "Failed",
};

const RESULT_CLASS: Record<RouteResult, string> = {
  success: "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300",
  partial: "bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-300",
  failed: "bg-rose-50 text-rose-700 dark:bg-rose-500/10 dark:text-rose-300",
};

export function RouteResultBadge({ result }: { result: RouteResult }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${RESULT_CLASS[result]}`}
    >
      {RESULT_LABEL[result]}
    </span>
  );
}

const RECOVERY_LABEL: Record<RecoveryStatus, string> = {
  recovered: "Recovered",
  unresolved: "Unresolved",
};

const RECOVERY_CLASS: Record<RecoveryStatus, string> = {
  recovered: "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300",
  unresolved: "bg-rose-50 text-rose-700 dark:bg-rose-500/10 dark:text-rose-300",
};

export function RecoveryStatusBadge({ status }: { status: RecoveryStatus }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${RECOVERY_CLASS[status]}`}
    >
      {RECOVERY_LABEL[status]}
    </span>
  );
}
