import type { ReactNode } from "react";

export function SectionHeader({
  icon,
  title,
  action,
}: {
  icon: ReactNode;
  title: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2.5">
        <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600 dark:bg-indigo-500/10 dark:text-indigo-300">
          {icon}
        </span>
        <h2 className="text-[15px] font-semibold text-[#102A5C] dark:text-zinc-50">{title}</h2>
      </div>
      {action}
    </div>
  );
}
