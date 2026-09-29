"use client";

import type { EvidencedText } from "@/lib/contracts/job";

// The backend does not yet populate evidence_ref (see CLAUDE.md "Not done
// yet": "evidence_ref links... not populated"), so this only ever renders
// the "No evidence reference" fallback today. Kept ready for when the
// backend adds a real GET /jobs/{id}/evidence/{evidence_ref} endpoint —
// at that point this shows a fetched excerpt instead of just the ref.
function EvidenceLink({ evidenceRef }: { evidenceRef: string | null }) {
  if (!evidenceRef) {
    return <span className="text-xs text-zinc-400 dark:text-zinc-500">No evidence reference</span>;
  }

  return <span className="text-xs text-zinc-500 dark:text-zinc-400">Evidence ref: {evidenceRef}</span>;
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
