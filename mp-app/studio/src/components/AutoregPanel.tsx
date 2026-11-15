import { useState } from "react";
import { suggestNextWeight, type WeightSuggestion } from "../lib/api";
import { fa } from "../lib/useApi";

/**
 * autoreg-1.0 — وزنهٔ ست بعدی.
 *
 * پیش از این، `POST /ai/suggest-weight` (موتور autoreg) هیچ مصرف‌کننده‌ای
 * نداشت: کد موتور و تست‌هایش بودند ولی در هیچ صفحه‌ای دیده نمی‌شد.
 *
 * قاعدهٔ بازنمایی: عدد پیشنهادی فقط وقتی نمایش داده می‌شود که سرور آن را
 * داده باشد. دلیل و نسخهٔ قاعده هم همراه عدد می‌آیند — عدد بی‌دلیل،
 * جعبهٔ سیاه است.
 */
export function AutoregPanel() {
  const [lastWeight, setLastWeight] = useState("60");
  const [repsDone, setRepsDone] = useState("8");
  const [targetReps, setTargetReps] = useState("10");
  const [rpe, setRpe] = useState("");
  const [result, setResult] = useState<WeightSuggestion | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function run() {
    const lw = Number(lastWeight);
    const rd = Number(repsDone);
    const tr = Number(targetReps);
    setError(null);
    setResult(null);
    if (!Number.isFinite(lw) || lw <= 0) {
      setError("وزنهٔ ست قبل باید عددی بزرگ‌تر از صفر باشد");
      return;
    }
    if (!Number.isInteger(rd) || rd < 0 || !Number.isInteger(tr) || tr < 1) {
      setError("تکرار انجام‌شده و هدف باید عدد صحیح باشند (هدف ≥ ۱)");
      return;
    }
    const rpeNum = rpe.trim() === "" ? null : Number(rpe);
    if (rpeNum !== null && (Number.isNaN(rpeNum) || rpeNum < 1 || rpeNum > 10)) {
      setError("RPE بین ۱ و ۱۰ است — یا خالی بگذارید");
      return;
    }
    setBusy(true);
    try {
      const r = await suggestNextWeight({
        last_weight: lw,
        reps_done: rd,
        target_reps: tr,
        rpe: rpeNum,
      });
      setResult(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : "خطای ناشناخته");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="glass-card space-y-3 p-5">
      <div>
        <h3 className="font-semibold">وزنهٔ ست بعدی</h3>
        <p className="text-xs text-ink-dim">
          قاعدهٔ autoreg — بر پایهٔ تکرار انجام‌شده نسبت به هدف و RPE ثبت‌شده
        </p>
      </div>

      <div className="flex flex-wrap items-end gap-2 text-xs">
        <label className="text-ink-dim">
          وزنهٔ ست قبل (کیلوگرم)
          <input
            value={lastWeight}
            onChange={(e) => setLastWeight(e.target.value)}
            inputMode="decimal"
            className="focus-ring mt-1 block w-24 rounded-lg bg-surface/70 px-3 py-2 text-sm"
          />
        </label>
        <label className="text-ink-dim">
          تکرار انجام‌شده
          <input
            value={repsDone}
            onChange={(e) => setRepsDone(e.target.value)}
            inputMode="numeric"
            className="focus-ring mt-1 block w-20 rounded-lg bg-surface/70 px-3 py-2 text-sm"
          />
        </label>
        <label className="text-ink-dim">
          تکرار هدف
          <input
            value={targetReps}
            onChange={(e) => setTargetReps(e.target.value)}
            inputMode="numeric"
            className="focus-ring mt-1 block w-20 rounded-lg bg-surface/70 px-3 py-2 text-sm"
          />
        </label>
        <label className="text-ink-dim">
          RPE (اختیاری)
          <input
            value={rpe}
            onChange={(e) => setRpe(e.target.value)}
            inputMode="decimal"
            placeholder="—"
            className="focus-ring mt-1 block w-20 rounded-lg bg-surface/70 px-3 py-2 text-sm"
          />
        </label>
        <button
          onClick={() => void run()}
          disabled={busy}
          className="btn-primary px-4 py-2 text-xs disabled:opacity-50"
        >
          {busy ? "در حال محاسبه…" : "محاسبه"}
        </button>
      </div>

      {error && (
        <p role="alert" className="text-xs text-rose-400">
          {error}
        </p>
      )}

      {result && (
        <div className="rounded-lg bg-surface/60 p-3 text-xs">
          <p className="text-sm">
            پیشنهاد: <b className="text-ink">{fa(result.next_weight)}</b> کیلوگرم
            <span
              className={
                result.action === "increase"
                  ? "text-emerald-400"
                  : result.action === "decrease"
                    ? "text-rose-400"
                    : "text-ink-dim"
              }
            >
              {" "}
              (
              {result.action === "increase"
                ? "افزایش"
                : result.action === "decrease"
                  ? "کاهش"
                  : "بدون تغییر"}
              )
            </span>
          </p>
          <p className="mt-1 text-ink-dim">{result.reason}</p>
          <p className="mt-1 text-[11px] text-ink-dim">
            قاعده: {result.rule_version}
          </p>
        </div>
      )}
    </section>
  );
}
