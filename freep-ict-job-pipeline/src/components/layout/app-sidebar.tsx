"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import Image from "next/image";

const NAV_ITEMS = [
  { href: "/jobs", label: "Jobs" },
  { href: "/scans", label: "Scan report" },
  { href: "/health", label: "Health" },
] as const;

export function AppSidebar() {
  const pathname = usePathname();

  return (
    <nav
      aria-label="Main navigation"
      className="flex w-56 shrink-0 flex-col gap-6 border-r border-zinc-200 bg-white px-4 py-6 dark:border-zinc-800 dark:bg-zinc-900"
    >
      <Link href="/jobs" className="flex items-center gap-2.5 px-2">
        <Image src="/donker-logo.svg" alt="" width={32} height={32} aria-hidden="true" />
        <span className="text-sm leading-tight font-semibold text-zinc-900 dark:text-zinc-50">
          Freep
          <br />
          ICT Job Pipeline
        </span>
      </Link>

      <ul className="flex flex-col gap-1">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href || pathname?.startsWith(`${item.href}/`);
          return (
            <li key={item.href}>
              <Link
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={
                  active
                    ? "block rounded-xl bg-violet-50 px-3 py-2 text-sm font-medium text-violet-700 dark:bg-violet-500/10 dark:text-violet-300"
                    : "block rounded-xl px-3 py-2 text-sm font-medium text-zinc-600 hover:bg-zinc-50 dark:text-zinc-400 dark:hover:bg-zinc-800"
                }
              >
                {item.label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
