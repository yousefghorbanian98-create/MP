/**
 * hook مشترک دریافت داده از API واقعی (M45-c1).
 *
 * سه حالت صریح، بدون پنهان‌کاری:
 *  loading | error (با پیام واقعی) | data
 * و یک حالت چهارم که مهم‌ترین است: `needsToken` — یعنی ۴۰۱/۴۰۳ گرفته‌ایم
 * و صفحه باید توکن بخواهد، نه اینکه دادهٔ ساختگی نشان دهد.
 */

import { useCallback, useEffect, useState } from "react";
import { AuthError } from "./api";

export interface ApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  needsToken: boolean;
  reload: () => void;
}

export function useApi<T>(
  fetcher: (signal?: AbortSignal) => Promise<T>,
  deps: unknown[] = [],
): ApiState<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [needsToken, setNeedsToken] = useState(false);
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
        setNeedsToken(false);
      })
      .catch((e: unknown) => {
        if (!alive) return;
        if (e instanceof DOMException && e.name === "AbortError") return;
        if (e instanceof AuthError) {
          setNeedsToken(true);
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

  return { data, loading, error, needsToken, reload };
}

/** فرمت اعداد فارسی — یک‌جا، تا هر صفحه جداگانه تکرارش نکند. */
export const fa = (n: number): string => n.toLocaleString("fa-IR");
