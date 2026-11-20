/**
 * تنظیمات — feature flags واقعی از `GET/PUT /admin/flags` (M46-c1).
 *
 * پیش از این، این صفحه ۴ سوییچ دکوری داشت که در `useState` محلی می‌ماند و
 * هیچ‌وقت به سرور نمی‌رسید. اکنون:
 *   - خواندن: `GET /admin/flags` (سرور منبع حقیقت)
 *   - نوشتن: `PUT /admin/flags` و سپس بازخوانی
 *   - خطا: پیام واقعی سرور، بدون سوییچِ خوش‌بینانه
 */
import { motion } from "framer-motion";
import { useMotionPreset } from "../lib/motion";
import { useCallback, useEffect, useState } from "react";
import { AdminPermissions } from "../components/AdminPermissions";
import { DeviceSessions } from "../components/DeviceSessions";
import { RoleManager } from "../components/RoleManager";
import { AuthError, fetchFlags, fetchHealth, putFlag, type FeatureFlagRow, type HealthInfo } from "../lib/api";

const LABELS: Record<string, { label: string; desc: string }> = {
  face_gate: { label: "گیت تشخیص چهره", desc: "ورود با چهره در کیوسک" },
  llm_explanations: { label: "توضیحات هوش مصنوعی", desc: "متن توضیحی (فقط متن — قانون G8)" },
  new_dashboard: { label: "داشبورد جدید", desc: "تجربهٔ آزمایشی داشبورد KPI" },
  sms_provider: { label: "ارسال پیامک", desc: "provider پیامک (OTP و یادآوری)" },
};

function labelFor(key: string) {
  return LABELS[key] ?? { label: key, desc: "" };
}

export function Settings() {
  const motionPreset = useMotionPreset();
  const [flags, setFlags] = useState<FeatureFlagRow[]>([]);
  const [health, setHealth] = useState<HealthInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [needsSession, setNeedsSession] = useState(false);
  const [busyKey, setBusyKey] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    return Promise.allSettled([fetchFlags(), fetchHealth()]).then(([f, h]) => {
      if (f.status === "fulfilled") {
        setFlags(f.value);
        setNeedsSession(false);
      } else {
        const msg = String((f.reason as Error)?.message ?? f.reason);
        if (f.reason instanceof AuthError) setNeedsSession(true);
        else setError(msg);
      }
      if (h.status === "fulfilled") setHealth(h.value);
      setLoading(false);
    });
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function toggle(row: FeatureFlagRow) {
    setBusyKey(row.key);
    setError(null);
    // خوش‌بینیِ نمایشی ممنوع: تا پاسخ سرور نیامده، وضعیت تغییر نمی‌کند.
    try {
      await putFlag(row.key, !row.enabled, row.description);
      await load();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusyKey(null);
    }
  }

  return (
    <motion.div {...motionPreset.rise} className="space-y-4">
      {needsSession && (
        <div className="glass-card border border-amber-500/30 p-4 text-sm">
          <p className="font-semibold text-amber-300">نشست معتبر نیست؛ با کد یک‌بارمصرف دوباره وارد شوید</p>
          <p className="mt-1 text-xs text-ink-dim">
            وضعیت واقعی از سرور خوانده می‌شود؛ دادهٔ نمایشی ساخته نمی‌شود.
          </p>
        </div>
      )}

      {error && (
        <div className="glass-card border border-rose-500/30 p-4 text-sm text-rose-300" role="alert">
          {error}
        </div>
      )}

      <div className="glass-card divide-y divide-primary/10">
        {loading && <p className="px-5 py-6 text-sm text-ink-dim">در حال خواندن پرچم‌ها از سرور…</p>}

        {!loading && !needsSession && flags.length === 0 && (
          <p className="px-5 py-6 text-sm text-ink-dim">
            هنوز هیچ پرچمی روی سرور تعریف نشده — دادهٔ نمایشی ساخته نمی‌شود.
          </p>
        )}

        {flags.map((f, i) => {
          const meta = labelFor(f.key);
          const busy = busyKey === f.key;
          return (
            <motion.div
              key={f.key}
              initial={{ opacity: 0, x: 14 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.04 }}
              className="flex items-center justify-between px-5 py-4"
            >
              <div>
                <p className="text-sm font-semibold">
                  {meta.label}
                  <span className="mr-2 font-mono text-[10px] text-ink-dim">{f.key}</span>
                </p>
                <p className="text-xs text-ink-dim">{f.description || meta.desc || "بدون توضیح"}</p>
              </div>
              <button
                onClick={() => void toggle(f)}
                disabled={busy}
                className={`focus-ring relative h-7 w-14 rounded-full transition-colors duration-300 disabled:opacity-50 ${
                  f.enabled ? "bg-primary/80" : "bg-surface"
                }`}
                aria-pressed={f.enabled}
                aria-label={`${meta.label}: ${f.enabled ? "روشن" : "خاموش"}`}
              >
                <motion.span
                  layout
                  transition={{ type: "spring", stiffness: 500, damping: 32 }}
                  className="absolute top-1 h-5 w-5 rounded-full bg-white shadow"
                  style={{ right: f.enabled ? 4 : 34 }}
                />
              </button>
            </motion.div>
          );
        })}
      </div>

      <div className="glass-card p-5">
        <h3 className="text-sm font-semibold">اطلاعات سیستم (از سرور)</h3>
        {health ? (
          <dl className="mt-3 grid grid-cols-2 gap-3 text-xs">
            <div className="rounded-xl bg-surface/60 p-3">
              <dt className="text-ink-dim">وضعیت</dt>
              <dd className="mt-1 font-mono">{health.status}</dd>
            </div>
            <div className="rounded-xl bg-surface/60 p-3">
              <dt className="text-ink-dim">نسخهٔ سرویس</dt>
              <dd className="mt-1 font-mono">{health.version}</dd>
            </div>
            <div className="rounded-xl bg-surface/60 p-3">
              <dt className="text-ink-dim">نام سرویس</dt>
              <dd className="mt-1 font-mono">{health.service}</dd>
            </div>
            <div className="rounded-xl bg-surface/60 p-3">
              <dt className="text-ink-dim">تعداد پرچم‌ها</dt>
              <dd className="mt-1 font-mono">{flags.length}</dd>
            </div>
          </dl>
        ) : (
          <p className="mt-3 text-xs text-ink-dim">سرور پاسخ نداد — مقدار حدسی نمایش داده نمی‌شود.</p>
        )}
      </div>

      <DeviceSessions />

      <RoleManager />

      <AdminPermissions />
    </motion.div>
  );
}
