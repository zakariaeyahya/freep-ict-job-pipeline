import type { RouteVisit } from "@/lib/contracts/scan";
import { RouteResultBadge } from "@/components/scans/route-result-badge";

export function RoutesTable({ routes }: { routes: RouteVisit[] }) {
  return (
    <div className="rounded-2xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">Routes</h2>
        <span className="text-xs text-zinc-500 dark:text-zinc-400">
          {routes.length} route{routes.length === 1 ? "" : "s"}
        </span>
      </div>

      <div className="mt-4 overflow-x-auto">
        <table className="min-w-full divide-y divide-zinc-200 dark:divide-zinc-800">
          <thead>
            <tr>
              <th scope="col" className="w-10 px-2 py-2 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
                #
              </th>
              <th scope="col" className="px-2 py-2 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
                Route URL
              </th>
              <th scope="col" className="px-2 py-2 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
                Pages visited
              </th>
              <th scope="col" className="px-2 py-2 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
                Result
              </th>
              <th scope="col" className="px-2 py-2 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
                Error
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
            {routes.map((route, index) => (
              <tr key={route.url}>
                <td className="px-2 py-2.5 text-sm text-zinc-500 dark:text-zinc-400">{index + 1}</td>
                <td className="max-w-xs truncate px-2 py-2.5 font-mono text-xs text-zinc-700 dark:text-zinc-300" title={route.url}>
                  {route.url}
                </td>
                <td className="px-2 py-2.5 text-sm text-zinc-700 dark:text-zinc-300">{route.pages_visited}</td>
                <td className="px-2 py-2.5 text-sm">
                  <RouteResultBadge result={route.result} />
                </td>
                <td className="px-2 py-2.5 text-sm text-zinc-500 dark:text-zinc-400">{route.error ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
