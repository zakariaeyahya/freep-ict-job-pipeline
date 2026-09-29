// GET /api/v1/exports/{scan_id}.jsonl — returns raw JSON Lines, not JSON,
// so it can't go through client.ts's apiFetch() (which assumes a JSON
// body). Downloads the file client-side via a Blob + temporary <a> click,
// since the endpoint requires the Bearer token that a plain <a href>
// navigation can't attach.

import { useAuthStore } from "@/store/auth-store";
import { ApiError } from "@/api/client";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function downloadScanExport(scanId: string): Promise<void> {
  const { accessToken, logout } = useAuthStore.getState();

  const response = await fetch(`${API_BASE_URL}/api/v1/exports/${encodeURIComponent(scanId)}.jsonl`, {
    headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : {},
  });

  if (response.status === 401) {
    logout();
    throw new ApiError(401, "unauthorized", "Your session has expired. Please sign in again.");
  }
  if (!response.ok) {
    throw new ApiError(response.status, "export_failed", "The export could not be downloaded.");
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${scanId}.jsonl`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
