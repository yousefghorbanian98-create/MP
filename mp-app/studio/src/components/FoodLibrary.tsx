import { useEffect, useMemo, useState } from "react";
import { browseFoods, type FoodRow } from "../lib/api";
import { fa } from "../lib/useApi";

/**
 * G12 — پایگاه غذای ایرانی: مرور و فیلتر جدول واقعی.
 *
 * منبع: `soooolag/food-finder` (MIT) — ۳۰۵ غذای ایرانی، ۱۱ دسته.
 * این کامپوننت فقط نمایش است: عددها همان عددهای جدول‌اند و دسته‌ها
 * از داده استخراج می‌شوند، نه فهرست دستی که با داده ناهم‌خوان شود.
 */

export function FoodLibrary() {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState<string | null>(null);
  const [rows, setRows] = useState<FoodRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const ctrl = new AbortController();
    let alive = true;
    setLoading(true);
    setError(null);
    browseFoods(query, 100, undefined, ctrl.signal)
      .then((d) => {
        // پاسخ سرور/استاب ممکن است شکل دیگری داشته باشد؛ آرایهٔ نامعتبر نباید
        // کل صفحه را با «rows is not iterable» بترکاند.
        if (alive) setRows(Array.isArray(d) ? d : []);
      })
      .catch((e: unknown) => {
        if (e instanceof DOMException && e.name === "AbortError") return;
        if (alive) setError(e instanceof Error ? e.message : "خطای ناشناخته");
      })
      .finally(() => {
        if (alive) setLoading(false);
      });
    return () => {
      alive = false;
      ctrl.abort();
    };
  }, [query]);

  // دسته‌ها از خود داده ساخته می‌شوند — نه فهرست ثابت که با داده ناهم‌خوان شود
  const categories = useMemo(() => {
    const map = new Map<string, number>();
    for (const r of rows) map.set(r.category, (map.get(r.category) ?? 0) + 1);
    return [...map.entries()].sort((a, b) => b[1] - a[1]);
  }, [rows]);

  const visible = category === null ? rows : rows.filter((r) => r.category === category);
  const dryCount = visible.filter((r) => r.dry_or_raw).length;

  return (
    <section className="glass-card space-y-3 p-5">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <h3 className="font-semibold">پایگاه غذای ایرانی</h3>
          <p className="text-xs text-ink-dim">
            جدول آزاد (مجوز MIT) · اعداد برای ۱۰۰ گرم · چربی از معادلهٔ آتووتر تخمین زده شده
          </p>
        </div>
        <span className="text-[11px] text-ink-dim">
          {fa(visible.length)} از {fa(rows.length)} غذا
          {dryCount > 0 && ` · ${fa(dryCount)} با وزن خشک/خام`}
        </span>
      </div>

      <div className="flex flex-wrap gap-2">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="جستجو (فارسی یا انگلیسی)"
          className="focus-ring min-w-[12rem] flex-1 rounded-lg bg-surface/70 px-3 py-2 text-sm"
        />
        <button
          onClick={() => {
            setCategory(null);
            setQuery("");
          }}
          className={`px-3 py-1.5 text-xs ${category === null ? "btn-primary" : "btn-ghost"}`}
        >
          همه
        </button>
      </div>

      {loading && <p className="text-sm text-ink-dim">در حال بارگذاری…</p>}
      {error && (
        <p className="rounded-lg bg-danger/10 px-3 py-2 text-xs text-danger" role="alert">
          {error}
        </p>
      )}

      {!loading && !error && rows.length === 0 && (
        <p className="rounded-lg bg-surface/50 p-6 text-center text-sm text-ink-dim">
          {query
            ? `«${query}» در جدول غذایی نیست — عبارت دیگری را امتحان کنید.`
            : "جدول غذایی خالی است. اسکریپت واردات را اجرا کنید (scripts/import_food_catalog.py)."}
        </p>
      )}

      {categories.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {categories.map(([cat, count]) => (
            <button
              key={cat}
              onClick={() => setCategory(category === cat ? null : cat)}
              className={`rounded-full px-2.5 py-1 text-[11px] transition-colors ${
                category === cat ? "bg-primary/25 text-white" : "bg-surface/60 text-ink-dim hover:bg-surface"
              }`}
            >
              {cat} <span className="opacity-60">{fa(count)}</span>
            </button>
          ))}
        </div>
      )}

      {visible.length > 0 && (
        <div className="max-h-[26rem] overflow-auto">
          <table className="w-full text-right text-xs">
            <thead className="sticky top-0 bg-surface/90 text-ink-dim">
              <tr>
                <th className="py-1.5 font-normal">غذا</th>
                <th className="py-1.5 font-normal">دسته</th>
                <th className="py-1.5 font-normal">کالری</th>
                <th className="py-1.5 font-normal">پروتئین</th>
                <th className="py-1.5 font-normal">کارب</th>
                <th className="py-1.5 font-normal">چربی</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((f) => (
                <tr key={f.id} className="border-t border-white/5">
                  <td className="py-1.5">
                    {f.name_fa}
                    {f.dry_or_raw && (
                      <span className="mr-1 text-[10px] text-amber-300">[خشک/خام]</span>
                    )}
                  </td>
                  <td className="py-1.5 text-ink-dim">{f.category}</td>
                  <td className="py-1.5">{fa(f.kcal_per_100g)}</td>
                  <td className="py-1.5">{fa(f.protein_g_per_100g)}</td>
                  <td className="py-1.5">{fa(f.carbs_g_per_100g)}</td>
                  <td className="py-1.5">
                    {f.fat_g_per_100g === 0 ? (
                      <span className="text-ink-dim" title="چربی از دادهٔ منبع قابل استخراج نبود">
                        نامعلوم
                      </span>
                    ) : (
                      fa(f.fat_g_per_100g)
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
