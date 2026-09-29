"use client";

import { fetchHealth } from "@/api/health";
import { useApiResource } from "@/lib/use-api-resource";
import { AGREED_SCAN_FREQUENCY_HOURS } from "@/lib/contracts/health";
import { formatDateTime, formatDuration } from "@/lib/format";
import { SectionHeader } from "@/components/layout/section-header";
import { ScanStatusBadge } from "@/components/scans/scan-status-badge";
import { LoadingState, ErrorState } from "@/components/layout/async-state";
import { ClockIcon, ShieldCheckIcon } from "@/components/icons";

export default function HealthPage() {
  const healthState = useApiResource(() => fetchHealth(), []);

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

        {healthState.status === "loading" ? (
          <div className="mt-4">
            <LoadingState label="Loading health…" />
          </div>
        ) : null}
        {healthState.status === "error" ? (
          <div className="mt-4">
            <ErrorState message={healthState.error} onRetry={healthState.refetch} />
          </div>
        ) : null}

        {healthState.status === "success" ? (
          healthState.data.last_successful_scan_id &&
          healthState.data.last_successful_scan_ended_at &&
          healthState.data.seconds_since_last_successful_scan !== null ? (
            <HealthDetails
              scanId={healthState.data.last_successful_scan_id}
              endedAt={healthState.data.last_successful_scan_ended_at}
              secondsSince={healthState.data.seconds_since_last_successful_scan}
            />
          ) : (
            <p className="mt-4 text-sm text-[#64748B] dark:text-zinc-400">
              No successful scan has been recorded yet.
            </p>
          )
        ) : null}
      </div>
    </div>
  );
}

function HealthDetails({
  scanId,
  endedAt,
  secondsSince,
}: {
  scanId: string;
  endedAt: string;
  secondsSince: number;
}) {
  const hoursSinceLastSuccess = secondsSince / 3600;
  const isFresh = hoursSinceLastSuccess <= AGREED_SCAN_FREQUENCY_HOURS;
  const now = new Date().toISOString();

  return (
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
        {/* The backend only ever reports a published (COMPLETE_WITHIN_SCAN_WINDOW) scan here — see get_last_published_scan(). */}
        <ScanStatusBadge status="COMPLETE_WITHIN_SCAN_WINDOW" />
      </div>

      <dl className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div>
          <dt className="text-[11px] font-semibold uppercase tracking-wide text-[#64748B] dark:text-zinc-400">
            Scan ID
          </dt>
          <dd className="mt-0.5 text-sm font-medium text-[#102A5C] dark:text-zinc-50">{scanId}</dd>
        </div>
        <div>
          <dt className="text-[11px] font-semibold uppercase tracking-wide text-[#64748B] dark:text-zinc-400">
            Completed at
          </dt>
          <dd className="mt-0.5 text-sm font-medium text-[#102A5C] dark:text-zinc-50">
            {formatDateTime(endedAt)}
          </dd>
        </div>
        <div>
          <dt className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-[#64748B] dark:text-zinc-400">
            <ClockIcon />
            Time since last success
          </dt>
          <dd className="mt-0.5 text-sm font-medium text-[#102A5C] dark:text-zinc-50">
            {formatDuration(endedAt, now)} ago
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
  );
}
