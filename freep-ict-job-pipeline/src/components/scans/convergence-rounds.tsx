import type { ConvergenceRound } from "@/lib/contracts/scan";
import { formatDateTime } from "@/lib/format";
import { SectionHeader } from "@/components/layout/section-header";
import { ConvergeIcon } from "@/components/icons";

export function ConvergenceRounds({ rounds }: { rounds: ConvergenceRound[] }) {
  return (
    <div className="w-full rounded-2xl border border-[#E5EAF2] bg-white p-5 lg:w-80 dark:border-zinc-800 dark:bg-zinc-900">
      <SectionHeader icon={<ConvergeIcon />} title="Convergence rounds" />
      <ol className="mt-5 flex flex-col">
        {rounds.map((round, index) => (
          <li key={round.round} className="flex gap-3">
            <div className="flex flex-col items-center">
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-emerald-500 text-xs font-semibold text-white">
                {round.round}
              </span>
              {index < rounds.length - 1 ? (
                <span className="my-1 w-px flex-1 bg-emerald-200 dark:bg-emerald-500/30" aria-hidden="true" />
              ) : null}
            </div>
            <div className="flex flex-1 flex-wrap items-start justify-between gap-2 pb-5">
              <div>
                <p className="text-sm font-medium text-[#102A5C] dark:text-zinc-50">
                  Round {round.round}: {round.new_routes_discovered} new route
                  {round.new_routes_discovered === 1 ? "" : "s"} discovered
                  {round.converged ? " — converged" : ""}
                </p>
                <p className="mt-0.5 text-xs text-[#64748B] dark:text-zinc-400">{formatDateTime(round.observed_at)}</p>
              </div>
              {round.converged ? (
                <span className="inline-flex items-center rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300">
                  Converged
                </span>
              ) : null}
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
