import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { AuthError, fetchLeaderboards, type Leaderboards } from "../lib/adminApi";

const sections: { key: keyof Leaderboards; title: string; hint: string }[] = [
  { key: "top_athletes", title: "بهترین ورزشکارها", hint: "میانگین نمرهٔ ۱۴ محور آخرین ارزیابی" },
  { key: "top_spenders", title: "بیشترین هزینه", hint: "جمع پرداخت‌های قطعی (paid)" },
  { key: "most_visits", title: "بیشترین مراجعه", hint: "چک‌این‌های موفق بازه" },
  { key: "most_time", title: "بیشترین تایم باشگاه", hint: "مجموع دقیقهٔ جلسات بسته‌شده" },
];

/** تحلیل‌های مدیریتی (M42-c3) — لیدربوردها از API واقعی، هر رتبه با روش محاسبه. */
export function Analytics() {
  const [data, setData] = useState<Leaderboards | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [needsToken, setNeedsToken] = useState(false);
  const [tokenInput, setTokenInput] = useState("");

  const load = () => {
    setError(null);
    fetchLeaderboards()
      .then(setData)
      .catch((e) => {
        if (e instanceof AuthError) {
          setNeedsToken(true);
        }
        setError(e instanceof Error ? e.message : "خطای ناشناخته");
      });
  };

  useEffect(load, []);

  return (
    <div className="space-y-5">
      <div className="glass-card flex flex-wrap items-center justify-between gap-3 p-5">
        <div>
          <h2 className="text-lg font-bold">تحلیل‌های مدیریتی</h2>
          <p className="mt-1 text-xs text-ink-dim">
            لیدربوردها از دادهٔ واقعی باشگاه — هر رتبه با روش محاسبه؛ بدون داده = بدون رتبه (نامعلوم ≠ صفر)
          </p>
        </div>
        {data && (
          <span className="rounded-full bg-primary/10 px-3 py-1 text-[11px] text-primary-light">
            {data.rule_version} · بازه {data.window_days.toLocaleString("fa-IR")} روز
          </span>
        )}
      </div>

      {needsToken && (
        <div className="glass-card flex items-center gap-2 p-4">
          <input
            className="input flex-1 rounded-xl bg-surface/70 px-3 py-2 text-sm"
            placeholder="توکن ادمین (JWT) را اینجا بچسبانید"
            value={tokenInput}
            onChange={(e) => setTokenInput(e.target.value)}
          />
          <button
            className="btn-primary rounded-xl px-4 py-2 text-sm"
            onClick={() => {
              localStorage.setItem("mp_token", tokenInput.trim());
              load();
            }}
          >
            ورود
          </button>
        </div>
      )}

      {error && !needsToken && <div className="glass-card p-4 text-sm text-red-400">{error}</div>}

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
        {sections.map((sec) => (
          <motion.div key={sec.key} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-5">
            <h3 className="text-sm font-bold">{sec.title}</h3>
            <p className="mt-0.5 text-[11px] text-ink-dim">{sec.hint}</p>
            <div className="mt-3 space-y-2">
              {(!data || (data[sec.key] as unknown[]).length === 0) && (
                <p className="text-xs text-ink-dim">داده‌ای ثبت نشده — رتبه‌ای نمایش داده نمی‌شود</p>
              )}
              {data &&
                (data[sec.key] as Record<string, unknown>[]).map((row, i) => (
                  <div key={String(row.member_id)} className="flex items-center gap-3 rounded-xl bg-surface/60 px-3 py-2">
                    <span className="w-6 text-center text-sm font-bold text-primary-light">
                      {(i + 1).toLocaleString("fa-IR")}
                    </span>
                    <span className="flex-1 truncate text-sm">{String(row.full_name || row.member_id)}</span>
                    <span className="text-xs text-ink-dim">
                      {sec.key === "top_athletes" && `میانگین ${Number(row.avg_axis_score).toLocaleString("fa-IR")}`}
                      {sec.key === "top_spenders" &&
                        `${Number(row.total_paid_rial).toLocaleString("fa-IR")} ریال`}
                      {sec.key === "most_visits" &&
                        `${Number(row.visits).toLocaleString("fa-IR")} مراجعه`}
                      {sec.key === "most_time" &&
                        `${Number(row.total_minutes).toLocaleString("fa-IR")} دقیقه`}
                    </span>
                  </div>
                ))}
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
