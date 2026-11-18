# M82 — تغییر شماره با اثبات دوطرفهٔ OTP

- تاریخ ثبت: ۲۰۲۶-۱۱-۱۶
- شاخه: `arena/4f336f66-mp`، وضعیت `active`، پایه `d64e3b008d1c6c20c65c5ebfa4816277d4d23ce0`
- نتیجهٔ loop: **`UNKNOWN` برای runtime اپ Flutter**؛ implementation کامل است و backend/Studio/static checks سبزند، اما Flutter SDK در محیط موجود نیست. `PASS` سراسری ادعا نمی‌شود.

## رفتار پیاده‌سازی‌شده

1. کاربر واردشده شمارهٔ جدید را به `POST /api/v1/auth/phone-change/request` می‌دهد. کد اول فقط به شمارهٔ فعلی حساب ارسال می‌شود.
2. `POST /api/v1/auth/phone-change/verify-old` کد فعلی را بررسی می‌کند؛ فقط در صورت موفقیت، OTP مستقل به شمارهٔ پیشنهادی فرستاده می‌شود.
3. `POST /api/v1/auth/phone-change/confirm` کد شمارهٔ جدید را بررسی می‌کند. سپس شمارهٔ یکتا تغییر می‌کند، همهٔ refresh sessionها revoke می‌شوند و `users.auth_version` در همان transaction افزایش می‌یابد.
4. ورود با شمارهٔ جدید همان حساب قبلی را پیدا می‌کند؛ شمارهٔ قدیمی آزاد می‌شود. challenge فقط برای user خود قابل استفاده است، expire/attempt-limit/invalidation دارد و replay رد می‌شود.

Challenge تصادفی به کاربر و زوج شماره bind شده؛ OTPها فقط با salt جداگانه به‌صورت hash ذخیره می‌شوند. هر هشت تست M82 از `FakeSmsProvider` در حافظه استفاده می‌کنند؛ هیچ SMS واقعی ارسال نشده است.

## ابطال نشست و یکتایی

Access JWTهای تازه claim نسخهٔ کاربر (`ver`) دارند. dependency نسخه را بررسی می‌کند و JWTهای قدیمی را بعد از تغییر رد می‌کند؛ این شامل tokenهای قبلی با `sid` و tokenهای legacy بدون `sid`/`ver` نیز هست. JWTهای versionless فقط تا وقتی `auth_version == 0` است سازگار می‌مانند. ورود/refresh تازه نسخهٔ جاری را صادر می‌کند.

شمارهٔ مقصد پیش از ارسال OTP و دوباره هنگام تأیید بررسی می‌شود؛ قید unique موجود روی `users.phone` همچنان مرجع نهایی است. بازبینی کشف کرد unique violation ممکن است هنگام اجرای `UPDATE` (نه صرفاً `commit`) رخ دهد؛ handler اکنون هر دو را پوشش می‌دهد. Regression race یک حساب رقیب را پس از preflight و پیش از `UPDATE` وارد می‌کند و پاسخ `409 phone_in_use` را می‌سنجد، بدون آن‌که نشست صاحب challenge را revoke کند.

OTP نادرست با `400 invalid_otp` پاسخ داده می‌شود، نه `401`: کلاینت‌ها 401 را به‌عنوان نشست منقضی refresh و retry می‌کنند و ممکن بود یک کد اشتباه دوبار شمرده شود. 401 برای احراز هویت/نشست نامعتبر می‌ماند.

اگر کاربر به شمارهٔ فعلی دسترسی ندارد، هیچ bypass حدسی/خودکاری اضافه نشده است. بازیابی انسانی نیازمند سیاست احراز هویت مصوب مالک است؛ این مسیر در M82 جعل نشده.

## Client و Studio

- Flutter: دیالوگ سه‌مرحله‌ای متصل به پروفایل، پشتیبانی از ارقام فارسی/عربی، نمایش dev-code فقط وقتی provider توسعه آن را برمی‌گرداند. در موفقیت، Client نشست محلی را پاک می‌کند و به `/otp` می‌رود. تست‌ها درخواست‌ها، header نشست، payload، ترتیب دو مرحله و اتصال دکمهٔ پروفایل به dialog را می‌سنجند.
- Studio: دیالوگ سه‌مرحله‌ای و ورودی شمارهٔ فعلی در TopBar؛ OTP نادرست بدون refresh/retry نشست نشان داده می‌شود. در موفقیت dialog بسته و از حساب خارج می‌شود.
- backend route-guard gate برای هر route یک guard لازم دارد؛ `require_authenticated` به‌عنوان guard صریح اضافه شد و مسیرهای authenticated از whitelist عمومی حذف شدند.

## شواهد اجرا

| گیت | نتیجه |
|---|---|
| `pytest -q` در `mp-app/backend` | **810 passed, 2 skipped**, 30 warning؛ شامل full regressions و هشت تست M82 |
| `ruff check` روی 10 فایل backend تغییرکرده + `ruff format --check` | **All checks passed; 10 files already formatted** |
| `python scripts/export_routes.py` | `backend/api/routes.json`: **118 routes** |
| Alembic با SQLite موقت: `upgrade head` سپس `alembic check` | head=`d9e0f1a2b3c4`; **No new upgrade operations detected** |
| `npm test` در `mp-app/studio` | **33 files passed, 1 skipped; 219 passed, 9 skipped** |
| `npm run build` در Studio | `tsc -b` و Vite build موفق؛ هشدارهای موجود دربارهٔ `act(...)` و dynamic/static import مانع build نبودند |
| `PYTHONPATH=/tmp/mp-m82-static/lib/python3.11/site-packages /tmp/mp-m82-static/bin/python tools/dart_gate.py --include-tests` | **60 فایل Dart، 0 یافته** |
| Flutter `pub get`, `flutter analyze`, widget/full `flutter test`, APK build | **اجرا‌نشده**؛ `flutter`, `dart`, `java`, `ANDROID_HOME` و `ANDROID_SDK_ROOT` در sandbox موجود نیستند |

`npm ci` برای اجرای Studio موفق شد؛ npm audit در dependency tree **14 advisory (2 moderate, 12 high)** گزارش کرد. dependency update یا `npm audit fix` انجام نشد چون خارج از M82 است.

## حفاظت workspace و محدودهٔ اجرا

- هیچ production database، دادهٔ واقعی، SMS واقعی، workflow/CI، deploy، release، push یا commit استفاده نشد.
- شاخه همان `arena/4f336f66-mp` باقی ماند. مخزن در آغاز فقط یک فایل tracked داشت و `mp-app/`, `.finn/` و دیگر baselineها untracked بودند؛ هیچ‌کدام reset یا حذف نشدند.
- بررسی Flutter runtime همچنان gate باز است؛ static Dart gate جایگزین Flutter analyzer/widget tests نیست. مسیر بازتولید و محدودیت‌ها در همین گزارش و `.finn/state/STATE.md` ثبت شده‌اند.
