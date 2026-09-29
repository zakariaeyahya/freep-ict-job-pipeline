"use client";

import { use } from "react";
import Link from "next/link";

import { fetchJob, fetchJobVersions } from "@/api/jobs";
import { useApiResource } from "@/lib/use-api-resource";
import { formatDateTime } from "@/lib/format";
import { StatusBadge, ChangeBadge } from "@/components/jobs/status-badge";
import { DetailField } from "@/components/jobs/detail-field";
import { EvidencedList } from "@/components/jobs/evidenced-list";
import { AttachmentsList } from "@/components/jobs/attachments-list";
import { QualityBlock } from "@/components/jobs/quality-block";
import { SourceBlock } from "@/components/jobs/source-block";
import { VersionHistory } from "@/components/jobs/version-history";
import { SectionHeader } from "@/components/layout/section-header";
import { LoadingState, ErrorState } from "@/components/layout/async-state";
import { BriefcaseIcon, DatabaseIcon, FileIcon, HistoryIcon, ListIcon, ShieldCheckIcon } from "@/components/icons";

export default function JobDetailPage({
  params,
}: {
  params: Promise<{ internal_job_id: string }>;
}) {
  const { internal_job_id: internalJobId } = use(params);

  const jobState = useApiResource(() => fetchJob(internalJobId), [internalJobId]);
  const versionsState = useApiResource(() => fetchJobVersions(internalJobId), [internalJobId]);

  if (jobState.status === "loading") return <LoadingState label="Loading job…" />;
  if (jobState.status === "error") {
    return <ErrorState message={jobState.error} onRetry={jobState.refetch} />;
  }

  const job = jobState.data;

  return (
    <div className="flex flex-col gap-5">
      <div>
        <Link
          href="/jobs"
          className="text-sm font-medium text-violet-700 underline-offset-2 hover:underline dark:text-violet-300"
        >
          ← Back to Jobs
        </Link>

        <div className="mt-2 flex flex-wrap items-center gap-3">
          <h1 className="text-[28px] font-bold leading-tight text-[#102A5C] dark:text-zinc-50">
            {job.core.title}
          </h1>
          <StatusBadge status={job.publication.status} />
          <ChangeBadge changeType={job.change_type} />
        </div>
        <p className="mt-1 text-sm text-[#64748B] dark:text-zinc-400">
          {job.identity.internal_job_id} · {job.core.client_name ?? "Unknown client"}
        </p>
      </div>

      {/* Core fields */}
      <div className="rounded-2xl border border-[#E5EAF2] bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
        <SectionHeader icon={<BriefcaseIcon />} title="Core details" />
        <dl className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
          <DetailField label="Client" value={job.core.client_name} />
          <DetailField label="Location" value={job.delivery.location} />
          <DetailField label="Remote policy" value={job.delivery.remote_policy} />
          <DetailField
            label="Hours"
            value={
              job.delivery.hours_min !== null || job.delivery.hours_max !== null
                ? `${job.delivery.hours_min ?? "?"}–${job.delivery.hours_max ?? "?"} h/week`
                : null
            }
          />
          <DetailField label="Start date" value={job.delivery.start_date} />
          <DetailField label="End date" value={job.delivery.end_date} />
          <DetailField
            label="Publication"
            value={job.publication.publication_datetime ? formatDateTime(job.publication.publication_datetime) : null}
          />
          <DetailField
            label="Closing"
            value={job.publication.closing_datetime ? formatDateTime(job.publication.closing_datetime) : null}
          />
          <DetailField label="Rate"
            value={
              job.commercial.rate_min !== null || job.commercial.rate_max !== null
                ? `${job.commercial.rate_min ?? "?"}–${job.commercial.rate_max ?? "?"} ${job.commercial.currency ?? ""}`
                : null
            }
          />
        </dl>
        {job.core.description_clean ? (
          <div className="mt-5 border-t border-[#E5EAF2] pt-4 dark:border-zinc-800">
            <dt className="text-[11px] font-semibold uppercase tracking-wide text-[#64748B] dark:text-zinc-400">
              Description
            </dt>
            <dd className="mt-1 text-sm text-[#102A5C] dark:text-zinc-100">{job.core.description_clean}</dd>
          </div>
        ) : null}
      </div>

      {/* Selection: hard_requirements, wishes, award_criteria, competencies — never merged (AC06) */}
      <div className="rounded-2xl border border-[#E5EAF2] bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
        <SectionHeader icon={<ListIcon />} title="Selection criteria" />
        <div className="mt-4 grid grid-cols-1 gap-5 sm:grid-cols-2">
          <EvidencedList title="Hard requirements" items={job.selection.hard_requirements} />
          <EvidencedList title="Wishes" items={job.selection.wishes} />
          <EvidencedList title="Award criteria" items={job.selection.award_criteria} />
          <EvidencedList title="Competencies" items={job.selection.competencies} />
        </div>
      </div>

      {/* Attachments */}
      <div className="rounded-2xl border border-[#E5EAF2] bg-[#FBFCFF] p-5 dark:border-zinc-800 dark:bg-zinc-900/60">
        <SectionHeader icon={<FileIcon />} title="Attachments" />
        <div className="mt-4">
          <AttachmentsList attachments={job.attachments} />
        </div>
      </div>

      {/* Quality */}
      <div className="rounded-2xl border border-[#E5EAF2] bg-[#FBFCFF] p-5 dark:border-zinc-800 dark:bg-zinc-900/60">
        <SectionHeader icon={<ShieldCheckIcon />} title="Quality" />
        <div className="mt-4">
          <QualityBlock quality={job.quality} />
        </div>
      </div>

      {/* Source */}
      <div className="rounded-2xl border border-[#E5EAF2] bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
        <SectionHeader icon={<DatabaseIcon />} title="Source" />
        <div className="mt-4">
          <SourceBlock job={job} />
        </div>
      </div>

      {/* Version history */}
      <div className="rounded-2xl border border-[#E5EAF2] bg-[#FBFCFF] p-5 dark:border-zinc-800 dark:bg-zinc-900/60">
        <SectionHeader icon={<HistoryIcon />} title="Version history" />
        <div className="mt-4">
          {versionsState.status === "loading" ? <LoadingState label="Loading version history…" /> : null}
          {versionsState.status === "error" ? (
            <ErrorState message={versionsState.error} onRetry={versionsState.refetch} />
          ) : null}
          {versionsState.status === "success" ? (
            <VersionHistory
              versions={versionsState.data}
              currentVersion={{
                record_version: job.version.record_version,
                observed_at: job.version.last_seen_at,
                content_hash: job.version.content_hash,
              }}
            />
          ) : null}
        </div>
      </div>
    </div>
  );
}
