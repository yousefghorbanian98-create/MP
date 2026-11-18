# راهنمای عملیات — MP

## ۱) Stack و سلامت

Composeها جایگزین هم‌اند، نه دو replica از یک سیستم:

| سرویس | Compose `deploy` | Compose `infra` | یادداشت |
|---|---:|---:|---|
| FastAPI | 8000 (فقط internal) | 8000 (فقط internal) | چهار worker؛ `/health` زنده‌بودن، `/api/v1/health/ready` آمادگی DB و storage rate-limit |
| Studio/Nginx | 127.0.0.1:8080 | پشت Caddy | `deploy` باید پشت reverse-proxy/TLS بیرونی باشد |
| Caddy | — | 80/443 | `infra` به DNS، دامنه و ایمیل واقعی نیاز دارد |
| Valkey | 6379 (internal) | 6379 (internal) | مشترک بین workerها؛ هیچ port روی host منتشر نیست |
| Prometheus | 9090 loopback | 9090 loopback | ruleها evaluate می‌شوند؛ Alertmanager/receiver هنوز نیاز به تنظیم عملیاتی دارد |

Production به `MP_SECRET_KEY`, `MP_BIOMETRIC_KEY`, originهای HTTPS، provider واقعی SMS، پذیرندهٔ live زرین‌پال و Valkey نیاز دارد. نمونهٔ fail-closed: `mp-app/backend/.env.example`; مقادیر واقعی فقط در secret manager یا `.env` با مجوز محدود.

## ۲) Backup و restore

هر دو Compose پس از readiness فوراً backup می‌گیرند، سپس هر ۲۴ ساعت؛ job ناموفق هر ساعت retry می‌شود. منبع باید `/data/mp.db` باشد؛ snapshot SQLite شامل WAL را در volume محلی `mp-backups` و manifest SHA256 می‌نویسد.

اسکریپت در `mp-app/backend/scripts/backup.py` است و job کانتینر از WORKDIR همان مسیر (`/srv/mp/backend`) صدا می‌زند؛ از ریشهٔ مخزن مسیر را کامل بدهید:

```bash
# داخل کانتینر/با WORKDIR = mp-app/backend:
python scripts/backup.py backup --db /data/mp.db --out /backups

# از ریشهٔ مخزن (محیط توسعه):
python mp-app/backend/scripts/backup.py backup --db /path/to/mp.db --out /tmp/mp-backups
```

- هر روز موفقیت job و فضای دیسک/آرشیو را بررسی کنید.
- نسخهٔ رمزگذاری‌شدهٔ backup را خارج از میزبان نگه دارید؛ volume روی همان host به‌تنهایی disaster recovery نیست.
- **تمرین ماهانه روی scratch، بدون نوشتن روی مسیرهای زنده** (M97):

```bash
python mp-app/backend/scripts/backup.py verify /tmp/mp-backups/mp_backup_<stamp>.tar.gz
python mp-app/backend/scripts/backup.py restore <archive>.tar.gz \
  --db /tmp/mp-drill/mp.db --extras-to /tmp/mp-drill
```

`verify` فقط manifest، SHA256 و `PRAGMA integrity_check` را می‌خواند و نسخهٔ Alembic داخل آرشیو را گزارش می‌دهد؛ هیچ فایلی نمی‌نویسد. در `restore` هم `--extras-to` لازم است: بدون آن، فایل‌های الحاقی آرشیو (`modules/updates/registry.json` و `shared/design-tokens.json`) در **مسیرهای اصلی خودشان** بازنویسی می‌شوند — یعنی یک آرشیو کهنه می‌تواند source/برنامهٔ در حال اجرا را به عقب برگرداند. برای restore تولیدی همان مسیرهای اصلی هدف است، برای تمرین هرگز.

سپس DB بازگردانده‌شده را با همان گیت‌های استقرار بسنجید:

```bash
cd mp-app/backend
MP_DATABASE_URL=sqlite:////tmp/mp-drill/mp.db python -m alembic current   # باید head بدهد
MP_DATABASE_URL=sqlite:////tmp/mp-drill/mp.db python -m alembic check     # باید «No new upgrade operations detected» بدهد
```

زمان RTO/RPO و نتیجهٔ هر دو دستور در گزارش incident ثبت می‌شود. این زنجیره روی دیتابیس scratch با تست `mp-app/backend/tests/integration/test_m97_migrations_and_backup.py` آزموده شده است؛ روی محیط واقعی باشگاه هنوز اجرا نشده.

- پیش از restore تولیدی: توقف backend، حفظ نسخهٔ فعلی، تأیید آرشیو/DB مقصد و مجوز مالک. هیچ restore تولیدی خودکار اجرا نمی‌شود.


## ۳) پایش و incident

- Prometheus scrape می‌کند `/api/v1/metrics` و Valkey exporter؛ exposition با `prometheus-client` استاندارد و تجمیع multiprocess است.
- آلارم‌های SLO ورود، backend down، نرخ 5xx و Valkey down در `mp-app/infra/monitoring/alerts.yml` هستند. Prometheus به‌تنهایی پیامک/ایمیل/صفحه‌بندی نمی‌فرستد؛ receiver و test notification عملیاتی‌اند.
- برای readiness: `GET /api/v1/health/ready` باید HTTP 200 و `ready=true` بدهد؛ 503 یعنی DB یا backend محدودسازی نرخ آماده نیست.
- لاگ‌ها JSON در stdout؛ `X-Request-ID` را برای تطبیق درخواست و لاگ نگه دارید و هیچ OTP، token، کلید یا embedding خام را لاگ/تیکت نکنید.
- اگر OTP limit فعال شد، تعداد درخواست‌ها را بررسی کنید؛ **Valkey را با fallback درون‌حافظه‌ای جایگزین نکنید**. در production storage rate limit مشترک است و readiness باید قطع آن را نشان دهد.

## ۴) انتشار و برگشت

- `container.yml` و `deploy.yml` اکنون GHCR push/manual webhook pipeline دارند؛ `container.yml` full-SHA و در tag انتشار version tag می‌سازد (بدون `latest`) و dispatch استقرار فقط از default branch پذیرفته می‌شود. اما secrets/environment reviewers و branch policy، GHCR pull در Dokploy، sync کردن `IMAGE_TAG`/Studio و health endpoint باید اپراتور تنظیم و staging verify کند. این workspace هیچ image push/deploy اجرا نکرده است.
- پیش از release: backup خارج از میزبان، migration scratch، SHA tag قبلی و digest ثبت‌شده، smoke test روی staging و readiness بررسی شوند؛ tag در GHCR mutable است مگر اینکه policy/دسترسی registry خلاف آن را تضمین کند.
- Rollback دستی با tag قبلی است و DB migration را خودکار برنمی‌گرداند؛ backup و سازگاری schema را پیش از اقدام بررسی کنید و تمرین staging را ثبت کنید.
- `infra/ansible/inventory.ini` فقط نمونهٔ کامنت‌شده است؛ host، `restic_repo`, credential و account واقعی باید توسط اپراتور تعریف شوند. IP یا secrets نمونه را در Git وارد نکنید.

## ۵) گام‌های incident

1. ثبت UTC زمان و `X-Request-ID`، بررسی logهای JSON و آلارم‌ها.
2. P1 قطعی API: readiness، resource/disk، DB و Valkey را بررسی کنید؛ قبل از restart، وضعیت DB/backup را حفظ کنید.
3. خرابی SMS: بررسی TLS/credential/provider و نتیجهٔ test محدود؛ SMS توسعه را در production فعال نکنید.
4. رویداد مالی یا دادهٔ بیومتریک: endpointهای audit بررسی شوند و دادهٔ حساس فقط از کانال محدود مجاز دیده شود.
5. ثبت اقدام، نتیجهٔ restore/rollback و follow-up در CHANGELOG و گزارش incident.
