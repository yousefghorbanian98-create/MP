// ساعت یکتای استودیو (P‑1 · نیمهٔ استودیوییِ F‑28).
// تنها فایلی که `new Date` و `Date.now` مستقیم دارد؛ قاعدهٔ ESLint بقیهٔ src را منع می‌کند.
// «امروز» همیشه در منطقهٔ فروشگاه حساب می‌شود، همان پیش‌فرض بک‌اند (app/config.py: shop_timezone).

/** منطقهٔ مرجع فروشگاه/تغذیه — همان پیش‌فرض `settings.shop_timezone` در بک‌اند. */
export const SHOP_TIMEZONE = "Asia/Tehran";

let override: Date | null = null;

/** ساعت فعلی. فقط تست/درایور با setClock آن را جابه‌جا می‌کند. */
export function now(): Date {
  return override ? new Date(override.getTime()) : new Date();
}

/** ساعت ثابت برای تست/درایور (ISO) — `null` یعنی ساعت واقعی. */
export function setClock(iso: string | null): void {
  override = iso === null ? null : new Date(iso);
}

const dayFormatter = new Intl.DateTimeFormat("en-CA", {
  timeZone: SHOP_TIMEZONE,
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
});

/** «امروز» در منطقهٔ فروشگاه به‌صورت YYYY-MM-DD. */
export function today(): string {
  return dayFormatter.format(now());
}

/** جابه‌جایی روز روی رشتهٔ YYYY-MM-DD بدون وابستگی به منطقهٔ محلی. */
export function shiftIsoDay(iso: string, days: number): string {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(Date.UTC(y, m - 1, d + days)).toISOString().slice(0, 10);
}

/** تجزیهٔ مقدار زمانی از سرور (فقط تجزیه؛ ساعت فعلی نیست). */
export function toDate(value: string | number | Date): Date {
  return new Date(value);
}

/** ساختن تاریخ محلی از اجزا (month صفرمبنا، مثل سازندهٔ Date). */
export function fromParts(year: number, monthIndex: number, day: number): Date {
  return new Date(year, monthIndex, day);
}
