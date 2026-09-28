import type { ReactNode } from "react";

import type { ScanRun } from "@/lib/contracts/scan";
import { formatDateTime, formatDuration } from "@/lib/format";

function Field({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div>
      <dt className="text-xs font-medium text-zinc-500 dark:text-zinc-400">{label}</dt>
      <dd className="mt-0.5 text-sm font-medium text-zinc-900 dark:text-zinc-50">{value}</dd>
    </div>
  );
}

export function ScanConfigCard({ scan }: { scan: ScanRun }) {
  return (
    <div className="flex-1 rounded-2xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
      <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">Scan window &amp; configuration</h2>
      <dl className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="flex flex-col gap-4">
          <Field label="Started at" value={formatDateTime(scan.started_at)} />
          <Field label="Ended at" value={formatDateTime(scan.ended_at)} />
        </div>
        <div className="flex flex-col gap-4 sm:border-l sm:border-zinc-200 sm:pl-4 dark:sm:border-zinc-800">
          <Field label="Duration" value={formatDuration(scan.started_at, scan.ended_at)} />
          <Field label="Configuration" value={scan.config} />
        </div>
        <div className="flex flex-col gap-4 sm:border-l sm:border-zinc-200 sm:pl-4 dark:sm:border-zinc-800">
          <Field label="Dedup rule" value={scan.dedup_rule} />
          <Field
            label="Published"
            value={
              <span
                className={
                  scan.published.value
                    ? "inline-flex items-center rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-medium text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300"
                    : "inline-flex items-center rounded-full bg-zinc-100 px-2.5 py-0.5 text-xs font-medium text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400"
                }
              >
                {scan.published.value ? "Yes" : "No"}
              </span>
            }
          />
        </div>
      </dl>
      {!scan.published.value && scan.published.reason ? (
        <p className="mt-3 text-xs text-zinc-500 dark:text-zinc-400">{scan.published.reason}</p>
      ) : null}
    </div>
  );
}
