# MEM-CLOSE — دور ۲ (فاز B): SEC-01 · STAFF-01(ب) · STAFF-02 · بستن testidها

> snapshot در HEAD همین commit. «PARTIAL/NOT_ACCEPTED» یعنی ساخته و با تست و
> mutation اثبات‌شده، ولی بدون بازبین مستقل و بدون اجرای مرورگر/دستگاه پذیرفته نشده.
> جدول ۱۶ ردیفیِ دور ۱ (فاز A) در همین پوشه، `summary.md`، دست‌نخورده مانده است.

| # | عنوان | تست‌ها | mutations | وضعیت | یادداشت |
|---|---|---|---|---|---|
| SEC-01 | پاسخ تبدیل‌پذیری ماتریس | ۴ گیت موجود + ۲۷ تست تازه | — | ANSWERED | `evidence/2026-11-27/SEC-01/convertibility.txt` — YES؛ ماتریس دوم ساخته نشد |
| STAFF-01(ب) | گیت مالکیت روی SEC-01 | ۲۷ (`test_staff_ownership_gate.py`) | 2 (M1, M2) | DONE (این بند) | `STAFF-01/ownership-gate.md` · جهش خام: `ownership-mutation-proof.txt` |
| STAFF-02 | اعضا: جست‌وجوی سرور + منفی دسترسی | ۷ بک‌اند + ۳ Studio | 3 (M3, M4, M7) | PARTIAL | detail/edit، pagination UI، stale و بین‌شعبه‌ای باز است |
| STAFF-07/QF-03 | بستن `permission-user` و `permission-expiry` | +۲ (`adminPermissions.test.tsx` → ۶) | 2 (M5, M6) | DONE (این بند) | `OPEN_TESTIDS: 2 → 0` |

## اعداد این دور (از دستورهای ④، نه از حافظه)

- `OPEN_TESTIDS=0` (هدف محقق شد؛ قبلاً ۲).
- `TODO_DONE=7` (بدون تیک تازه — STAFF-02 کامل نشد، پس تیک نخورد).
- `STAFF_GATED=23` — تعریف این دور: تعداد مسیرهای staff-only با تستِ ۴۰۳ در سطح HTTP.
  عدد ۵ در دورهای قبل از خانوادهٔ دیگری (کامل‌بودن route/render/test) بود و هم‌تعریف
  نیست؛ به همین دلیل هر دو عدد با تعریف صریح گزارش می‌شوند، نه به‌عنوان رشد یک سری.
- `MEMBER_ROUTES=11` · `MEMBER_SCREENS=11` بدون تغییر (این دور فاز B بود).

## بدهی‌های ثبت‌شده (نه پنهان)

- STAFF-02: detail/edit UI، pagination در جدول، حالت stale، منفیِ بین‌شعبه‌ای
  (دادهٔ تست تک‌شعبه است) و debounce جست‌وجو.
- گیت مالکیت، مالکیت سطری/داده‌ای را اثبات نمی‌کند (کنترل در service است).
- `interaction_map` پس از تغییر کلاینت بازتولید شد و **بدون تغییر** ماند (رانش صفر).
