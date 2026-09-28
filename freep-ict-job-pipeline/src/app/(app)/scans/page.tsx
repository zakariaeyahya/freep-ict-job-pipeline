import { getLatestScan } from "@/lib/mock/scans";
import { ScanStatusBadge } from "@/components/scans/scan-status-badge";
import { ScanConfigCard } from "@/components/scans/scan-config-card";
import { ConvergenceRounds } from "@/components/scans/convergence-rounds";
import { CountsSummary } from "@/components/scans/counts-summary";
import { RoutesTable } from "@/components/scans/routes-table";
import { ErrorsList } from "@/components/scans/errors-list";
import { IncompleteWarningBanner } from "@/components/scans/incomplete-warning-banner";
import { SectionHeader } from "@/components/layout/section-header";
import { BarChartIcon, DownloadIcon, MoreIcon } from "@/components/icons";

export default function ScanReportPage() {
  const scan = getLatestScan();

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-[32px] font-bold leading-tight text-[#102A5C] dark:text-zinc-50">
              Scan Report
            </h1>
            <ScanStatusBadge status={scan.scan_status} />
          </div>
          <p className="mt-1 text-sm text-[#64748B] dark:text-zinc-400">Scan ID: {scan.scan_id}</p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            disabled
            title="Export is not available yet — no backend export service is connected."
            className="flex items-center gap-2 rounded-xl border border-[#E5EAF2] bg-white px-3.5 py-2 text-sm font-medium text-[#102A5C] outline-none disabled:cursor-not-allowed disabled:opacity-50 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-200"
          >
            <DownloadIcon />
            Download report
          </button>
          <button
            type="button"
            disabled
            aria-label="More actions"
            title="No further actions are available yet."
            className="flex h-9 w-9 items-center justify-center rounded-xl border border-[#E5EAF2] bg-white text-[#64748B] outline-none disabled:cursor-not-allowed disabled:opacity-50 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-400"
          >
            <MoreIcon />
          </button>
        </div>
      </div>

      {scan.scan_status === "INCOMPLETE" ? <IncompleteWarningBanner /> : null}

      <div className="flex flex-col gap-4 lg:flex-row">
        <ScanConfigCard scan={scan} />
        <ConvergenceRounds rounds={scan.convergence_rounds} />
      </div>

      <div className="rounded-2xl border border-[#E5EAF2] bg-[#FBFCFF] p-5 dark:border-zinc-800 dark:bg-zinc-900/60">
        <SectionHeader icon={<BarChartIcon />} title="Counts summary" />
        <div className="mt-4">
          <CountsSummary counts={scan.counts} />
        </div>
      </div>

      <RoutesTable routes={scan.routes} />
      <ErrorsList errors={scan.errors} />
    </div>
  );
}
