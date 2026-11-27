import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { roleFromToken } from "../lib/roleNav";
import {
  API_BASE,
  SESSION_EXPIRED_EVENT,
  clearSession,
  getAccessToken,
  getRefreshToken,
  logoutSession,
  sessionFetch,
  storeTokenPair,
  verifyOtp,
} from "../lib/session";

export type AuthStatus = "checking" | "authenticated" | "unauthenticated";

interface AuthContextValue {
  status: AuthStatus;
  notice: string | null;
  signIn: (phone: string, code: string) => Promise<void>;
  signOut: () => Promise<boolean>;
}

const noProvider: AuthContextValue = {
  status: "authenticated",
  notice: null,
  signIn: async () => undefined,
  signOut: async () => false,
};
const AuthContext = createContext<AuthContextValue>(noProvider);

const APP_ROLES = new Set(["super_admin", "admin", "manager", "coach", "reception", "member"]);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>("checking");
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    const onSessionExpired = () => {
      setNotice("نشست منقضی یا لغو شده است؛ دوباره وارد شوید.");
      setStatus("unauthenticated");
    };
    window.addEventListener(SESSION_EXPIRED_EVENT, onSessionExpired);

    const restore = async () => {
      if (!getAccessToken() && !getRefreshToken()) {
        if (active) setStatus("unauthenticated");
        return;
      }
      try {
        const response = await sessionFetch(`${API_BASE}/members/me`);
        const role = roleFromToken(getAccessToken());
        if (response.ok) {
          const identity = await response.json().catch(() => null) as { role?: unknown } | null;
          if (APP_ROLES.has(role) && identity?.role === role) {
            if (active) setStatus("authenticated");
            return;
          }
          await logoutSession();
          if (active) {
            setNotice("نقش نشست با هویت حساب در سرور هم‌خوان نیست؛ دوباره وارد شوید.");
            setStatus("unauthenticated");
          }
          return;
        }
        if (response.status >= 500) {
          if (active) {
            setNotice("سرور نتوانست نشست را بررسی کند؛ اتصال را بررسی و دوباره تلاش کنید.");
            setStatus("unauthenticated");
          }
          return;
        }
        clearSession();
        if (active) {
          if (response.status !== 401) setNotice("نشست معتبر نیست؛ دوباره وارد شوید.");
          setStatus("unauthenticated");
        }
      } catch {
        // A network error cannot restore a protected screen; retain credentials for an explicit retry.
        if (active) {
          setNotice("برای بررسی نشست به سرور دسترسی نیست؛ اتصال را بررسی و دوباره وارد شوید.");
          setStatus("unauthenticated");
        }
      }
    };
    void restore();

    return () => {
      active = false;
      window.removeEventListener(SESSION_EXPIRED_EVENT, onSessionExpired);
    };
  }, []);

  const signIn = useCallback(async (phone: string, code: string) => {
    const pair = await verifyOtp(phone, code);
    const role = roleFromToken(pair.access_token);
    if (!APP_ROLES.has(role)) {
      await logoutSession(pair.refresh_token);
      throw new Error("این حساب مجاز به ورود به برنامه نیست");
    }
    storeTokenPair(pair);
    setNotice(null);
    setStatus("authenticated");
  }, []);

  const signOut = useCallback(async () => {
    const revocation = logoutSession();
    // Hide protected UI immediately; the server call only confirms remote revocation.
    setStatus("unauthenticated");
    const serverRevoked = await revocation;
    setNotice(
      serverRevoked
        ? "از حساب خارج شدید."
        : "از این مرورگر خارج شدید، اما لغو نشست سرور تأیید نشد.",
    );
    return serverRevoked;
  }, []);

  return <AuthContext.Provider value={{ status, notice, signIn, signOut }}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  return useContext(AuthContext);
}
