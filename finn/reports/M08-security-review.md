# گزارش security-reviewer — M08 (احراز هویت و اختیارات)

## دامنهٔ بازبینی
security/rbac.py (casbin)، auth service (OTP/refresh)، app/deps.py (guardها)، تست‌های نفوذ سطحی

## یافته‌ها
| # | سطح | یادداشت |
|---|-----|---------|
| 1 | ✅ OK | OTP فقط هش‌شده (salt + SHA-256 + compare_digest) — R-002 پابرجا |
| 2 | ✅ OK | refresh token: هش‌شده در DB + rotation + ابطال؛ «خروج از همهٔ دستگاه‌ها» همه را باطل می‌کند (تست‌شده) |
| 3 | ✅ OK | RBAC با casbin: ماتریس ۲۷گانهٔ تست‌شده (member/coach/reception/manager) — guard سطح روتر روی همهٔ endpointهای حساس |
| 4 | ✅ OK | rate-limit روی OTP/لاگین (slowapi) + قفل موقت بعد از ۵ تلاش اشتباه |
| 5 | ✅ OK | تست نفوذ سطحی: توکن نامعتبر/بدون توکن (401)، نقش نامجاز (403)، تلاش عضو برای admin (403) |
| 6 | ℹ️ Info | مالکیت داده (member فقط دادهٔ خودش) فعلاً در service — ABAC کامل در صورت نیاز بعداً |

## Blockerها: **ندارد** ✅
## گیت‌ها: ۹۱ تست سبز | پوشش ۸۵٪ | bandit صفر | ruff صفرخطا
