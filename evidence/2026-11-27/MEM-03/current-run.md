# MEM-03 / PWA-32 — تغییر شماره و نشست‌های دستگاه، اجرای ۲۰۲۶-۱۱-۲۷ UTC

- **Branch:** `arena/3c08bfbd-mp` (شاخه‌شده از `main` در commit `ebebef3ad153277f0223c2011efc4f9a9c855654` = merge commit PR #30؛ `gh pr view 30` → `state=MERGED`, `mergedAt=2026-11-27T16:49:20Z`).
- **وضعیت کارت:** `MEM-03 / PWA-32 = PARTIAL / NOT_ACCEPTED`؛ checkbox canonical **باز** می‌ماند. این سند «اجرا شد» را فقط برای همان چیزی می‌گوید که فرمان و خروجی‌اش زیر ثبت شده است.
- **محیط:** بدون مرورگر/دستگاه واقعی؛ `BROWSER_AVAILABLE=no` (در این sandbox کروم اجرا نشد). SMS واقعی ارسال نشد؛ فقط `DevSmsProvider` در حالت `development` با echo کد.

## ۱) مرور scope — پیش از تغییر کد

| پرسش | یافته (بر پایهٔ کد همان مسیر) |
| --- | --- |
| آیا endpoint فرضی لازم است؟ | نه. قرارداد واقعی از قبل کامل است: `POST /auth/phone-change/{request,verify-old,confirm}`، `GET /auth/sessions`، `DELETE /auth/sessions/{id}`، `POST /auth/logout-all` و ۱۸ آزمون backend در سه فایل مرتبط. |
| شکاف محصول | `PhoneChangeDialog` و `DeviceSessions` فقط در shell کارکنان (`TopBar`) سوار شده بودند؛ `MemberShell` نه ورودی تغییر شماره داشت و نه مدیریت نشست. `POST /auth/logout-all` هیچ مصرف‌کنندهٔ UI نداشت و در گیت `apiCoverage` با `TODO: پنل امنیتی` مستثنا شده بود. |
| شکاف قرارداد زنده | job «live-contract» در CI فقط `/members/me` و memberships را می‌آزمود؛ هیچ آزمون زنده‌ای برای سه‌مرحلهٔ تغییر شماره و `logout-all` وجود نداشت. |
| ریسک پاسخ دیررس | `confirm` موفق، سپس `signOut()` روی **نشست فعلی**. اگر در فاصلهٔ درخواست تا پاسخ، حساب دیگری در همین مرورگر وارد شده باشد، `logoutSession()` نشست حساب تازه را پاک **و refresh token آن را سمت سرور revoke** می‌کند. تست‌های موجود (`session.test.ts`) فقط «پاسخ دیررس refresh پس از logout» را پوشش می‌دادند، نه این مسیر. |

## ۲) تغییرها — فقط همین دامنه

| فایل | تغییر |
| --- | --- |
| `mp-app/studio/src/lib/session.ts` | `tokenSubject`/`SessionGuard`/`captureSessionGuard`/`clearSessionForAccount`: پایان نشست فقط اگر حسابِ نشست فعلی همان حسابِ آغاز مرحله باشد؛ `different-account` = امتناع، نه خطا. |
| `mp-app/studio/src/auth/AuthContext.tsx` | `finishPhoneChange(guard)` (پاک‌سازی همگام + revocation best-effort) و `signOutEverywhere()` (فقط با تأیید سرور؛ در خطا نشست محلی حفظ می‌شود). |
| `mp-app/studio/src/components/PhoneChangeDialog.tsx` | guard **پیش از** فرستادن `confirm` گرفته می‌شود و همراه نتیجه به صاحب UI داده می‌شود. |
| `mp-app/studio/src/lib/api.ts` | `logoutAllSessions()` روی endpoint موجود `POST /auth/logout-all`. |
| `mp-app/studio/src/components/MemberSecurity.tsx` (نو) | کارت عضو: فهرست نشست‌های خودِ حساب + «خروج از همهٔ دستگاه‌ها» با تأیید و پیام خطای قابل‌تلاش. |
| `mp-app/studio/src/pages/MemberAccount.tsx` | دکمهٔ «تغییر شماره» کنار شمارهٔ سرور + سیم‌کشی `finishPhoneChange`. |
| `mp-app/studio/src/App.tsx` | `MemberSecurity` در صفحهٔ خانهٔ عضو و `ToastViewport` در shell عضو. |
| `mp-app/studio/src/components/TopBar.tsx` | مسیر کارکنان هم از guard استفاده می‌کند؛ حالت `different-account` با toast صادق گزارش می‌شود. |
| `mp-app/studio/tests/apiCoverage.test.ts` | استثنای `TODO: پنل امنیتی` برای `/api/v1/auth/logout-all` حذف شد؛ اکنون مصرف‌کنندهٔ واقعی دارد و گیت همین را الزام می‌کند. |
| `.github/workflows/ci.yml` | `MP_ALLOW_DEV_OTP_ECHO=true` فقط برای سرور synthetic همان job + step تازهٔ «live phone-change + logout-all» بعد از قرارداد حساب عضو. |
| `mp-app/studio/tests/liveContractPhoneChange.test.ts` (نو) | قرارداد زندهٔ سه مرحله + ابطال نشست + `logout-all` روی API محلی. |

هیچ endpoint، مدل داده، migration، policy یا رفتار backend تغییر نکرد.

## ۳) آزمون‌های offline

- `studio-focused-tests.txt`: **۶ فایل / ۴۲ تست pass** —
  `session.test.ts` (۲۱)، `phoneChange.test.tsx` (۲)، `memberSecurity.test.tsx` (۳)، `memberAccountPage.test.tsx` (۸)، `apiCoverage.test.ts` (۳)، `deviceSessions.test.tsx` (۴).
- تست‌های تازهٔ همان race: پاسخ موفق `confirm` که پس از ورود حساب دیگر می‌رسد، نشست حساب تازه را پاک نمی‌کند (`different-account`)، همان حساب بسته می‌شود (`ended`)، نشست ناموجود `signed-out`، توکن ناخوانا fail-closed.
- `studio-full-tests.txt`: **۵۵ فایل pass / ۴ skip؛ ۳۹۲ pass / ۱۵ skip**. skipها همان مجموعهٔ قبلی + ۱ تست زندهٔ تازه بدون `MP_API_BASE` هستند و pass شمرده نشده‌اند.
- `studio-gates.txt`: `tsc -b` exit 0، `eslint .` exit 0، `npm run build` موفق (۱۵.۸۵s).
- `backend-focused-tests.txt`: `test_m82_phone_change.py` + `test_wp14_logout_all.py` + `test_phase4_identity_session.py` → **۱۸ passed / ۱ warning** (هشدار Starlette/httpx از قبل موجود). این اجرا فقط بازآزمون قرارداد موجود است، نه شاهد تازه‌ای برای محصول.

## ۴) قرارداد زنده — API واقعی، دادهٔ مصنوعی

- سرور: `uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8765` با `MP_ENVIRONMENT=development`، `MP_ALLOW_DEV_OTP_ECHO=true`، `MP_DATABASE_URL=sqlite:////tmp/live_mem03.db`. هیچ سرویس بیرونی یا دادهٔ واقعی استفاده نشد؛ هیچ secret چاپ نشد.
- fixture: دو کاربر مصنوعی `09120000004` و `09120000005` + یک پروفایل/عضویت ساختگی. شمارهٔ ورود هدف `09120000104` (آزاد) بود.
- فرمان: `MP_API_BASE=http://127.0.0.1:8765 npx vitest run tests/liveContractPhoneChange.test.ts` → **exit 0، ۱ فایل / ۱ تست pass** (`live-contract-phone-change.raw.txt`).
- مسیرهایی که واقعاً اجرا شدند (`api-request-log.txt`): `409` برای شمارهٔ متعلق به حساب دیگر، `400` برای کد نادرست در هر دو مرحله، `200` برای تأییدهای درست، سپس `401` روی `GET /members/me` و `POST /auth/refresh` با اعتبارنامهٔ کهنه، ورود با شمارهٔ جدید با همان `User.id`، `GET /auth/sessions` با یک نشست `current=true`، و `200` روی `POST /auth/logout-all` که با `401` بعدی برای همان توکن تأیید شد.
- وضعیت DB پس از اجرا (`db-state-after-run.txt`): `user id=2` با شمارهٔ `09120000104`، `auth_version=2` (یک bump برای `confirm` و یک برای `logout-all`)، هر دو refresh row با `revoked=True`، و challenge با `old_attempts=2`/`new_attempts=2` و `completed=True`. این اعداد نشان می‌دهند مسیرهای «کد غلط» واقعاً اجرا شده‌اند، نه mock.

## ۵) محدودیت‌ها — چرا پذیرش نیست

- SMS واقعی، provider/line/account، تحویل به گوشی و نرخ/شکست عملیاتی اجرا نشد؛ `dev_code` فقط در `development` برمی‌گردد.
- مرورگر/دستگاه/OS، صفحه‌خوان و بازبینی انسانی اجرا نشد؛ تست‌های UI با jsdom و `fetch` واقعیِ stub‌شده‌اند.
- CI این شاخه هنوز اجرا نشده است؛ نتیجهٔ محلی جای CI همان SHA را نمی‌گیرد.
- داده‌های شمارهٔ قدیم/جدید در `phone_change_challenges` به‌صورت ستون متنی می‌مانند و مسیر پاک‌سازی/retention در auth/modules/scripts پیدا نشد؛ این یک پرسش **policy حریم خصوصی** است، نه نتیجهٔ compliance.
- تست زنده به حساب synthetic وابسته است و باید **آخرین** مصرف‌کنندهٔ آن حساب باشد، چون شمارهٔ ورودش را تغییر می‌دهد.

## ۶) اقدام بعدی دقیق

1. اجرای CI همین شاخه و ثبت نتیجهٔ متصل به SHA.
2. در صورت وجود دستگاه/مرورگر مجاز: اجرای دستی مسیر `/member` → تغییر شماره → ورود با شمارهٔ جدید و بررسی نشست‌های دستگاه روی دستگاه دوم.
3. تصمیم مالک دربارهٔ retention/purge شماره‌های challenge.

## ۷) دور اصلاحی ۲۰۲۶-۱۱-۲۷ — گیت digest، شاهد redacted اسکن راز، تست guard

این بخش فقط شکاف‌های ابزار/شاهد را می‌بندد؛ وضعیت محصول همچنان `MEM-03/PWA-32=PARTIAL/NOT_ACCEPTED` و release=`NO-GO` است.

### ۷.۱ گیت تازهٔ digest
`scripts/verify_crosswalk_digests.py` اضافه شد و در job `docs` (پس از `Interaction map gate`) اجرا می‌شود. شرط‌ها:
`evidence/**/*-crosswalk.json` به‌جز `*.STALE.json`؛ `meta.tracked_dirty is False` (کلید v1 یعنی `dirty` کافی نیست)؛ digest هر منبع در `meta.sources` با SHA-256 فایل فعلی `mp-app/<path>` برابر باشد (هر دو شکل bare-hex و `sha256:` پذیرفته می‌شود)؛
و اگر `meta.sha` در clone موجود بود، `git diff --name-only <meta.sha> HEAD` برای همان منابع خالی باشد (در clone کم‌عمق فقط `NOTE` می‌دهد).

خروجی روی `d71dbe0` پیش از بازتولید: `EXIT=1`، ۶ خطا در ۲ artifact — `INV-02` و `INV-03` هر دو روی `studio/src/lib/api.ts` (recorded `f5e977948640` / actual `ca62f4a37a28`) و `studio/src/lib/navigation.ts` (recorded `71fa84e7d3d0` / actual `6f9b434207f6`) کهنه‌اند و `tracked_dirty=True` دارند. یعنی دامنهٔ کهنگی **دو فایل** است، نه یک فایل. شاهد: [`digest-gate-before.txt`](digest-gate-before.txt).

`scripts/crosswalk_v2.py` هم دو تغییر گرفت: (۱) همهٔ digestها با پیشوند `sha256:` نوشته می‌شوند تا الگوی key/value در `generic-api-key` دیگر match نشود؛ (۲) روی درخت dirty با `exit 4` متوقف می‌شود (پیش از `build()`)، چون digest درخت dirty بازتولیدپذیر نیست.

### ۷.۲ شاهد redacted اسکن راز (بدون هیچ مقدار محرمانه)
پنج یافتهٔ `generic-api-key` روی commit `ebebef3…` (و همان پنج روی `6593cb4b…`) فقط با `File`/`RuleID`/`Line`/`Commit`/`Fingerprint` ثبت شدند: [`secret-scan-redacted.txt`](secret-scan-redacted.txt).
رفع در دو مسیر مجاز (بدون allowlist بر اساس rule یا path): پیشوند `sha256:` برای artifactهای آینده، و ۵ خط fingerprint **دقیق** تازه در `.gitleaksignore` (۵ خط `6593cb4b…` از قبل بود). `.gitleaksignore` از ۵۱۶ به ۵۲۱ خط رسید؛ `git diff --numstat` = ۵ افزوده.
job `secret-scan` در CI حالا `Fingerprint` را در step summary چاپ می‌کند و `/tmp/gitleaks-findings.json` را به‌عنوان artifact آپلود می‌کند؛ پیش از این، لاگ job با EOF قابل دانلود نبود.

### ۷.۳ تست guard برای `finishPhoneChange`
سه تست به `mp-app/studio/tests/session.test.ts` اضافه شد: `different-account` (storage دست‌نخورده و هیچ فراخوانی `/auth/logout`)، `ended` (refresh token خودش revoke و وضعیت `unauthenticated`)، `signed-out`.
برای اثبات غیر‌توخالی‌بودن تست، `logoutSession` عمداً به بالای guard منتقل شد: **۲ تست قرمز** شدند؛ سپس فایل بازگردانده شد و فایل دوباره `24 passed` داد. شاهد: [`guard-mutation-test.txt`](guard-mutation-test.txt).

### ۷.۴ اجرای محلی این دور
- `npx vitest run tests/session.test.ts` → ۲۴ pass.
- `npx vitest run` (کل استودیو) → ۵۵ فایل pass / ۴ فایل skip؛ ۳۹۵ تست pass / ۱۵ skip.
- `npx tsc -b` / `npx eslint .` / `npm run build` → پاک (exit 0).
- `python3 scripts/docs_gate.py` → ۳۸ Markdown، ۶۱۹ لینک محلی، ۱۵ Mermaid، pass.
- تست policy گیتلکس (`scripts/test_retired_signing_scan.py`) → assertها pass؛ **اسکن واقعی gitleaks اینجا NOT_RUN** (دانلود release با `SSL_ERROR_SYSCALL` شکست می‌خورد).

### ۷.۵ محدودیت‌ها و کار باقی‌مانده
- نتیجهٔ CI روی SHA این commit هنوز دیده نشده؛ ادعای سبزی تا آن لحظه مجاز نیست.
- بازتولید `INV-02`/`INV-03` باید روی **درخت تمیز** و در commit بلافاصلهٔ بعد انجام شود؛ `docs` تا آن لحظه قرمز است.
- v1 artifactها byte-for-byte بازتولیدشدنی نیستند (generator v1 در repo نیست) و به همین دلیل با `git mv` به `*.STALE.{md,json}` تغییر نام دادند.
