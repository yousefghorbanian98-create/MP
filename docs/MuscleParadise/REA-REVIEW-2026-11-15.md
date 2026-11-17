# بازبینی جامع REA — 2026-11-15 (پس از M42)

دامنه: کل سیستم (backend / client / studio / docs / شواهد). قاعدهٔ پژوهش: REA فقط روی
APK/OSS خودمان؛ رقبا فقط از منابع عمومی (در `design/ADMIN-ARCHITECTURE.md`).

## الف) نتایج گیت‌های کیفی (همه سبز)

| گیت | نتیجه | شاهد |
|---|---|---|
| تست بک‌اند | ۲۷۹ سبز (۲۷۶ قبل + ۳ regression جدید) | `pytest tests/` |
| eval درصد (axis-score) | ۴/۴ (طلایی ۲۱۱۲/۲۱۱۲) | `eval/scoring_eval.py` |
| eval تجویز (G4) | ۳/۳ صفر نقض | `eval/prescription_eval.py` |
| ruff | صفر خطا | `ruff check .` |
| TypeScript استودیو | صفر خطا | `tsc --noEmit` |
| vitest استودیو | ۱۸ سبز | `vitest run` |
| زنجیرهٔ migration | تک‌head خطی `f1a2b3c4d5e6` | `alembic history` |
| شواهد (rule-evidence) | ۱۱ فایل + گزارش‌های eval | `finn/reports/evidence/` |

## ب) یافته‌های REA (باگ‌های واقعی — فیکس‌شده در همین نوبت)

1. **`super_admin` در هیچ `require_roles` نبود** ← مالک سیستم از `/reports`، `/population`،
   `/classes`، `/ai`، بازبینی ارزیابی قفل می‌شد (ناسازگار با سیاست casbin «super_admin: همه‌چیز»).
   → فیکس ریشه‌ای در `app/deps.py` (super_admin همیشه مجاز) + تست regression.
2. **`/population` به‌روی عضو بسته بود** ← فرم ورودی کلاینت (`intake_page.dart`) با نقش عضو
   `gate-check` می‌زند و ۴۰۳ می‌گرفت ← مسیر ثبت‌نام واقعی می‌شکست.
   → فیکس: member/reception به guard اضافه شد + تست regression (`test_rea_fixes.py`).
3. **نبود policy برای `/ai`** ← عضو در فرم ورودی از `program/generate` و `nutrition/generate`
   ۴۰۳ می‌گرفت (ماژول ai_engine با casbin بود ولی policy نداشت) — هم‌خانوادهٔ باگ ۲.
4. **تضاد طراحی تولید برنامه** (تست قدیمی «عضو ممنوع» ↔ فرم ورودی «عضو صدا می‌زند») — حل شد
   با D-005: عضو فقط برای خودش + مالکیت اجباری.
5. **سبک‌های مخلوط مجوز**: دو مکانیزم موازی (`casbin require_permission` در اکثر ماژول‌ها،
   `require_roles` در ۷ ماژول) — خطر فراموشی نقش جدید در یکی از دو لایه.
   → ✅ **M43-c3 انجام شد**: همهٔ ماژول‌ها به casbin (`require_permission`) منتقل شدند + مکانیزم
   `DENIES` (ردِ صریح بر allow مقدم) برای حفظ معنای دقیق (گزارش محرمانه بدون manager؛ بازبینی بدون coach).

## ج) ممیزی «ادعاشده در برابر واقعی» (E13/E05)

| مورد | وضعیت |
|---|---|
| نُرم‌ها: هر عدد ← URL شاهد | ✅ ثابت‌شده در `scripts/seed_norms.py` (fitnessnorms.com + Cleveland PDF) |
| بدنهٔ حرکتی ۸۷۶تایی | ✅ free-exercise-db (Unlicense, f00c92c7) + digest |
| تست‌های کلاینت (Flutter) | ⚠️ فقط CI (flutter محلی نیست) — در README/گزارش‌ها همین‌طور ثبت است |
| استودیو | ⚠️ صفحه‌های Dashboard/Members/Programs/CheckIn/Finance با **دادهٔ نمونه (mock)**؛ فقط «تحلیل‌ها» به API واقعی وصل است — هیچ‌جا ادعاشده نشده، اما باید در صف حل شود (M45) |
| S3c (۱۳۷rps) | ✅ `M39c3-set-feedback.perf.json` با متدولوژی کامل |
| پایلوت M40 | ✅ dry-run مستند؛ **پایلوت میدانی ۷ روزه هنوز اجرا نشده** (نیاز به انسان واقعی — در `PILOT-PROTOCOL-M40.md` آماده است) |

## د) تأیید تصمیم معماری توسط مالک (2026-11-15)

مالک باشگاه انتخاب کرد: **«یک برنامهٔ جامع + admin pass»** ← D-003 نهایی شد.
پیامد: قابلیت اعطا/ابطال نقش (admin pass) به اولویت تبدیل می‌شود ← **M43**.

## ه) نقشهٔ لوپ جدید (M43 تا M46) — ثبت‌شده در `BUILD-QUEUE.md`

- **M43 — admin pass (اعطا/ابطال نقش)**: c1 API + audit؛ c2 استودیو Settings؛ c3 یکسان‌سازی مجوز به casbin
- **M44 — پیش‌بینی ریزش (churn/retention)**: c1 قواعد ریسک (بدون LLM در عدد)؛ c2 API + صفحهٔ ریسک؛ c3 هارنس + گزارش
- **M45 — اتصال کامل استودیو به API (حذف mock)**: c1 اعضا/مالی واقعی؛ c2 حضور/برنامه‌ها؛ c3 تست‌های E2E
- **M46 — گزارش کارکرد مربیان** (الگوی زمان‌پرداز + کمیسیون M27): c1 موتور محاسبه؛ c2 گزارش؛ c3 تست
- صف قبلی (تغذیه G5/G3، JP7، آفلاین/sync، وب) پس از M46.
