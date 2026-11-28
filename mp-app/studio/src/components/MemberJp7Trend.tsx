/**
 * MEM-07 / PWA-36 — «ارزیابی و روند» در مسیر عضو، روی قرارداد واقعی سرور.
 *
 * ## چرا کامپوننت جدا از `Jp7TrendPanel` (که برای کارکنان است)
 * پنل کارکنان برای مربی نوشته شده و فرض می‌گیرد خواننده تفسیر را می‌فهمد. معیار پذیرش
 * MEM-07 برای **عضو** سخت‌گیرتر است: «۰ کیلو پیشرفت» هرگز وقتی داده نیست؛ و
 * `unknown` / `missing` / `stale` / `not comparable` باید از پیشرفت واقعی جدا شوند.
 *
 * ## قرارداد سرور (همه با `grep -n` تولید شده)
 * - `modules/assessment/service.py:193` → `measured_at` برای هر اندازه‌گیری.
 * - `service.py:194` → `sum_mm` (واحد در نام فیلد: میلی‌متر؛ کلید جدا `unit` وجود ندارد).
 * - `service.py:276-282` → `first_at`/`last_at`/`span_days`/`delta_mm`/`delta_mm_per_week`.
 * - `service.py:204-211` → با کمتر از دو اندازه‌گیری `trend: null` و
 *   `data_state: "insufficient_measurements"`؛ یعنی «روند نیست» یک وضعیت صریح است.
 * - `service.py:147` → `JP7_SUM_CHANGE_MM = 2.0` به‌عنوان `interpretation.threshold_mm`.
 *
 * ## قاعده‌ها
 * - هر عدد با واحد و تاریخ و منبعش نمایش داده می‌شود؛ عدد بدون واحد نداریم.
 * - `trend === null` ⇒ هیچ عددی از «پیشرفت» ساخته نمی‌شود (نه صفر، نه −۰٫۰).
 * - `data_state` ناشناخته ⇒ وضعیت صریح «قابل مقایسه نیست»، نه حالت آماده.
 * - درصد چربی اگر `null` باشد «قفل» گفته می‌شود؛ عکس پیشرفت بدن نه پیاده‌سازی و نه
 *   نمایش داده می‌شود (این فایل هیچ ارجاع تصویری ندارد).
 */
import { useEffect, useState } from "react";
import { ApiError, ForbiddenError, fetchJp7Trend, fetchMe, type Jp7Trend } from "../lib/api";
import { toDate } from "../lib/clock";
import { formatMemberDateTime } from "../lib/memberAccount";

const TREND_SOURCE = "منبع: GET /api/v1/assessments/jp7/member/{member_id}/trend";
const ME_SOURCE = "منبع: GET /api/v1/members/me";

const UNIT_MM = "میلیمتر";

const statusLabels: Record<string, string> = {
  stable: "تغییر معناداری نیست",
  decreasing: "کاهش بافت زیرجلدی",
  increasing: "افزایش بافت زیرجلدی",
  insufficient: "روند نیست — داده کافی نیست",
};

/** `data_state` تنها حالتی که «مقایسه» را مجاز می‌کند. */
const COMPARABLE_STATE = "trend_available";

type Load =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "ready"; data: Jp7Trend };

function mm(value: number): string {
  // عدد + واحد، همیشه با هم؛ هیچ‌جا عدد لخت چاپ نمی‌شود.
  return `${value.toLocaleString("fa-IR", { maximumFractionDigits: 1 })} ${UNIT_MM}`;
}

function measuredAt(iso: string | null): string {
  if (!iso) return "تاریخ اندازه‌گیری در پاسخ نبود";
  // `toDate` از lib/clock است تا قاعدهٔ no-restricted-syntax (ساخت مستقیم Date) حفظ شود.
  if (!Number.isFinite(toDate(iso).getTime())) return "تاریخ اندازه‌گیری قابل‌خواندن نبود";
  return formatMemberDateTime(iso);
}

export function MemberJp7Trend({ memberId: memberIdProp }: { memberId?: number } = {}) {
  const [memberId, setMemberId] = useState<number | null>(memberIdProp ?? null);
  const [load, setLoad] = useState<Load>({ kind: "loading" });

  // شناسهٔ عضو از سرور می‌آید، نه از انتخاب کلاینت (همان قاعدهٔ MEM-04).
  useEffect(() => {
    if (memberIdProp !== undefined) return;
    const controller = new AbortController();
    fetchMe(undefined, controller.signal)
      .then((profile) => setMemberId(profile.id))
      .catch((error: unknown) => {
        const message = error instanceof ApiError ? error.message : "پروفایل از سرور دریافت نشد";
        setLoad({ kind: "error", message });
      });
    return () => controller.abort();
  }, [memberIdProp]);

  useEffect(() => {
    if (memberId === null) return;
    const controller = new AbortController();
    setLoad({ kind: "loading" });
    fetchJp7Trend(memberId, undefined, controller.signal)
      .then((data) => setLoad({ kind: "ready", data }))
      .catch((error: unknown) => {
        // ۴۰۳ در `getJson` به `ForbiddenError` تبدیل می‌شود (نه ApiError با status).
        if (error instanceof ForbiddenError) {
          setLoad({ kind: "error", message: "دسترسی به ارزیابی این عضو مجاز نیست؛ داده‌ای نمایش داده نمی‌شود." });
          return;
        }
        const message = error instanceof ApiError ? error.message : "ارزیابی از سرور دریافت نشد";
        setLoad({ kind: "error", message });
      });
    return () => controller.abort();
  }, [memberId]);

  if (load.kind === "error") {
    return (
      <section aria-labelledby="member-trend-title" className="space-y-3">
        <h3 id="member-trend-title" className="text-base font-semibold">
          ارزیابی و روند
        </h3>
        <p role="alert" className="text-sm text-danger">
          {load.message}
        </p>
      </section>
    );
  }

  if (load.kind === "loading") {
    return (
      <section aria-labelledby="member-trend-title" className="space-y-3">
        <h3 id="member-trend-title" className="text-base font-semibold">
          ارزیابی و روند
        </h3>
        <p role="status" className="text-sm text-ink-dim">
          در حال دریافت ارزیابی از سرور…
        </p>
      </section>
    );
  }

  const { data } = load;
  const comparable = data.data_state === COMPARABLE_STATE && data.trend !== null;
  const interpretation = data.interpretation;
  const status = interpretation?.status ?? "unknown";

  return (
    <section aria-labelledby="member-trend-title" className="space-y-4">
      <div>
        <h3 id="member-trend-title" className="text-base font-semibold">
          ارزیابی و روند
        </h3>
        <p className="mt-1 text-xs text-ink-dim">
          روند روی «مجموع هفت چین پوستی خام» ساخته می‌شود، نه درصد چربی؛ هر عدد با واحد
          ({UNIT_MM}) و تاریخ اندازه‌گیری می‌آید.
        </p>
      </div>

      {/* وضعیت مقایسه — جدا از عدد پیشرفت، و پیش از آن. */}
      <div
        data-trend-state={data.data_state}
        data-comparable={comparable ? "yes" : "no"}
        className="rounded-xl border border-primary/15 bg-surface/70 px-4 py-3 text-xs leading-6"
      >
        <p className="text-sm font-semibold">{statusLabels[status] ?? "وضعیت تفسیر ناشناخته"}</p>
        <p>
          {comparable
            ? interpretation.headline
            : "این پاسخ «قابل مقایسه» نیست؛ پس هیچ عدد پیشرفتی (نه صفر) ساخته نمی‌شود."}
        </p>
        {interpretation?.detail ? <p className="text-ink-dim">{interpretation.detail}</p> : null}
        <p className="text-ink-dim">
          وضعیت داده: {data.data_state} · نسخهٔ قاعده: {data.rule_version}
          {interpretation?.confidence ? ` · اطمینان: ${interpretation.confidence}` : ""}
        </p>
        <p className="text-ink-dim">{TREND_SOURCE}</p>
      </div>

      {/* عدد پیشرفت فقط وقتی `trend` واقعی و `data_state` قابل‌مقایسه است. */}
      {comparable && data.trend ? (
        <dl className="grid gap-3 sm:grid-cols-2">
          <div className="rounded-xl border border-primary/10 px-4 py-3">
            <dt className="text-xs text-ink-dim">تغییر مجموع چین</dt>
            <dd className="mt-1 text-sm font-semibold">
              {data.trend.delta_mm > 0 ? "+" : ""}
              {mm(data.trend.delta_mm)}
            </dd>
            <p className="mt-1 text-[11px] text-ink-dim">
              از {mm(data.trend.first_sum_mm)} به {mm(data.trend.last_sum_mm)} در{" "}
              {data.trend.span_days.toLocaleString("fa-IR")} روز
            </p>
            <p className="mt-1 text-[11px] text-ink-dim">
              آستانهٔ تغییر: {mm(interpretation?.threshold_mm ?? 2)} (خطای اندازه‌گیری کالیپر)
            </p>
          </div>
          <div className="rounded-xl border border-primary/10 px-4 py-3">
            <dt className="text-xs text-ink-dim">سرعت تغییر</dt>
            <dd className="mt-1 text-sm font-semibold">
              {data.trend.delta_mm_per_week === null
                ? "قابل محاسبه نیست — بازهٔ کمتر از یک هفته"
                : `${mm(data.trend.delta_mm_per_week)} در هفته`}
            </dd>
            <p className="mt-1 text-[11px] text-ink-dim">
              بیشترین تغییر: {data.trend.biggest_change_site} ({mm(data.trend.biggest_change_mm)})
            </p>
            {interpretation?.suggestion ? (
              <p className="mt-1 text-[11px] text-ink-dim">{interpretation.suggestion}</p>
            ) : null}
          </div>
        </dl>
      ) : null}

      {/* سری خام — همیشه با واحد، تاریخ و منبع. */}
      <div className="space-y-2">
        <h4 className="text-sm font-semibold">اندازه‌گیری‌ها ({data.measurements.length.toLocaleString("fa-IR")})</h4>
        {data.measurements.length === 0 ? (
          <p role="status" className="text-sm text-ink-dim">
            سرور هیچ اندازه‌گیری‌ای برنگرداند. این «پیشرفت صفر» نیست؛ یعنی داده‌ای ثبت نشده است.
          </p>
        ) : (
          <ul className="space-y-1 text-xs text-ink-dim">
            {data.measurements.map((point) => (
              <li key={point.id}>
                <span className="font-semibold">{measuredAt(point.measured_at)}</span> · مجموع چین:{" "}
                {mm(point.sum_mm)} · درصد چربی:{" "}
                {point.body_fat_pct === null || point.body_fat_pct === undefined
                  ? "قفل (نمایش داده نمی‌شود)"
                  : `${point.body_fat_pct.toLocaleString("fa-IR", { maximumFractionDigits: 1 })}٪`}
              </li>
            ))}
          </ul>
        )}
        <p className="text-[11px] text-ink-dim">{TREND_SOURCE}</p>
        <p className="text-[11px] text-ink-dim">{data.body_fat_note}</p>
      </div>

      <p className="text-[11px] text-ink-dim">
        عکس پیشرفت بدن در این برش نه پیاده‌سازی شده و نه نمایش داده می‌شود.
      </p>
      <p className="text-[11px] text-ink-dim">{ME_SOURCE}</p>
    </section>
  );
}
