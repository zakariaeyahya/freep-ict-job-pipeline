"use client";

// Shared data-fetching hook for pages backed by the real API. Every
// consumer gets the same explicit state machine (loading/success/error) —
// CLAUDE.md: "Design every async component for its full state machine".
//
// Re-fetches whenever `deps` changes, and ignores a stale response that
// resolves after a newer request has started (guards against race
// conditions from fast filter/pagination changes).

import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError } from "@/api/client";

export type ApiResourceState<T> =
  | { status: "loading" }
  | { status: "error"; error: string }
  | { status: "success"; data: T };

export function useApiResource<T>(
  fetcher: () => Promise<T>,
  deps: unknown[]
): ApiResourceState<T> & { refetch: () => void } {
  const [state, setState] = useState<ApiResourceState<T>>({ status: "loading" });
  const requestId = useRef(0);
  const [refetchToken, setRefetchToken] = useState(0);

  useEffect(() => {
    const thisRequestId = ++requestId.current;
    setState({ status: "loading" });

    fetcher()
      .then((data) => {
        if (requestId.current !== thisRequestId) return; // a newer request superseded this one
        setState({ status: "success", data });
      })
      .catch((err) => {
        if (requestId.current !== thisRequestId) return;
        const message =
          err instanceof ApiError
            ? err.message
            : "We couldn't load this data. Please try again.";
        setState({ status: "error", error: message });
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, refetchToken]);

  const refetch = useCallback(() => setRefetchToken((n) => n + 1), []);

  return { ...state, refetch };
}
