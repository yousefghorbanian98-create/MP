# دفترچهٔ شرایط اضطراری (Incident Runbook) — M13

## سطوح
| severity | معنی | واکنش |
|----------|------|--------|
| page | سرویس/گیت قطع یا SLO نقض | فوری — readiness/Prometheus را بررسی و incident lead را مطلع کن |
| warn | تخریب جزئی (5xx، cache یا job) | بررسی در ساعات کاری؛ اثر مشتری را پایش کن |

## SLO اصلی
- **گیت ورود: ۹۹٪ چک‌این‌ها < ۲ ثانیه** (NFR-2) — آلارم `CheckinSLOBreach` با p99 histogram پنج‌دقیقه‌ای.
- Prometheus ruleها را ارزیابی می‌کند، اما Alertmanager/receiver هنوز پیکربندی نشده؛ تا test notification موفق، paging خودکار فرض نشود.

## مسیرها
1. **BackendDown یا readiness 503** → `docker compose ps` و `docker compose logs backend`؛ بررسی DB و Valkey. قبل از image rollback، backup و migration compatibility را طبق `runbooks/rollback.md` بررسی کن. SQLite failover/slave در این استقرار تنظیم نشده است.
2. **CheckinSLOBreach** → readiness/resourceها و نمودار PromQL `histogram_quantile(0.99, sum by (le) (rate(mp_checkin_duration_seconds_bucket[5m])))` را بررسی کن؛ در بحران از پذیرش دستی استفاده و نتیجه را ثبت کن.
3. **ValkeyDown** → backend readiness باید 503 شود و محدودسازی نرخ مشترک نباید به memory downgrade کند؛ storage را بررسی کن و پس از سالم‌شدن، readiness و OTP limits را بازآزمایی کن. Cache غیرحساس ممکن است fallback داخلی داشته باشد، پس stale-data را هم بررسی کن.
4. **رویداد داده/پرداخت** → `audit_log` و شناسهٔ درخواست را بررسی کن؛ OTP/token/secret/embedding خام را در لاگ یا تیکت قرار نده.
5. **SMS یا پرداخت** → credential/TLS/provider و gateway status را از پنل مجاز بررسی کن؛ درگاه mock و پاسخ OTP توسعه در production ممنوع‌اند.

## اطلاع‌رسانی
- هیچ مقصد public از پیش تنظیم‌شده نیست. اگر لازم است، healthcheck اختیاری فقط با `MP_NTFY_URL` و `MP_NTFY_TOPIC` به ntfy self-hosted اپراتور می‌فرستد؛ آدرس و topic عمومی را در Compose پیش‌فرض نگذار.
- پس از هر incident page، جلسهٔ بازبینی و ثبت timeline، علت، اقدام و پیشگیری را در سامانهٔ incident سازمان انجام بده.
