import type { JobVersionEntry } from "@/lib/contracts/job-version";
import { formatDateTime } from "@/lib/format";
import { ChangeBadge } from "@/components/jobs/status-badge";

export function VersionHistory({
  versions,
  currentVersion,
}: {
  versions: JobVersionEntry[];
  currentVersion: { record_version: number; observed_at: string; content_hash: string };
}) {
  // Past versions must be strictly older than the current observation —
  // guards against a data mistake producing a duplicate record_version.
  const pastVersions = versions.filter((v) => v.record_version < currentVersion.record_version);

  const allEntries: Array<{
    record_version: number;
    observed_at: string;
    content_hash: string;
    change_type: JobVersionEntry["change_type"] | null;
    summary: string | null;
  }> = [
    ...pastVersions,
    {
      record_version: currentVersion.record_version,
      observed_at: currentVersion.observed_at,
      content_hash: currentVersion.content_hash,
      change_type: null,
      summary: "Current observation.",
    },
  ].sort((a, b) => b.record_version - a.record_version);

  return (
    <ol className="flex flex-col gap-3">
      {allEntries.map((entry) => (
        <li
          key={entry.record_version}
          className="flex flex-wrap items-start justify-between gap-2 rounded-xl border border-zinc-200 bg-white px-3 py-2.5 dark:border-zinc-800 dark:bg-zinc-900"
        >
          <div>
            <p className="text-sm font-medium text-[#102A5C] dark:text-zinc-50">
              Version {entry.record_version}
              {entry.change_type ? null : (
                <span className="ml-2 text-xs font-normal text-zinc-400 dark:text-zinc-500">(current)</span>
              )}
            </p>
            <p className="text-xs text-zinc-500 dark:text-zinc-400">{formatDateTime(entry.observed_at)}</p>
            {entry.summary ? (
              <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">{entry.summary}</p>
            ) : null}
            <p className="mt-1 font-mono text-xs text-zinc-400 dark:text-zinc-500">{entry.content_hash}</p>
          </div>
          {entry.change_type ? <ChangeBadge changeType={entry.change_type} /> : null}
        </li>
      ))}
    </ol>
  );
}
