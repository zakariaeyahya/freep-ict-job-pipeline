import type { ConvergenceRound } from "@/lib/contracts/scan";
import { formatDateTime } from "@/lib/format";

export function ConvergenceRounds({ rounds }: { rounds: ConvergenceRound[] }) {
  return (
    <div className="w-full rounded-2xl border border-zinc-200 bg-white p-5 lg:w-80 dark:border-zinc-800 dark:bg-zinc-900">
      <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">Convergence rounds</h2>
      <ol className="mt-4 flex flex-col gap-4">
        {rounds.map((round, index) => (
          <li key={round.round} className="flex gap-3">
            <div className="flex flex-col items-center">
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-xs font-semibold text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300">
                {round.round}
              </span>
              {index < rounds.length - 1 ? (
                <span className="mt-1 h-full w-px bg-zinc-200 dark:bg-zinc-700" aria-hidden="true" />
              ) : null}
            </div>
            <div className="flex flex-1 flex-wrap items-start justify-between gap-2 pb-1">
              <div>
                <p className="text-sm text-zinc-900 dark:text-zinc-50">
                  Round {round.round}: {round.new_routes_discovered} new route
                  {round.new_routes_discovered === 1 ? "" : "s"} discovered
                  {round.converged ? " — converged" : ""}
                </p>
                <p className="text-xs text-zinc-500 dark:text-zinc-400">{formatDateTime(round.observed_at)}</p>
              </div>
              {round.converged ? (
                <span className="inline-flex items-center rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-medium text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300">
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
