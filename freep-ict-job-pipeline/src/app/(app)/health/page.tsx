import { getScans } from "@/lib/mock/scans";
import { AGREED_SCAN_FREQUENCY_HOURS } from "@/lib/contracts/health";
import { formatDateTime, formatDuration } from "@/lib/format";
import { SectionHeader } from "@/components/layout/section-header";
import { ScanStatusBadge } from "@/components/scans/scan-status-badge";
import { ClockIcon, ShieldCheckIcon } from "@/components/icons";

export default function HealthPage() {
  const scans = getScans();
  const lastSuccessfulScan = scans.find((scan) => scan.scan_status === "COMPLETE_WITHIN_SCAN_WINDOW") ?? null;

  const now = new Date().toISOString();
  const hoursSinceLastSuccess = lastSuccessfulScan
    ? (Date.now() - new Date(lastSuccessfulScan.ended_at).getTime()) / (1000 * 60 * 60)
    : null;

  const isFresh = hoursSinceLastSuccess !== null && hoursSinceLastSuccess <= AGREED_SCAN_FREQUENCY_HOURS;

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h1 className="text-[32px] font-bold leading-tight text-[#102A5C] dark:text-zinc-50">Health</h1>
        <p className="mt-1 text-sm text-[#64748B] dark:text-zinc-400">
          Freshness of the published job data against the agreed scan frequency.
        </p>
      </div>

      <div className="rounded-2xl border border-[#E5EAF2] bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
        <SectionHeader icon={<ShieldCheckIcon />} title="Last successful scan" />

        {lastSuccessfulScan ? (
          <div className="mt-4 flex flex-col gap-4">
            <div className="flex flex-wrap items-center gap-3">
              <span
                className={
                  isFresh
                    ? "inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-emerald-700 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-300"
                    : "inline-flex items-center gap-1.5 rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-amber-700 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-300"
                }
              >
                <span aria-hidden="true">{isFresh ? "✓" : "!"}</span>
                {isFresh ? "Fresh" : "Stale"}
              </span>
              <ScanStatusBadge status={lastSuccessfulScan.scan_status} />
            </div>

            <dl className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div>
                <dt className="text-[11px] font-semibold uppercase tracking-wide text-[#64748B] dark:text-zinc-400">
                  Scan ID
                </dt>
                <dd className="mt-0.5 text-sm font-medium text-[#102A5C] dark:text-zinc-50">
                  {lastSuccessfulScan.scan_id}
                </dd>
              </div>
              <div>
                <dt className="text-[11px] font-semibold uppercase tracking-wide text-[#64748B] dark:text-zinc-400">
                  Completed at
                </dt>
                <dd className="mt-0.5 text-sm font-medium text-[#102A5C] dark:text-zinc-50">
                  {formatDateTime(lastSuccessfulScan.ended_at)}
                </dd>
              </div>
              <div>
                <dt className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-[#64748B] dark:text-zinc-400">
                  <ClockIcon />
                  Time since last success
                </dt>
                <dd className="mt-0.5 text-sm font-medium text-[#102A5C] dark:text-zinc-50">
                  {formatDuration(lastSuccessfulScan.ended_at, now)} ago
                </dd>
              </div>
            </dl>

            <p className="text-xs text-[#64748B] dark:text-zinc-400">
              Agreed scan frequency: every {AGREED_SCAN_FREQUENCY_HOURS}h.{" "}
              {isFresh
                ? "The last successful scan is within this window."
                : "The last successful scan is older than this window — data may be stale."}
            </p>
          </div>
        ) : (
          <p className="mt-4 text-sm text-[#64748B] dark:text-zinc-400">
            No successful scan has been recorded yet.
          </p>
        )}
      </div>
    </div>
  );
}
