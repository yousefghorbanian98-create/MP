# چک‌لیست OWASP Top 10 — Muscle Paradise (M09)

> وضعیت: به‌روزرسانی در هر release بزرگ | مرجع: OWASP Cheat Sheet Series

| # | آسیب‌پذیری | اقدام MP | وضعیت |
|---|-----------|----------|--------|
| A01 | Broken Access Control | RBAC casbin (ماتریس ۴ نقش) + guard سطح روتر + کنترل مالکیت در service | ✅ تست‌شده (M08) |
| A02 | Cryptographic Failures | OTP/refresh فقط هش‌شده؛ FaceTemplate با PyNaCl SecretBox؛ JWT HS256 با کلید env | ✅ تست‌شده (M03/M08) |
| A03 | Injection | SQLAlchemy ORM (بدون SQL خام) + Pydantic validation برای همهٔ ورودی‌ها | ✅ |
| A04 | Insecure Design | موتور قواعد قطعی (G8) + تأیید مربی + محدودیت نرخ + audit log | ✅ |
| A05 | Security Misconfiguration | هدرهای امنیتی (CSP/HSTS/...) در middleware + Caddyfile در M11 | ✅ تست‌شده |
| A06 | Vulnerable Components | pip-audit + npm audit در هر چرخه | ✅ هر چرخه |
| A07 | Auth Failures | OTP با TTL/attempts/قفل موقت + rate-limit + rotation refresh | ✅ تست‌شده (M08) |
| A08 | Data Integrity Failures | migration نسخه‌دار (Alembic) + audit log غیرقابل‌حذف برای عملیات حساس | ✅ |
| A09 | Logging Failures | structlog ساختاریافته + AuditLog (actor/action/entity/time) | ✅ (M05/M09) |
| A10 | SSRF | هیچ fetch کاربر-کنترل‌شده‌ای به URL خارجی وجود ندارد (فقط providerهای ثابت) | ✅ |

## قواعد اختصاصی MP
1. **دادهٔ بیومتریک**: فقط embedding رمزنگاری‌شده؛ تصویر خام هرگز ذخیره نمی‌شود (NFR-3)
2. **پنتست LLM-محور (Strix)**: فقط روی staging با دادهٔ مصنوعی — هرگز دادهٔ واقعی اعضا
3. **عملیات حساس ثبت می‌شوند**: تغییر برنامه، پرداخت، حذف چهره، خروج همه، تغییر flag (US-406)
