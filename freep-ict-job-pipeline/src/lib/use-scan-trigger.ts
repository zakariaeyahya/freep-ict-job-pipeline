"use client";

// Drives the "Run scan now" button: starts a scan (POST /scans/trigger),
// then polls fetchLatestScan() until a scan more recent than the one
// that was current when the button was clicked appears — that's the
// signal the triggered scan finished (brief §9.2, Scheduler: "starts
// scheduled and manual scans").

import { useCallback, useEffect, useRef, useState } from "react";

import { triggerScan } from "@/api/scans";
import type { ScanRun } from "@/lib/contracts/scan";
import { ApiError } from "@/api/client";

const POLL_INTERVAL_MS = 5000;

export type ScanTriggerState = "idle" | "starting" | "running" | "error";

export function useScanTrigger(
  currentScan: ScanRun | null,
  fetchLatest: () => Promise<ScanRun | null>,
  onScanFinished: (scan: ScanRun) => void
) {
  const [state, setState] = useState<ScanTriggerState>("idle");
  const [error, setError] = useState<string | null>(null);
  const baselineScanId = useRef<string | null>(currentScan?.scan_id ?? null);
  const pollHandle = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = useCallback(() => {
    if (pollHandle.current !== null) {
      clearInterval(pollHandle.current);
      pollHandle.current = null;
    }
  }, []);

  useEffect(() => stopPolling, [stopPolling]);

  const start = useCallback(async () => {
    if (state === "starting" || state === "running") return;

    setState("starting");
    setError(null);
    baselineScanId.current = currentScan?.scan_id ?? null;

    try {
      await triggerScan();
    } catch (err) {
      const message =
        err instanceof ApiError && err.status === 409
          ? "A scan is already running. Please wait for it to finish."
          : err instanceof ApiError
            ? err.message
            : "We couldn't start the scan. Please try again.";
      setState("error");
      setError(message);
      return;
    }

    setState("running");
    pollHandle.current = setInterval(async () => {
      try {
        const latest = await fetchLatest();
        if (latest && latest.scan_id !== baselineScanId.current) {
          stopPolling();
          setState("idle");
          onScanFinished(latest);
        }
      } catch {
        // A transient poll failure isn't fatal — keep polling rather than
        // surfacing an error for what may just be one dropped request.
      }
    }, POLL_INTERVAL_MS);
  }, [state, currentScan, fetchLatest, onScanFinished, stopPolling]);

  return { state, error, start };
}
