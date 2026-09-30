"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

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

const PAGE_SIZE = 8;

export function JobsTable({ jobs }: { jobs: JobRecord[] }) {
  const router = useRouter();
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<JobStatus | "all">("all");
  const [changeType, setChangeType] = useState<ChangeType | "all">("all");
  const [changedSince, setChangedSince] = useState("");
  const [page, setPage] = useState(1);

  const filtered = useMemo(() => {
    const query = search.trim().toLowerCase();
    const changedSinceMs = changedSince ? new Date(changedSince).getTime() : null;

    return jobs.filter((job) => {
      if (status !== "all" && job.publication.status !== status) return false;
      if (changeType !== "all" && job.change_type !== changeType) return false;
      if (changedSinceMs !== null && new Date(job.version.last_seen_at).getTime() < changedSinceMs) return false;

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
  }, [jobs, search, status, changeType, changedSince]);

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const currentPage = Math.min(page, pageCount);
  const paginated = filtered.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE);

  function updateFilter<T>(setter: (value: T) => void) {
    return (value: T) => {
      setter(value);
      setPage(1);
    };
  }

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
            onChange={(event) => updateFilter(setSearch)(event.target.value)}
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
            onChange={(event) => updateFilter(setStatus)(event.target.value as JobStatus | "all")}
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
            onChange={(event) => updateFilter(setChangeType)(event.target.value as ChangeType | "all")}
            className="rounded-2xl border border-zinc-200 bg-white px-4 py-2.5 text-sm text-zinc-900 outline-none focus-visible:border-violet-500 focus-visible:ring-2 focus-visible:ring-violet-500/30 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50"
          >
            {CHANGE_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div className="flex flex-col gap-1.5">
          <label htmlFor="job-changed-since" className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
            Changed since
          </label>
          <div className="flex items-center gap-1.5">
            <input
              id="job-changed-since"
              type="date"
              value={changedSince}
              onChange={(event) => updateFilter(setChangedSince)(event.target.value)}
              className="rounded-2xl border border-zinc-200 bg-white px-4 py-2.5 text-sm text-zinc-900 outline-none focus-visible:border-violet-500 focus-visible:ring-2 focus-visible:ring-violet-500/30 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50"
            />
            {changedSince ? (
              <button
                type="button"
                onClick={() => updateFilter(setChangedSince)("")}
                aria-label="Clear changed since filter"
                className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl text-zinc-500 outline-none hover:bg-zinc-50 focus-visible:ring-2 focus-visible:ring-violet-500/30 dark:text-zinc-400 dark:hover:bg-zinc-800"
              >
                ×
              </button>
            ) : null}
          </div>
        </div>
      </div>

      <div className="overflow-x-auto rounded-2xl border border-zinc-200 dark:border-zinc-800">
        <table className="min-w-full divide-y divide-zinc-200 dark:divide-zinc-800">
          <thead className="bg-zinc-50 dark:bg-zinc-900">
            <tr>
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
            {paginated.map((job) => (
              <tr
                key={job.identity.internal_job_id}
                onClick={(event) => {
                  // The title link handles its own navigation (keyboard, new tab).
                  if ((event.target as HTMLElement).closest("a")) return;
                  router.push(`/jobs/${job.identity.internal_job_id}`);
                }}
                className="cursor-pointer transition-colors hover:bg-violet-50 focus-within:bg-violet-50 dark:hover:bg-violet-500/10 dark:focus-within:bg-violet-500/10"
              >
                <td className="px-4 py-3 text-sm">
                  <Link
                    href={`/jobs/${job.identity.internal_job_id}`}
                    className="font-medium text-violet-700 underline-offset-2 hover:underline focus-visible:underline dark:text-violet-300"
                  >
                    {job.core.title}
                  </Link>
                </td>
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
                <td colSpan={6} className="px-4 py-8 text-center text-sm text-zinc-500 dark:text-zinc-400">
                  No jobs match your search and filters.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          Showing {paginated.length === 0 ? 0 : (currentPage - 1) * PAGE_SIZE + 1}
          {"–"}
          {(currentPage - 1) * PAGE_SIZE + paginated.length} of {filtered.length} jobs
        </p>

        {pageCount > 1 ? (
          <nav aria-label="Jobs pagination" className="flex items-center gap-1">
            <button
              type="button"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              aria-label="Previous page"
              className="flex h-8 w-8 items-center justify-center rounded-xl border border-zinc-200 text-sm text-zinc-600 outline-none focus-visible:ring-2 focus-visible:ring-violet-500/30 disabled:cursor-not-allowed disabled:opacity-40 dark:border-zinc-700 dark:text-zinc-400"
            >
              ‹
            </button>

            {Array.from({ length: pageCount }, (_, i) => i + 1).map((pageNumber) => (
              <button
                key={pageNumber}
                type="button"
                onClick={() => setPage(pageNumber)}
                aria-current={pageNumber === currentPage ? "page" : undefined}
                className={
                  pageNumber === currentPage
                    ? "flex h-8 w-8 items-center justify-center rounded-xl bg-violet-600 text-sm font-medium text-white outline-none focus-visible:ring-2 focus-visible:ring-violet-600 focus-visible:ring-offset-2"
                    : "flex h-8 w-8 items-center justify-center rounded-xl text-sm text-zinc-600 outline-none hover:bg-zinc-50 focus-visible:ring-2 focus-visible:ring-violet-500/30 dark:text-zinc-400 dark:hover:bg-zinc-800"
                }
              >
                {pageNumber}
              </button>
            ))}

            <button
              type="button"
              onClick={() => setPage((p) => Math.min(pageCount, p + 1))}
              disabled={currentPage === pageCount}
              aria-label="Next page"
              className="flex h-8 w-8 items-center justify-center rounded-xl border border-zinc-200 text-sm text-zinc-600 outline-none focus-visible:ring-2 focus-visible:ring-violet-500/30 disabled:cursor-not-allowed disabled:opacity-40 dark:border-zinc-700 dark:text-zinc-400"
            >
              ›
            </button>
          </nav>
        ) : null}
      </div>
    </div>
  );
}
