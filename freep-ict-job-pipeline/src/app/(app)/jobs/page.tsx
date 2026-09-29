"use client";

import { fetchJobs } from "@/api/jobs";
import { fetchLatestScan } from "@/api/scans";
import { useApiResource } from "@/lib/use-api-resource";
import { JobsSummary } from "@/components/jobs/jobs-summary";
import { JobsTable } from "@/components/jobs/jobs-table";
import { ScanStatusBanner } from "@/components/jobs/scan-status-banner";
import { LoadingState, ErrorState } from "@/components/layout/async-state";

export default function JobsPage() {
  const jobsState = useApiResource(() => fetchJobs({ limit: 200 }), []);
  const scanState = useApiResource(() => fetchLatestScan(), []);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-50">Freep ICT Jobs</h1>
        <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
          Manage and review discovered assignments
        </p>
      </div>

      {jobsState.status === "loading" ? <LoadingState label="Loading jobs…" /> : null}
      {jobsState.status === "error" ? (
        <ErrorState message={jobsState.error} onRetry={jobsState.refetch} />
      ) : null}
      {jobsState.status === "success" ? (
        <>
          <JobsSummary jobs={jobsState.data.items} />
          {scanState.status === "success" && scanState.data ? (
            <ScanStatusBanner scan={scanState.data} />
          ) : null}
          <JobsTable jobs={jobsState.data.items} />
        </>
      ) : null}
    </div>
  );
}
