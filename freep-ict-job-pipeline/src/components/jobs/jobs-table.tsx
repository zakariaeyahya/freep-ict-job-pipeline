"use client";

import { useMemo, useState } from "react";
import Link from "next/link";

import type { ChangeType, JobRecord, JobStatus } from "@/lib/contracts/job";
import { formatDateTime } from "@/lib/format";
import { ChangeBadge, StatusBadge } from "@/components/jobs/status-badge";

const STATUS_OPTIONS: Array<{ value: JobStatus | "all"; label: string }> = [
  { value: "all", label: "All" },
  { value: "open", label: "Open" },
  { value: "closed", label: "Closed" },
  { value: "unknown", label: "Unknown" },
];

const CHANGE_OPTIONS: Array<{ value: ChangeType | "all"; label: string }> = [
  { value: "all", label: "All" },
  { value: "new", label: "New" },
  { value: "changed", label: "Modified" },
  { value: "unchanged", label: "Unchanged" },
  { value: "closed", label: "Closed" },
  { value: "temporarily_not_found", label: "Temporarily not found" },
  { value: "uncertain", label: "Uncertain" },
];

export function JobsTable({ jobs }: { jobs: JobRecord[] }) {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<JobStatus | "all">("all");
  const [changeType, setChangeType] = useState<ChangeType | "all">("all");

  const filtered = useMemo(() => {
    const query = search.trim().toLowerCase();

    return jobs.filter((job) => {
      if (status !== "all" && job.publication.status !== status) return false;
      if (changeType !== "all" && job.change_type !== changeType) return false;

      if (!query) return true;

      const haystack = [
        job.identity.internal_job_id,
        job.core.title,
        job.core.client_name ?? "",
        job.delivery.location ?? "",
      ]
        .join(" ")
        .toLowerCase();

      return haystack.includes(query);
    });
  }, [jobs, search, status, changeType]);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
        <div className="flex flex-1 flex-col gap-1.5">
          <label htmlFor="job-search" className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
            Search
          </label>
          <input
            id="job-search"
            type="search"
            placeholder="Search by title, client or location…"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            className="rounded-2xl border border-zinc-200 bg-white px-4 py-2.5 text-sm text-zinc-900 outline-none placeholder:text-zinc-400 focus-visible:border-violet-500 focus-visible:ring-2 focus-visible:ring-violet-500/30 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50"
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <label htmlFor="job-status" className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
            Status
          </label>
          <select
            id="job-status"
            value={status}
            onChange={(event) => setStatus(event.target.value as JobStatus | "all")}
            className="rounded-2xl border border-zinc-200 bg-white px-4 py-2.5 text-sm text-zinc-900 outline-none focus-visible:border-violet-500 focus-visible:ring-2 focus-visible:ring-violet-500/30 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50"
          >
            {STATUS_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div className="flex flex-col gap-1.5">
          <label htmlFor="job-change" className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
            Change
          </label>
          <select
            id="job-change"
            value={changeType}
            onChange={(event) => setChangeType(event.target.value as ChangeType | "all")}
            className="rounded-2xl border border-zinc-200 bg-white px-4 py-2.5 text-sm text-zinc-900 outline-none focus-visible:border-violet-500 focus-visible:ring-2 focus-visible:ring-violet-500/30 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50"
          >
            {CHANGE_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="overflow-x-auto rounded-2xl border border-zinc-200 dark:border-zinc-800">
        <table className="min-w-full divide-y divide-zinc-200 dark:divide-zinc-800">
          <thead className="bg-zinc-50 dark:bg-zinc-900">
            <tr>
              <th scope="col" className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
                ID
              </th>
              <th scope="col" className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
                Title
              </th>
              <th scope="col" className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
                Client
              </th>
              <th scope="col" className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
                Location
              </th>
              <th scope="col" className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
                Status
              </th>
              <th scope="col" className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
                Change
              </th>
              <th scope="col" className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
                Last seen
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-200 bg-white dark:divide-zinc-800 dark:bg-zinc-900">
            {filtered.map((job) => (
              <tr key={job.identity.internal_job_id} className="hover:bg-zinc-50 dark:hover:bg-zinc-800/60">
                <td className="px-4 py-3 text-sm">
                  <Link
                    href={`/jobs/${job.identity.internal_job_id}`}
                    className="font-medium text-violet-700 underline-offset-2 hover:underline focus-visible:underline dark:text-violet-300"
                  >
                    {job.identity.internal_job_id}
                  </Link>
                </td>
                <td className="px-4 py-3 text-sm text-zinc-900 dark:text-zinc-100">{job.core.title}</td>
                <td className="px-4 py-3 text-sm text-zinc-600 dark:text-zinc-400">
                  {job.core.client_name ?? "Unknown"}
                </td>
                <td className="px-4 py-3 text-sm text-zinc-600 dark:text-zinc-400">
                  {job.delivery.location ?? "Unknown"}
                </td>
                <td className="px-4 py-3 text-sm">
                  <StatusBadge status={job.publication.status} />
                </td>
                <td className="px-4 py-3 text-sm">
                  <ChangeBadge changeType={job.change_type} />
                </td>
                <td className="px-4 py-3 text-sm text-zinc-600 dark:text-zinc-400">
                  {formatDateTime(job.version.last_seen_at)}
                </td>
              </tr>
            ))}

            {filtered.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-sm text-zinc-500 dark:text-zinc-400">
                  No jobs match your search and filters.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>

      <p className="text-sm text-zinc-500 dark:text-zinc-400">
        Showing {filtered.length} of {jobs.length} jobs
      </p>
    </div>
  );
}
