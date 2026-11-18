# M104 — Startup measurement / وضعیت و پروتکل اجرا

- تاریخ ثبت: `2026-11-16`
- شاخه: `arena/4f336f66-mp`
- وضعیت: **`UNKNOWN` — هیچ اندازه‌گیری runtime انجام نشده است.**

## بررسی محیط فعلی

در workspace جاری این ابزارها پیدا نشدند: `flutter`، `dart` و `adb`. متغیرهای `ANDROID_HOME` و `ANDROID_SDK_ROOT` هم خالی‌اند؛ emulator/device از این محیط در دسترس نیست. بنابراین build، اجرای Android، cold/warm timing و ثبت trace اجرا نشدند و عددی گزارش نمی‌شود.

این نتیجه دربارهٔ موجودبودن دستگاه شخصی کاربر نیست؛ فقط محدودیت همین sandbox را ثبت می‌کند. برای عبور از M104 باید سنجش روی یک emulator یا دستگاه واقعی با SDK حاضر و نسخهٔ Android ثبت‌شده تکرار شود.

## مسیر startup مشاهده‌شده در سورس

- `mp-app/client/lib/main.dart`: `main()` قبل از `runApp()`، `authProvider.notifier.restore()` را `await` می‌کند؛ مسیر بعدی با نتیجهٔ آن `/home` یا `/otp` است.
- `mp-app/client/lib/core/session.dart`: `restore()` ابتدا `SharedPreferences` را می‌خواند؛ اگر توکن ذخیره باشد، `/auth/refresh` و سپس `/members/me` را امتحان می‌کند. پس زمان ورود به صفحه می‌تواند شامل disk/preferences و رفت‌وبرگشت شبکه باشد؛ زمان «اولین frame» به‌تنهایی معیار کافی نیست.
- این‌ها مشاهدهٔ کدند، نه اندازه‌گیری عملکرد؛ هیچ توکن یا دادهٔ عضو واقعی در این گزارش کپی نشده است.

## پروتکل پیشنهادی برای اجرای بعدی

1. از profile/release build استفاده شود، نه debug. در header این گزارش، device model، Android/API level، build type، app version/commit و network condition ثبت شوند.
2. هر حالت با test account/test backend یا fixture غیرواقعی اجرا شود؛ از حساب تولیدی و دادهٔ شخصی استفاده نشود.
3. هر سناریو حداقل ۵ بار سنجیده شود و median و بازهٔ نتایج ثبت شود؛ process cold و warm جدا بمانند.
4. سه نشانگر را جدا ثبت کن: Activity launch، اولین Flutter frame، و صفحهٔ واقعاً قابل‌استفاده (route نهایی آشکار است و overlay/بارگذاری مانع تعامل نیست). زمان کل تا صفحهٔ قابل‌استفاده نیز نگه داشته شود.
5. سناریوها:
   - **بدون نشست:** preferences تست پاک/خارج‌شده؛ انتظار مسیر `/otp`.
   - **نشست معتبر:** test account با refresh موفق و `/members/me` موفق؛ انتظار مسیر `/home`.
   - **restore ناموفق:** refresh نامعتبر یا backend تست در دسترس نیست؛ رفتار و route نهایی ثبت شود، بدون credential واقعی.
6. برای trace از Android Studio/Perfetto و Flutter DevTools در حالت profile استفاده کن؛ برای هر run دستور و نشانگر زمانی را ذخیره کن. هر تأخیر دستی یا artificial launch delay ممنوع است.

## جدول ثبت — خالی تا اجرای واقعی

| سناریو | تکرار | Device / API | Activity launch | Flutter first frame | usable route | network/build notes |
|---|---:|---|---:|---:|---:|---|
| بدون نشست / cold | — | — | — | — | — | اندازه‌گیری نشده |
| نشست معتبر / cold | — | — | — | — | — | اندازه‌گیری نشده |
| restore ناموفق / cold | — | — | — | — | — | اندازه‌گیری نشده |
| نشست موجود / warm resume | — | — | — | — | — | اندازه‌گیری نشده |

**گیت:** M104 تا زمانی که روش/دستگاه/نسخه و دادهٔ قابل‌بازتولید وارد جدول نشده `UNKNOWN` می‌ماند. M105 همچنان تا بسته‌شدن M103 و شواهد M104 `BLOCKED` است.
