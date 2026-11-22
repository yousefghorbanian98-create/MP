/**
 * مبلغ ریالی (F‑09): فقط عدد صحیح ایمن.
 * Number(...) روی مبلغ «1e3»، «1000.5» و اعداد بالای ۲^۵۳ را بی‌صدا می‌پذیرد؛
 * این توابع ورودی را رشته‌ای می‌گیرند، ارقام فارسی/عربی و جداکننده‌ها را نرمال می‌کنند
 * و فقط عدد صحیح در بازهٔ ایمن را برمی‌گردانند.
 */

export const MAX_SAFE_RIAL = Number.MAX_SAFE_INTEGER;

const PERSIAN_ARABIC_DIGITS = "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩";

function normalize(raw: string): string {
  let out = "";
  for (const ch of raw) {
    const idx = PERSIAN_ARABIC_DIGITS.indexOf(ch);
    if (idx >= 0) out += String(idx % 10);
    else if (ch === "٬" || ch === "،" || ch === "," || ch === " " || ch === "\u200c") continue;
    else out += ch;
  }
  return out;
}

/** عدد صحیح ایمن یا null. */
export function parseRial(raw: string | number): number | null {
  const text = normalize(String(raw).trim());
  if (!/^\d+$/.test(text)) return null;
  const n = Number(text);
  return Number.isSafeInteger(n) && n <= MAX_SAFE_RIAL ? n : null;
}

/** مثل parseRial اما خطا می‌دهد؛ برای فرم‌ها. */
export function parseRialOrThrow(raw: string, label: string): number {
  const n = parseRial(raw);
  if (n === null) throw new Error(`${label} باید عدد صحیح و معتبر (بدون اعشار) باشد`);
  return n;
}

/** نمایش مبلغ دریافتی از سرور (عدد صحیح). */
export function formatRial(value: number | string): string {
  const n = typeof value === "number" ? value : parseRial(value);
  if (n === null || !Number.isSafeInteger(n)) return String(value);
  return n.toLocaleString("fa-IR");
}
