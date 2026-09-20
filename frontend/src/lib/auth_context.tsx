/** Auth context — in-memory session for the farmer flow (Phase 2).

 * Tokens live only in memory (docs/12 §1 — no tokens in localStorage).
 * Session persistence, refresh-token rotation in the browser, and protected
 * route redirection are TODO — FUTURE PHASE (Phase 2+).
 */

import { createContext, useContext, useState, useCallback, type ReactNode } from "react";
import type { UserDto } from "@/types/api";

interface AuthState {
  user: UserDto | null;
  token: string | null;
  loading: boolean;
}

interface AuthContextValue extends AuthState {
  signIn: (user: UserDto, token: string) => void;
  signOut: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    token: null,
    loading: true,
  });

  const signIn = useCallback((user: UserDto, token: string) => {
    setState({ user, token, loading: false });
  }, []);

  const signOut = useCallback(() => {
    setState({ user: null, token: null, loading: false });
  }, []);

  return (
    <AuthContext.Provider value={{ ...state, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside an AuthProvider");
  return ctx;
}