import { getLatestScan } from "@/lib/mock/scans";
import { ScanStatusBadge } from "@/components/scans/scan-status-badge";
import { ScanConfigCard } from "@/components/scans/scan-config-card";
import { ConvergenceRounds } from "@/components/scans/convergence-rounds";
import { CountsSummary } from "@/components/scans/counts-summary";
import { RoutesTable } from "@/components/scans/routes-table";
import { ErrorsList } from "@/components/scans/errors-list";
import { IncompleteWarningBanner } from "@/components/scans/incomplete-warning-banner";

export default function ScanReportPage() {
  const scan = getLatestScan();

  return (
    <div className="flex flex-col gap-6">
      <div>
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-50">Scan Report</h1>
          <ScanStatusBadge status={scan.scan_status} />
        </div>
        <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">Scan ID: {scan.scan_id}</p>
      </div>

      {scan.scan_status === "INCOMPLETE" ? <IncompleteWarningBanner /> : null}

      <div className="flex flex-col gap-4 lg:flex-row">
        <ScanConfigCard scan={scan} />
        <ConvergenceRounds rounds={scan.convergence_rounds} />
      </div>

      <div className="rounded-2xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
        <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">Counts summary</h2>
        <div className="mt-4">
          <CountsSummary counts={scan.counts} />
        </div>
      </div>

      <RoutesTable routes={scan.routes} />
      <ErrorsList errors={scan.errors} />
    </div>
  );
}
