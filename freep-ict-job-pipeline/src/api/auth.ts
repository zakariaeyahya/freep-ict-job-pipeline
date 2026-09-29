// POST /api/v1/auth/login — deliberately does not go through client.ts's
// apiFetch(): there is no token yet (that's what this call produces), and
// a failed login must never trigger apiFetch's 401-clears-session path.

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type LoginResult = {
  access_token: string;
  expires_in: number;
  refresh_token: string | null;
  refresh_expires_in: number | null;
};

export async function login(email: string, password: string): Promise<LoginResult> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    let message = "Incorrect email or password.";
    try {
      const body = (await response.json()) as { message?: string };
      if (body.message) message = body.message;
    } catch {
      // Non-JSON error body — keep the generic message.
    }
    throw new Error(message);
  }

  return (await response.json()) as LoginResult;
}
