import type { ReactNode } from "react";

export function DetailField({ label, value }: { label: string; value: ReactNode | string | number | null }) {
  const isEmpty = value === null || value === undefined || value === "";

  return (
    <div>
      <dt className="text-[11px] font-semibold uppercase tracking-wide text-[#64748B] dark:text-zinc-400">
        {label}
      </dt>
      <dd className="mt-0.5 text-sm font-medium text-[#102A5C] dark:text-zinc-50">
        {isEmpty ? <span className="text-zinc-400 dark:text-zinc-500">Unknown</span> : value}
      </dd>
    </div>
  );
}
