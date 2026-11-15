import { fetchReadiness } from "../lib/api";
import { useAppStore } from "../stores/appStore";
import { fa, useApi } from "../lib/useApi";

/**
 * G13 — آمادگی/خستگی: چند سیگنال، یک تصمیم.
 *
 * این پنل باید همیشه نشان دهد **چرا** امتیاز این است — و اگر سیگنالی
 * نامعلوم بوده، همان را بگوید. کاهش خودکار حجم بدون نمایش دلیل،
 * جعبهٔ سیاه است و برای پروژهٔ پژوهشی بی‌ارزش.
 */

const bandMap: Record<string, { label: string; cls: string; color: string }> = {
  ready: { label: "آماده", cls: "pill-green", color: "bg-emerald-400" },
  monitor: { label: "مراقبت", cls: "pill-gold", color: "bg-amber-400" },
  fatigued: { label: "خسته", cls: "pill-red", color: "bg-rose-500" },
  insufficient: { label: "داده ناکافی", cls: "pill-red", color: "bg-surface" },
};

const signalLabels: Record<string, string> = {
  rep_drop: "افت تکرار",
  rir_mismatch: "اختلاف RIR",
  soreness: "درد عضلانی",
  volume_spike: "پرش حجم هفتگی",
};

const recMap: Record<string, { label: string; cls: string }> = {
  deload: { label: "کاهش خودکار حجم (−۱ ست)", cls: "text-rose-300" },
  keep: { label: "حفظ حجم", cls: "text-ink" },
  increase: { label: "افزایش حجم", cls: "text-emerald-300" },
  insufficient: { label: "تصمیمی نیست", cls: "text-ink-dim" },
};

export function ReadinessPanel() {
  const memberId = useAppStore((s) => s.selectedMemberId);
  const { data, loading, error } = useApi(
    (s) => (memberId === null ? Promise.resolve(null) : fetchReadiness(memberId, undefined, s)),
    [memberId],
  );

  if (memberId === null) {
    return (
      <section className="glass-card p-6 text-center text-sm text-ink-dim">
        برای دیدن آمادگی، یک عضو را از صفحهٔ «اعضا» انتخاب کنید.
      </section>
    );
  }

  const r = data?.readiness;
  const band = bandMap[r?.band ?? "insufficient"];
  const rec = recMap[r?.recommendation ?? "insufficient"];

  return (
    <section className="glass-card space-y-3 p-5">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <h3 className="font-semibold">آمادگی / خستگی</h3>
          <p className="text-xs text-ink-dim">
            چند سیگنال، یک تصمیم — وزن‌دار و قابل بازبینی
          </p>
        </div>
        {r && <span className={band.cls}>{band.label}</span>}
      </div>

      {loading && <p className="text-sm text-ink-dim">در حال محاسبه…</p>}
      {error && (
        <p className="rounded-lg bg-danger/10 px-3 py-2 text-xs text-danger" role="alert">
          {error}
        </p>
      )}

      {data && !r && (
        <p className="rounded-lg bg-surface/50 px-3 py-2 text-xs text-ink-dim">{data.reason}</p>
      )}

      {r && (
        <>
          <div className="flex items-center gap-4">
            <div className="text-center">
              <p className="text-3xl font-bold">
                {r.score === null ? "—" : fa(Math.round(r.score))}
              </p>
              <p className="text-[10px] text-ink-dim">از ۱۰۰</p>
            </div>
            <div className="flex-1">
              <div className="relative h-2.5 overflow-hidden rounded-full bg-surface/70">
                <div
                  className={`absolute inset-y-0 left-0 ${band.color}`}
                  style={{ width: `${r.score ?? 0}%` }}
                />
                {/* آستانهٔ کاهش حجم روی نوار، تا عدد در بستر خودش دیده شود */}
                <div
                  className="absolute inset-y-0 w-0.5 bg-white/50"
                  style={{ left: `${r.thresholds.deload_below}%` }}
                  title={`آستانهٔ کاهش حجم: ${r.thresholds.deload_below}`}
                />
              </div>
              <p className="mt-1 text-[11px] text-ink-dim">
                زیر {fa(r.thresholds.deload_below)} ⇒ کاهش خودکار حجم
              </p>
            </div>
          </div>

          <p className="text-xs">
            توصیه: <b className={rec.cls}>{rec.label}</b>
          </p>
          <p className="text-[11px] text-ink-dim">{r.reason}</p>

          <div className="space-y-1.5">
            {r.signals.map((s) => (
              <div key={s.name} className="flex items-start gap-2 text-[11px]">
                <span className="w-24 shrink-0 text-ink-dim">
                  {signalLabels[s.name] ?? s.name}
                </span>
                <div className="mt-1 h-1.5 w-16 shrink-0 overflow-hidden rounded-full bg-surface/70">
                  {s.score !== null && (
                    <div className="h-full bg-primary-light" style={{ width: `${s.score}%` }} />
                  )}
                </div>
                <span className={s.score === null ? "text-ink-dim" : "text-ink"}>
                  {s.score === null ? "نامعلوم" : `${fa(Math.round(s.score))}`}
                </span>
                <span className="text-ink-dim">{s.reason}</span>
              </div>
            ))}
          </div>

          {r.missing_signals.length > 0 && (
            <p className="rounded-lg bg-surface/40 px-3 py-2 text-[11px] text-amber-300">
              سیگنال نامعلوم: {r.missing_signals.map((n) => signalLabels[n] ?? n).join(" · ")} —
              وزن این سیگنال‌ها به بقیه توزیع شده، نه اینکه صفر حساب شوند.
            </p>
          )}

          {data?.data_counts && (
            <p className="text-[10px] text-ink-dim">
              {fa(data.data_counts.feedback_rows)} بازخورد ست ·{" "}
              {fa(data.data_counts.sets_last_7_days)} ست در ۷ روز اخیر ·{" "}
              {fa(data.data_counts.sets_prior_7_days)} ست در ۷ روز قبل
            </p>
          )}

          {data?.note && (
            <p className="border-t border-white/10 pt-2 text-[10px] text-ink-dim">{data.note}</p>
          )}

          <details className="text-[10px] text-ink-dim">
            <summary className="cursor-pointer">وزن سیگنال‌ها و آستانه‌ها</summary>
            <p className="mt-1" dir="ltr">
              {Object.entries(r.weights)
                .map(([k, v]) => `${k}=${v}`)
                .join(" · ")}
            </p>
            <p dir="ltr">
              deload&lt;{r.thresholds.deload_below} · recovery&lt;{r.thresholds.recovery_below} ·
              spike&gt;{r.thresholds.volume_spike_ratio}×
            </p>
          </details>
        </>
      )}
    </section>
  );
}
