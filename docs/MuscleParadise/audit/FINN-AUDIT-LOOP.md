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
| 0.1 | — | DONE | همین commit (WP 0.1) | `BASELINE.md §ز`: ۴۹ ردیف؛ ۴۰ `MEASURED-BY-YOU`، ۹ `DEFERRED(D‑n)` (D‑1…D‑4)؛ pytest `1191 passed/2 skipped/exit 0`؛ AD‑9 |
| 0.2 | F-12 | BLOCKED | WP 0.2 commit (see EXECUTION-LOG) | ۱٬۱۴۱ سلول زنده: ارزیاب سه‌ارزشی ۰ ناهمخوانی؛ گیت باینری کیت قرمز (۵۹۲ drift؛ ۶۹ سلول شرطی) — نیازمند تصمیم مالک، AD‑10 |
| 0.3 | F-13 | DONE | `b9e88e5` | pytest کامل ۱۰۹۷ passed |
| 0.4 | F-07 | DONE | (این کامیت، WP 0.4) | پوشش per-directory با همهٔ آستانه‌ها سبز: modules 92.33≥90، app 96.62≥92، api 93.69≥90، engine 97.24≥95، security 96.61≥95، db 98.97≥80، jobs 84.55≥80، cache 76.60≥75، scripts 65.85≥60؛ XML در CI artifact؛ ۱۲۴۶ passed/۲ skipped؛ AD‑11 |
| 0.5 | F-10 | DONE | `bf1daa1` | eslint ۰/۰ (قبل: ۴۲ خطا + ۵ هشدار) |
| 0.6 | F-24 | DONE | (این کامیت) | ثابت منسوخ `HTTP_422_UNPROCESSABLE_ENTITY` حذف شد (AST: ۰ مورد در app/scripts)؛ هشدار asyncio با `asyncio_default_fixture_loop_scope` بسته شد؛ شمارش ۱۴۱ مسیر/۱۶۳ عملیات از OpenAPI و پیمایشگر یکی است؛ بار و import اپ بدون StarletteDeprecationWarning. باقی‌مانده (فقط تست): هشدار httpx در `starlette.testclient` — نیازمند وابستگی `httpx2` (تصمیم جدا) |
| 0.7 | — | PARTIAL | (این کامیت) | قاعدهٔ کیت به `.semgrep/mp-harness-rules.yml` (sha256 `d58146b4…`) و CI به‌صورت «غیرمسدودکننده» (`continue-on-error`) اضافه شد. پایه روی `mp-app`: ۵ یافته (۰ silent-except-pass)، exit 0. گیت صفر یافته در پایان فاز ۴ باز است؛ مسدودکننده‌شدن در فاز ۴ |
| 0.9 | الحاقیهٔ A1 | DONE (گام ۱–۵) | — | پیکربندی `5d820a0`؛ ERA001 `e335653`؛ گیت `d4c0f3e`؛ رفع ایمن ۴۵ `9868a11`؛ CI+پین `07f096d`؛ 430→419 (base PASS)؛ pytest 1132/0 exit 0 |
| 0.8 | A5 | DONE | (این commit) | گیت کیت ۴۲/۴۲ — اندازه‌گیری: ۴۳ خط `uses:` در ۷ فایل workflow، **۴۳/۴۳ پین به SHA** (۰ تگ‌محور)؛ هر ۷ SHA یکتا با `gh api repos/…/commits/<sha>` در مخزن upstream یافت شد. باقی‌مانده A5 (SBOM/امضا) خارج از گیت این WP |
| 1.1 | F-01 | PARTIAL | `ccf44ce` | e2e: قبل ۳۰×200، بعد ≥۲۷×429؛ متریک `key_source` باقی |
| 1.2 | F-02 | PARTIAL | `ccf44ce` | BD-3؛ گیت زنده روی استقرار BLOCKED-ENV |
| 1.3 | F-06, A2 | DONE | `fae50c5` | ۳۲ تست مانیتورینگ passed؛ pytest ۱۱۰۴ |
| 1.4 | F-08 | PARTIAL | `d30aed8` | BD-6: bump auth_version؛ قبل ۲۰۰ ⇒ بعد ۴۰۱؛ pytest ۱۱۳۲ passed؛ قاعدهٔ Semgrep باقی (WP 0.7) |
| 1.5 | F-09 | DONE | (این کامیت) | red: ۲۳ ناموفق ⇒ green: ۳۳ تست بک‌اند + ۱۵ استودیو؛ گیت after-wp15 PASS؛ pytest ۱۱۸۴/۲/۰؛ AD‑7 |
| 2.1 | F-03 | DONE | e57a992 (B1، D‑13 C1–C5؛ C4/C5 باز) | لاگ با `ConsoleRenderer` در پروسهٔ سرویس؛ `QueueHandler` | |
| 2.2 | F-04 | DONE | b9ce7be (B1، D‑13 C6–C11؛ C9/C10 باز، C11 ادعا نشده) | گیج‌های pool؛ ۵۰۳ به‌جای ۵۰۰ | |
| 2.3 | F-18 | DONE | f852675 (WEB_CONCURRENCY=1، بودجه در OPS-RUNBOOK؛ گسترش validate = TODO، D‑14) | BD-4: یک ورکر + سقف مستند؛ `gateway.py` sync→async | |
| 2.4 | F-05 | DONE | (این کامیت) | red: `tests/regression/test_wp24_rbac_decision_cache.py` (۵۰ ارزیابی casbin برای یک درخواست تکراری؛ ۱۰۰۰ ارزیابی برای ۱۰۰۰ شناسهٔ مختلف؛ کش و متریک نبود)؛ اصلاح: `security/rbac.py` کش محدود LRU با نرمال‌سازی شناسه، `get_enforcer` با قفل، `mp_rbac_decisions_total`/`mp_rbac_errors_total`؛ بار کیت (۸۰×۴۰۰، ۳۲٬۰۰۰ فراخوانی): قبل `SystemError` ۱، p50 ۱٫۰۱۶ ms ⇒ بعد ۰، p50 ۰٫۰۰۶ ms (`evidence/after/wp24/`)؛ AD‑19 |
| 2.5 | F-17 | DONE | `a9146c7` | کیت: semgrep `mp-silent-except-pass` = 0؛ نام شمارنده‌ها طبق کیت (`mp_metrics_scrape_errors_total`، `mp_dast_errors_total`)؛ `/health/ready` بازتاب می‌دهد؛ red 6 تست ⇒ green؛ pytest کامل `1254 passed, 2 skipped, rc=0`. یادداشت: گیت semgrep پیش از تغییر هم ۰ بود؛ تست‌های قرمز شکاف واقعی (نام/بازتاب) را ثبت می‌کنند |
| 2.6 | F-29 | DONE | (این کامیت) | red: ۶ تست exc_info ناموفق ⇒ green: ۱۴ تست؛ pytest ۱۱۴۶/۲/۰؛ AD‑6 (متن استثنا پنهان) |
| 3.1 | F-25 | DONE | (این کامیت) | گیت: `unexpected_2xx_on_bad_id` ۴۸ ⇒ ۰ (۸۷۲ سلول)؛ `id_guard_rejections` ۷۰ ⇒ ۳۳۸ (۴×۵۷ مسیر پارامتری برآورده)؛ بار `plain-dev 10 40` بدون رگرسیون (نسبت‌ها در `evidence/after/wp31-load-ratios.json`)؛ red: `test_wp31_id_floor.py` (۲۴۸/۲۴۸ ناموفق) ⇒ ۵ سبز؛ pytest کامل `1262 passed, 2 skipped, rc=0` |
| 3.2 | F-26 | DONE | (این کامیت) | گیت کیت: `fastapi_default_detail` ۷۰ ⇒ ۰ روی ۸۷۲ سلول (`evidence/after/wp32/summary.json`)؛ اصلاح: پیام خاص `HTTPException` برنامه حفظ شد (red: `test_wp32_detail_preserved.py`)؛ pytest کامل `1257 passed, 2 skipped, rc=0` |
| 3.3 | F-14 | DONE | 9024f44 (پرداخت ناموجود ⇒ 404؛ D‑15) | `gateway-return` با شناسهٔ نامعتبر ⇒ 404 (BD-5) | |
| 3.4 | F-27 | DONE | (این کامیت) | red: `test_wp34_member_profile_required.py` (`shop_online_closed`→۴۰۴ به‌جای ۴۰۹)؛ اصلاح: `_own_member` ⇒ `ConflictError(code=member_profile_required)` ۴۰۹؛ گیت ایستا `check_shop_purchase_guard` در `deploy_gate.py` (۱۵ بررسی، ۰ مشکل)؛ pytest کامل `1268 passed, 2 skipped, rc=0`؛ سفارش به‌نیابت: AD‑17 |
| 3.5 | F-09/F-25 | TODO | — | آزمون قراردادی سراسری در CI |
| 3.6 | F-28 | DONE | (این کامیت) | red: ۳ تست (سن، اسکن، TZ) ناموفق روی کد قبل ⇒ green: ۵ تست؛ گیت after-wp36 PASS؛ pytest ۱۱۵۱/۲/۰؛ AD‑1 |
| 4.1 | F-15 | TODO | — | شکستن `validate_production_configuration` (radon F(47)) |
| 4.2 | F-11 | TODO | — | سه جهش واقعی؛ ≥۸۰٪ |
| 4.3 | F-19 | DONE | cf33ad8 (حذف await import؛ یک‌لایه‌سازی سه API = TODO، D‑14) | یک لایهٔ داده در استودیو؛ حذف `await import` در onClick | |
| 4.4 | F-20/F-23 | DONE | cf33ad8 (updateProduct حذف؛ getToken unexport در این بسته: ‏ببینید EXECUTION-LOG) | BD-2: حذف `updateProduct` کلاینت | |
| 4.5 | F-21/F-22 | DONE | (این کامیت) | F-22 red: ۱ ناموفق (۴ خط) ⇒ green؛ semgrep قاعده repair شد (مرده بود، AD‑8)؛ S فعال و بلوکینگ؛ گیت after-wp45 PASS؛ pytest ۱۱۹۱/۲/۰ |
| 4.6 | F-16 | DONE | (این کامیت) | red: `tests/nutritionNoMemberSentinel.test.tsx` (درخواست `member_id=-1` بدون عضو)؛ اصلاح `Nutrition.tsx` ⇒ بدون عضو درخواست نمی‌رود؛ `mp-ts-float-money` روی `Analytics.tsx:106` (شمارندهٔ دقیقه) false positive ⇒ regex با lookahead محدود شد (AD‑18) و fixture `.semgrep/tests/mp-ts-float-money.ts` دقیقاً ۵/۵ مطابقت؛ `studio/src` ⇒ ۰ یافته؛ `tsc` rc=0؛ vitest ۲۹۹ passed، rc=0 |
| 4.7 | — | TODO | — | Semgrep blocking، بار پله‌ای، جهش، گیت نهایی |

**باقی‌مانده‌های `BLOCKED-ENV`** (کاربر باید مطلع شود، نه متوقف شود): Docker/Postgres/Valkey برای بار ۲۰۰ کاربر و `pgBackRest`؛ Prometheus/Alertmanager؛ دستگاه واقعی و اسکرین‌شات Flutter؛ امضای APK؛ آزمون ابری.

## ۴. تصمیم‌ها

BD-1 تا BD-5 در `DECISIONS.md` (بخش D-5) با دلیل و نحوهٔ برگرداندن ثبت شده‌اند.

## ۵. قاعدهٔ ادامه برای اجرای بعدی

۱. `git status` و `git log -3`؛ تغییرهای قبلی را حفظ کن.
۲. اولین ردیف `READY` بالاترین اولویت (ترتیب بالا) را بردار؛ وابستگی‌ها را از بریف بخوان.
۳. با «قرمز» شروع کن؛ اصلاح؛ گیت هدف؛ کامیت؛ به‌روزرسانی این جدول و `status.json`.
۴. پایان هر فاز: گیت سلامت کامل.

## الحاقیهٔ A1 (ruff و دو یافتهٔ تازه) — وضعیت در حلقه

- منبع: الحاقیهٔ «A1» (ruff 0.17.6). ثبت خط پایه و اختلاف‌ها: `BASELINE.md` و `EXECUTION-LOG.md` (بخش الحاقیه).
- افزوده‌ها: WP 0.9 (فاز ۰)، WP 2.6 (فاز ۲، F‑29)، WP 3.6 (فاز ۳، F‑28)؛ WP 4.5 اصلاح‌شده.
- ترتیب: 0.9 پیش‌نیاز گیت عددی 2.6 و 3.6 است؛ 2.6 بعد از 2.1 (F‑03) انجام شود تا لاگ بی‌محتوا نماند.
- تصمیم‌ها: AD‑1 (منطقهٔ «امروز») و AD‑2 (سیاست noqa) در `DECISIONS.md`.
- **شرط WP 0.9:** `ruff-recommended.toml` در این مخزن نیست؛ باید از مشخصات الحاقیه بازسازی و اعداد ستون «بعد» آن با اندازه‌گیری تأیید شود (شمارش ۴۳۰/۵۲ ادعای الحاقیه قابل تأیید از فایل مرجع نیست).
