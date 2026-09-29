"use client";

// Route guard for the (app) route group: redirects to /sign-in when there
// is no valid session. Renders nothing while the Zustand persist
// middleware is still hydrating from sessionStorage (a brief instant on
// first paint) to avoid a flash of "redirecting" before the real session
// state is known.

import { useEffect, useState, type ReactNode } from "react";
import { useRouter } from "next/navigation";

import { useAuthStore } from "@/store/auth-store";

export function AuthGuard({ children }: { children: ReactNode }) {
  const router = useRouter();
  const accessToken = useAuthStore((state) => state.accessToken);
  const isTokenExpired = useAuthStore((state) => state.isTokenExpired);
  const logout = useAuthStore((state) => state.logout);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (!hydrated) return;

    if (!accessToken || isTokenExpired()) {
      logout();
      router.replace("/sign-in");
    }
  }, [hydrated, accessToken, isTokenExpired, logout, router]);

  if (!hydrated || !accessToken || isTokenExpired()) {
    return null;
  }

  return <>{children}</>;
}
