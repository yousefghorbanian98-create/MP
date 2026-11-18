# گزارش تست بار M22-smoke — Locust 2.47 (کاربران فیک)

- تاریخ: ۲۰۲۶-۱۱-۱۴ | ابزار: `locustio/locust` (BSD-3, رایگان) — نصب در venv جدا (`/tmp/tools-venv`)
- سناریو: `mp-app/backend/tests/load/locustfile.py` — ۴۰ کاربر فیک، نرخ ورود ۸/ثانیه، مدت ۲۰s، هدف `http://127.0.0.1:8000`
- داده: تماماً ساختگی (E09) — هیچ کاربر واقعی ساخته نشد

## نتیجه
| شاخص | مقدار |
|---|---|
| کل درخواست‌ها | **835** (~42 req/s) |
| پاسخ موفق | 590 (70.7%) |
| «خطا» | **245 (29.3%) — همه HTTP 429 روی `/auth/otp/request`** |
| کرش/قطع سرویس | **صفر** — سرور پایدار ماند |
| p50 / p95 / p99 | **5ms / 13ms / 26ms** |
| max | 210ms (پاسخ‌های اولیه) |

## یافته‌ها
1. **پایداری تأیید شد:** ۴۰ کاربر هم‌زمان هیچ قطعی/کرشی ایجاد نکرد؛ زمان پاسخ تک‌رقمی میلی‌ثانیه.
2. **rate-limit (`5/minute` روی OTP) زیر بار درست عمل کرد** — طوفان ورود (ساعت اوج باشگاه) را مهار می‌کند؛ اما برای تجربهٔ واقعی «ساعت افتتاح» باید در M28 برای OTP سقف انفجاری/صف در نظر گرفته شود تا کاربران واقعی پشت ۴۲۹ نمانند.
3. فایل‌های CSV خام: `finn/reports/load/M22-smoke_stats.csv/_stats_history.csv/_failures.csv/_exceptions.csv`

## تکرار آزمون
```bash
/tmp/tools-venv/bin/pip install locust
# سرور: cd mp-app/backend && ../../.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
/tmp/tools-venv/bin/locust -f mp-app/backend/tests/load/locustfile.py \
  --headless -u 40 -r 8 -t 20s --host http://127.0.0.1:8000 --csv=finn/reports/load/M22-smoke
```
