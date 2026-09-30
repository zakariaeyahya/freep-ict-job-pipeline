import type { ReactNode } from "react";
import type { JobRecord } from "@/lib/contracts/job";

function count(jobs: JobRecord[], predicate: (job: JobRecord) => boolean): number {
  return jobs.reduce((total, job) => (predicate(job) ? total + 1 : total), 0);
}

type Accent = "lavender" | "mint" | "sky" | "violet" | "rose" | "turquoise";

const ACCENT_CLASSES: Record<Accent, { bg: string; icon: string; card: string; glow: string }> = {
  lavender: {
    bg: "bg-indigo-50 dark:bg-indigo-500/10",
    icon: "text-indigo-600 dark:text-indigo-300",
    card: "from-indigo-50/80 via-white to-white dark:from-indigo-500/15 dark:via-zinc-900 dark:to-zinc-900",
    glow: "bg-indigo-300/50 dark:bg-indigo-400/25",
  },
  mint: {
    bg: "bg-emerald-50 dark:bg-emerald-500/10",
    icon: "text-emerald-600 dark:text-emerald-300",
    card: "from-emerald-50/80 via-white to-white dark:from-emerald-500/15 dark:via-zinc-900 dark:to-zinc-900",
    glow: "bg-emerald-300/50 dark:bg-emerald-400/25",
  },
  sky: {
    bg: "bg-sky-50 dark:bg-sky-500/10",
    icon: "text-sky-600 dark:text-sky-300",
    card: "from-sky-50/80 via-white to-white dark:from-sky-500/15 dark:via-zinc-900 dark:to-zinc-900",
    glow: "bg-sky-300/50 dark:bg-sky-400/25",
  },
  violet: {
    bg: "bg-violet-50 dark:bg-violet-500/10",
    icon: "text-violet-600 dark:text-violet-300",
    card: "from-violet-50/80 via-white to-white dark:from-violet-500/15 dark:via-zinc-900 dark:to-zinc-900",
    glow: "bg-violet-300/50 dark:bg-violet-400/25",
  },
  rose: {
    bg: "bg-rose-50 dark:bg-rose-500/10",
    icon: "text-rose-600 dark:text-rose-300",
    card: "from-rose-50/80 via-white to-white dark:from-rose-500/15 dark:via-zinc-900 dark:to-zinc-900",
    glow: "bg-rose-300/50 dark:bg-rose-400/25",
  },
  turquoise: {
    bg: "bg-teal-50 dark:bg-teal-500/10",
    icon: "text-teal-600 dark:text-teal-300",
    card: "from-teal-50/80 via-white to-white dark:from-teal-500/15 dark:via-zinc-900 dark:to-zinc-900",
    glow: "bg-teal-300/50 dark:bg-teal-400/25",
  },
};

function BriefcaseIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
      <rect x="3" y="7" width="18" height="13" rx="2" />
      <path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
      <path d="M3 12h18" />
    </svg>
  );
}

function UnlockedBriefcaseIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
      <rect x="3" y="7" width="18" height="13" rx="2" />
      <path d="M9 7V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2" />
      <path d="M3 12h18" />
    </svg>
  );
}

function SparkleIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
      <path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5 18 18M18 6l-2.5 2.5M8.5 15.5 6 18" />
    </svg>
  );
}

function RefreshIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
      <path d="M4 12a8 8 0 0 1 14-5.3L21 9" />
      <path d="M21 5v4h-4" />
      <path d="M20 12a8 8 0 0 1-14 5.3L3 15" />
      <path d="M3 19v-4h4" />
    </svg>
  );
}

function MinusCircleIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
      <circle cx="12" cy="12" r="9" />
      <path d="M8 12h8" />
    </svg>
  );
}

function ShieldCheckIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
      <path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6l7-3Z" />
      <path d="M9 12l2 2 4-4" />
    </svg>
  );
}

type Stat = {
  label: string;
  value: number | string;
  accent: Accent;
  icon: ReactNode;
};

export function JobsSummary({ jobs }: { jobs: JobRecord[] }) {
  const uncertainCount = count(
    jobs,
    (job) => job.change_type === "uncertain" || job.change_type === "temporarily_not_found",
  );

  const stats: Stat[] = [
    { label: "Total ICT Jobs", value: jobs.length, accent: "lavender", icon: <BriefcaseIcon /> },
    {
      label: "Open Jobs",
      value: count(jobs, (job) => job.publication.status === "open"),
      accent: "mint",
      icon: <UnlockedBriefcaseIcon />,
    },
    {
      label: "New Jobs",
      value: count(jobs, (job) => job.change_type === "new"),
      accent: "sky",
      icon: <SparkleIcon />,
    },
    {
      label: "Changed Jobs",
      value: count(jobs, (job) => job.change_type === "changed"),
      accent: "violet",
      icon: <RefreshIcon />,
    },
    {
      label: "Closed Jobs",
      value: count(jobs, (job) => job.publication.status === "closed"),
      accent: "rose",
      icon: <MinusCircleIcon />,
    },
    {
      label: "Needs Attention",
      value: uncertainCount,
      accent: "turquoise",
      icon: <ShieldCheckIcon />,
    },
  ];

  return (
    <dl className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
      {stats.map((stat) => {
        const accent = ACCENT_CLASSES[stat.accent];
        return (
          <div
            key={stat.label}
            className={`relative isolate flex flex-col gap-3 overflow-hidden rounded-2xl border border-zinc-200 bg-gradient-to-br px-4 py-4 dark:border-zinc-800 ${accent.card}`}
          >
            <span
              aria-hidden="true"
              className={`pointer-events-none absolute -right-5 -top-6 h-24 w-24 rounded-full opacity-70 blur-2xl ${accent.glow}`}
            />
            <span
              aria-hidden="true"
              className={`relative z-10 flex h-8 w-8 items-center justify-center rounded-full ${accent.bg} ${accent.icon}`}
            >
              {stat.icon}
            </span>
            <div className="relative z-10">
              <dt className="text-xs font-medium text-zinc-500 dark:text-zinc-400">{stat.label}</dt>
              <dd className="mt-1 text-[28px] font-bold leading-none text-zinc-900 dark:text-zinc-50">
                {stat.value}
              </dd>
            </div>
          </div>
        );
      })}
    </dl>
  );
}
