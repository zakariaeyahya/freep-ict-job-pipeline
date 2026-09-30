"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import Image from "next/image";

import { useAuthStore } from "@/store/auth-store";

const NAV_ITEMS = [
  { href: "/jobs", label: "Jobs" },
  { href: "/scans", label: "Scan report" },
  { href: "/health", label: "Health" },
] as const;

export function AppSidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const logout = useAuthStore((state) => state.logout);

  function handleSignOut() {
    logout();
    router.push("/sign-in");
  }

  return (
    <nav
      aria-label="Main navigation"
      className="sticky top-0 flex h-screen w-56 shrink-0 flex-col gap-6 self-start overflow-y-auto border-r border-zinc-200 bg-white px-4 py-6 dark:border-zinc-800 dark:bg-zinc-900"
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

      <button
        type="button"
        onClick={handleSignOut}
        className="mt-auto block w-full rounded-xl border border-zinc-200 px-3 py-2 text-left text-sm font-medium text-zinc-600 outline-none hover:bg-zinc-50 focus-visible:ring-2 focus-visible:ring-violet-500/30 dark:border-zinc-700 dark:text-zinc-400 dark:hover:bg-zinc-800"
      >
        Sign out
      </button>
    </nav>
  );
}
