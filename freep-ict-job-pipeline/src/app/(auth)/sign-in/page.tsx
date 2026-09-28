"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";

import { signIn } from "@/lib/auth/session";

export default function SignInPage() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (submitting) return;

    setSubmitting(true);
    setError(null);

    const result = signIn(email, password);

    if (!result.ok) {
      setError(result.error);
      setSubmitting(false);
      return;
    }

    router.push("/jobs");
  }

  return (
    <div className="flex min-h-screen flex-1 items-center justify-center bg-zinc-50 px-4 dark:bg-zinc-950">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <p className="text-sm font-medium text-zinc-500 dark:text-zinc-400">
            Dreev Professionals
          </p>
          <h1 className="mt-1 text-xl font-semibold text-zinc-900 dark:text-zinc-50">
            Freep pipeline review
          </h1>
        </div>

        <form
          onSubmit={handleSubmit}
          noValidate
          className="rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900"
        >
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <label
                htmlFor="email"
                className="text-sm font-medium text-zinc-700 dark:text-zinc-300"
              >
                Email
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                aria-invalid={error ? true : undefined}
                aria-describedby={error ? "sign-in-error" : undefined}
                className="rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 outline-none focus-visible:ring-2 focus-visible:ring-zinc-900 focus-visible:ring-offset-2 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-50 dark:focus-visible:ring-zinc-100 dark:focus-visible:ring-offset-zinc-900"
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <label
                htmlFor="password"
                className="text-sm font-medium text-zinc-700 dark:text-zinc-300"
              >
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                aria-invalid={error ? true : undefined}
                aria-describedby={error ? "sign-in-error" : undefined}
                className="rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 outline-none focus-visible:ring-2 focus-visible:ring-zinc-900 focus-visible:ring-offset-2 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-50 dark:focus-visible:ring-zinc-100 dark:focus-visible:ring-offset-zinc-900"
              />
            </div>

            {error ? (
              <p
                id="sign-in-error"
                role="alert"
                className="text-sm text-red-700 dark:text-red-400"
              >
                {error}
              </p>
            ) : null}

            <button
              type="submit"
              disabled={submitting}
              className="mt-2 rounded-md bg-zinc-900 px-3 py-2 text-sm font-medium text-white outline-none focus-visible:ring-2 focus-visible:ring-zinc-900 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-zinc-50 dark:text-zinc-900 dark:focus-visible:ring-zinc-100 dark:focus-visible:ring-offset-zinc-900"
            >
              {submitting ? "Signing in…" : "Sign in"}
            </button>
          </div>
        </form>

        <p className="mt-4 text-center text-xs text-zinc-500 dark:text-zinc-500">
          Front-only demo access. No account data leaves this browser.
        </p>
      </div>
    </div>
  );
}
