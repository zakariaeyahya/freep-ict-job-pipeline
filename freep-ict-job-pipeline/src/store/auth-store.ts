// Auth state: the access token and the signed-in reviewer's email.
//
// Persisted to sessionStorage (not localStorage) via zustand's `persist`
// middleware — the token survives a page refresh but is cleared when the
// tab closes, and every other API call reads the token from this store
// (src/api/client.ts), never from a cookie or window global.

import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

import { login as loginRequest } from "@/api/auth";

type AuthState = {
  accessToken: string | null;
  email: string | null;
  expiresAt: number | null; // epoch ms
  status: "idle" | "loading" | "authenticated" | "error";
  error: string | null;
};

type AuthActions = {
  login: (email: string, password: string) => Promise<{ ok: true } | { ok: false; error: string }>;
  logout: () => void;
  isTokenExpired: () => boolean;
};

const initialState: AuthState = {
  accessToken: null,
  email: null,
  expiresAt: null,
  status: "idle",
  error: null,
};

export const useAuthStore = create<AuthState & AuthActions>()(
  persist(
    (set, get) => ({
      ...initialState,

      login: async (email, password) => {
        set({ status: "loading", error: null });

        try {
          const result = await loginRequest(email, password);
          set({
            accessToken: result.access_token,
            email,
            expiresAt: Date.now() + result.expires_in * 1000,
            status: "authenticated",
            error: null,
          });
          return { ok: true };
        } catch (err) {
          const message = err instanceof Error ? err.message : "Incorrect email or password.";
          set({ ...initialState, status: "error", error: message });
          return { ok: false, error: message };
        }
      },

      logout: () => {
        set({ ...initialState });
      },

      isTokenExpired: () => {
        const { expiresAt } = get();
        return expiresAt === null || Date.now() >= expiresAt;
      },
    }),
    {
      name: "freep-auth",
      storage: createJSONStorage(() => sessionStorage),
      // Only persist what a refresh needs to restore — never persist
      // transient UI state like `status`/`error`.
      partialize: (state) => ({
        accessToken: state.accessToken,
        email: state.email,
        expiresAt: state.expiresAt,
      }),
    }
  )
);
