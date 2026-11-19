/**
 * hook مشترک دریافت داده از API واقعی (M45-c1).
 *
 * سه حالت صریح، بدون پنهان‌کاری:
 * loading | error (با پیام واقعی) | data
 * و یک حالت چهارم: `needsSession` — نشست پس از refresh هم ۴۰۱ گرفته است و
 * کاربر باید دوباره با OTP وارد شود؛ ۴۰۳ در error می‌ماند چون مسئله نقش است.
 */

import { useCallback, useEffect, useState } from "react";
import { AuthError } from "./api";

export interface ApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  needsSession: boolean;
  reload: () => void;
}

export function useApi<T>(
  fetcher: (signal?: AbortSignal) => Promise<T>,
  deps: unknown[] = [],
): ApiState<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [needsSession, setNeedsSession] = useState(false);
  const [nonce, setNonce] = useState(0);

  const reload = useCallback(() => setNonce((n) => n + 1), []);

  useEffect(() => {
    const ctrl = new AbortController();
    let alive = true;
    setLoading(true);
    setError(null);
    fetcher(ctrl.signal)
      .then((d) => {
        if (!alive) return;
        setData(d);
        setNeedsSession(false);
      })
      .catch((e: unknown) => {
        if (!alive) return;
        if (e instanceof DOMException && e.name === "AbortError") return;
        if (e instanceof AuthError) {
          setNeedsSession(true);
          setData(null);
        }
        setError(e instanceof Error ? e.message : "خطای ناشناخته");
      })
      .finally(() => {
        if (alive) setLoading(false);
      });
    return () => {
      alive = false;
      ctrl.abort();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, nonce]);

  return { data, loading, error, needsSession, reload };
}

/**
 * فرمت اعداد فارسی — یک‌جا، تا هر صفحه جداگانه تکرارش نکند.
 *
 * `null`/`undefined` به «—» تبدیل می‌شود، نه به کرش و نه به صفر. دلیل: در
 * پاسخ ناقص یا هنوز نیامده، «۰ ریال» یک عدد جعلی است؛ «—» صادقانه می‌گوید
 * داده نداریم. این باگ در تست a11y دیده شد: صفحهٔ مالی قبل از رسیدن KPI
 * با `n.toLocaleString` می‌ترکید (Unhandled error در Vitest).
 */
export const fa = (n: number | null | undefined): string =>
  typeof n === "number" && Number.isFinite(n) ? n.toLocaleString("fa-IR") : "—";
