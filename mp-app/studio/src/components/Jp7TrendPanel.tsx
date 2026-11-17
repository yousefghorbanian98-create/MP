import { fetchJp7Trend } from "../lib/api";
import { fa, useApi } from "../lib/useApi";

/**
 * G6 — روندنمای JP7 با تفسیر خودکار.
 *
 * دو چیز که این پنل عمداً نشان **نمی‌دهد**:
 *   ۱. درصد چربی — تا تأیید مرجع مستقل قفل است (D-012)؛ روند از مجموع
 *      چین خام ساخته می‌شود، نه از عدد تأییدنشده.
 *   ۲. «تغییر» برای اختلاف زیر خطای کالیپر — آن را «بدون تغییر» می‌نامد.
 */

const statusMap: Record<string, { label: string; cls: string; bar: string }> = {
  decreasing: { label: "کاهش", cls: "pill-green", bar: "bg-emerald-400" },
  increasing: { label: "افزایش", cls: "pill-gold", bar: "bg-amber-400" },
  stable: { label: "بدون تغییر", cls: "pill-gold", bar: "bg-sky-400" },
  insufficient: { label: "داده ناکافی", cls: "pill-red", bar: "bg-rose-400" },
};

const confidenceLabel: Record<string, string> = {
  high: "اطمینان بالا",
  medium: "اطمینان متوسط",
  low: "اطمینان کم",
  insufficient: "داده ناکافی",
};

/** نمودار خطی ساده از مجموع چین‌ها — بدون کتابخانه، بدون وابستگی. */
function Sparkline({ values }: { values: number[] }) {
  if (values.length < 2) return null;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const w = 100;
  const h = 28;
  const pts = values
    .map((v, i) => {
      const x = (i / (values.length - 1)) * w;
      const y = h - ((v - min) / span) * h;
      return `${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join(" ");
  return (
    <svg
      viewBox={`0 0 ${w} ${h}`}
      className="h-12 w-full"
      preserveAspectRatio="none"
      role="img"
      aria-label="نمودار تغییر مجموع چین‌های پوستی"
    >
      <polyline points={pts} fill="none" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  );
}

export function Jp7TrendPanel({ memberId }: { memberId: number }) {
  const { data, loading, error, needsSession } = useApi(
    (s) => fetchJp7Trend(memberId, undefined, s),
    [memberId],
  );

  const interp = data?.interpretation;
  const meta = statusMap[interp?.status ?? "insufficient"];

  return (
    <section className="glass-card space-y-3 p-5">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <h3 className="font-semibold">روند چین‌های پوستی (JP7)</h3>
          <p className="text-xs text-ink-dim">
            سیستم فقط ثبت نمی‌کند — تغییر را تفسیر می‌کند
          </p>
        </div>
        {interp && <span className={meta.cls}>{meta.label}</span>}
      </div>

      {needsSession && <p className="text-sm text-ink-dim">برای دیدن روند، وارد شوید.</p>}
      {loading && <p className="text-sm text-ink-dim">در حال محاسبه…</p>}
      {error && (
        <p className="rounded-lg bg-danger/10 px-3 py-2 text-xs text-danger" role="alert">
          {error}
        </p>
      )}

      {data && (
        <>
          {data.trend ? (
            <>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                <div className="rounded-xl bg-surface/60 p-3">
                  <p className="text-[11px] text-ink-dim">مجموع فعلی</p>
                  <p className="text-lg font-bold">
                    {fa(data.trend.last_sum_mm)}
                    <span className="ml-1 text-[11px] font-normal text-ink-dim">mm</span>
                  </p>
                </div>
                <div className="rounded-xl bg-surface/60 p-3">
                  <p className="text-[11px] text-ink-dim">تغییر کل</p>
                  <p
                    className={`text-lg font-bold ${
                      data.trend.delta_mm < 0 ? "text-emerald-300" : "text-amber-300"
                    }`}
                    dir="ltr"
                  >
                    {data.trend.delta_mm > 0 ? "+" : ""}
                    {data.trend.delta_mm.toFixed(1)}
                  </p>
                </div>
                <div className="rounded-xl bg-surface/60 p-3">
                  <p className="text-[11px] text-ink-dim">در هفته</p>
                  <p className="text-lg font-bold" dir="ltr">
                    {data.trend.delta_mm_per_week === null
                      ? "—"
                      : `${data.trend.delta_mm_per_week > 0 ? "+" : ""}${data.trend.delta_mm_per_week.toFixed(2)}`}
                  </p>
                </div>
                <div className="rounded-xl bg-surface/60 p-3">
                  <p className="text-[11px] text-ink-dim">بازه</p>
                  <p className="text-lg font-bold">{fa(data.trend.span_days)} روز</p>
                </div>
              </div>

              <div className="text-primary-light">
                <Sparkline values={data.measurements.map((m) => m.sum_mm)} />
              </div>
            </>
          ) : (
            <p className="rounded-lg bg-surface/50 px-3 py-2 text-xs text-ink-dim">
              {data.measurements.length === 0
                ? "هیچ اندازه‌گیری JP7 برای این عضو ثبت نشده است."
                : `فقط ${fa(data.measurements.length)} اندازه‌گیری ثبت شده — برای تفسیر روند حداقل دو نقطه لازم است.`}
            </p>
          )}

          {interp && (
            <div className="rounded-xl bg-surface/50 p-3">
              <p className="text-sm font-medium">{interp.headline}</p>
              <p className="mt-1 text-[11px] text-ink-dim">{interp.detail}</p>
              {interp.suggestion && (
                <p className="mt-2 text-[11px] text-primary-light">↳ {interp.suggestion}</p>
              )}
              <p className="mt-2 text-[10px] text-ink-dim">
                دقت: {confidenceLabel[interp.confidence] ?? interp.confidence}
                {interp.threshold_mm !== undefined && ` · آستانهٔ تغییر ${fa(interp.threshold_mm)} mm`}
              </p>
            </div>
          )}

          {data.site_deltas && Object.keys(data.site_deltas).length > 0 && (
            <details className="text-[11px] text-ink-dim">
              <summary className="cursor-pointer">تغییر هر ناحیه</summary>
              <table className="mt-2 w-full text-right">
                <thead>
                  <tr>
                    <th className="py-1 font-normal">ناحیه</th>
                    <th className="py-1 font-normal">اول</th>
                    <th className="py-1 font-normal">آخر</th>
                    <th className="py-1 font-normal">تغییر</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(data.site_deltas).map(([site, d]) => (
                    <tr key={site} className="border-t border-white/5">
                      <td className="py-1" dir="ltr">
                        {site}
                      </td>
                      <td className="py-1">{fa(d.first_mm)}</td>
                      <td className="py-1">{fa(d.last_mm)}</td>
                      <td className="py-1" dir="ltr">
                        {d.delta_mm > 0 ? "+" : ""}
                        {d.delta_mm}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </details>
          )}

          <p className="border-t border-white/10 pt-2 text-[10px] text-ink-dim">
            {data.body_fat_note}
          </p>
        </>
      )}
    </section>
  );
}
