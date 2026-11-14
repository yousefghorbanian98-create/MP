# Runbook — Provisioning سرور باشگاه (M11)

> بازتولیدپذیری: از یک سرور خالی تا استک کامل با یک playbook.

## پیش‌نیاز
- سرور: ۴ هسته / ۸ گیگ (شروع)، اوبونتو ۲۲.۰۴+، دسترسی SSH
- دامنه + DNS (برای TLS خودکار Caddy)

## مراحل
1. **Ansible**: `ansible-playbook -i inventory.ini playbook.yml` (نصب docker/ffmpeg/restic + بالا آوردن استک)
2. **متغیرهای محیطی**: فایل `.env` با `MP_SECRET_KEY`، `MP_BIOMETRIC_KEY`، `MP_TLS_EMAIL` (از `.env.example`)
3. **اعتبارسنجی**:
   - `curl https://<domain>/health` → `{"status":"ok"}`
   - `docker compose ps` → همه healthy
   - تست گیت ورود: `curl` به `/api/v1/face/checkin` < ۲s
4. **بکاپ**: cron شبانهٔ restic (در playbook) — **هر ماه یک بازیابی واقعی تست شود** (بکاپ تست‌نشده = بکاپ نیست)

## استک
| سرویس | نقش | پورت |
|-------|------|------|
| caddy | ریورس‌پراکسی + TLS + هدرها | 80/443 |
| backend | FastAPI | 8751 (internal) |
| valkey | کش (لایهٔ ۱۲) | internal |
| ollama | LLM محلی (فقط توضیح — G8) | 11434 (internal) |

## فایل‌های استاتیک
ویدیوهای حرکات: `bash scripts/compress-media.sh in/ out/` (ffmpeg H.264) → در `/srv/media` توسط Caddy سرو می‌شود.
