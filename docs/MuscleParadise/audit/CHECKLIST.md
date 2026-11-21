# فهرست خط‌به‌خط ممیزی MP

> تولیدشده با `scripts/build_audit_inventory.py` — **دستی ویرایش نکنید.** وضعیت هر مورد در `status.json` است.

منبع: بستهٔ ممیزی `MP-PROBLEMS-2026-11-20.md` و `MP-FINAL-AUDIT-REPORT-2026-11-20.md` (از مخزن `Chat2DB` شاخهٔ `arena/2cde32d6-chat2db`).

وضعیت‌ها: `OPEN` باز · `IN-PROGRESS` در حال کار · `FIXED` رفع‌شده با شاهد · `DEFERRED` به تصمیم مالک · `NOT-REPRODUCED` بازتولید نشد · `VERIFIED-IN-CODE` در کد دیده شد (هنوز بازتولید اجرایی نشده).

## الف) ۵۸ مشکل (بخش‌های A–D بریف)

| شناسه | عنوان | وضعیت | یادداشت |
|---|---|---|---|
| A1 | قفل‌شدگی کامل سرور بر اثر پر شدن استخر اتصال — ریشه‌یابی نشده | OPEN |  |
| A2 | `/api/v1/metrics` کاملاً بدون احراز هویت و عمومی است | FIXED | همان شاهد F-06 (WP 1.3). پیش از اصلاح: ۲۰۰ بدون توکن با ۳۴۶ خط متریک. |
| A3 | `MP_TRUSTED_PROXIES` پیش‌فرض خالی است و در production اعتبارسنجی نمی‌شود → همه‌ی کاربران یک سبد rate-limit | OPEN |  |
| A4 | `mp.db` در ریشهٔ مخزن ترک‌شده است (دیتابیس واقعی در Git) | OPEN |  |
| A5 | زنجیرهٔ تأمین آرتیفکت صفر گیت دارد | IN-PROGRESS | WP 0.8: همهٔ ۴۲ ارجاع uses: در ۷ workflow به SHA کامیت پین شد (هر خط با برچسب نسخه در کامنت). گیت‌های لایهٔ تأمین (SBOM/امضا/provenance) هنوز اضافه نشده‌اند. |
| A6 | هیچ گزارش خطا/crash در زمان اجرا وجود ندارد | OPEN |  |
| A7 | `Content-Security-Policy` هیچ‌جا تعریف نشده | OPEN |  |
| A8 | بیلد release اندروید بدون shrink/obfuscation و بدون AAB | OPEN |  |
| A9 | ۲۱ آیتم باز در `RELEASE-CHECKLIST.md` (تعریف خودتان از «آمادهٔ انتشار») | OPEN |  |
| B1 | کیوسک / چک‌این انتها‌به‌انتها ناقص است | OPEN |  |
| B2 | `POST /api/v1/axis-assessments/{id}/review` و روتر `classes` گارد تکراری دارند (کد روی کد) | OPEN |  |
| B3 | استودیو شناسهٔ نامعتبر `1-` را به API می‌فرستد و سرور ۲۰۰ می‌دهد | OPEN |  |
| B4 | همزمانی کوپن روی PostgreSQL تست نشده (فقط SQLite) | OPEN |  |
| B5 | پول/شناسه‌ها از مرز `2^53−1` در لایهٔ JS رد می‌شوند — فقط یک مورد اصلاح شده | OPEN |  |
| B6 | قواعد گردکردن و تقسیم پول مستند/تست نشده | OPEN |  |
| B7 | هیچ تست طلایی/رگرسیون بصری برای کلاینت Flutter نیست | OPEN |  |
| B8 | هیچ تست روی‌دستگاه (integration/patrol) وجود ندارد | OPEN |  |
| B9 | دسترس‌پذیری کلاینت Flutter تقریباً وجود ندارد | OPEN |  |
| B10 | سخت‌گیری نوع در Dart فعال نیست | OPEN |  |
| B11 | اسکریپت `lint` استودیو مرده است | OPEN |  |
| B12 | نصب غیرقطعی در CI | OPEN |  |
| B13 | وابستگی اعلام‌نشده: DAST روی محیط تازه می‌شکند | OPEN |  |
| B14 | `openapi.json` در مخزن commit نشده ⇒ تغییر شکننده دیده نمی‌شود | OPEN |  |
| B15 | `live-contract` فقط استودیو را پوشش می‌دهد، نه کلاینت Flutter | OPEN |  |
| B16 | ماتریس مجوز/مالکیت به‌صورت سیستماتیک تست نشده | OPEN |  |
| B17 | `MP_REQUIRE_WORKER=False` ⇒ readiness می‌تواند بدون worker صف سبز شود | OPEN |  |
| B18 | `MP_DATABASE_URL` در production اعتبارسنجی نمی‌شود | OPEN |  |
| B19 | سه `except Exception: pass` بی‌صدا در مسیر مانیتورینگ | OPEN |  |
| B20 | وبِ کلاینت هرگز در PR/push گیت نمی‌شود | OPEN |  |
| B21 | Electron و Service Worker سخت‌سازی/تست نشده‌اند | OPEN |  |
| B22 | تست بار فقط ۲ اندپوینت سبک را می‌کوبد و فقط روی SQLite/یک worker معتبر است | OPEN |  |
| C1 | ۶۷۰ یافتهٔ سلامت کد (۲۵ critical، ۷۰ high) | OPEN |  |
| C2 | شش نقطهٔ داغ critical: | OPEN |  |
| C3 | توابع بیش‌ازحد بزرگ: | OPEN |  |
| C4 | `io_in_loop` در چند اسکریپت ابزار و importer | OPEN |  |
| C5 | ۳۵ یافتهٔ کد مرده: | OPEN |  |
| C6 | ۲۵ یافتهٔ رانش مستندات در ۱۴ سند | OPEN |  |
| C7 | هیچ ابزار سنجش تکرار/مرده/پیچیدگی در CI نیست: | OPEN |  |
| C8 | هیچ تست جهش (mutation) نیست | OPEN |  |
| C9 | هیچ تست ویژگی‌محور (property) نیست | OPEN |  |
| C10 | هیچ l10n/i18n نیست: | OPEN |  |
| C11 | دو نقص نمایشی بازِ QA: | OPEN |  |
| C12 | ۴۱ `print()` در کد غیرتست بک‌اند | OPEN |  |
| C13 | ۴۸ `TODO/FIXME/HACK` در `mp-app` | OPEN |  |
| C14 | ۶ تست skip/disabled در بک‌اند + ۹ skip در استودیو + ۲ skip گزارش‌شده | OPEN |  |
| C15 | هیچ گیت خودکار لایسنس وابستگی‌ها نیست | OPEN |  |
| C16 | هیچ ابزار آشوب/تنزل نیست: | OPEN |  |
| C17 | provenance تصاویر مستند نشده: | OPEN |  |
| C18 | `.semgrep/project-rules.yml` فقط یک فایل قاعده دارد | OPEN |  |
| C19 | فایل‌های سنگین و بزرگ‌ترین‌های ترک‌شده: | OPEN |  |
| D1 | جدول مجوزها (§۷) خالی چاپ شده | OPEN |  |
| D2 | §۶ مقدار پیش‌فرض `MP_CORS_ORIGINS` را `(` نشان می‌دهد | OPEN |  |
| D3 | §۱۳ می‌گوید «`web.yml` و `apk.yml` فقط `workflow_dispatch` دارند» | OPEN |  |
| D4 | §۲ می‌گوید پیشوندهای بی‌پوشه «در `api/` یا `app/` تعریف شده‌اند» | OPEN |  |
| D5 | سند روی شاخهٔ مرج‌نشده است | OPEN |  |
| D6 | §۱۱ می‌گوید اسکرین‌شات‌ها در `docs/MuscleParadise/screenshots/` | OPEN |  |
| D7 | اختلاف اعداد بین دو سند RepoWise: | OPEN |  |
| D8 | §۲ فهرست ماژول‌ها ناقص است: | OPEN |  |

## ب) ۲۹ یافته (F-01 … F-29)

| شناسه | عنوان | وضعیت | یادداشت |
|---|---|---|---|
| F-01 | دورزدن rate‑limit با `X-Forwarded-For` (فرمان Dockerfile) | FIXED-PARTIAL | WP 1.1: uvicorn فقط به MP_TRUSTED_PROXIES اعتماد می‌کند (scripts/uvicorn_proxy_flags.sh)؛ production بدون فهرست معتبر بالا نمی‌آید. شاهد: e2e زنده ۳۰ درخواست با XFF جعلی ⇒ ≥۲۷×429 (قبل: ۳۰×200). تست: tests/regression/test_wp11_xff_trust.py. باقی‌مانده: متریک mp_rate_limit_key_source. |
| F-02 | پیش‌فرض fail‑open محیط: `MP_ENVIRONMENT=development` + `MP_SMS_PROVIDER=dev` ⇒ `dev_code` در پاسخ | FIXED-PARTIAL | WP 1.2 (BD-3): MP_ENVIRONMENT صریح الزامی؛ dev_code فقط development+MP_ALLOW_DEV_OTP_ECHO؛ رد echo در production؛ WARNING شروع؛ گیت استاتیک deploy_gate. تست: tests/regression/test_wp12_env_failsafe.py. باقی‌مانده: گیت زنده روی استقرار BLOCKED. |
| F-03 | قفل شدن سرور زیر بار؛ رندر `rich` روی event loop | OPEN |  |
| F-04 | اشباع استخر اتصال؛ نبودِ هیچ متریک pool؛ ناسازگاری ظرفیت‌ها | OPEN |  |
| F-05 | `SystemError` در `casbin enforce` زیر همزمانی (compile در هر درخواست) | OPEN |  |
| F-06 | `/api/v1/metrics` بدون احراز هویت | FIXED | WP 1.3: /api/v1/metrics با Bearer (MP_METRICS_TOKEN) محافظت شد: بدون هدر/توکن غلط ۴۰۱، بدون توکن تنظیم‌شده ۴۰۳؛ Caddy مسیر را ۴۰۴ می‌کند؛ Prometheus با credentials؛ Compose الزام متغیر دارد. تست: tests/integration/test_wp13_metrics_auth.py. |
| F-07 | پوشش مستند ۹۴٫۲۸٪ در برابر واقعی ۸۳٫۷۳٪ | OPEN |  |
| F-08 | `logout-all` توکن‌های بدون `sid` را باطل نمی‌کند | FIXED-PARTIAL | WP 1.4 (BD-6): logout-all عدد auth_version را bump می‌کند؛ توکن بی‌sid پس از آن ۴۰۱ (قبل ۲۰۰). دو اسکریپت توکن با sid واقعی و بدون چاپ روی stdout. تست: tests/integration/test_wp14_logout_all.py. باقی‌مانده: قاعدهٔ Semgrep (WP 0.7). |
| F-09 | پول بزرگ: `2^53`، `2^53+1`، `10^18` پذیرفته می‌شوند + coercion رشته→عدد | OPEN |  |
| F-10 | ۳۱ خطای ESLint در استودیو (هیچ lint واقعی اجرا نمی‌شد) | FIXED | WP 0.5: eslint.config.mjs (flat) + اسکریپت lint = `eslint .` + گیت در CI. اندازه‌گیری قبل: ۴۲ خطا + ۵ هشدار (بریف: ۳۱ خطا؛ عدد دقیق با همین پیکربندی ۴۲ بود). بعد: ۰ خطا، ۰ هشدار. قاعدهٔ label-has-associated-control با controlComponents برای کنترل‌های antd تنظیم شد؛ autoFocus به فوکوس ref تبدیل شد. |
| F-11 | امتیاز جهش ۵۷٫۸٪ در ماژول پولی؛ ۳ شکاف واقعی | OPEN |  |
| F-12 | `routes.json` مجموعهٔ گاردهای واقعی را کم‌تر نشان می‌دهد ⇒ اوراکل نامعتبر | OPEN |  |
| F-13 | guard تکراری روی یک مسیر (دو بار casbin enforce) | FIXED | WP 0.3: گارد تکراری روی review حذف شد؛ شاهد: قبل ۲ بار enforce، بعد ۱ بار (tests/integration/test_wp03_axis_single_guard.py، tests/regression/test_no_duplicate_guard.py) |
| F-14 | `gateway-return` با شناسهٔ نامعتبر → HTTP 200 | OPEN |  |
| F-15 | ۵۵ هشدار پیچیدگی (lizard) و ۴۱ بلوک ≥C (radon)؛ بدترین درجهٔ radon **F** با CC ‏۴۷ و ۴۶ | OPEN |  |
| F-16 | ۷ محل پولِ شناور در استودیو + ۱ sentinel منفی | OPEN |  |
| F-17 | ۴ خطای «except بی‌صدا» (از جمله در `api/v1/monitoring.py:18`) | OPEN |  |
| F-18 | ناسازگاری ظرفیت‌ها: ۱۶۴ handler سنکرون، threadpool=40، pool=60، 4 worker | OPEN |  |
| F-19 | ۳ لایهٔ جداگانهٔ دسترسی به داده در استودیو + `await import()` پویا در هندلر | OPEN |  |
| F-20 | ۲ export مرده در `lib/api.ts` | OPEN |  |
| F-21 | ۵ session بدون context manager در اسکریپت‌ها | OPEN |  |
| F-22 | ۴ SQL با f‑string در یک migration | OPEN |  |
| F-23 | ۱۰ دکمه بدون `onClick` (موجودی، نه لزوماً نقص) | OPEN |  |
| F-24 | هشدارهای انباشتهٔ runtime | IN-PROGRESS | WP 0.6: HTTP_422_UNPROCESSABLE_ENTITY → HTTP_422_UNPROCESSABLE_CONTENT در app/errors.py؛ هشدار Starlette دیگر در تست خطاها نیست. هشدارهای دیگر (httpx در TestClient، asyncio_default_fixture_loop_scope) باقی‌اند. |
| F-25 | گارد شناسه **کف** ندارد: ۱۲ endpoint با `-1`/`0`/`-0`/INT64_MIN پاسخ **۲۰۰** می‌دهند | OPEN |  |
| F-26 | دو شکلِ متفاوت برای پاکت خطا: `{"error":…}` در برابر `{"detail":…}` | OPEN |  |
| F-27 | پیش‌نیازِ «پروندهٔ عضو» در سبد خرید با `404 not_found` بیان می‌شود؛ سفارش به‌نیابت ممکن نیست | OPEN |  |
| F-28 | «امروز» سه برداشت متفاوت دارد: nutrition و axis_assessment از `date.today()` (ساعت UTC کانتینر) استفاده می‌کنند؛ shop از Asia/Tehran. هر شب ۰۰:۰۰–۰۳:۳۰ تهران روز اشتباه | OPEN | الحاقیهٔ A1 — WP 3.6. اندازه‌گیری (662ff88): date.today() ×3 (DTZ011) در axis_assessment/service.py:31، nutrition/service.py:124،182. |
| F-29 | شش خطای ارسال SMS با `log.error` بدون traceback ثبت می‌شوند (app/sms.py:66,69,72,99,102,105) — علت واقعی خطای فراهم‌کننده در لاگ نیست | FIXED | الحاقیهٔ A1 — WP 2.6. قبل: ۶ شاخهٔ except در app/sms.py با log.error و بدون traceback (red: ۶ تست exc_info ناموفق). بعد: _log_provider_failure با traceback و متن استثنای پنهان (AD‑6)؛ ۱۴ تست regression/test_wp26_sms_logging.py سبز؛ test_sms ۶۱ سبز؛ pytest کامل ۱۱۴۶ passed، ۲ skipped، exit 0. S310 سه مورد با noqa دلیل‌دار؛ TRY400 در sms=0. |

## ج) موانع محیطی (BLOCKED)

| شناسه | عنوان | وضعیت | یادداشت |
|---|---|---|---|
| E1 | APK امضاشده: secretهای MP_ANDROID_* تنظیم نشده‌اند | OPEN |  |
| E2 | چرخش کلید signing افشاشده + بازنویسی تاریخچه (فقط با تأیید مالک) | OPEN |  |
| E3 | اجرای Flutter در sandbox: pub.dev و storage.googleapis.com مسدود | OPEN |  |
| E4 | دستگاه واقعی، پرداخت بانکی، push/SMS، Valkey، PostgreSQL، Prometheus | OPEN |  |
| E5 | JADX/بازبینی باینری APK: JDK در محیط نیست | OPEN |  |

## د) مواردی که مشکل نیستند (دوباره بررسی نشوند)

| شناسه | عنوان | وضعیت | یادداشت |
|---|---|---|---|
| N1 | امضای Android: fallback به کلید debug حذف شده | OPEN |  |
| N2 | اعتبارسنجی پیکربندی production قوی است (app/config.py:127-243) | OPEN |  |
| N3 | پول همه‌جا عدد صحیح ریال است | OPEN |  |
| N4 | زمان: هیچ datetime.now() naive نیست | OPEN |  |
| N5 | XFF/پراکسی امن پیاده شده (فقط تنظیمش اجباری نیست) | OPEN |  |
| N6 | مالکیت در مسیر چهره رعایت شده (delete_face) | OPEN |  |
| N7 | Electron پایه امن است (contextIsolation/nodeIntegration) | OPEN |  |
| N8 | هدرهای امنیتی بک‌اند و Caddy کامل‌اند (CSP مانده) | OPEN |  |
| N9 | کد stub وجود ندارد (NotImplementedError = ۰) | OPEN |  |
| N10 | استودیو type-safe است (strict، any = ۰) | OPEN |  |
| N11 | پین SDK و drift حل شده (client-pinned) | OPEN |  |
| N12 | DAST انجام شده: ۰ یافته، ۰ پاسخ 2xx بدون احراز هویت (evidence/m60/dast.json) | OPEN |  |
| N13 | گیت‌های موجود سبز و ارزشمندند (interaction_map، docs_gate، Gitleaks) | OPEN |  |
| N14 | QA مرورگری: ۱۱ صفحه، ۱۰۱ دکمه، ۴۵ کلیک، ۰ خطا | OPEN |  |

## خلاصه

| بخش | وضعیت | تعداد |
|---|---|---|
| blocked | OPEN | 5 |
| findings | FIXED | 4 |
| findings | FIXED-PARTIAL | 3 |
| findings | IN-PROGRESS | 1 |
| findings | OPEN | 21 |
| non_issues | OPEN | 14 |
| problems | FIXED | 1 |
| problems | IN-PROGRESS | 1 |
| problems | OPEN | 56 |
