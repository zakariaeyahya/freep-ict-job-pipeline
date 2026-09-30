import type { ScanError } from "@/lib/contracts/scan";
import { RecoveryStatusBadge } from "@/components/scans/route-result-badge";
import { SectionHeader } from "@/components/layout/section-header";
import { WarningTriangleIcon } from "@/components/icons";

export function ErrorsList({ errors }: { errors: ScanError[] }) {
  if (errors.length === 0) {
    return (
      <div className="rounded-2xl border border-[#E5EAF2] bg-[#FBFCFF] p-5 transition-colors hover:border-violet-200 hover:bg-violet-50/40 dark:border-zinc-800 dark:bg-zinc-900/60 dark:hover:border-violet-500/30 dark:hover:bg-violet-500/5">
        <SectionHeader icon={<WarningTriangleIcon />} title="Errors" />
        <p className="mt-3 text-sm text-[#64748B] dark:text-zinc-400">No errors recorded for this scan.</p>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-[#E5EAF2] bg-[#FBFCFF] p-5 transition-colors hover:border-violet-200 hover:bg-violet-50/40 dark:border-zinc-800 dark:bg-zinc-900/60 dark:hover:border-violet-500/30 dark:hover:bg-violet-500/5">
      <SectionHeader icon={<WarningTriangleIcon />} title="Errors" />

      <div className="mt-4 overflow-x-auto rounded-xl border border-[#E5EAF2] dark:border-zinc-800">
        <table className="min-w-full divide-y divide-[#E5EAF2] dark:divide-zinc-800">
          <thead className="bg-[#EEF0FF] dark:bg-zinc-800/60">
            <tr>
              <th scope="col" className="px-3 py-2.5 text-left text-[11px] font-semibold uppercase tracking-wide text-[#64748B] dark:text-zinc-400">
                Job ID / Route
              </th>
              <th scope="col" className="px-3 py-2.5 text-left text-[11px] font-semibold uppercase tracking-wide text-[#64748B] dark:text-zinc-400">
                Reason
              </th>
              <th scope="col" className="px-3 py-2.5 text-left text-[11px] font-semibold uppercase tracking-wide text-[#64748B] dark:text-zinc-400">
                Retry count
              </th>
              <th scope="col" className="px-3 py-2.5 text-left text-[11px] font-semibold uppercase tracking-wide text-[#64748B] dark:text-zinc-400">
                Recovery status
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#E5EAF2] bg-white dark:divide-zinc-800 dark:bg-zinc-900">
            {errors.map((error) => (
              <tr key={`${error.reference}-${error.reason}`} className="transition-colors hover:bg-violet-50 dark:hover:bg-violet-500/10">
                <td className="max-w-xs truncate px-3 py-3 font-mono text-xs text-[#102A5C] dark:text-zinc-300" title={error.reference}>
                  {error.reference}
                </td>
                <td className="px-3 py-3 text-sm text-[#102A5C] dark:text-zinc-300">{error.reason}</td>
                <td className="px-3 py-3 text-sm text-[#64748B] dark:text-zinc-400">
                  {error.retry_count} retr{error.retry_count === 1 ? "y" : "ies"}
                </td>
                <td className="px-3 py-3 text-sm">
                  <RecoveryStatusBadge status={error.recovery_status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
