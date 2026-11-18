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

## مهاجرت schema و drift (M97)

دو مسیر provisioning در این پروژه وجود دارد و **باید** همان schema را بسازند:

| مسیر | کجا استفاده می‌شود | چه‌طور |
|---|---|---|
| Alembic | production/کانتینر | `CMD` ایمیج قبل از uvicorn، `alembic upgrade head` را اجرا می‌کند |
| `Base.metadata.create_all` | تست و محیط توسعه | `mp-app/backend/db/base.py: init_db` |

- مرجعِ ساخت، migrationها هستند؛ برای هر تغییر schema یک revision تازه با `upgrade()` و `downgrade()` نوشته می‌شود و `downgrade` توخالی (فقط `pass`) مجاز نیست.
- قبل از ثبت: روی DB آزمایشی هر سه حالت سنجیده شود — `upgrade head`، `downgrade base`، دوباره `upgrade head`، و `alembic check` که باید «No new upgrade operations detected» بدهد.
- یک DB قدیمی که فقط با `create_all` ساخته شده، با `alembic stamp head` baseline می‌شود؛ پس از آن `alembic check` باید drift صفر بدهد. هیچ‌گاه schema یک DB موجود را با `ALTER TABLE` دستی عوض نکنید.
- تاریخچه باید **یک head** داشته باشد؛ اگر دو شاخه ساخته شد، یک merge revision اضافه شود (الگو: `f9b0c1d2e3f4_merge_heads_unique_gateway_authority.py`).

گیت‌های خودکار همین موارد در `mp-app/backend/tests/integration/test_m97_migrations_and_backup.py` (تاریخچه، parity دو مسیر، baseline و مانور backup/restore) و `test_m47_migration_drift.py` (upgrade/downgrade و `alembic check`) هستند. اجرای محلی:

```bash
cd mp-app/backend && python -m pytest -q \
  tests/integration/test_m97_migrations_and_backup.py \
  tests/integration/test_m47_migration_drift.py
```

## استک
| سرویس | نقش | پورت |
|-------|------|------|
| caddy | ریورس‌پراکسی + TLS + هدرها | 80/443 |
| backend | FastAPI | 8000 (internal) |
| valkey | کش (لایهٔ ۱۲) | internal |
| ollama | LLM محلی (فقط توضیح — G8) | 11434 (internal) |

## فایل‌های استاتیک
ویدیوهای حرکات: `bash scripts/compress-media.sh in/ out/` (ffmpeg H.264) → در `/srv/media` توسط Caddy سرو می‌شود.
