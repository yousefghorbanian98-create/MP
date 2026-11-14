# Runbook — Rollback (M10)

> هرگز rollback در ساعت شلوغی بدون مانیتورینگ انجام نشود (لایهٔ ۱۰/۱۳).

## کی rollback کنیم؟
- خطای ۵xx بیش از ۱٪ درخواست‌ها پس از دیپلوی
- شکست health gate (`/health` پاسخ ندهد)
- گزارش خرابی گیت ورود (SLO < 2s شکسته شود)

## چگونه
1. **Dokploy**: در پنل Dokploy، ایمیج قبلی (last-known-good) را انتخاب و Restore کن
2. **CI**: اجرای `mp-app/infra/scripts/rollback.sh <webhook> <image-tag>` (workflow_dispatch گردش‌کار mp-deploy)
3. **دستی**: `docker stop mp-backend && docker run -d mp-backend:<previous-tag>`

## پس از rollback
- [ ] `/health` سبز است
- [ ] گیت ورود < ۲s (Prometheus)
- [ ] لاگ GlitchTip بررسی شود
- [ ] علت در LEDGER ثبت + برای چرخهٔ بعد بازطراحی شود

## تست سناریو (هر ماه)
1. دیپلوی نسخهٔ جدید در staging
2. شبیه‌سازی خطا (kill process)
3. اجرای rollback → تأیید بازگشت
