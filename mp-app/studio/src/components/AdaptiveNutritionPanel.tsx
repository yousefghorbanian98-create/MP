import { useState } from "react";
import { fetchAdaptiveReport, logWeight } from "../lib/api";
import { fa, useApi } from "../lib/useApi";

/**
 * G3 — تخمین TDEE واقعی و پیشنهاد اصلاح کالری.
 *
 * این کامپوننت عمداً «عدد قشنگ» نشان نمی‌دهد: اگر داده کافی نباشد،
 * همان را می‌گوید و دلیلش را می‌نویسد. عدد بی‌پایه بدتر از «نمی‌دانم» است.
 */

const confidenceMap: Record<string, { label: string; cls: string }> = {
  high: { label: "اطمینان بالا", cls: "pill-green" },
  medium: { label: "اطمینان متوسط", cls: "pill-gold" },
  low: { label: "اطمینان کم", cls: "pill-gold" },
  insufficient: { label: "داده ناکافی", cls: "pill-red" },
};

const actionMap: Record<string, { label: string; cls: string }> = {
  increase: { label: "افزایش کالری", cls: "text-emerald-300" },
  decrease: { label: "کاهش کالری", cls: "text-rose-300" },
  keep: { label: "بدون تغییر", cls: "text-ink" },
  none: { label: "پیشنهادی نیست", cls: "text-ink-dim" },
};

function todayIso(): string {
  const d = new Date();
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

export function AdaptiveNutritionPanel({ memberId }: { memberId: number }) {
  const { data, loading, error, reload } = useApi(
    (s) => fetchAdaptiveReport(memberId, undefined, s),
    [memberId],
  );

  const [weight, setWeight] = useState("");
  const [date, setDate] = useState(todayIso());
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function saveWeight() {
    const kg = Number(weight);
    if (!Number.isFinite(kg) || kg < 20 || kg > 400) {
      setErr("وزن باید بین ۲۰ و ۴۰۰ کیلوگرم باشد.");
      return;
    }
    setBusy(true);
    setErr(null);
    setMsg(null);
    try {
      const res = await logWeight(memberId, [{ weight_kg: kg, logged_for_date: date }]);
      if (res.rejected.length > 0) {
        setErr(res.rejected.map((r) => r.reason).join(" · "));
      } else {
        setMsg(res.reason);
        setWeight("");
        reload();
      }
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const est = data?.estimate;
  const trend = est?.trend;
  const sug = data?.suggestion;
  const conf = confidenceMap[est?.confidence ?? "insufficient"];
  const act = actionMap[sug?.action ?? "none"];

  return (
    <section className="glass-card space-y-4 p-5">
      <div>
        <h3 className="font-semibold">تغذیهٔ سازگار — TDEE واقعی</h3>
        <p className="text-xs text-ink-dim">
          تخمین از روی روند وزن و مصرف واقعی، نه فقط فرمول. هر کیلوگرم تغییر وزن ≈ ۷۷۰۰
          کیلوکالری.
        </p>
      </div>

      {loading && <p className="text-sm text-ink-dim">در حال محاسبه…</p>}
      {error && (
        <p className="rounded-lg bg-danger/10 px-3 py-2 text-xs text-danger" role="alert">
          {error}
        </p>
      )}

      {data && est && (
        <>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <div className="rounded-xl bg-surface/60 p-3">
              <p className="text-[11px] text-ink-dim">TDEE برآوردی</p>
              <p className="text-lg font-bold">
                {est.tdee_kcal === null ? "نامعلوم" : fa(Math.round(est.tdee_kcal))}
              </p>
            </div>
            <div className="rounded-xl bg-surface/60 p-3">
              <p className="text-[11px] text-ink-dim">روند وزن</p>
              <p className="text-lg font-bold" dir="ltr">
                {trend?.slope_kg_per_week === null || trend?.slope_kg_per_week === undefined
                  ? "—"
                  : `${trend.slope_kg_per_week > 0 ? "+" : ""}${trend.slope_kg_per_week.toFixed(2)}`}
                <span className="ml-1 text-[11px] font-normal text-ink-dim">kg/هفته</span>
              </p>
            </div>
            <div className="rounded-xl bg-surface/60 p-3">
              <p className="text-[11px] text-ink-dim">میانگین مصرف</p>
              <p className="text-lg font-bold">
                {est.mean_intake_kcal === null ? "—" : fa(Math.round(est.mean_intake_kcal))}
              </p>
            </div>
            <div className="rounded-xl bg-surface/60 p-3">
              <p className="text-[11px] text-ink-dim">هدف فعلی</p>
              <p className="text-lg font-bold">
                {data.current_target_kcal === null ? "بدون برنامه" : fa(data.current_target_kcal)}
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2 text-[11px] text-ink-dim">
            <span className={conf.cls}>{conf.label}</span>
            <span>
              {fa(data.data_counts.weight_entries)} وزن · {fa(data.data_counts.intake_days)} روز غذا
            </span>
            {data.latest_weight_kg !== null && (
              <span>آخرین وزن: {fa(data.latest_weight_kg)} کیلوگرم</span>
            )}
          </div>

          <p className="text-[11px] text-ink-dim">{est.reason}</p>

          {trend?.notes && trend.notes.length > 0 && (
            <ul className="space-y-1 text-[11px] text-amber-300">
              {trend.notes.map((n) => (
                <li key={n}>⚠ {n}</li>
              ))}
            </ul>
          )}

          {sug && (
            <div className="rounded-xl bg-surface/50 p-3">
              <p className="text-xs">
                پیشنهاد هفتهٔ بعد:{" "}
                <b className={act.cls}>{act.label}</b>
                {sug.action !== "none" && sug.action !== "keep" && (
                  <span dir="ltr" className="ml-2 font-mono">
                    {sug.delta_kcal > 0 ? `+${sug.delta_kcal}` : sug.delta_kcal} kcal →{" "}
                    {sug.suggested_target_kcal}
                  </span>
                )}
                {sug.capped && <span className="ml-2 text-[10px] text-amber-300">(سقف ۱۵٪)</span>}
              </p>
              <p className="mt-1 text-[11px] text-ink-dim">{sug.reason}</p>
            </div>
          )}

          {est.assumptions && (
            <details className="text-[11px] text-ink-dim">
              <summary className="cursor-pointer">فرض‌های محاسبه</summary>
              <ul className="mt-1 list-inside list-disc space-y-0.5">
                {est.assumptions.map((a) => (
                  <li key={a}>{a}</li>
                ))}
              </ul>
            </details>
          )}
        </>
      )}

      <div className="border-t border-white/10 pt-3">
        {msg && <p className="mb-2 text-xs text-emerald-300">{msg}</p>}
        {err && (
          <p className="mb-2 rounded-lg bg-rose-500/10 px-3 py-2 text-xs text-rose-300" role="alert">
            {err}
          </p>
        )}
        <div className="flex flex-wrap items-end gap-3">
          <label className="text-xs text-ink-dim">
            وزن امروز (کیلوگرم)
            <input
              value={weight}
              onChange={(e) => setWeight(e.target.value)}
              inputMode="decimal"
              className="focus-ring mt-1 block w-24 rounded-lg bg-surface/70 px-3 py-2 text-sm"
            />
          </label>
          <label className="text-xs text-ink-dim">
            تاریخ
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="focus-ring mt-1 block rounded-lg bg-surface/70 px-3 py-2 text-sm text-ink"
            />
          </label>
          <button
            onClick={() => void saveWeight()}
            disabled={busy}
            className="btn-primary px-4 py-2 text-xs disabled:opacity-50"
          >
            {busy ? "در حال ثبت…" : "ثبت وزن"}
          </button>
        </div>
      </div>
    </section>
  );
}
