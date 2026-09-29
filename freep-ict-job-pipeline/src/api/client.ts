// Central fetch wrapper: injects the Bearer token from the auth store into
// every request, and normalizes the backend's uniform error body
// (timestamp/status/error/message/path) into a typed ApiError.
//
// api/auth.ts (login itself) does NOT go through this — it has no token
// yet by definition. Every other src/api/*.ts module should call
// apiFetch() rather than fetch() directly, so token injection and error
// handling stay in one place.

import { useAuthStore } from "@/store/auth-store";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  readonly status: number;
  readonly errorCode: string;

  constructor(status: number, errorCode: string, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.errorCode = errorCode;
  }
}

type ApiErrorBody = {
  timestamp: string;
  status: number;
  error: string;
  message: string;
  path: string;
};

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const { accessToken, logout } = useAuthStore.getState();

  const headers = new Headers(init?.headers);
  headers.set("Accept", "application/json");
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers });

  if (response.status === 401) {
    // The token is missing/expired/rejected — clear the stale session so
    // the UI falls back to the sign-in page rather than showing broken
    // authenticated screens.
    logout();
    throw new ApiError(401, "unauthorized", "Your session has expired. Please sign in again.");
  }

  if (!response.ok) {
    let body: ApiErrorBody | null = null;
    try {
      body = (await response.json()) as ApiErrorBody;
    } catch {
      // Response wasn't JSON — fall through to the generic message below.
    }
    throw new ApiError(
      response.status,
      body?.error ?? "unknown_error",
      body?.message ?? `Request failed with status ${response.status}`
    );
  }

  if (response.status === 204) {
    // No body to parse (e.g. GET /scans/current when idle) — callers
    // expecting this must type T as including null/undefined.
    return null as T;
  }

  return (await response.json()) as T;
}
