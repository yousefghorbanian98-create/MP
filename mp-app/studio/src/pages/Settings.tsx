import { motion } from "framer-motion";
import { useState } from "react";

const initialFlags = [
  { key: "face_gate", label: "گیت تشخیص چهره", enabled: true, desc: "فعال‌سازی ورود با چهره در کیوسک" },
  { key: "llm_explanations", label: "توضیحات هوش مصنوعی", enabled: true, desc: "متن‌های توضیحی Ollama (فقط متن — قانون G8)" },
  { key: "new_dashboard", label: "داشبورد جدید", enabled: false, desc: "تجربهٔ آزمایشی داشبورد KPI" },
  { key: "sms_provider", label: "ارسال پیامک", enabled: false, desc: "provider پیامک (OTP و یادآوری)" },
];

/** تنظیمات — feature flags با سوئیچ انیمیشنی. */
export function Settings() {
  const [flags, setFlags] = useState(initialFlags);

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
      <div className="glass-card divide-y divide-primary/10">
        {flags.map((f, i) => (
          <motion.div
            key={f.key}
            initial={{ opacity: 0, x: 14 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.06 }}
            className="flex items-center justify-between px-5 py-4"
          >
            <div>
              <p className="text-sm font-semibold">{f.label}</p>
              <p className="text-xs text-ink-dim">{f.desc}</p>
            </div>
            <button
              onClick={() =>
                setFlags((prev) => prev.map((x) => (x.key === f.key ? { ...x, enabled: !x.enabled } : x)))
              }
              className={`focus-ring relative h-7 w-14 rounded-full transition-colors duration-300 ${
                f.enabled ? "bg-primary/80" : "bg-surface"
              }`}
              aria-pressed={f.enabled}
            >
              <motion.span
                layout
                transition={{ type: "spring", stiffness: 500, damping: 32 }}
                className="absolute top-1 h-5 w-5 rounded-full bg-white shadow"
                style={{ right: f.enabled ? 4 : 34 }}
              />
            </button>
          </motion.div>
        ))}
      </div>

      <div className="glass-card p-5">
        <h3 className="text-sm font-semibold">اطلاعات سیستم</h3>
        <dl className="mt-3 grid grid-cols-2 gap-3 text-xs">
          <div className="rounded-xl bg-surface/60 p-3">
            <dt className="text-ink-dim">نسخهٔ API</dt>
            <dd className="mt-1 font-mono">v1.0.0</dd>
          </div>
          <div className="rounded-xl bg-surface/60 p-3">
            <dt className="text-ink-dim">موتور قواعد</dt>
            <dd className="mt-1 font-mono">rules-1.0 (ACSM/NSCA)</dd>
          </div>
          <div className="rounded-xl bg-surface/60 p-3">
            <dt className="text-ink-dim">پایگاه‌داده</dt>
            <dd className="mt-1 font-mono">SQLite (مسیر مهاجرت Postgres)</dd>
          </div>
          <div className="rounded-xl bg-surface/60 p-3">
            <dt className="text-ink-dim">دادهٔ بیومتریک</dt>
            <dd className="mt-1 font-mono">PyNaCl — رمزنگاری‌شده</dd>
          </div>
        </dl>
      </div>
    </motion.div>
  );
}
