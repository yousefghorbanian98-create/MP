# Runbook — Provisioning سرور باشگاه (M11)

> بازتولیدپذیری: از یک سرور خالی تا استک کامل با یک playbook.

## پیش‌نیاز
- سرور: ۴ هسته / ۸ گیگ (شروع)، اوبونتو ۲۲.۰۴+، دسترسی SSH
- دامنه + DNS (برای TLS خودکار Caddy)

## مراحل
1. **موارد اپراتوری پیش از provision**: از `.env.example` فایل `.env` بسازید و مقادیر را در password manager تولید و نگهداری کنید. مقدارهای `MP_SECRET_KEY` و `MP_BIOMETRIC_KEY` باید کلیدهای جداگانه و معتبر باشند؛ برای `MP_CORS_ORIGINS` فقط originهای HTTPS موردنیاز را ثبت کنید. `IMAGE_OWNER` و `IMAGE_TAG` را روی مالک GHCR و نسخهٔ SHA منتشرشده تنظیم کنید. `PUBLIC_DOMAIN` و `TLS_EMAIL` باید در `.env` stack مربوط به `infra` با DNS و ایمیل عملیاتی واقعی تطبیق داشته باشند. Ansible inventory، حساب SSH محدود، `restic_repo` و credential backup خارج از Git تنظیم شوند.
2. **بررسی سازگاری استقرار**: deployment جاری روی GHCR images و متغیرهای موردنیاز `IMAGE_OWNER`/`IMAGE_TAG` استوار است. playbook فعلی فقط Compose و Caddyfile را کپی می‌کند و `.env`، inventory، `restic_repo` یا credential را تولید/کپی نمی‌کند؛ deployment خودکار GitHub Actions نیز جایگزین Ansible نیست. پیش از اجرا Compose نهایی را با `.env` واقعی رندر و بررسی کنید؛ workflow استقرار تا زمان اجرای اعتبارسنجی و اتصال Dokploy/GHCR برای محیط هدف عملیاتی محسوب نمی‌شود.
3. **Ansible / Docker Compose**: `ansible-playbook -i inventory.ini playbook.yml` فقط پس از تأمین متغیرهای فوق و بررسی تغییرات playbook اجرا شود. این دستور سرویس‌های موجود را مستقر می‌کند؛ در محیط آزمون غیرتولیدی ابتدا imageها را pull کرده و readiness را بررسی کنید. Docker/Ansible در این workspace اجرا نشده‌اند.
4. **اعتبارسنجی**:
   - `curl https://<domain>/api/v1/health/ready` باید HTTP 200 و `ready: true` برگرداند؛ endpoint `/health` مسیر readiness جاری نیست.
   - `docker compose ps` باید سرویس‌ها را طبق healthcheckهایشان healthy نشان دهد.
   - یک flow چک‌این آزمون‌شده را با حساب/دادهٔ آزمایشی اجرا کنید؛ از درخواست ساختگی به endpoint واقعی چهره یا پرداخت استفاده نکنید.
5. **بکاپ**: استک Compose دارای سرویس backup دوره‌ای به `mp-backups` محلی است. job restic این playbook، اگر با repo/credential واقعی پیکربندی شود، بکاپ ثانویهٔ `/opt/muscle-paradise/data` می‌گیرد؛ از دسترسی repo و نگهداری خارج از سرور اطمینان حاصل کنید. **هر ماه بازیابی واقعی را در محیط جداگانه تمرین کنید**؛ بکاپ اجرا/بازیابی نشده اعتبارسنجی نشده است.

## استک
| سرویس | نقش | پورت |
|-------|------|------|
| caddy | ریورس‌پراکسی + TLS + هدرها | 80/443 |
| backend | FastAPI | 8000 (internal) |
| valkey | کش (لایهٔ ۱۲) | internal |
| ollama | LLM محلی (فقط توضیح — G8) | 11434 (internal) |

## فایل‌های استاتیک
ویدیوهای حرکات: `bash scripts/compress-media.sh in/ out/` (ffmpeg H.264) → در `/srv/media` توسط Caddy سرو می‌شود.
