import type { RetrievalStatus } from "@/lib/contracts/job";

const LABEL: Record<RetrievalStatus, string> = {
  retrieved: "Retrieved",
  failed: "Failed",
  not_attempted: "Not attempted",
};

const CLASS: Record<RetrievalStatus, string> = {
  retrieved: "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300",
  failed: "bg-rose-50 text-rose-700 dark:bg-rose-500/10 dark:text-rose-300",
  not_attempted: "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400",
};

export function RetrievalStatusBadge({ status }: { status: RetrievalStatus }) {
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${CLASS[status]}`}>
      {LABEL[status]}
    </span>
  );
}
