import type { ChangeType, JobStatus } from "@/lib/contracts/job";

const STATUS_LABEL: Record<JobStatus, string> = {
  open: "Open",
  closed: "Closed",
  unknown: "Unknown",
};

const STATUS_CLASS: Record<JobStatus, string> = {
  open: "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300",
  closed: "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400",
  unknown: "bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-300",
};

export function StatusBadge({ status }: { status: JobStatus }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_CLASS[status]}`}
    >
      {STATUS_LABEL[status]}
    </span>
  );
}

const CHANGE_LABEL: Record<ChangeType, string> = {
  new: "New",
  changed: "Modified",
  unchanged: "Unchanged",
  closed: "Closed",
  temporarily_not_found: "Temporarily not found",
  uncertain: "Uncertain",
};

const CHANGE_CLASS: Record<ChangeType, string> = {
  new: "bg-violet-50 text-violet-700 dark:bg-violet-500/10 dark:text-violet-300",
  changed: "bg-blue-50 text-blue-700 dark:bg-blue-500/10 dark:text-blue-300",
  unchanged: "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400",
  closed: "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400",
  temporarily_not_found: "bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-300",
  uncertain: "bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-300",
};

export function ChangeBadge({ changeType }: { changeType: ChangeType }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${CHANGE_CLASS[changeType]}`}
    >
      {CHANGE_LABEL[changeType]}
    </span>
  );
}
