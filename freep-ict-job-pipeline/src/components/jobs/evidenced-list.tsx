"use client";

import { useState } from "react";
import type { EvidencedText } from "@/lib/contracts/job";
import { getEvidence } from "@/lib/mock/evidence";

function EvidenceLink({ evidenceRef }: { evidenceRef: string | null }) {
  const [open, setOpen] = useState(false);

  if (!evidenceRef) {
    return <span className="text-xs text-zinc-400 dark:text-zinc-500">No evidence reference</span>;
  }

  const evidence = getEvidence(evidenceRef);

  return (
    <div>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="text-xs font-medium text-violet-700 underline-offset-2 outline-none hover:underline focus-visible:underline dark:text-violet-300"
      >
        {open ? "Hide evidence" : "View evidence"} ({evidenceRef})
      </button>
      {open ? (
        <div className="mt-1.5 rounded-xl border border-zinc-200 bg-zinc-50 p-3 text-xs dark:border-zinc-800 dark:bg-zinc-800/50">
          {evidence ? (
            <>
              <p className="font-mono text-zinc-700 dark:text-zinc-300">&ldquo;{evidence.excerpt}&rdquo;</p>
              <a
                href={evidence.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-1.5 inline-block text-violet-700 underline-offset-2 hover:underline dark:text-violet-300"
              >
                Open source
              </a>
            </>
          ) : (
            <p className="text-zinc-500 dark:text-zinc-400">
              No source excerpt available yet for this reference.
            </p>
          )}
        </div>
      ) : null}
    </div>
  );
}

export function EvidencedList({ title, items }: { title: string; items: EvidencedText[] }) {
  return (
    <div>
      <h3 className="text-[11px] font-semibold uppercase tracking-wide text-[#64748B] dark:text-zinc-400">
        {title}
      </h3>
      {items.length === 0 ? (
        <p className="mt-1.5 text-sm text-zinc-400 dark:text-zinc-500">None found in the source.</p>
      ) : (
        <ol className="mt-1.5 flex flex-col gap-2.5">
          {items.map((item, index) => (
            <li key={`${title}-${index}`} className="rounded-xl border border-zinc-200 bg-white p-3 dark:border-zinc-800 dark:bg-zinc-900">
              <p className="text-sm text-[#102A5C] dark:text-zinc-50">{item.text}</p>
              <div className="mt-1.5">
                <EvidenceLink evidenceRef={item.evidence_ref} />
              </div>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
