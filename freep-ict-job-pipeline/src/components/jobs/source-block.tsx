import type { JobRecord } from "@/lib/contracts/job";
import { formatDateTime } from "@/lib/format";
import { DetailField } from "@/components/jobs/detail-field";

export function SourceBlock({ job }: { job: JobRecord }) {
  return (
    <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      <DetailField
        label="Freep URL"
        value={
          <a
            href={job.identity.canonical_url}
            target="_blank"
            rel="noopener noreferrer"
            className="truncate text-violet-700 underline-offset-2 hover:underline dark:text-violet-300"
          >
            {job.identity.canonical_url}
          </a>
        }
      />
      <DetailField label="Observed at" value={formatDateTime(job.version.last_seen_at)} />
      <DetailField label="Content hash" value={<span className="font-mono text-xs">{job.version.content_hash}</span>} />
      <DetailField label="Record version" value={job.version.record_version} />
      <DetailField label="Schema version" value={job.schema_version} />
    </dl>
  );
}
