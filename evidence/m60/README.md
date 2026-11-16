# شواهد M60 — بازرسی ثابت APK و DAST جانشین

هر فایل JSON خروجی دستگاهی است که آن را ساخته، نه متن دست‌نویس.

| فایل | ابزار | چه چیزی را ثابت می‌کند |
|---|---|---|
| `flutter-*.json` | `rea identify-flutter-build` | payload فلاتر در هر سه ABI، hash اسنپ‌شات دارت، build-id کتابخانهٔ موتور، پیلود ELF سالم |
| `apk-audit.json` | `mp-app/client/tools/apk_audit.py` (+ androguard) | امضا v2 معتبر، مجوزها (فقط INTERNET)، minSdk 24 / targetSdk 36، `debuggable` خالی، `allowBackup=false`، تطابق sha256 با فایل `.sha256` |
| `pkg-arm64.json` | `rea inspect-android-package` | **شکست** — به `REA_JADX_MCP_JAR` نیاز دارد؛ در این محیط JAR در دسترس نیست |
| `res-arm64.json` | `rea decode-android-resources` | **شکست** — به `apktool`/JAVA نیاز دارد؛ نصب نمی‌شود |
| `aot-arm64.json` | `rea inspect-dart-aot` | **شکست** — `_kDartVmSnapshotData` در جدول نماد پویا نیست (سیمبل‌های Dart در بیلد release حذف می‌شوند) |
| `dast.json` | `scripts/dast.py` (schemathesis) | ۱۰۲۴ درخواست روی ۱۲۸ عملیات، ۰ یافته، ۰ مسیر بی‌توکن |

سه فایل شکست عمداً نگه داشته شده‌اند: دقیقاً نشان می‌دهند کدام قابلیت با کدام
وابستگی غایب ممکن نیست، تا در گزارش «نمی‌شود» با شاهد باشد، نه با حدس.
جایگزین هر سه: خروجی `apk-audit.json` که همان سؤال‌ها (امضا/مجوز/نسخه/یکپارچگی)
را با ابزار خالص‌پایتون جواب می‌دهد.
