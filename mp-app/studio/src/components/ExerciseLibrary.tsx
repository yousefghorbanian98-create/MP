import { useEffect, useMemo, useState } from "react";
import { browseExercises, type ExerciseRow } from "../lib/api";
import { fa } from "../lib/useApi";

/**
 * G9 — کتابخانهٔ حرکات با تصویر اجرا.
 *
 * پیش از این، در برنامهٔ ورزشی فقط «نام» حرکت دیده می‌شد و شاگرد
 * نمی‌دانست حرکت را چطور اجرا کند. تصاویر از free-exercise-db
 * (Unlicense / مالکیت عمومی) می‌آیند و از خودِ همان API سرو می‌شوند —
 * پس PWA آفلاین هم تصویر دارد و هیچ hotlink به سرور بیرونی نداریم.
 *
 * دو فریم برای هر حرکت (شروع/پایان) نمایش داده می‌شود؛ با کلیک روی
 * حرکت، فریم دوم و گروه عضلانی/ابزار دیده می‌شود.
 */

const MUSCLE_LABELS: Record<string, string> = {
  legs: "پا",
  posterior_chain: "زنجیرهٔ پشتی",
  chest_shoulders: "سینه و سرشانه",
  back_biceps: "زیربغل و جلوبازو",
  core: "مرکز بدن",
  full_body: "کل بدن",
};

export function ExerciseLibrary() {
  const [rows, setRows] = useState<ExerciseRow[]>([]);
  const [group, setGroup] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const ctrl = new AbortController();
    let alive = true;
    setLoading(true);
    setError(null);
    browseExercises(group, query, undefined, ctrl.signal)
      .then((d) => {
        if (alive) setRows(d);
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
  }, [group, query]);

  // گروه‌ها از خود داده ساخته می‌شوند تا با داده ناهم‌خوان نشوند
  const groups = useMemo(() => {
    const map = new Map<string, number>();
    for (const r of rows) map.set(r.muscle_group, (map.get(r.muscle_group) ?? 0) + 1);
    return [...map.entries()].sort((a, b) => b[1] - a[1]);
  }, [rows]);

  return (
    <section className="glass-card space-y-3 p-5">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <h3 className="font-semibold">کتابخانهٔ حرکات</h3>
          <p className="text-xs text-ink-dim">
            تصاویر اجرا از پایگاه آزاد (Unlicense) · دو فریم شروع و پایان
          </p>
        </div>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="جست‌وجوی نام حرکت…"
          className="focus-ring w-52 rounded-lg bg-surface/70 px-3 py-2 text-sm"
        />
      </div>

      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => setGroup(null)}
          className={`rounded-full px-3 py-1 text-xs ${group === null ? "bg-accent text-white" : "bg-surface/70 text-ink-dim"}`}
        >
          همه ({loading ? "…" : fa(rows.length)})
        </button>
        {groups.map(([g, n]) => (
          <button
            key={g}
            onClick={() => setGroup(g === group ? null : g)}
            className={`rounded-full px-3 py-1 text-xs ${g === group ? "bg-accent text-white" : "bg-surface/70 text-ink-dim"}`}
          >
            {MUSCLE_LABELS[g] ?? g} ({fa(n)})
          </button>
        ))}
      </div>

      {error && <p className="text-xs text-red-400">{error}</p>}

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
        {rows.map((r) => {
          const isOpen = open === r.exercise_id;
          const src = isOpen && r.image_url_alt ? r.image_url_alt : r.image_url;
          return (
            <button
              key={r.exercise_id}
              onClick={() => setOpen(isOpen ? null : r.exercise_id)}
              aria-pressed={isOpen}
              className="focus-ring overflow-hidden rounded-xl bg-surface/60 text-right"
            >
              {src ? (
                <img
                  src={src}
                  alt={`اجرای ${r.name_fa} — ${isOpen ? "فریم پایان" : "فریم شروع"}`}
                  loading="lazy"
                  width={300}
                  height={300}
                  className="h-auto w-full object-cover"
                />
              ) : (
                <div className="flex h-32 items-center justify-center text-xs text-ink-dim">
                  بدون تصویر
                </div>
              )}
              <div className="space-y-0.5 p-2">
                <p className="text-sm font-medium">{r.name_fa}</p>
                <p className="text-[11px] text-ink-dim">
                  {MUSCLE_LABELS[r.muscle_group] ?? r.muscle_group}
                  {r.equipment ? ` · ${r.equipment}` : ""}
                </p>
                {isOpen && r.name_en && (
                  <p dir="ltr" className="text-[11px] text-ink-dim">
                    {r.name_en}
                  </p>
                )}
              </div>
            </button>
          );
        })}
      </div>

      {!loading && !error && rows.length === 0 && (
        <p className="text-xs text-ink-dim">حرکتی با این فیلتر پیدا نشد.</p>
      )}
    </section>
  );
}
