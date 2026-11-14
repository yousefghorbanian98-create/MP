# گزارش code-reviewer — M04 (قرارداد API)

## دامنهٔ بازبینی
app/ (factory، errors، deps، jwt)، modules/* (router/service/schemas)، api/v1/api.py، تست‌های قرارداد

## یافته‌ها
| # | سطح | یادداشت |
|---|-----|---------|
| 1 | ✅ OK | نسخه‌بندی `/api/v1` از روز اول؛ OpenAPI با تگ‌های فارسی/انگلیسی |
| 2 | ✅ OK | slowapi روی `/auth/otp/request`، `/auth/otp/verify`، `/auth/refresh` — تست rate-limit سبز |
| 3 | ✅ OK | قالب خطای یکپارچه (`error.code/message/details`) + 422 ساختاریافته |
| 4 | ✅ OK | اسکیمای Pydantic برای همهٔ خانواده‌های endpoint (auth/members/payments/assessment/programs/nutrition/face/notifications/admin) |
| 5 | ✅ OK | OTP فقط هش‌شده (R-002)؛ refresh با rotation + ابطال |
| 6 | ℹ️ Info | guard نقش روی endpointها در M08 (casbin) سخت‌گیرانه می‌شود — فعلی: require_roles آماده |

## Blockerها: **ندارد** ✅
## گیت‌ها: ۵۰ تست سبز | پوشش ۸۴٪ | ruff صفرخطا | bandit/pip-audit تمیز
