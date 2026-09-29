"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError } from "@/api/client";

export type ApiResourceState<T> =
  | { status: "loading" }
  | { status: "error"; error: string }
  | { status: "success"; data: T };

type ApiResourceResult<T> = {
  dependencies: unknown[];
  refetchToken: number;
  state: Exclude<ApiResourceState<T>, { status: "loading" }>;
};

export function useApiResource<T>(
  fetcher: () => Promise<T>,
  deps: unknown[]
): ApiResourceState<T> & { refetch: () => void } {
  const [result, setResult] = useState<ApiResourceResult<T> | null>(null);
  const requestId = useRef(0);
  const [refetchToken, setRefetchToken] = useState(0);

  useEffect(() => {
    const thisRequestId = ++requestId.current;
    const requestDependencies = [...deps];
    const thisRefetchToken = refetchToken;

    fetcher()
      .then((data) => {
        if (requestId.current !== thisRequestId) return; // a newer request superseded this one
        setResult({
          dependencies: requestDependencies,
          refetchToken: thisRefetchToken,
          state: { status: "success", data },
        });
      })
      .catch((err) => {
        if (requestId.current !== thisRequestId) return;
        const message =
          err instanceof ApiError
            ? err.message
            : "We couldn't load this data. Please try again.";
        setResult({
          dependencies: requestDependencies,
          refetchToken: thisRefetchToken,
          state: { status: "error", error: message },
        });
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, refetchToken]);

  const refetch = useCallback(() => setRefetchToken((n) => n + 1), []);
  const isCurrentResult =
    result !== null &&
    result.refetchToken === refetchToken &&
    result.dependencies.length === deps.length &&
    result.dependencies.every((dependency, index) => Object.is(dependency, deps[index]));
  const state: ApiResourceState<T> = isCurrentResult
    ? result.state
    : { status: "loading" };

  return { ...state, refetch };
}
