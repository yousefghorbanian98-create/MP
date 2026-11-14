# دفترچهٔ شرایط اضطراری (Incident Runbook) — M13

## سطوح
| severity | معنی | واکنش |
|----------|------|--------|
| page | سرویس/گیت قطع یا SLO نقض | فوری — healthcheck → ntfy → تیم |
| warn | تخریب جزئی (5xx، کش) | بررسی در ساعات کاری |

## SLO اصلی
- **گیت ورود: ۹۹٪ چک‌این‌ها < ۲ ثانیه** (NFR-2) — آلارم `CheckinSLOBreach`

## مسیرها
1. **بک‌اند قطع (`BackendDown`)** → `docker compose ps` → لاگ `docker compose logs backend` → بازگردانی نسخهٔ قبل (runbook/rollback.md) → اگر DB مقصر است failover اسلاو
2. **SLO گیت (`CheckinSLOBreach`)** → بررسی بار (PromQL `rate(mp_checkin_duration_seconds_count)`) → اسکیل افقی → در حالت بحران، ورود دستی پذیرش (کارت عضویت)
3. **Valkey قطع (`ValkeyDown`)** → کش fallback می‌شود (NFR-6) — عملکرد افت می‌کند ولی سرویس بالا است؛ `docker compose restart valkey`
4. **داده‌ی بد / پرداخت ناموفق** → از `audit_log` (M09) ریشه را بگیر؛ `payment_failed` را با کارت و سند مطابقت بده

## اطلاع‌رسانی
- ntfy: `https://ntfy.sh/<MP_NTFY_TOPIC>` (اسکریپت `healthcheck.sh`)
- جلسهٔ بازبینی پس از هر page: «چه شد؟ چرا؟ چه چیزی مانع تکرار است؟» → ثبت در `.finn/state/REGRESSIONS.md`
