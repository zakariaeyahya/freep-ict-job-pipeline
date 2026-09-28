import type { ScanError } from "@/lib/contracts/scan";
import { RecoveryStatusBadge } from "@/components/scans/route-result-badge";

export function ErrorsList({ errors }: { errors: ScanError[] }) {
  if (errors.length === 0) {
    return (
      <div className="rounded-2xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
        <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">Errors</h2>
        <p className="mt-3 text-sm text-zinc-500 dark:text-zinc-400">No errors recorded for this scan.</p>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
      <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">Errors</h2>

      <div className="mt-4 overflow-x-auto">
        <table className="min-w-full divide-y divide-zinc-200 dark:divide-zinc-800">
          <thead>
            <tr>
              <th scope="col" className="px-2 py-2 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
                Job ID / Route
              </th>
              <th scope="col" className="px-2 py-2 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
                Reason
              </th>
              <th scope="col" className="px-2 py-2 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
                Retry count
              </th>
              <th scope="col" className="px-2 py-2 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
                Recovery status
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
            {errors.map((error) => (
              <tr key={`${error.reference}-${error.reason}`}>
                <td className="max-w-xs truncate px-2 py-2.5 font-mono text-xs text-zinc-700 dark:text-zinc-300" title={error.reference}>
                  {error.reference}
                </td>
                <td className="px-2 py-2.5 text-sm text-zinc-700 dark:text-zinc-300">{error.reason}</td>
                <td className="px-2 py-2.5 text-sm text-zinc-600 dark:text-zinc-400">
                  {error.retry_count} retr{error.retry_count === 1 ? "y" : "ies"}
                </td>
                <td className="px-2 py-2.5 text-sm">
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
