# گزارش بازبینی کد M20 — آپدیت تفاضلی (code-reviewer)

**بازبین:** ایجنت code-reviewer | **تاریخ:** 2026-11-14 | **دور:** دوم

## دامنه
`modules/updates/` (service+router+registry.json)، `studio/public/sw.js`، `studio/src/lib/update.ts` + `UpdateBanner.tsx`، `client/lib/core/updater/update_service.dart`، ۶ تست بک‌اند + ۱ تست Vitest.

## یافته‌ها
- ✅ endpoint مانیفست **عمومی** (بررسی پیش از ورود) با اعتبارسنجی پلتفرم (422 برای ناشناخته)
- ✅ یکپارچگی پچ: sha256 اجباری + fallback به full در نبود مسیر delta + `force` برای نسخهٔ زیر min_supported
- ✅ منطق مقایسهٔ نسخه در سه لایه (Py/TS/Dart) با نرمال‌سازی یکسان — تست صریح
- ⚠️ اعمال patch باینری (bsdiff) به native وابسته است — fallback full تست شده (D-011)

## حکم
**صفر Blocker**.
