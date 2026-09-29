"use client";

// Drives the "Run scan now" button AND detects a scan already running —
// e.g. started from another tab, another reviewer, or (once one exists) a
// recurring scheduler — by checking GET /api/v1/scans/current on mount,
// not only after this page's own button is clicked. Once running (either
// way), polls both fetchScanProgress() (for the live "scan in progress"
// view — phase/jobs processed/activity feed) and fetchLatest() (to detect
// once a scan more recent than the baseline appears — that's the signal
// the scan finished) (brief §9.2, Scheduler: "starts scheduled and manual
// scans").

import { useCallback, useEffect, useRef, useState } from "react";

import { fetchScanProgress, triggerScan } from "@/api/scans";
import type { ScanRun } from "@/lib/contracts/scan";
import type { ScanProgress } from "@/lib/contracts/scan-progress";
import { ApiError } from "@/api/client";

const PROGRESS_POLL_INTERVAL_MS = 2000;
const COMPLETION_POLL_INTERVAL_MS = 5000;

export type ScanTriggerState = "idle" | "starting" | "running" | "error";

export function useScanTrigger(
  currentScan: ScanRun | null,
  fetchLatest: () => Promise<ScanRun | null>,
  onScanFinished: (scan: ScanRun) => void
) {
  const [state, setState] = useState<ScanTriggerState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<ScanProgress | null>(null);
  const baselineScanId = useRef<string | null>(currentScan?.scan_id ?? null);
  const progressPollHandle = useRef<ReturnType<typeof setInterval> | null>(null);
  const completionPollHandle = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    baselineScanId.current = currentScan?.scan_id ?? null;
  }, [currentScan]);

  const stopPolling = useCallback(() => {
    if (progressPollHandle.current !== null) {
      clearInterval(progressPollHandle.current);
      progressPollHandle.current = null;
    }
    if (completionPollHandle.current !== null) {
      clearInterval(completionPollHandle.current);
      completionPollHandle.current = null;
    }
  }, []);

  useEffect(() => stopPolling, [stopPolling]);

  const beginPolling = useCallback(() => {
    setState("running");

    progressPollHandle.current = setInterval(async () => {
      try {
        setProgress(await fetchScanProgress());
      } catch {
        // A transient poll failure isn't fatal — keep polling rather than
        // surfacing an error for what may just be one dropped request.
      }
    }, PROGRESS_POLL_INTERVAL_MS);

    completionPollHandle.current = setInterval(async () => {
      try {
        const latest = await fetchLatest();
        if (latest && latest.scan_id !== baselineScanId.current) {
          stopPolling();
          setState("idle");
          setProgress(null);
          onScanFinished(latest);
        }
      } catch {
        // Same reasoning as above — one dropped poll isn't fatal.
      }
    }, COMPLETION_POLL_INTERVAL_MS);
  }, [fetchLatest, onScanFinished, stopPolling]);

  // On mount: check whether a scan is already running (started elsewhere)
  // rather than only reacting to this page's own button.
  useEffect(() => {
    let cancelled = false;

    fetchScanProgress()
      .then((initialProgress) => {
        if (cancelled || initialProgress === null) return;
        setProgress(initialProgress);
        beginPolling();
      })
      .catch(() => {
        // No scan running (or a transient failure) — stay idle; the user
        // can still use the button, and polling will pick up any actual
        // in-progress scan shortly if this was just a dropped request.
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const start = useCallback(async () => {
    if (state === "starting" || state === "running") return;

    setState("starting");
    setError(null);
    setProgress(null);
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

    beginPolling();
  }, [state, currentScan, beginPolling]);

  return { state, error, progress, start };
}
