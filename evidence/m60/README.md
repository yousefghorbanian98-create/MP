# شواهد M60 — بازرسی ثابت APK و DAST جانشین

هر فایل JSON خروجی دستگاهی است که آن را ساخته، نه متن دست‌نویس.

| فایل | ابزار | چه چیزی را ثابت می‌کند |
|---|---|---|
| `flutter-*.json` | `rea identify-flutter-build` | payload فلاتر در هر سه ABI، hash اسنپ‌شات دارت، build-id کتابخانهٔ موتور، پیلود ELF سالم |
| `apk-audit.json` | `mp-app/client/tools/apk_audit.py` (+ androguard) | امضا v2 معتبر، مجوزها (فقط INTERNET)، minSdk 24 / targetSdk 36، `debuggable` خالی، `allowBackup=false`، تطابق sha256 با فایل `.sha256` |
| `pkg-arm64.json` | `rea inspect-android-package` | **شکست** — JAR جادکس پیدا شد (`npm i jadx-mcp`, 1.4.1) و REA آن را شناخت، ولی به JDK کامل با `jdk.compiler` نیاز دارد؛ jdk4py روی PyPI فقط JRE دارد (۳۶ ماژول، بدون `jdk.compiler`) |
| `res-arm64.json` | `rea decode-android-resources` | **موفق شد (بازبینی مجدد)** — apktool 2.9.3 + Temurin 25؛ ۴۷۴ فایل، coverage=complete، package/version/minSdk/targetSdk از مانیفست واقعی |
| `apk-deep-audit.json` | `mp-app/client/tools/apk_deep_audit.py` (apktool واقعی) | **جدید** — بازرسی سه ABI: مجوزها (فقط INTERNET + مجوز امضایی خودِ اپ)، `exported`, `allowBackup=false`, cleartext، و جست‌وجوی راز/URL عمومی در `libapp.so` → ۰ یافته، کد دارت ارسال نشده |
| `aot-arm64.json` | `rea inspect-dart-aot` | **شکست** — `_kDartVmSnapshotData` در جدول نماد پویا نیست (سیمبل‌های Dart در بیلد release حذف می‌شوند) |
| `dast.json` | `scripts/dast.py` (schemathesis) | ۱۰۲۴ درخواست روی ۱۲۸ عملیات، ۰ یافته، ۰ مسیر بی‌توکن |

سه فایل شکست عمداً نگه داشته شده‌اند: دقیقاً نشان می‌دهند کدام قابلیت با کدام
وابستگی غایب ممکن نیست، تا در گزارش «نمی‌شود» با شاهد باشد، نه با حدس.
جایگزین هر سه: خروجی `apk-audit.json` که همان سؤال‌ها (امضا/مجوز/نسخه/یکپارچگی)
را با ابزار خالص‌پایتون جواب می‌دهد.

## بازبینی مجدد دو مورد «مسدود»

هر دو موردی که پیش‌تر «نمی‌شود» نوشته شده بود، دوباره بررسی شد و یکی‌شان حل شد:

**۱) apktool — حل شد.** سه مانع پشت سر هم بود و هر سه دور زده شد:
   - `java` نبود → `pip install jdk4py` (Temurin 25، از PyPI؛ `api.adoptium.net` و
     `cdn.azul.com` و `release-assets.githubusercontent.com` مسدودند).
   - بستهٔ npm `apktool` نسخهٔ ۲٫۰٫۳ می‌دهد و REA حداقل ۲٫۷٫۰ می‌خواهد →
     `npm i apk-revise` نسخهٔ ۲٫۹٫۳ را در `bin/apktool.jar` دارد.
   - `rea` خودش apktool را صدا می‌زد و نسخهٔ قدیمی را رد می‌کرد → یک لانچر
     `/tmp/apktool` روی مسیر PATH قرار گرفت و بعد `rea decode-android-resources`
     با `provider.version = 2.9.3` موفق شد.
   نتیجه: `res-*.json` برای هر سه ABI با `coverage: complete`.

**۲) JADX — هنوز مسدود، با دلیل دقیق‌تر از قبل.** این‌بار JAR پیدا شد
(`npm i jadx-mcp` → `jadx-mcp.jar`، نسخهٔ ۱٫۴٫۱، شامل کلاس‌های `jadx.cli`)،
پس مانع «JAR نیست» برداشته شد. مانع واقعی: REA برای پل منبع، `jdk.compiler`
می‌خواهد و `jdk4py` روی PyPI **فقط JRE** است (۳۶ ماژول، `java.compiler` دارد ولی
`jdk.compiler` ندارد). مسیرهای تأمین JDK کامل همه مسدودند:
`api.adoptium.net`, `cdn.azul.com`, `adoptium.net`, `raw.githubusercontent.com`
(TLS بسته می‌شود). `cjdk`, `jdk4py`, `install-jdk`, `jabba`, `jdkman` همه فقط
دانلودکننده‌اند و از همین میزبان‌ها می‌خوانند؛ هیچ بستهٔ PyPI/npm یافت نشد که
خودِ JDK کامل را در خود داشته باشد.

## اثبات زنده

`live-proof.md` خروجی curl واقعی روی سرور `:8123` است برای R3 (۴۰۳ مالی برای
coach/member، ۴۰۳ نوشتن کاتالوگ برای admin)، R5 (رسید ۲۰۰ برای صاحب سفارش،
۴۰۳ برای عضو دیگر، ۲۰۰ برای کارمند) و R6 (`gif_url` + سرو واقعی GIF با
`content-type: image/gif`).
