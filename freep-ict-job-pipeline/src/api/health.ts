// GET /api/v1/health — deliberately does NOT require auth on the backend,
// but still goes through apiFetch() here for consistency; apiFetch omits
// the Authorization header when there is no token, which is fine since
// the backend doesn't check it on this route.

import { apiFetch } from "@/api/client";
import type { HealthResponse } from "@/lib/contracts/health-response";

export async function fetchHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>("/api/v1/health");
}
