# استقرار Muscle Paradise — تنظیمات تولید و پیش‌نیازها

## دو Compose مستقل

این دو stack را **جایگزین یکدیگر** بدانید و هم‌زمان روی یک دیتابیس اجرا نکنید:

- `mp-app/deploy/docker-compose.yml`: Studio/Nginx فقط روی `127.0.0.1:8080` (قابل تغییر با `STUDIO_PORT`)؛ API فقط داخل شبکه است و reverse proxy/TLS بیرونی لازم دارد.
- `mp-app/infra/docker-compose.yml`: Studio/Nginx پشت Caddy برای TLS روی 80/443، backend فقط روی شبکهٔ داخلی پورت 8000، Valkey و پایش Prometheus.

هر دو Compose برای محیط production هستند و بدون secret/providerهای واقعی fail-closed می‌شوند؛ Compose جای secret manager یا مدیریت دسترسی میزبان را نمی‌گیرد.

## آماده‌سازی فایل محیطی

از دایرکتوری Compose فایل محلی بسازید؛ `.env` واقعی را commit نکنید و مجوزش را محدود کنید:

```bash
cd mp-app/deploy
umask 077
cp ../backend/.env.example .env
# سپس فایل را با مقادیر واقعی و secret manager مورد استفادهٔ سازمان تکمیل کنید.
```

برای stack مبتنی بر Caddy فایل محیطی جدا بسازید:

```bash
cd ../infra
umask 077
cp ../backend/.env.example .env
# مقادیر secret/providerها را تکمیل کنید؛ سپس دامنه و ایمیل واقعی را نیز اضافه کنید.
```

کلیدها باید جدا و تصادفی باشند؛ دستورهای ساخت مقدار در فایل نمونه توضیح داده شده‌اند. این موارد برای **هر دو** stack لازم‌اند:

| متغیر | الزام تولید |
|---|---|
| `IMAGE_OWNER` | نام owner/repository در GHCR، lowercase و بدون `ghcr.io/`؛ حساب/توکن pull را روی host به‌صورت امن تنظیم کنید |
| `IMAGE_TAG` | ترجیحاً SHA کامل ۴۰ کاراکتری از build بررسی‌شده، نه `latest`؛ SHA/version tag به‌تنهایی immutable نیست مگر نوشتن/بازنویسی tag در GHCR محدود شود؛ digest و دسترسی registry را جداگانه بررسی کنید |
| `MP_SECRET_KEY` | دست‌کم ۳۲ بایت تصادفی؛ نه مقدار نمونه یا پیش‌فرض توسعه |
| `MP_BIOMETRIC_KEY` | Base64 از دقیقاً ۳۲ بایت تصادفی، مجزا از کلید JWT |
| `MP_CORS_ORIGINS` | فهرست originهای واقعی HTTPS، با کاما جداشده؛ نه localhost و نه `*` |
| `MP_SMS_PROVIDER` | `webmagfa` یا `kavenegar`، به‌همراه URL HTTPS و credentialهای همان provider؛ `dev` مجاز نیست |
| `MP_PAYMENT_GATEWAY` | `zarinpal`، شناسهٔ پذیرندهٔ واقعی و `MP_PAYMENT_SANDBOX=false` |
| `MP_TRUSTED_PROXIES` | **الزامی در production** — IP یا CIDR پروکسی Caddy/nginx، کاماجدا (مثلاً `172.18.0.0/16`). uvicorn فقط به همین فهرست `X-Forwarded-For` می‌دهد (`scripts/uvicorn_proxy_flags.sh`)؛ خالی یعنی هیچ هدری پذیرفته نمی‌شود (`--no-proxy-headers`). هرگز `*` ننویسید (WP 1.1 / F-01). |
| `MP_METRICS_TOKEN` | **الزامی در هر دو Compose** — توکن Bearer قوی و تصادفی؛ همان مقدار باید به backend و Prometheus برسد. Compose در صورت خالی/تنظیم‌نشدن fail-closed است؛ مقدار واقعی فقط در secret manager یا `.env` محلی. |
| `MP_ENVIRONMENT` | **صریح** لازم است؛ بدون آن اپ بالا نمی‌آید (WP 1.2 / F-02). مقدار: `production` یا `development`. |
| `MP_ALLOW_DEV_OTP_ECHO` | پیش‌فرض `false`. فقط در `development` و با `true` کد OTP در پاسخ می‌آید؛ در production رد می‌شود. |
| `MP_REQUIRE_WORKER` | `true` در استقراری که worker دارد؛ بدون heartbeat تازهٔ outbox، `/api/v1/health/ready` با ۵۰۳ پاسخ می‌دهد (QF-27) |

در هر دو Compose، `MP_VALKEY_URL` داخل شبکه به سرویس Valkey اشاره می‌کند؛ backend نباید از `localhost` استفاده کند. دقت کنید secretها، API key پیامک، شناسهٔ پذیرنده و دامنه را در گزارش/چت/لاگ چاپ نکنید.

برای stack مبتنی بر Caddy (`infra`)، علاوه بر آن:

```dotenv
PUBLIC_DOMAIN=دامنه-واقعی-شما
TLS_EMAIL=ایمیل-عملیاتی-شما
```

Caddy برای همان دامنه TLS می‌گیرد. DNS رکوردهای دامنه باید به سرور اشاره کنند و پورت‌های 80 و 443 از بیرون قابل‌دسترسی باشند. `MP_CORS_ORIGINS` باید origin مرورگری‌ای باشد که واقعاً از همان deployment سرو می‌شود.

برای stack `deploy`، پورت 8080 را مستقیم روی اینترنت منتشر نکنید؛ reverse proxy بیرونی باید TLS داشته باشد و درخواست `/api/` را از طریق Nginx به backend بفرستد. Nginx آدرس client را خودش در `X-Forwarded-For` می‌نویسد تا زنجیرهٔ ارسالی کاربر مبنای محدودیت نرخ نشود.

## اجرا و راستی‌آزمایی

```bash
# IMAGE_OWNER و IMAGE_TAG را قبل از اجرا در .env با release/tag بررسی‌شده پر کنید.
docker compose up -d --build
docker compose ps
curl -fsS http://localhost:8080/api/v1/health/ready  # stack deploy، پشت TLS بیرونی
```

اگر روی میزبان فقط imageهای GHCR اجرا می‌شوند، ابتدا login را از secret manager تأمین کنید و `docker compose pull && docker compose up -d` را اجرا کنید؛ از `latest` برای rollout/rollback استفاده نکنید.

در stack `infra`، `/health` فقط liveness را می‌سنجد؛ readiness عملیاتی را از `https://<دامنه-واقعی>/api/v1/health/ready` بررسی کنید و انتظار HTTP 200 با `ready: true` داشته باشید. این بررسی علاوه بر API، دیتابیس و storage مشترک نرخ‌محدودسازی (Valkey) را می‌سنجد؛ Prometheus UI روی `127.0.0.1:9090` فقط از خود میزبان قابل‌دسترسی است. قواعد alert بارگذاری می‌شوند، اما **ارسال اعلان alert** نیازمند پیکربندی جداگانهٔ Alertmanager/receiver است.

پیش از ورود دادهٔ واقعی:

- [ ] health و readiness سبز باشند و `/api/v1/metrics` با توکن `MP_METRICS_TOKEN` در Prometheus دیده شود (بدون توکن ۴۰۱، و از مسیر عمومی ۴۰۴).
- [ ] OTP با provider واقعی در sandbox/provider-approved test انجام شود؛ پاسخ OTP توسعه در production غیرفعال است.
- [ ] درگاه زنده فقط پس از تأیید پذیرنده/کسب‌وکار؛ کد/Compose موفقیت درگاه واقعی را اثبات نمی‌کند.
- [ ] عضویت/مالکیت، گردش کیف‌پول و دسترسی اعضا روی دادهٔ مصنوعی بازبینی شوند.
- [ ] archive اولیه در `mp-backups` ساخته شود؛ restore drill انجام و نسخهٔ رمزگذاری‌شده خارج از همان میزبان نگهداری شود.
- [ ] TLS، DNS، firewall، ساعت سیستم، retention، مانیتورینگ و گیرندهٔ alert توسط اپراتور تأیید شوند.

Backup container در هر دو Compose پس از readiness فوراً یک archive می‌سازد و سپس روزانه از `/data/mp.db` snapshot سازگار SQLite (با WAL) می‌گیرد؛ در خطا هر ساعت retry می‌کند. manifest شامل SHA256 است و نسخهٔ backend این image، registry و design tokens را نیز کنار DB می‌بندد. archive در volume محلی `mp-backups` است؛ این volume به‌تنهایی backup خارج از میزبان یا disaster recovery نیست؛ replication/نسخهٔ offsite و restore ماهانه الزام عملیاتی‌اند.

## انتشار و عملیات بیرونی

- `.github/workflows/container.yml` با tag `v*` یا dispatch به GHCR، full-SHA tag و در release tag معتبر، version tag را push می‌کند و `latest` نمی‌سازد؛ `.github/workflows/deploy.yml` اکنون **فقط دستی** است، SHA-tagged backend/Studio می‌سازد و به Dokploy webhook می‌زند. برای هر GitHub environment (`staging`, `production`) باید operator secrets `DOKPLOY_WEBHOOK` و `APP_URL`، required reviewers/branch policy و دسترسی pull به GHCR را تنظیم کند. workflow پیش از build هم dispatch از default branch مخزن را الزام می‌کند؛ همان branch را در policy محیط‌ها مجاز کنید.
- Dokploy باید `IMAGE_OWNER` و `IMAGE_TAG` را برای همان build بررسی‌شده تنظیم و image Studio هم‌نسخه را مصرف کند؛ webhook موجود image backend را می‌فرستد، پس wiring دقیق Dokploy/frontend باید در staging آزموده شود. workflow و GHCR این workspace سیاست منع بازنویسی tag یا pin کردن digest را اعمال نمی‌کنند؛ تا وقتی اپراتور این کنترل را جداگانه تأیید نکرده، SHA tag را ذاتاً immutable فرض نکنید. این workspace هیچ deploy/push واقعی انجام نداده است.
- rollback workflow دستی است و SHA/version tag قبلی را صریح می‌خواهد؛ فایل `.last-good-image` خودکار نوشته نمی‌شود. Rollback image به‌تنهایی migration دیتابیس را برنمی‌گرداند؛ پیش از اقدام backup، سازگاری schema و restore plan را بررسی و روی staging تمرین کنید.
- `mp-app/infra/ansible/inventory.ini` فقط host نمونهٔ کامنت‌شده دارد. اپراتور باید inventory واقعی، حساب محدود، کلید SSH، `restic_repo`/دسترسی backup و `community.docker` را تأمین و بررسی کند؛ آدرس ساختگی اضافه نکنید.
- هیچ مدل Ollama/چهره‌ای را صرفاً به‌دلیل آزادبودن runtime وارد نکنید: مجوز وزن‌ها، دادهٔ آموزش و مجوز تجاری باید برای همان مدل جداگانه تأیید شود.
