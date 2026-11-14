# راهنمای عملیات (M30) — OPS RUNBOOK

## ۱. سرویس‌ها
| سرویس | دستور اجرا | پورت | یادداشت |
|---|---|---|---|
| API (FastAPI) | `mp-app/backend` ← `uvicorn app.main:app --host 0.0.0.0 --port 8000` | 8000 | مستندات /docs |
| Studio (admin) | `mp-app/studio` ← `npm run dev` | 5173 | داخلی/هتلینگ |
| Client (Flutter) | اندروید APK (`mp-app/client/ci_apk.sh`) | — | offline-first |

## ۲. پشتیبان‌گیری (روزانه)
```bash
cd mp-app/backend && ../../.venv/bin/python scripts/backup.py backup --out backups/
```
- خروجی: `mp-backup-*.tar.gz` شامل `mp.db` + `registry.json` + manifest با SHA256.
- **مانور ماهانه**: `backup` ← حذف آزمایشی ← `restore` ← تأیید SHA256 (تست خودکار: `tests/integration/test_backup_drill.py`).

## ۳. بازیابی فاجعه (RTO هدف: < ۳۰ دقیقه)
1. `python scripts/backup.py restore <archive>` (روی همان مسیر mp.db).
2. ری‌استارت API.
3. بررسی سلامت: `GET /api/v1/health` + شمارش اعضا از `/admin/kpis`.
4. ثبت رویداد در CHANGELOG.

## ۴. پایش
- **کندی**: Locust (TOOLING-RUNBOOK §4) — آستانه: p95 > 500ms یا هر 5xx.
- **لاگ‌ها**: uvicorn stdout ← سیستم لاگ مرکزی (journald/docker logs).
- **نرخ‌شمار OTP**: لیمیترها ۱۰/دقیقه + ۳/ثانیه؛ سیل 429 طبیعی است.

## ۵. انتشار دلتا (بدون حذف‌نصب)
- backend: `alembic upgrade head` ← ری‌استارت (M20 همهٔ endpoint ها PATCH ساختاری دارند).
- client: APK با `--build-number` بالاتر ← نصب روی قبلی (حافظهٔ محلی/صف آفلاین حفظ می‌شود — ANDROID-OFFLINE-PLAN).
- studio: `npm run build` ← جایگزینی artifact (کش‌شکنی از هش محتوا).

## ۶. تماس/اولویت
- P1 قطع کامل API ← ری‌استارت + بررسی دیسک/دیتابیس.
- P2 خرابی پیامک ← تعویض ارائه‌دهنده با `sms_provider` (dev برای رفع اضطراری نیست — فقط توسعه).
- P3 گزارش محرمانه ← هرگز در لاگ/تیکت عمومی ارسال نشود (E11).
