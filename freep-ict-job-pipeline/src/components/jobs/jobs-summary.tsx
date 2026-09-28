import type { JobRecord } from "@/lib/contracts/job";

function count(jobs: JobRecord[], predicate: (job: JobRecord) => boolean): number {
  return jobs.reduce((total, job) => (predicate(job) ? total + 1 : total), 0);
}

export function JobsSummary({ jobs }: { jobs: JobRecord[] }) {
  const stats = [
    { label: "Total jobs", value: jobs.length },
    { label: "Open", value: count(jobs, (job) => job.publication.status === "open") },
    { label: "New", value: count(jobs, (job) => job.change_type === "new") },
    { label: "Changed", value: count(jobs, (job) => job.change_type === "changed") },
    { label: "Closed", value: count(jobs, (job) => job.publication.status === "closed") },
    {
      label: "Needs attention",
      value: count(
        jobs,
        (job) => job.change_type === "uncertain" || job.change_type === "temporarily_not_found",
      ),
    },
  ];

  return (
    <dl className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
      {stats.map((stat) => (
        <div
          key={stat.label}
          className="rounded-2xl border border-zinc-200 bg-white px-4 py-3 dark:border-zinc-800 dark:bg-zinc-900"
        >
          <dt className="text-xs font-medium text-zinc-500 dark:text-zinc-400">{stat.label}</dt>
          <dd className="mt-1 text-2xl font-semibold text-zinc-900 dark:text-zinc-50">{stat.value}</dd>
        </div>
      ))}
    </dl>
  );
}
