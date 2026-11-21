import { useCallback, useState } from "react";
import { fetchDailyNutrition, logFood, searchFoods, type FoodRow } from "../lib/api";
import { AdaptiveNutritionPanel } from "../components/AdaptiveNutritionPanel";
import { FoodLibrary } from "../components/FoodLibrary";
import { useAppStore } from "../stores/appStore";
import { fa, useApi } from "../lib/useApi";
import { JalaliDateField } from "../components/ui/JalaliDateField";
import { Select } from "antd";

/**
 * G5 — تغذیه: جستجوی جدول غذایی واقعی، ثبت وعده، جمع روزانه.
 *
 * سه چیزی که این صفحه **نمی‌کند** و مهم است:
 *   ۱. اگر روزی ثبت نشده باشد، صفر نشان نمی‌دهد و «ثبت نشده» می‌نویسد.
 *   ۲. هدف فقط از برنامهٔ تأییدشده می‌آید؛ وگرنه «برنامه‌ای تأیید نشده».
 *   ۳. برای مواد خشک/خام هشدار وزن می‌دهد — ۲۵۰ گرم برنج خشک
 *      ۹۰۰ کالری است، نه ۳۲۵.
 */

const slots = [
  { key: "breakfast", label: "صبحانه" },
  { key: "lunch", label: "ناهار" },
  { key: "dinner", label: "شام" },
  { key: "snack", label: "میان‌وعده" },
];

function todayIso(): string {
  // تاریخ محلی، نه UTC — «امروز» برای کاربر یعنی امروز
  const d = new Date();
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

export function Nutrition() {
  // عضو انتخابی از صفحهٔ «اعضا» می‌آید — بدون آن هیچ عضوی فرض نمی‌شود.
  const memberId = useAppStore((s) => s.selectedMemberId);
  const [date, setDate] = useState(todayIso());
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<FoodRow[]>([]);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [slot, setSlot] = useState("lunch");
  const [grams, setGrams] = useState("100");
  const [selected, setSelected] = useState<FoodRow | null>(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  // WP 4.6 / F‑16: بدون عضو درخواست نفرست (قبلاً `?? -1` می‌فرستاد).
  const { data, loading, error, reload } = useApi(
    (s) =>
      memberId === null
        ? Promise.resolve(null)
        : fetchDailyNutrition(memberId, date, undefined, s),
    [memberId, date],
  );

  const runSearch = useCallback(async () => {
    const q = query.trim();
    if (!q) {
      setResults([]);
      setSearchError("عبارت جستجو خالی است.");
      return;
    }
    setSearching(true);
    setSearchError(null);
    try {
      const rows = await searchFoods(q);
      setResults(rows);
      if (rows.length === 0) setSearchError(`«${q}» در جدول غذایی نیست.`);
    } catch (e) {
      setSearchError((e as Error).message);
    } finally {
      setSearching(false);
    }
  }, [query]);

  async function submit() {
    if (!selected) {
      setErr("اول یک مادهٔ غذایی از نتایج انتخاب کنید.");
      return;
    }
    if (memberId === null) {
      setErr("عضوی انتخاب نشده است.");
      return;
    }
    const g = Number(grams);
    if (!Number.isFinite(g) || g <= 0) {
      setErr("وزن باید عددی بزرگ‌تر از صفر باشد.");
      return;
    }
    setBusy(true);
    setErr(null);
    setMsg(null);
    try {
      const res = await logFood(memberId, [
        { food_id: selected.id, grams: g, meal_slot: slot, logged_for_date: date },
      ]);
      if (res.rejected.length > 0) {
        setErr(res.rejected.map((r) => r.reason).join(" · "));
      } else {
        setMsg(`${selected.name_fa} — ${fa(g)} گرم در ${slots.find((s) => s.key === slot)?.label} ثبت شد.`);
        setSelected(null);
        setQuery("");
        setResults([]);
        reload();
      }
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  if (memberId === null) {
    return (
      <div className="glass-card p-10 text-center text-sm text-ink-dim">
        برای ثبت غذا اول یک عضو را از صفحهٔ «اعضا» انتخاب کنید — بدون عضو، هیچ
        وعده‌ای ثبت نمی‌شود و دادهٔ نمایشی ساخته نمی‌شود.
      </div>
    );
  }

  // پاسخ ناقص نباید صفحه را بشکند: هر فیلد با مقدار امن شروع می‌شود.
  const items = data?.items ?? [];
  const totals = data?.totals;
  const target = data?.target;
  const hasTarget = data?.target_source === "approved_plan";

  return (
    <div className="space-y-4">
      <div className="glass-card flex flex-wrap items-end gap-3 p-4">
        <JalaliDateField label="تاریخ" value={date} onChange={setDate} />
        <div className="text-xs text-ink-dim">
          عضو #{fa(memberId)}
          <p className="mt-1 text-[11px]">ثبت و مشاهدهٔ وعده‌های واقعی — نه برنامهٔ تجویزی</p>
        </div>
      </div>

      {/* جمع روز */}
      {loading && <p className="text-sm text-ink-dim">در حال دریافت…</p>}
      {error && (
        <p className="rounded-lg bg-danger/10 px-3 py-2 text-xs text-danger" role="alert">
          {error}
        </p>
      )}
      {data && (
        <div className="glass-card space-y-3 p-5">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <h3 className="font-semibold">جمع {data.date}</h3>
            <span className={data.data_state === "logged" ? "pill-green" : "pill-gold"}>
              {data.data_state === "logged" ? "ثبت‌شده" : "ثبت نشده"}
            </span>
          </div>

          {totals && (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              {[
                { k: "kcal", label: "کالری", unit: "kcal" },
                { k: "protein_g", label: "پروتئین", unit: "g" },
                { k: "carbs_g", label: "کربوهیدرات", unit: "g" },
                { k: "fat_g", label: "چربی", unit: "g" },
              ].map(({ k, label, unit }) => {
                const value = totals[k as keyof typeof totals];
                const tgt = target ? target[k as keyof typeof target] : 0;
                return (
                  <div key={k} className="rounded-xl bg-surface/60 p-3">
                    <p className="text-[11px] text-ink-dim">{label}</p>
                    <p className="text-lg font-bold">
                      {fa(Math.round(value))}
                      <span className="ml-1 text-[11px] font-normal text-ink-dim">{unit}</span>
                    </p>
                    <p className="text-[11px] text-ink-dim">
                      {hasTarget ? `از ${fa(Math.round(tgt))}` : "بدون هدف"}
                    </p>
                  </div>
                );
              })}
            </div>
          )}

          {!hasTarget && (
            <p className="rounded-lg bg-surface/50 px-3 py-2 text-[11px] text-ink-dim">
              برنامهٔ تغذیهٔ تأییدشده‌ای برای این عضو نیست — پس هدفی هم نمایش داده نمی‌شود.
              هدف از هوا ساخته نمی‌شود.
            </p>
          )}

          {items.length > 0 ? (
            <table className="w-full text-right text-xs">
              <thead className="text-ink-dim">
                <tr>
                  <th className="py-1 font-normal">وعده</th>
                  <th className="py-1 font-normal">مادهٔ غذایی</th>
                  <th className="py-1 font-normal">گرم</th>
                  <th className="py-1 font-normal">کالری</th>
                  <th className="py-1 font-normal">پروتئین</th>
                </tr>
              </thead>
              <tbody>
                {items.map((it) => (
                  <tr key={it.id} className="border-t border-white/5">
                    <td className="py-1.5">
                      {slots.find((s) => s.key === it.meal_slot)?.label ?? it.meal_slot}
                    </td>
                    <td className="py-1.5">
                      {it.name_fa}
                      {it.warning && (
                        <span className="mr-2 text-[10px] text-amber-300">⚠ {it.warning}</span>
                      )}
                    </td>
                    <td className="py-1.5">{fa(it.grams)}</td>
                    <td className="py-1.5">{fa(Math.round(it.kcal))}</td>
                    <td className="py-1.5">{fa(it.protein_g)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="text-xs text-ink-dim">{data.reason}</p>
          )}
        </div>
      )}

      <AdaptiveNutritionPanel memberId={memberId} />

      {/* ثبت وعده */}
      <div className="glass-card space-y-3 p-5">
        <h3 className="font-semibold">ثبت وعده</h3>

        {msg && <p className="rounded-lg bg-emerald-500/10 px-3 py-2 text-xs text-emerald-300">{msg}</p>}
        {err && (
          <p className="rounded-lg bg-rose-500/10 px-3 py-2 text-xs text-rose-300" role="alert">
            {err}
          </p>
        )}

        <div className="flex flex-wrap gap-2">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") void runSearch();
            }}
            placeholder="نام غذا (مثلاً: مرغ، برنج، عدس)"
            className="focus-ring min-w-[12rem] flex-1 rounded-lg bg-surface/70 px-3 py-2 text-sm"
          />
          <button
            onClick={() => void runSearch()}
            disabled={searching}
            className="btn-ghost px-4 py-2 text-xs disabled:opacity-50"
          >
            {searching ? "جستجو…" : "جستجو"}
          </button>
        </div>
        {searchError && <p className="text-[11px] text-ink-dim">{searchError}</p>}

        {results.length > 0 && (
          <div className="max-h-56 space-y-1 overflow-auto">
            {results.map((f) => (
              <button
                key={f.id}
                onClick={() => setSelected(f)}
                className={`flex w-full items-center justify-between rounded-lg px-3 py-2 text-right text-xs transition-colors ${
                  selected?.id === f.id ? "bg-primary/20 text-white" : "bg-surface/50 hover:bg-surface/80"
                }`}
              >
                <span>
                  {f.name_fa}
                  {f.dry_or_raw && (
                    <span className="mr-2 text-[10px] text-amber-300">وزن خشک/خام</span>
                  )}
                </span>
                <span className="text-ink-dim">
                  {fa(f.kcal_per_100g)} kcal · P{fa(f.protein_g_per_100g)} / ۱۰۰گ
                </span>
              </button>
            ))}
          </div>
        )}

        <div className="flex flex-wrap items-end gap-3">
          <div className="text-xs text-ink-dim">
            <span>وعده</span>
            <Select
              aria-label="وعده"
              className="mt-1 block w-44"
              options={slots.map((s) => ({ value: s.key, label: s.label }))}
              value={slot}
              onChange={(value) => setSlot(value)}
            />
          </div>
          <label className="text-xs text-ink-dim">
            وزن (گرم)
            <input
              value={grams}
              onChange={(e) => setGrams(e.target.value)}
              inputMode="decimal"
              className="focus-ring mt-1 block w-24 rounded-lg bg-surface/70 px-3 py-2 text-sm"
            />
          </label>
          <button
            onClick={() => void submit()}
            disabled={busy || !selected}
            className="btn-primary px-4 py-2 text-xs disabled:opacity-50"
          >
            {busy ? "در حال ثبت…" : "ثبت"}
          </button>
        </div>

        {selected && (
          <p className="text-[11px] text-ink-dim">
            انتخاب‌شده: <b className="text-ink">{selected.name_fa}</b>
            {selected.dry_or_raw && " — اعداد برای وزن خشک/خام است"}
          </p>
        )}
      </div>

      <FoodLibrary />
    </div>
  );
}
