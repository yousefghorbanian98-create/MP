import { useId } from "react";
import DatePicker, { DateObject } from "react-multi-date-picker";
import persian from "react-date-object/calendars/persian";
import persian_fa from "react-date-object/locales/persian_fa";
import { fromParts } from "../../lib/clock";

/**
 * فیلد تاریخ جلالی — فقط پوستهٔ نازک دور `react-multi-date-picker`.
 *
 * Q11: کنترل از کتابخانه می‌آید، اینجا فقط «تبدیل مقدار» نوشته شده است:
 *   ورودی/خروجی این کامپوننت ISO میلادی (`YYYY-MM-DD`) است — همان چیزی که
 *   API می‌فهمد — ولی کاربر تقویم و اعداد شمسی می‌بیند. تبدیل با
 *   `react-date-object` انجام می‌شود، نه با کد تاریخ‌نویسی دست‌ساز.
 */

export interface JalaliDateFieldProps {
  /** تاریخ به شکل `YYYY-MM-DD` میلادی؛ رشتهٔ خالی یعنی «انتخاب نشده». */
  value: string;
  onChange: (isoDate: string) => void;
  label: string;
  disabled?: boolean;
}

const ISO_RE = /^(\d{4})-(\d{2})-(\d{2})$/;

export function isoFromLocal(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

export function toDateObject(iso: string): DateObject | undefined {
  const match = ISO_RE.exec(iso);
  if (!match) return undefined;
  // تاریخ میلادی را به‌صورت محلی می‌سازیم تا مرز روز با تغییر تایم‌زون جابه‌جا نشود.
  const asDate = fromParts(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
  return new DateObject({ date: asDate, calendar: persian, locale: persian_fa });
}

export function JalaliDateField({ value, onChange, label, disabled }: JalaliDateFieldProps) {
  // کتابخانه `aria-label` روی input نمی‌گذارد؛ پس برچسب واقعی `<label for>` می‌سازیم
  // و id را به کامپوننت می‌دهیم تا صفحه‌خوان و تست a11y هر دو نام فیلد را ببینند.
  const id = useId();
  return (
    <div className="text-xs text-ink-dim">
      <label htmlFor={id}>{label}</label>
      <DatePicker
        id={id}
        calendar={persian}
        calendarPosition="bottom-right"
        className="mp-jalali-picker"
        containerClassName="mp-jalali-container"
        disabled={disabled}
        format="YYYY/MM/DD"
        inputClass="focus-ring mt-1 block w-40 rounded-lg border border-primary/20 bg-surface/70 px-3 py-2 text-sm text-ink"
        locale={persian_fa}
        value={toDateObject(value)}
        onChange={(selected) => {
          const picked = Array.isArray(selected) ? selected[0] : selected;
          if (!picked) return;
          onChange(isoFromLocal(picked.toDate()));
        }}
      />
    </div>
  );
}
