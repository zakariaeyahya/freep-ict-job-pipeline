import type { ScanCounts } from "@/lib/contracts/scan";

type Accent = "blue" | "green" | "grey" | "violet" | "cyan" | "red";

const DOT_CLASSES: Record<Accent, string> = {
  blue: "bg-blue-500",
  green: "bg-emerald-500",
  grey: "bg-zinc-400",
  violet: "bg-violet-500",
  cyan: "bg-cyan-500",
  red: "bg-rose-500",
};

const TILES: Array<{ key: keyof ScanCounts; label: string; accent: Accent }> = [
  { key: "discovered", label: "Discovered", accent: "blue" },
  { key: "processed", label: "Processed", accent: "green" },
  { key: "duplicates", label: "Duplicates", accent: "grey" },
  { key: "new", label: "New", accent: "violet" },
  { key: "changed", label: "Changed", accent: "blue" },
  { key: "closed", label: "Closed", accent: "grey" },
  { key: "temporarily_not_found", label: "Temporarily not found", accent: "cyan" },
  { key: "errors", label: "Errors", accent: "red" },
];

function Dot({ accent }: { accent: Accent }) {
  return <span aria-hidden="true" className={`h-2 w-2 shrink-0 rounded-full ${DOT_CLASSES[accent]}`} />;
}

export function CountsSummary({ counts }: { counts: ScanCounts }) {
  return (
    <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-8">
      {TILES.map((tile) => (
        <div
          key={tile.key}
          className="rounded-xl border border-[#E5EAF2] bg-[#FBFCFF] px-3.5 py-3 dark:border-zinc-800 dark:bg-zinc-800/50"
        >
          <dt className="flex items-center gap-1.5 text-[11px] font-medium text-[#64748B] dark:text-zinc-400">
            <Dot accent={tile.accent} />
            {tile.label}
          </dt>
          <dd className="mt-1.5 text-xl font-bold text-[#102A5C] dark:text-zinc-50">{counts[tile.key]}</dd>
        </div>
      ))}
    </dl>
  );
}
