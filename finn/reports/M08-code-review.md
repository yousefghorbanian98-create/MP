# گزارش بازبینی کد M08 — احراز هویت (code-reviewer)

**بازبین:** ایجنت code-reviewer | **تاریخ:** 2026-11-14 (بازبینی پس‌انداخت — backfill)

## دامنه
`security/rbac.py` (casbin)، چرخش JWT + logout-all در `app/security/jwt.py` و `modules/auth`، نگهبان `require_permission()` در `app/deps.py`، ۸ روتر محافظت‌شده، `tests/test_rbac` (۲۷ ماتریس)، `tests/integration/test_api_contract` (بازنویسی auth).

## یافته‌ها
- ✅ ماتریس RBAC: ۴ نقش × عملیات — exact + `/*` (keyMatch2) بدون سیاست اضافی
- ✅ logout-all: ابطال واقعی (نه فقط پاک‌کردن کلاینت)
- ⚠️ نکتهٔ بازبینی‌شده: `Annotated["User", ...]` با `from __future__ import annotations` حل نمی‌شود (درس LEDGER #4) — رفع شد با import زمان اجرا
- ⚠️ فیکسچرها: تداخل شمارهٔ تلفن (UNIQUE) و شمارندهٔ rate-limit — هر دو رفع و در REGRESSIONS ثبت شد (R-004)

## حکم
**صفر Blocker** — ۹۱ تست سبز / ۸۵٪. تغییرات امنیتی مطابق OWASP A01 (کنترل دسترسی) پذیرفته شد.
