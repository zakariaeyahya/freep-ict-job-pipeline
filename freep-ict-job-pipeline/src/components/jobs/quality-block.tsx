import type { JobRecord } from "@/lib/contracts/job";
import { DetailField } from "@/components/jobs/detail-field";

const COMPLETENESS_LABEL: Record<JobRecord["quality"]["completeness_status"], string> = {
  complete_within_scan_window: "Complete within scan window",
  incomplete: "Incomplete",
  failed: "Failed",
};

const COMPLETENESS_CLASS: Record<JobRecord["quality"]["completeness_status"], string> = {
  complete_within_scan_window: "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300",
  incomplete: "bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-300",
  failed: "bg-rose-50 text-rose-700 dark:bg-rose-500/10 dark:text-rose-300",
};

export function QualityBlock({ quality }: { quality: JobRecord["quality"] }) {
  return (
    <div className="flex flex-col gap-4">
      <DetailField
        label="Completeness status"
        value={
          <span
            className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${COMPLETENESS_CLASS[quality.completeness_status]}`}
          >
            {COMPLETENESS_LABEL[quality.completeness_status]}
          </span>
        }
      />

      <div>
        <dt className="text-[11px] font-semibold uppercase tracking-wide text-[#64748B] dark:text-zinc-400">
          Validation errors
        </dt>
        {quality.validation_errors.length === 0 ? (
          <dd className="mt-0.5 text-sm text-zinc-400 dark:text-zinc-500">None</dd>
        ) : (
          <ul className="mt-1 flex flex-col gap-1">
            {quality.validation_errors.map((error, index) => (
              <li
                key={index}
                className="rounded-lg bg-rose-50 px-2.5 py-1 text-xs text-rose-700 dark:bg-rose-500/10 dark:text-rose-300"
              >
                {error}
              </li>
            ))}
          </ul>
        )}
      </div>

      <DetailField
        label="Source evidence references"
        value={quality.source_evidence.length > 0 ? quality.source_evidence.join(", ") : null}
      />
    </div>
  );
}
