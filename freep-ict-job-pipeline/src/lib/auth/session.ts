// Front-only session for the review UI demo.
//
// There is no backend yet, so nothing here is a real security boundary:
// any script running in the browser can read or forge this session.
// When the backend exists, replace this file with real calls to it
// (e.g. an HttpOnly cookie set by the server) and keep the same
// `getSession` / `signIn` / `signOut` shape so callers do not change.

const STORAGE_KEY = "freep-reviewer-session";

// Anyone who needs to review the pipeline output uses this single
// shared demo login. Replace with real accounts once the backend
// issues them.
const DEMO_EMAIL = "reviewer@dreev.local";
const DEMO_PASSWORD = "dreev-demo-2026";

export type Session = {
  email: string;
  signedInAt: string;
};

export function getSession(): Session | null {
  if (typeof window === "undefined") return null;

  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as Session;
  } catch {
    return null;
  }
}

export type SignInResult = { ok: true } | { ok: false; error: string };

export function signIn(email: string, password: string): SignInResult {
  const normalizedEmail = email.trim().toLowerCase();

  if (!normalizedEmail || !password) {
    return { ok: false, error: "Enter your email and password." };
  }

  if (normalizedEmail !== DEMO_EMAIL || password !== DEMO_PASSWORD) {
    return { ok: false, error: "Incorrect email or password." };
  }

  const session: Session = {
    email: normalizedEmail,
    signedInAt: new Date().toISOString(),
  };

  window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(session));
  return { ok: true };
}

export function signOut(): void {
  window.sessionStorage.removeItem(STORAGE_KEY);
}
