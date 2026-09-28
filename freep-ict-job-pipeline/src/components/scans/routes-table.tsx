import type { RouteVisit } from "@/lib/contracts/scan";
import { RouteResultBadge } from "@/components/scans/route-result-badge";
import { SectionHeader } from "@/components/layout/section-header";
import { MoreIcon, RouteIcon } from "@/components/icons";

export function RoutesTable({ routes }: { routes: RouteVisit[] }) {
  return (
    <div className="rounded-2xl border border-[#E5EAF2] bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
      <SectionHeader
        icon={<RouteIcon />}
        title="Routes"
        action={
          <span className="text-xs font-medium text-[#64748B] dark:text-zinc-400">
            {routes.length} route{routes.length === 1 ? "" : "s"}
          </span>
        }
      />

      <div className="mt-4 overflow-x-auto rounded-xl border border-[#E5EAF2] dark:border-zinc-800">
        <table className="min-w-full divide-y divide-[#E5EAF2] dark:divide-zinc-800">
          <thead className="bg-[#EEF0FF] dark:bg-zinc-800/60">
            <tr>
              <th scope="col" className="w-10 px-3 py-2.5 text-left text-[11px] font-semibold uppercase tracking-wide text-[#64748B] dark:text-zinc-400">
                #
              </th>
              <th scope="col" className="px-3 py-2.5 text-left text-[11px] font-semibold uppercase tracking-wide text-[#64748B] dark:text-zinc-400">
                Route URL
              </th>
              <th scope="col" className="px-3 py-2.5 text-left text-[11px] font-semibold uppercase tracking-wide text-[#64748B] dark:text-zinc-400">
                Pages visited
              </th>
              <th scope="col" className="px-3 py-2.5 text-left text-[11px] font-semibold uppercase tracking-wide text-[#64748B] dark:text-zinc-400">
                Result
              </th>
              <th scope="col" className="px-3 py-2.5 text-left text-[11px] font-semibold uppercase tracking-wide text-[#64748B] dark:text-zinc-400">
                Error
              </th>
              <th scope="col" className="w-10 px-3 py-2.5" />
            </tr>
          </thead>
          <tbody className="divide-y divide-[#E5EAF2] bg-white dark:divide-zinc-800 dark:bg-zinc-900">
            {routes.map((route, index) => (
              <tr key={route.url} className="hover:bg-[#FBFCFF] dark:hover:bg-zinc-800/40">
                <td className="px-3 py-3 text-sm text-[#64748B] dark:text-zinc-400">{index + 1}</td>
                <td className="max-w-xs truncate px-3 py-3 font-mono text-xs text-[#102A5C] dark:text-zinc-300" title={route.url}>
                  {route.url}
                </td>
                <td className="px-3 py-3 text-sm font-semibold text-[#102A5C] dark:text-zinc-100">{route.pages_visited}</td>
                <td className="px-3 py-3 text-sm">
                  <RouteResultBadge result={route.result} />
                </td>
                <td className="px-3 py-3 text-sm text-[#64748B] dark:text-zinc-400">{route.error ?? "—"}</td>
                <td className="px-3 py-3 text-right">
                  <button
                    type="button"
                    disabled
                    aria-label="Row actions"
                    title="No actions are available yet."
                    className="inline-flex h-7 w-7 items-center justify-center rounded-lg text-[#64748B] outline-none disabled:cursor-not-allowed disabled:opacity-40 dark:text-zinc-400"
                  >
                    <MoreIcon />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
