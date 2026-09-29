"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { useAuthStore } from "@/store/auth-store";

function initialsFrom(email: string): string {
  const name = email.split("@")[0] ?? "";
  const parts = name.split(/[.\-_]/).filter(Boolean);
  const letters = parts.length > 1 ? [parts[0][0], parts[1][0]] : [name[0], name[1]];
  return letters.join("").toUpperCase();
}

export function AppTopbar() {
  const router = useRouter();
  const email = useAuthStore((state) => state.email);
  const logout = useAuthStore((state) => state.logout);
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setMenuOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  function handleSignOut() {
    logout();
    router.push("/sign-in");
  }

  if (!email) return <header className="border-b border-zinc-200 bg-white px-4 py-3 sm:px-6 lg:px-8 dark:border-zinc-800 dark:bg-zinc-900" />;

  return (
    <header className="flex items-center justify-end border-b border-zinc-200 bg-white px-4 py-3 sm:px-6 lg:px-8 dark:border-zinc-800 dark:bg-zinc-900">
      <div ref={menuRef} className="relative">
        <button
          type="button"
          onClick={() => setMenuOpen((open) => !open)}
          aria-expanded={menuOpen}
          aria-haspopup="menu"
          className="flex items-center gap-2 rounded-2xl px-2 py-1.5 outline-none focus-visible:ring-2 focus-visible:ring-violet-500/30"
        >
          <span className="flex h-8 w-8 items-center justify-center rounded-full bg-violet-100 text-xs font-semibold text-violet-700 dark:bg-violet-500/20 dark:text-violet-300">
            {initialsFrom(email)}
          </span>
          <span className="text-sm font-medium text-zinc-700 dark:text-zinc-300">{email}</span>
        </button>

        {menuOpen ? (
          <div
            role="menu"
            className="absolute right-0 z-10 mt-2 w-44 rounded-2xl border border-zinc-200 bg-white py-1 dark:border-zinc-800 dark:bg-zinc-900"
          >
            <button
              type="button"
              role="menuitem"
              onClick={handleSignOut}
              className="block w-full px-4 py-2 text-left text-sm text-zinc-700 hover:bg-zinc-50 dark:text-zinc-300 dark:hover:bg-zinc-800"
            >
              Sign out
            </button>
          </div>
        ) : null}
      </div>
    </header>
  );
}
