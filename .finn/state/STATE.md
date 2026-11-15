# FINN State — وضعیت جاری لوپ

- وضعیت: READY (فاز ۰ بازسازی‌شده با ابزارهای رسمی — آمادهٔ M45)
- میکرو-چرخه جاری: M43-c3 + M44 تمام‌شده | بعدی: **M45** (استودیو روی API واقعی)
- شمارنده تلاش‌های رفع خطا در چرخه جاری: 0
- آخرین گیت سبز: REA-REVIEW-2026-11-15 (۲۷۹ تست، ۴/۴ eval درصد، ۳/۳ eval تجویز، ruff 0، tsc 0، vitest 18)
- آخرین به‌روزرسانی: 2026-11-15
- شاخهٔ کاری: arena/86fc9529-mp

## ابزارها (نصب‌شده و تأییدشده)

- **ECC:** `affaan-m/ECC` — کامیت `d2ef2680594f9a17526a6e1a2e18b3d242c5d17b` (۲۰۲۶-۱۱-۰۶، v2.2.3)
  - ۷۱ ایجنت / ۳۱۴ اسکیل / ۹۸ فرمان / ۲۳ بستهٔ قوانین / هوک‌ها → در `.claude/`
  - نصب‌مایهٔ کامل (۴۸MB) در `.finn/ecc/` (gitignored، کامیت پین‌شده)
  - ⚠️ نصب قبلی از فورک `WorldFlowAI/everything-claude-code@432485ba` بود (۲۰۲۶-۰۱-۲۳) — منسوخ شد
- **REA:** `morluto/rea` v6.9.0 — `~/toolchain/rea` (خارج از مخزن، بازتولید با اسکریپت)
  - Node لازم: `^22.23.4 || ^24.22.1 || >=26.12.1`؛ سیستم `22.22.3` است → portable `24.22.3` در `~/toolchain/node-linux-x64`
  - skill: `.claude/skills/reverse-engineer-anything` · MCP: `.mcp.json` (gitignored)
  - موتور native (Ghidra/Hopper/IDA/JADX): **نصب نیست — لازم هم نیست**
  - اثبات کارکرد: `identify-flutter-build` روی APK خودمان → `flutter_detected: true`, `dart_version 3.14.0`, coverage: partial
  - راهنما: `docs/MuscleParadise/REA-OPERATIONS.md`
- **اسکریپت بازتولید:** `docs/MuscleParadise/finn/install-toolchain.sh` (`all|ecc|rea`، idempotent)

## وضعیت CI (ران 43723865660 — قرمز)

| Job | علت قرمز | رفع |
|---|---|---|
| backend | `ruff format --check`: ۵۲ فایل | `ruff format .` |
| client-flutter | `test/set_feedback_sheet_test.dart` ایمپورت `package:mp_app/...` (نام پکیج `mp_client`) | تغییر ایمپورت → ۵ خطا + ۱ تست فیل رفع می‌شود |
| studio | ✅ سبز | — |
| e2e-api | ⏭️ skip (وابستهٔ backend) | بعد از سبزی backend |

تست واقعی: backend `298 passed`، client `17 passed / 1 failed-to-load` → **کد سالم است، قرمزی از فرمت و نام پکیج است.**

## M45 — استودیو روی API واقعی (2026-11-15) ✅

| جزء | شاهد |
|---|---|
| `GET /admin/attendance` (سری روزانه، جلسه باز/بسته) | ۹ تست در `test_m45_admin_attendance.py` |
| `GET /admin/members-summary` (وضعیت اشتراک + days_left سقف‌دار) | همان فایل |
| `GET /admin/checkins` (جریان ورودها، شامل ردشده) | ۵ تست در `test_m45_checkin_feed.py` |
| `GET /programs` (فهرست با نام عضو + شمارش وضعیت) | ۵ تست در `test_m45_programs_list.py` |
| استودیو: `src/data/mock.ts` **حذف شد** | REA evidence `ev_a3e81c13…` — ۲۶ منبع سورس، بدون mock |
| استودیو: Dashboard/Members/Programs/CheckIn روی API | ۳۰ تست vitest + tsc صفر خطا |

**گیت‌ها:** backend ۳۱۷ تست سبز · ruff check/format ۰ · studio tsc ۰ · vitest ۳۰.
**نکتهٔ صادقانه:** `alembic check` drift نشان می‌دهد (۲ نبود-index + nullable ناسازگار) — این drift **قبل از M45** وجود داشت، من مدلی اضافه نکردم. برای M46 در صف است.
