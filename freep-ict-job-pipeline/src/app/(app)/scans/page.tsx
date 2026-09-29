"use client";

import { useState } from "react";

import { fetchLatestScan } from "@/api/scans";
import { downloadScanExport } from "@/api/exports";
import { useApiResource } from "@/lib/use-api-resource";
import { useScanTrigger, type ScanTriggerState } from "@/lib/use-scan-trigger";
import { ScanStatusBadge } from "@/components/scans/scan-status-badge";
import { ScanConfigCard } from "@/components/scans/scan-config-card";
import { ConvergenceRounds } from "@/components/scans/convergence-rounds";
import { CountsSummary } from "@/components/scans/counts-summary";
import { RoutesTable } from "@/components/scans/routes-table";
import { ErrorsList } from "@/components/scans/errors-list";
import { IncompleteWarningBanner } from "@/components/scans/incomplete-warning-banner";
import { SectionHeader } from "@/components/layout/section-header";
import { LoadingState, ErrorState } from "@/components/layout/async-state";
import { BarChartIcon, DownloadIcon, PlayIcon } from "@/components/icons";

export default function ScanReportPage() {
  const scanState = useApiResource(() => fetchLatestScan(), []);
  const [downloading, setDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const scan = scanState.status === "success" ? scanState.data : null;
  const scanTrigger = useScanTrigger(scan, fetchLatestScan, () => scanState.refetch());

  async function handleDownload(scanId: string) {
    setDownloading(true);
    setDownloadError(null);
    try {
      await downloadScanExport(scanId);
    } catch {
      setDownloadError("We couldn't download the export. Please try again.");
    } finally {
      setDownloading(false);
    }
  }

  if (scanState.status === "loading") return <LoadingState label="Loading latest scan…" />;
  if (scanState.status === "error") {
    return <ErrorState message={scanState.error} onRetry={scanState.refetch} />;
  }

  if (!scan) {
    return (
      <div className="flex flex-col items-center gap-4 rounded-2xl border border-[#E5EAF2] bg-white px-4 py-16 text-center dark:border-zinc-800 dark:bg-zinc-900">
        <p className="text-sm text-[#64748B] dark:text-zinc-400">No scan has been recorded yet.</p>
        <RunScanButton scanTrigger={scanTrigger} />
      </div>
    );
  }

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

        <div className="flex flex-col items-end gap-1.5">
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => handleDownload(scan.scan_id)}
              disabled={downloading}
              className="flex items-center gap-2 rounded-xl border border-[#E5EAF2] bg-white px-3.5 py-2 text-sm font-medium text-[#102A5C] outline-none hover:bg-[#F8FAFF] focus-visible:ring-2 focus-visible:ring-violet-500/30 disabled:cursor-not-allowed disabled:opacity-60 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-200"
            >
              <DownloadIcon />
              {downloading ? "Downloading…" : "Download report"}
            </button>
            <RunScanButton scanTrigger={scanTrigger} />
          </div>
          {downloadError ? (
            <p role="alert" className="text-xs text-red-700 dark:text-red-400">
              {downloadError}
            </p>
          ) : null}
          {scanTrigger.state === "error" && scanTrigger.error ? (
            <p role="alert" className="text-xs text-red-700 dark:text-red-400">
              {scanTrigger.error}
            </p>
          ) : null}
          {scanTrigger.state === "running" ? (
            <p role="status" className="text-xs text-[#64748B] dark:text-zinc-400">
              Scan in progress — this page will update automatically.
            </p>
          ) : null}
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

function RunScanButton({
  scanTrigger,
}: {
  scanTrigger: { state: ScanTriggerState; start: () => void };
}) {
  const isBusy = scanTrigger.state === "starting" || scanTrigger.state === "running";
  const label =
    scanTrigger.state === "starting" ? "Starting…" : scanTrigger.state === "running" ? "Running…" : "Run scan now";

  return (
    <button
      type="button"
      onClick={scanTrigger.start}
      disabled={isBusy}
      className="flex items-center gap-2 rounded-xl bg-violet-600 px-3.5 py-2 text-sm font-medium text-white outline-none hover:bg-violet-700 focus-visible:ring-2 focus-visible:ring-violet-600 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60 dark:focus-visible:ring-offset-zinc-950"
    >
      <PlayIcon />
      {label}
    </button>
  );
}
