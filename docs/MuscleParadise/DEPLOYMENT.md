# راهنمای استقرار (M32) — Docker + GitHub، مرحله‌به‌مرحله

> وضعیت تست: فرمان‌های داخل ایمیج‌ها (pip install، npm run build، uvicorn، alembic) در سندباکس تأیید شد؛
> خودِ `docker build` در سندباکس اجرا نشده (Docker نصب‌نشدنی — D-003) و باید روی سرور/CI اجرا شود.

## الف) در GitHub (یک‌بار، ~۱۰ دقیقه)

### ۱) ریپو و شاخه
- مخزن `yousefghorbanian98-create/MP` شاخهٔ `arena/a0408b29-mp` همهٔ کد است.
- (اختیاری) برای انتشار پایدار: از همین شاخه PR به `main` بدهید تا CI سبز روی main هم اجرا شود.

### ۲) Actions را روشن کنید
- صفحهٔ ریپو ← تب **Actions** ← «Enable workflows» (اگر قبلاً روشن نشده).
- سه workflow آماده است:
  | Workflow | چه می‌کند | چگونه اجرا شود |
  |---|---|---|
  | `mp-ci` | لینت + تست + اسکن | خودکار با هر push |
  | `mp-apk` | ساخت **APK اندروید** + SHA256 | تگ `v*` یا Run workflow (دستی) |
  | `mp-container` | ساخت ایمیج Docker + push به **GHCR** | Run workflow (دستی) یا تگ `v*` |

### ۳) ساخت ایمیج‌های Docker (mp-container)
1. تب Actions ← **mp-container** ← «Run workflow».
2. پس از موفقیت، ایمیج‌ها در **Packages** ریپو (ghcr.io) دیده می‌شوند:
   `ghcr.io/<owner>/mp-backend:latest` و `ghcr.io/<owner>/mp-studio:latest`.
3. در Packages ← Package settings ← «Visibility» در صورت نیاز private بماند (پیش‌فرض).

### ۴) ساخت APK (mp-apk)
1. Actions ← **mp-apk** ← Run workflow (یا push تگ: `git tag v0.2.0 && git push origin v0.2.0`).
2. در انتهای اجرا ← Artifacts ← **muscleparadise-apk** ← دانلود zip (APK + فایل sha256).
3. روی گوشی: نصب APK (یا دلتا روی نسخهٔ قبلی — بدون حذف‌نصب).

## ب) روی سرور محلی باشگاه (لینوکس، ~۲۰ دقیقه)

### ۱) نصب Docker
```bash
curl -fsSL https://get.docker.com | sh      # یا طبق مستند توزیع خودتان
sudo usermod -aG docker $USER               # ورود دوباره
```

### ۲) دریافت ایمیج‌ها
```bash
echo <TOKEN> | docker login ghcr.io -u <github-user> --password-stdin
docker pull ghcr.io/<owner>/mp-backend:latest
docker pull ghcr.io/<owner>/mp-studio:latest
```
*(TOKEN: GitHub ← Settings ← Developer settings ← PAT با scope `read:packages`)*

### ۳) فایل‌های اجرا
- پوشهٔ `mp-app/deploy/` را روی سرور بگذارید (فقط `docker-compose.yml` + یک فایل `.env`).

### ۴) فایل `.env` کنار docker-compose.yml
```bash
MP_JWT_SECRET=$(openssl rand -hex 32)
MP_CORS_ORIGINS=http://IP-یا-دامنه-سرور:8080
# پیامک (اختیاری — بدون آن حالت dev):
# MP_SMS_PROVIDER=webmagfa
# MP_SMS_API_URL=https://...
# MP_SMS_USERNAME=... MP_SMS_PASSWORD=... MP_SMS_ORIGINATOR=...
```

### ۵) اجرا
```bash
docker compose up -d
curl http://localhost:8080/api/v1/health     # ← {"status":"ok"} انتظار می‌رود
```
- استودیو (ادمین): `http://IP-سرور:8080`
- داده: ولوم `mp-data` (پایدار — حذف کانتینر داده را نمی‌برد).
- بکاپ روزانه: سرویس `backup` در همان compose (به ولوم `mp-backups`).

### ۶) به‌روزرسانی (دلتا — بدون حذف‌نصب)
```bash
docker compose pull && docker compose up -d
# بک‌اند خودش alembic upgrade head را هنگام بالا آمدن اجرا می‌کند
```

## ج) چک‌لیست بعد از استقرار
- [ ] `/api/v1/health` سبز
- [ ] OTP با پیامک واقعی (یا dev فقط برای آزمایش)
- [ ] `GET /face/privacy-notice` و `GET /face/deep-status` پاسخ می‌دهند
- [ ] بکاپ: فایل tar.gz در `/var/lib/docker/volumes/mp-backups` ساخته می‌شود
- [ ] روی گوشی: APK نصب ← ورود با OTP ← خانه/برنامه/گزارش‌ها نمایش داده می‌شود
- [ ] ساعت سرور و منطقهٔ زمانی درست (تقویم جلالی)

## پرسش‌های رایج
- **چرا پورت 8080؟** برای استودیو؛ API فقط داخل شبکهٔ compose است (expose بدون publish) — امن‌تر.
- **PostgreSQL؟** مسیر پیش‌فرض SQLite (تست‌شده، تک‌باشگاهی). برای مقیاس بزرگ‌تر: سرویس postgres به compose افزوده و `MP_DATABASE_URL=postgresql://...` — قبل از تولید حتماً تست شود.
- **HTTPS؟** پشت یک reverse-proxy (Nginx/Caddy) با گواهی Let's Encrypt — پورت 8080 را داخلی کنید و فقط 443 باز باشد.
