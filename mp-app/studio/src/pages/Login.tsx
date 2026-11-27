import { useState } from "react";
import { requestOtp } from "../lib/session";
import { useAuth } from "../auth/AuthContext";

function normalizeDigits(value: string): string {
  return value
    .replace(/[۰-۹]/g, (digit) => String(digit.charCodeAt(0) - 0x06f0))
    .replace(/[٠-٩]/g, (digit) => String(digit.charCodeAt(0) - 0x0660));
}

export function Login() {
  const { signIn, notice } = useAuth();
  const [phone, setPhone] = useState("");
  const [code, setCode] = useState("");
  const [requested, setRequested] = useState(false);
  const [expiresIn, setExpiresIn] = useState<number | null>(null);
  const [devCode, setDevCode] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const requestCode = async () => {
    setError(null);
    if (!/^09\d{9}$/.test(phone)) {
      setError("شمارهٔ موبایل باید ۱۱ رقم و با ۰۹ شروع شود");
      return;
    }
    setBusy(true);
    try {
      const result = await requestOtp(phone);
      setRequested(true);
      setExpiresIn(result.expires_in);
      setDevCode(import.meta.env.DEV ? result.dev_code ?? null : null);
      setCode("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "ارسال کد ناموفق بود");
    } finally {
      setBusy(false);
    }
  };

  const verifyCode = async () => {
    setError(null);
    if (!/^\d{6}$/.test(code)) {
      setError("کد ورود باید شش رقم باشد");
      return;
    }
    setBusy(true);
    try {
      await signIn(phone, code);
    } catch (err) {
      setError(err instanceof Error ? err.message : "ورود ناموفق بود");
    } finally {
      setBusy(false);
    }
  };

  return (
    <main dir="rtl" className="flex min-h-screen items-center justify-center p-5">
      <section className="glass-card w-full max-w-md space-y-5 p-7" aria-labelledby="login-title">
        <header className="text-center">
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/20 font-bold text-primary-light">
            MP
          </div>
          <h1 id="login-title" className="text-xl font-bold">ورود به استودیو</h1>
          <p className="mt-2 text-sm text-ink-dim">برای کارکنان مجاز باشگاه؛ کد یک‌بارمصرف پیامکی</p>
        </header>

        <div className="space-y-4">
          <label className="block space-y-1.5 text-sm">
            <span>شمارهٔ موبایل</span>
            <input
              autoComplete="tel"
              inputMode="tel"
              dir="ltr"
              maxLength={11}
              value={phone}
              onChange={(event) => setPhone(normalizeDigits(event.target.value).replace(/\D/g, ""))}
              className="focus-ring w-full rounded-xl border border-primary/20 bg-surface/70 px-3 py-2.5"
              placeholder="09121234567"
              aria-label="شمارهٔ موبایل"
            />
          </label>

          {!requested ? (
            <button
              type="button"
              className="btn-primary w-full rounded-xl px-4 py-2.5 text-sm disabled:opacity-50"
              onClick={() => void requestCode()}
              disabled={busy}
            >
              {busy ? "در حال ارسال…" : "دریافت کد ورود"}
            </button>
          ) : (
            <>
              <label className="block space-y-1.5 text-sm">
                <span>کد یک‌بارمصرف</span>
                <input
                  autoComplete="one-time-code"
                  inputMode="numeric"
                  dir="ltr"
                  maxLength={6}
                  value={code}
                  onChange={(event) => setCode(normalizeDigits(event.target.value).replace(/\D/g, ""))}
                  className="focus-ring w-full rounded-xl border border-primary/20 bg-surface/70 px-3 py-2.5 tracking-[0.35em]"
                  placeholder="••••••"
                  aria-label="کد یک‌بارمصرف"
                />
              </label>
              <p className="text-xs text-ink-dim">
                کد برای {phone} ارسال شد{expiresIn ? `؛ اعتبار ${expiresIn} ثانیه` : ""}.
              </p>
              {devCode && (
                <p className="rounded-lg bg-amber-500/10 px-3 py-2 text-xs text-amber-200" role="status">
                  کد آزمایشی محیط توسعه: <b dir="ltr">{devCode}</b>
                </p>
              )}
              <button
                type="button"
                className="btn-primary w-full rounded-xl px-4 py-2.5 text-sm disabled:opacity-50"
                onClick={() => void verifyCode()}
                disabled={busy}
              >
                {busy ? "در حال بررسی…" : "ورود امن"}
              </button>
              <button
                type="button"
                className="w-full rounded-xl px-4 py-2 text-xs text-ink-dim hover:bg-surface/70"
                onClick={() => void requestCode()}
                disabled={busy}
              >
                ارسال دوبارهٔ کد
              </button>
            </>
          )}
        </div>
        {notice && <p role="status" className="rounded-xl bg-amber-500/10 p-3 text-sm text-amber-200">{notice}</p>}
        {error && <p role="alert" className="rounded-xl bg-danger/15 p-3 text-sm text-red-300">{error}</p>}
        <p className="text-center text-[11px] leading-5 text-ink-dim">
          توکن نشست فقط در این مرورگر نگه‌داری می‌شود. کد آزمایشی فقط وقتی سرور در حالت development باشد نمایش داده می‌شود.
        </p>
      </section>
    </main>
  );
}
