import type { Attachment } from "@/lib/contracts/job";
import { RetrievalStatusBadge } from "@/components/jobs/retrieval-status-badge";

export function AttachmentsList({ attachments }: { attachments: Attachment[] }) {
  if (attachments.length === 0) {
    return <p className="text-sm text-zinc-400 dark:text-zinc-500">No attachments found in the source.</p>;
  }

  return (
    <ul className="flex flex-col gap-2">
      {attachments.map((attachment) => (
        <li
          key={attachment.url}
          className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-zinc-200 bg-white px-3 py-2.5 dark:border-zinc-800 dark:bg-zinc-900"
        >
          <div className="min-w-0">
            <a
              href={attachment.url}
              target="_blank"
              rel="noopener noreferrer"
              className="block truncate text-sm font-medium text-violet-700 underline-offset-2 hover:underline dark:text-violet-300"
              title={attachment.url}
            >
              {attachment.name}
            </a>
            <p className="text-xs text-zinc-500 dark:text-zinc-400">{attachment.type}</p>
          </div>
          <RetrievalStatusBadge status={attachment.retrieval_status} />
        </li>
      ))}
    </ul>
  );
}
