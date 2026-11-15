import { useCallback, useEffect, useState } from "react";
import { fetchReminders, type RemindersReport } from "../lib/api";
import { fa } from "../lib/useApi";
import { useAppStore } from "../stores/appStore";

/**
 * G11 — یادآوری‌های عضو.
 *
 * نکتهٔ طراحی: بارگذاری صفحه یادآوری‌ها را در سرور «ماده» می‌کند
 * (`created_notifications`). دکمهٔ بازخوانی واقعاً همان را صدا می‌زند،
 * ولی سرور با قاعدهٔ ۲۴ ساعته از تکرار جلوگیری می‌کند.
 */

const PRIORITY_FA: Record<string, string> = {
  high: "فوری",
  normal: "عادی",
};

export function RemindersPanel() {
  const selectedMemberId = useAppStore((s) => s.selectedMemberId);
  const [report, setReport] = useState<RemindersReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (selectedMemberId === null) {
      setReport(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await fetchReminders(selectedMemberId);
      // پاسخ ناقص نباید کل پنل را با استثنا از کار بیندازد: هر فیلد به
      // مقدار امن فروکاسته می‌شود، ولی به‌عنوان دادهٔ واقعی جعل نمی‌شود.
      setReport({
        ...data,
        reminders: data.reminders ?? [],
        skipped: data.skipped ?? [],
        thresholds: {
          renewal_lead_days: data.thresholds?.renewal_lead_days ?? 0,
          inactivity_days: data.thresholds?.inactivity_days ?? 0,
          reassess_days: data.thresholds?.reassess_days ?? 0,
        },
      });
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [selectedMemberId]);

  useEffect(() => {
    void load();
  }, [load]);

  if (selectedMemberId === null) {
    return (
      <p className="glass-card p-4 text-xs text-ink-dim">
        برای دیدن یادآوری‌ها، یک عضو را از صفحهٔ «اعضا» انتخاب کنید.
      </p>
    );
  }

  return (
    <div className="glass-card space-y-3 p-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold">یادآوری‌ها</h3>
        <button onClick={() => void load()} className="btn-ghost px-2 py-1 text-[11px]">
          بازخوانی
        </button>
      </div>

      {error && (
        <p role="alert" className="rounded-lg bg-danger/10 px-3 py-2 text-xs text-danger">
          {error}
        </p>
      )}
      {loading && <p className="text-xs text-ink-dim">در حال محاسبه…</p>}

      {!loading && report && (
        <>
          {report.reminders.length === 0 ? (
            <p className="text-xs text-ink-dim">
              در حال حاضر یادآوری‌ای لازم نیست.
            </p>
          ) : (
            <ul className="space-y-2">
              {report.reminders.map((r) => (
                <li
                  key={r.key}
                  className={`rounded-lg px-3 py-2 text-xs ${
                    r.priority === "high" ? "bg-amber-400/10" : "bg-surface/60"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium">
                      {r.title}
                      <span className="mr-2 text-[10px] text-ink-dim">
                        {PRIORITY_FA[r.priority] ?? r.priority}
                      </span>
                    </span>
                    {r.due_in_days > 0 && (
                      <span className="text-[10px] text-ink-dim">
                        {fa(r.due_in_days)} روز دیگر
                      </span>
                    )}
                  </div>
                  <p className="mt-1 text-ink-dim">{r.body}</p>
                  <p className="mt-1 text-[10px] text-ink-dim/70">قاعده: {r.rule}</p>
                </li>
              ))}
            </ul>
          )}

          {report.skipped.length > 0 && (
            <div className="border-t border-white/10 pt-2">
              <p className="text-[10px] text-ink-dim">
                یادآوری ساخته‌نشده (دادهٔ ناکافی — نه «همه‌چیز خوب است»):
              </p>
              <ul className="mt-1 space-y-0.5">
                {report.skipped.map((s) => (
                  <li key={s.key} className="text-[10px] text-ink-dim">
                    · {s.key}: {s.reason}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <p className="text-[10px] text-ink-dim/70">
            آستانه‌ها: تمدید {fa(report.thresholds.renewal_lead_days)} روز قبل ·
            بی‌تحرکی {fa(report.thresholds.inactivity_days)} روز · ارزیابی{" "}
            {fa(report.thresholds.reassess_days)} روز
          </p>
        </>
      )}
    </div>
  );
}
