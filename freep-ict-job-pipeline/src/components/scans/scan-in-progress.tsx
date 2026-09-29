// Live "scan in progress" view for the Scan Report page, driven by
// GET /api/v1/scans/current (via useScanTrigger's progress polling).
// Phases match the real pipeline stages (pipeline.py's ScanPipeline),
// not an invented set of steps — "discovering" (finding job routes),
// "processing" (fetching/parsing/extracting each job), "storing"
// (validating and persisting results).

import type { ScanProgress } from "@/lib/contracts/scan-progress";
import { SectionHeader } from "@/components/layout/section-header";
import { ClockIcon, RouteIcon } from "@/components/icons";

const PHASE_LABEL: Record<ScanProgress["phase"], string> = {
  discovering: "Discovering job routes…",
  processing: "Fetching and processing jobs…",
  storing: "Validating and storing results…",
};

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
}

export function ScanInProgress({ progress }: { progress: ScanProgress }) {
  const total = progress.jobs_total;
  const processed = progress.jobs_processed;
  const percent = total && total > 0 ? Math.round((processed / total) * 100) : null;

  return (
    <div className="flex flex-col gap-4 lg:flex-row">
      <div className="flex-1 rounded-2xl border border-[#E5EAF2] bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
        <SectionHeader icon={<RouteIcon />} title={PHASE_LABEL[progress.phase]} />
        <p className="mt-1 text-sm text-[#64748B] dark:text-zinc-400">Scanning Freep job sources</p>

        {total !== null ? (
          <div className="mt-4">
            <div className="flex items-center justify-between text-xs font-medium text-[#64748B] dark:text-zinc-400">
              <span>{processed} / {total} jobs processed</span>
              {percent !== null ? <span>{percent}%</span> : null}
            </div>
            <div
              role="progressbar"
              aria-valuenow={percent ?? undefined}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuetext={`${processed} of ${total} jobs processed`}
              aria-label="Scan progress"
              className="mt-1.5 h-2 w-full overflow-hidden rounded-full bg-[#EEF0FF] dark:bg-zinc-800"
            >
              <div
                className="h-full rounded-full bg-violet-600 transition-[width] duration-500 ease-out"
                style={{ width: `${percent ?? 0}%` }}
              />
            </div>
          </div>
        ) : (
          <p className="mt-4 text-xs font-medium text-[#64748B] dark:text-zinc-400">
            Counting available job routes…
          </p>
        )}
      </div>

      <div className="w-full rounded-2xl border border-[#E5EAF2] bg-[#FBFCFF] p-5 dark:border-zinc-800 dark:bg-zinc-900/60 lg:w-80">
        <SectionHeader icon={<RouteIcon />} title="Live activity" />
        {progress.activity.length === 0 ? (
          <p className="mt-4 text-sm text-[#64748B] dark:text-zinc-400">Starting up…</p>
        ) : (
          <ol className="mt-4 flex flex-col gap-3">
            {[...progress.activity].reverse().map((event, index) => (
              <li key={`${event.at}-${index}`} className="flex items-start gap-2.5">
                <span
                  aria-hidden="true"
                  className={
                    index === 0
                      ? "mt-1 h-2 w-2 shrink-0 rounded-full bg-violet-600"
                      : "mt-1 h-2 w-2 shrink-0 rounded-full bg-[#CBD5E1] dark:bg-zinc-700"
                  }
                />
                <div className="min-w-0">
                  <p className="truncate text-sm text-[#102A5C] dark:text-zinc-200">{event.message}</p>
                  <p className="text-xs text-[#94A3B8] dark:text-zinc-500">{formatTime(event.at)}</p>
                </div>
              </li>
            ))}
          </ol>
        )}
      </div>
    </div>
  );
}
