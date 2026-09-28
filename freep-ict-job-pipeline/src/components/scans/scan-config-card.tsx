import type { ReactNode } from "react";

import type { ScanRun } from "@/lib/contracts/scan";
import { formatDateTime, formatDuration } from "@/lib/format";
import { SectionHeader } from "@/components/layout/section-header";
import { CalendarIcon, ClockIcon, LinkIcon, SettingsIcon } from "@/components/icons";

function Field({ icon, label, value }: { icon: ReactNode; label: string; value: ReactNode }) {
  return (
    <div className="flex items-start gap-2.5">
      <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-indigo-50 text-indigo-500 dark:bg-indigo-500/10 dark:text-indigo-300">
        {icon}
      </span>
      <div>
        <dt className="text-[11px] font-semibold uppercase tracking-wide text-[#64748B] dark:text-zinc-400">
          {label}
        </dt>
        <dd className="mt-0.5 text-sm font-semibold text-[#102A5C] dark:text-zinc-50">{value}</dd>
      </div>
    </div>
  );
}

export function ScanConfigCard({ scan }: { scan: ScanRun }) {
  return (
    <div className="flex-1 rounded-2xl border border-[#E5EAF2] bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
      <SectionHeader icon={<CalendarIcon />} title="Scan window & configuration" />
      <dl className="mt-5 grid grid-cols-1 gap-5 sm:grid-cols-3">
        <div className="flex flex-col gap-4">
          <Field icon={<CalendarIcon />} label="Started at" value={formatDateTime(scan.started_at)} />
          <Field icon={<CalendarIcon />} label="Ended at" value={formatDateTime(scan.ended_at)} />
        </div>
        <div className="flex flex-col gap-4 sm:border-l sm:border-[#E5EAF2] sm:pl-5 dark:sm:border-zinc-800">
          <Field icon={<ClockIcon />} label="Duration" value={formatDuration(scan.started_at, scan.ended_at)} />
          <Field icon={<SettingsIcon />} label="Configuration" value={scan.config} />
        </div>
        <div className="flex flex-col gap-4 sm:border-l sm:border-[#E5EAF2] sm:pl-5 dark:sm:border-zinc-800">
          <Field icon={<LinkIcon />} label="Dedup rule" value={scan.dedup_rule} />
          <Field
            icon={<LinkIcon />}
            label="Published"
            value={
              <span
                className={
                  scan.published.value
                    ? "inline-flex items-center rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300"
                    : "inline-flex items-center rounded-full bg-zinc-100 px-2.5 py-0.5 text-xs font-semibold text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400"
                }
              >
                {scan.published.value ? "Yes" : "No"}
              </span>
            }
          />
        </div>
      </dl>
      {!scan.published.value && scan.published.reason ? (
        <p className="mt-4 text-xs text-[#64748B] dark:text-zinc-400">{scan.published.reason}</p>
      ) : null}
    </div>
  );
}
