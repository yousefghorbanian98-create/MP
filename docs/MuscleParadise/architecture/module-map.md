# نقشهٔ ماژول‌های Backend — مرزها و مسئولیت‌ها

> چرخه: M02 | ADR-001 | نقشهٔ اولیه برای مرور مرز ماژول؛ جدول و جریان‌های پایین تاریخی‌اند و فهرست کامل ماژول‌ها یا ادعای اجرای E2E نیستند.
>
> **به‌روزرسانی دامنه:** پرداخت انتشار اول کارت‌به‌کارت با فیش و تأیید مستقل انسانی است، نه الزام درگاه؛ چهره، wger/OFF/USDA و زمان گیت چهره به‌عنوان قابلیت یا دیتای انتشار اول فرض نشوند. برای جریان‌های هدف، نقش‌ها، صندوق و بانک [نقشهٔ ابری/مالی](cloud-finance-access.md)؛ برای دامنه و وضعیت [TODO مالک](../TODO-CLOUD-FINANCE-ACCESS.md). مسیرهای فعلی را با کد و تست بازبینی کنید.

| ماژول | مسئولیت | وابستگی به ماژول دیگر | جداول اصلی (M03) |
|-------|---------|------------------------|------------------|
| `auth` | OTP، JWT access/refresh، ابطال، «خروج همه» | — | User, OtpCode, RefreshToken |
| `membership` | عضو، پروفایل، اهداف، اشتراک (Membership) | auth | Member, Membership |
| `payments` | پرداخت (زرین‌پال/نقدی)، کیف‌پول، رسید | membership | Payment, WalletTransaction |
| `assessment` | ارزیابی ۱۴ دامنه، DomainScore، JP7 | membership | Assessment14Domain, DomainScore, JacksonPollockMeasurement |
| `programs` | WorkoutProgram، ProgramWeek، تأیید مربی | assessment, ai_engine | WorkoutProgram, ProgramWeek, ProgramExercise |
| `nutrition` | NutritionPlan، MealItem | ai_engine, content | NutritionPlan, MealItem |
| `face_id` | FaceTemplate (رمزنگاری)، consent، چک‌این چهره/QR | membership | FaceTemplate, BiometricConsent, CheckIn |
| `notification` | اعلان درون‌برنامه‌ای/پیامک، یادآوری، jobها | membership | Notification |
| `ai_engine` | موتور قواعد (ACSM/NSCA) + پل Ollama (فقط متن) | assessment | RuleRun (لاگ خروجی موتور) |
| `content` | کتابخانهٔ حرکات/غذا (wger/OFF/USDA + seed محلی) | — | Exercise, FoodItem |
| `admin` | audit log، feature flags، گزارش‌های مدیر | همه (فقط خواندن) | AuditLog, FeatureFlag, Campaign, Offer |

## جریان‌های حیاتی (مسیرهای E2E — M14)

1. **ثبت‌نام → پرداخت → چک‌این:** auth (OTP) → membership → payments (زرین‌پال/نقدی) → face_id (QR/چهره)
2. **تأیید برنامه توسط مربی:** assessment (۱۴ دامنه + هدف) → ai_engine (قواعد) → programs (draft) → مربی (approve) → notification → عضو
3. **گیت چهره:** face_id (liveness + SFace match) → CheckIn (< ۲s) → fallback QR
