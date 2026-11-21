# FINN Loop — ممیزی `MP-BUILDER-PROMPT-2026-11-21`

> این سند حلقهٔ خودکار اجرای ممیزی است. هر اجرا از همین‌جا شروع می‌کند، نه از حافظهٔ گفتگو.
> شاخه: `arena/da474b65-mp` · PR #23 · مرجع پروتکل: `docs/MuscleParadise/FINN_LOOP.md` (G1–G10).
> بریف کامل: `MP-BUILDER-PROMPT-2026-11-21.md` (در بستهٔ `share/` شاخهٔ Chat2DB).

## ۱. قرارداد خودمختاری

1. **بدون نظارت روتین.** هر WP با `READY` بی‌وقفه اجرا می‌شود. تصمیم محدود، برگشت‌پذیر و درون‌دامنه‌ای با پیش‌فرض امن گرفته و در `DECISIONS.md` ثبت می‌شود.
2. **توقف فقط برای این‌ها:** (الف) تصمیم مالی/حقوقی واقعی که بریف و مستندات پاسخ نمی‌دهند؛ (ب) `BLOCKED` واقعی روی منبعی که در محیط نیست (Docker، Postgres، Prometheus، دستگاه، secrets GitHub). `BLOCKED` باید با شاهد فنی ثبت شود، نه با حدس.
3. **هیچ گیت قرمزی رد نمی‌شود (G2).** تست/لینت/اسکن شکست‌خورده = WP تمام نشده. skip، ignore یا شُل کردن آستانه ممنوع. اصلاح کد/تست، نه گارد.
4. **هر باگ = یک تست رگرسیون (G3).** تست باید پیش از اصلاح قرمز دیده شود. اگر قرمز بودنش دیده نشد، صریحاً در `EXECUTION-LOG.md` ثبت شود.
5. **حداکثر سه تلاش برای یک خطا (G4)**؛ پس از آن `BLOCKED` با شاهد.
6. **ادعا فقط با شاهد.** هر «انجام شد» یک خروجی واقعی دارد: فرمان، exit code، شمارش.
7. **یک کامیت برای هر WP، push فقط به `arena/da474b65-mp`، بدون force.** `mp-app/studio/dist` قبل از کامیت حذف شود.
8. **merge نمی‌شود** تا پایان کار و تأیید مالک.

## ۲. حلقهٔ هر WP (Forge → Inspect → Normalize → Next)

| مرحله | کار | شاهد |
|---|---|---|
| Forge | بازتولید شکست؛ تست قرمز؛ کوچک‌ترین اصلاح | خروجی قرمز |
| Inspect | تست هدف + تست‌های مرتبط + گیت عددی بریف | خروجی سبز و عدد |
| Normalize | `EXECUTION-LOG.md`، `status.json`، `DECISIONS.md`، مستندات؛ `ruff`؛ `build_audit_inventory.py --check` پس از کامیت | خروجی |
| Next | کامیت، push، WP بعدی | `git log -1` |

گیت سلامت پس از هر فاز: `pytest` کامل بک‌اند، `npm run lint` و `tsc` و `vitest` استودیو، `route_guard_gate.py`، `deploy_gate.py`.

## ۳. صف کاری (ترتیب اجرا)

وضعیت: `DONE` = کامیت‌شده با شاهد · `PARTIAL` = کد/تست انجام، بخشی از بریف باز · `READY` = آمادهٔ اجرا · `BLOCKED-ENV` = منبع خارج از محیط · `TODO` = بعد از وابستگی‌ها.

| WP | یافته | وضعیت | کامیت | شاهد / باقی‌مانده |
|---|---|---|---|---|
| 0.1 | — | PARTIAL | `f0fe83b` | خط پایه در `EXECUTION-LOG`؛ `BASELINE.md` هنوز با ۴۹ ردیف ساخته نشده |
| 0.2 | F-12 | TODO | — | ماتریس ۱۶۳×۷ و ۶۰۲ سلول مخالف؛ نیاز به `routes.json` کامل با گاردهای مؤثر |
| 0.3 | F-13 | DONE | `b9e88e5` | pytest کامل ۱۰۹۷ passed |
| 0.4 | F-07 | TODO | — | آستانهٔ هر دایرکتوری (`db` و `scripts` زیر آستانه) |
| 0.5 | F-10 | DONE | `bf1daa1` | eslint ۰/۰ (قبل: ۴۲ خطا + ۵ هشدار) |
| 0.6 | F-24 | PARTIAL | `bf1daa1` | 422 اصلاح؛ هشدار httpx و asyncio باقی |
| 0.7 | — | READY | — | semgrep روی PyPI نصب می‌شود (میزبان مجاز)؛ قاعدهٔ `harness/semgrep-mp.yml` در CI به‌صورت non-blocking |
| 0.8 | A5 | PARTIAL | `40c64f7` | ۴۲/۴۲ پین؛ گیت‌های SBOM/امضا باقی |
| 1.1 | F-01 | PARTIAL | `ccf44ce` | e2e: قبل ۳۰×200، بعد ≥۲۷×429؛ متریک `key_source` باقی |
| 1.2 | F-02 | PARTIAL | `ccf44ce` | BD-3؛ گیت زنده روی استقرار BLOCKED-ENV |
| 1.3 | F-06, A2 | DONE | `fae50c5` | ۳۲ تست مانیتورینگ passed؛ pytest ۱۱۰۴ |
| 1.4 | F-08 | PARTIAL | `d30aed8` | BD-6: bump auth_version؛ قبل ۲۰۰ ⇒ بعد ۴۰۱؛ pytest ۱۱۳۲ passed؛ قاعدهٔ Semgrep باقی (WP 0.7) |
| 1.5 | F-09 | READY | — | نوع `Rial` و strict؛ ۷ محل پولی شناور در استودیو؛ ۲ محل تقسیم پول در بک‌اند |
| 2.1 | F-03 | READY | — | لاگ با `ConsoleRenderer` در پروسهٔ سرویس؛ `QueueHandler` |
| 2.2 | F-04 | READY | — | گیج‌های pool؛ ۵۰۳ به‌جای ۵۰۰ |
| 2.3 | F-18 | READY | — | BD-4: یک ورکر + سقف مستند؛ `gateway.py` sync→async |
| 2.4 | F-05 | READY | — | RBAC پیش‌کامپایل؛ قفل `_enforcer` |
| 2.5 | F-17 | READY | — | ۴ `except: pass` ⇒ لاگ + شمارنده |
| 3.1 | F-25 | READY | — | کف شناسه در `id_guard.py`؛ `PathId` در امضاها |
| 3.2 | F-26 | READY | — | نگاشت `StarletteHTTPException` به پاکت پروژه |
| 3.3 | F-14 | TODO | — | `gateway-return` با شناسهٔ نامعتبر ⇒ 404 (BD-5) |
| 3.4 | F-27 | READY | — | BD-1: 409 `member_profile_required` |
| 3.5 | F-09/F-25 | TODO | — | آزمون قراردادی سراسری در CI |
| 4.1 | F-15 | TODO | — | شکستن `validate_production_configuration` (radon F(47)) |
| 4.2 | F-11 | TODO | — | سه جهش واقعی؛ ≥۸۰٪ |
| 4.3 | F-19 | READY | — | یک لایهٔ داده در استودیو؛ حذف `await import` در onClick |
| 4.4 | F-20/F-23 | READY | — | BD-2: حذف `updateProduct` کلاینت |
| 4.5 | F-21/F-22 | READY | — | الگوی session، `hypothesis` در pyproject، SQL f-string |
| 4.6 | F-16 | READY | — | قاعدهٔ `int` ریال؛ حذف sentinel منفی |
| 4.7 | — | TODO | — | Semgrep blocking، بار پله‌ای، جهش، گیت نهایی |

**باقی‌مانده‌های `BLOCKED-ENV`** (کاربر باید مطلع شود، نه متوقف شود): Docker/Postgres/Valkey برای بار ۲۰۰ کاربر و `pgBackRest`؛ Prometheus/Alertmanager؛ دستگاه واقعی و اسکرین‌شات Flutter؛ امضای APK؛ آزمون ابری.

## ۴. تصمیم‌ها

BD-1 تا BD-5 در `DECISIONS.md` (بخش D-5) با دلیل و نحوهٔ برگرداندن ثبت شده‌اند.

## ۵. قاعدهٔ ادامه برای اجرای بعدی

۱. `git status` و `git log -3`؛ تغییرهای قبلی را حفظ کن.
۲. اولین ردیف `READY` بالاترین اولویت (ترتیب بالا) را بردار؛ وابستگی‌ها را از بریف بخوان.
۳. با «قرمز» شروع کن؛ اصلاح؛ گیت هدف؛ کامیت؛ به‌روزرسانی این جدول و `status.json`.
۴. پایان هر فاز: گیت سلامت کامل.
