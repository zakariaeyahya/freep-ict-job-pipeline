import type { ScanCounts } from "@/lib/contracts/scan";

const TILES: Array<{ key: keyof ScanCounts; label: string }> = [
  { key: "discovered", label: "Discovered" },
  { key: "processed", label: "Processed" },
  { key: "duplicates", label: "Duplicates" },
  { key: "new", label: "New" },
  { key: "changed", label: "Changed" },
  { key: "closed", label: "Closed" },
  { key: "temporarily_not_found", label: "Temporarily not found" },
  { key: "errors", label: "Errors" },
];

export function CountsSummary({ counts }: { counts: ScanCounts }) {
  return (
    <dl className="grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-8">
      {TILES.map((tile) => (
        <div
          key={tile.key}
          className="rounded-2xl border border-zinc-200 bg-zinc-50 px-3 py-2.5 dark:border-zinc-800 dark:bg-zinc-800/50"
        >
          <dt className="text-xs font-medium text-zinc-500 dark:text-zinc-400">{tile.label}</dt>
          <dd className="mt-0.5 text-xl font-bold text-zinc-900 dark:text-zinc-50">{counts[tile.key]}</dd>
        </div>
      ))}
    </dl>
  );
}
