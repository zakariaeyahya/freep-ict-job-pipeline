import { getJobs } from "@/lib/mock/jobs";
import { JobsSummary } from "@/components/jobs/jobs-summary";
import { JobsTable } from "@/components/jobs/jobs-table";
import { ScanStatusBanner } from "@/components/jobs/scan-status-banner";

export default function JobsPage() {
  const jobs = getJobs();

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-50">Freep ICT Jobs</h1>
        <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
          Manage and review discovered assignments
        </p>
      </div>

      <JobsSummary jobs={jobs} />
      <ScanStatusBanner />
      <JobsTable jobs={jobs} />
    </div>
  );
}
