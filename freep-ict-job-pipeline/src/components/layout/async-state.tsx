// Shared loading/error presentation for pages using useApiResource.
// Plain-language error messages only — never a raw stack trace or status
// code (CLAUDE.md: "Show user-facing errors in plain language").

export function LoadingState({ label }: { label: string }) {
  return (
    <div role="status" className="flex items-center justify-center rounded-2xl border border-zinc-200 bg-white px-4 py-16 text-sm text-zinc-500 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-400">
      {label}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div role="alert" className="flex flex-col items-center gap-3 rounded-2xl border border-red-200 bg-red-50 px-4 py-10 text-center dark:border-red-500/30 dark:bg-red-500/10">
      <p className="text-sm font-medium text-red-800 dark:text-red-300">{message}</p>
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="rounded-xl border border-red-300 bg-white px-3 py-1.5 text-sm font-medium text-red-700 outline-none focus-visible:ring-2 focus-visible:ring-red-500/30 dark:border-red-500/40 dark:bg-zinc-900 dark:text-red-300"
        >
          Try again
        </button>
      ) : null}
    </div>
  );
}
