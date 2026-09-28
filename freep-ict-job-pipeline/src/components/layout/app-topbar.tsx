"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { getSession, signOut, type Session } from "@/lib/auth/session";

export function AppTopbar() {
  const router = useRouter();
  const [session, setSession] = useState<Session | null>(null);

  useEffect(() => {
    setSession(getSession());
  }, []);

  function handleSignOut() {
    signOut();
    router.push("/sign-in");
  }

  return (
    <header className="flex items-center justify-end border-b border-zinc-200 bg-white px-4 py-3 sm:px-6 lg:px-8 dark:border-zinc-800 dark:bg-zinc-900">
      {session ? (
        <div className="flex items-center gap-3">
          <span className="text-sm text-zinc-600 dark:text-zinc-400">{session.email}</span>
          <button
            type="button"
            onClick={handleSignOut}
            className="rounded-xl border border-zinc-200 px-3 py-1.5 text-sm font-medium text-zinc-700 outline-none focus-visible:ring-2 focus-visible:ring-violet-500/30 dark:border-zinc-700 dark:text-zinc-300"
          >
            Sign out
          </button>
        </div>
      ) : null}
    </header>
  );
}
