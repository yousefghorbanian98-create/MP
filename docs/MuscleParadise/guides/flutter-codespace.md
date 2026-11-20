# راهنمای مرحله‌ای: Flutter در Codespace و ساخت پکیج نهایی

این راهنما برای اجرای کلاینت Flutter (`mp-app/client`) در GitHub Codespaces و ساخت نسخهٔ وب و APK است.
دستورها عیناً از `.github/workflows/web.yml` و `.github/workflows/apk.yml` گرفته شده‌اند.

> **توجه:** در sandbox پروژه `pub.dev` و `storage.googleapis.com` مسدود است، پس ساخت Flutter در sandbox ممکن نیست.
> در Codespace معمولاً دسترسی کامل به اینترنت هست. اگر شبکهٔ Codespace هم این دامنه‌ها را ببندد، ساخت فقط از طریق CI انجام می‌شود.

## ۱. باز کردن Codespace
1. صفحهٔ مخزن را در GitHub باز کنید و **Code → Codespaces → Create codespace on main** را بزنید.
2. شاخهٔ کاری را انتخاب کنید (برای نسخهٔ نهایی `main`).

## ۲. نصب Flutter (کانال stable، همان CI)
```bash
git clone https://github.com/flutter/flutter.git -b stable ~/flutter
export PATH="$HOME/flutter/bin:$PATH"
flutter --version
flutter doctor
```
نسخهٔ Flutter را با نسخه‌ای که در CI استفاده می‌شود مقایسه کنید (`channel: stable` در `web.yml`).

## ۳. وابستگی‌ها و تست
```bash
cd mp-app/client
flutter pub get
flutter analyze
flutter test
```

## ۴. ساخت نسخهٔ وب
```bash
cd mp-app/client
flutter build web --release --base-href /
# خروجی: build/web
```
برای آزمایش محلی:
```bash
cd build/web && python3 -m http.server 8080 --bind 0.0.0.0
```
(در Codespace پورت ۸۰۸۰ را از تب Ports باز کنید.)

## ۵. ساخت APK (امضاشده)
ساخت امضاشده به اسرار (secrets) مخزن نیاز دارد. بدون آن‌ها `apk.yml` عمداً شکست می‌خورد.

### ۵.الف. ساخت keystore اختصاصی انتشار (یک‌بار، روی سیستم خودتان)
```bash
keytool -genkeypair -v -keystore mp-release.p12 -storetype PKCS12 \
  -alias mp-release -keyalg RSA -keysize 2048 -validity 10000
# رمز عبور را امن نگه دارید؛ این فایل را هرگز commit نکنید.
base64 -w0 mp-release.p12 > mp-release.p12.b64
keytool -list -v -keystore mp-release.p12 -alias mp-release | grep SHA256
```

### ۵.ب. تنظیم اسرار و متغیر در GitHub
| نام | نوع | مقدار |
|---|---|---|
| `MP_ANDROID_KEYSTORE_BASE64` | secret | محتوای `mp-release.p12.b64` |
| `MP_ANDROID_STORE_PASSWORD` | secret | رمز keystore |
| `MP_ANDROID_KEY_ALIAS` | secret | `mp-release` |
| `MP_ANDROID_KEY_PASSWORD` | secret | رمز کلید |
| `MP_ANDROID_CERT_SHA256` | variable | اثرانگشت SHA-256 از مرحلهٔ بالا |

از **Settings → Secrets and variables → Actions** در مخزن استفاده کنید، یا با `gh secret set` و `gh variable set`.

### ۵.ج. اجرای ساخت
```bash
gh workflow run apk.yml --ref main -f build_number=<شماره>
gh run watch
```
خروجی APK در artifacts همان run است. `MP_ANDROID_CERT_SHA256` باید با اثرانگشت keystore یکی باشد؛ در غیر این صورت job شکست می‌خورد.

## ۶. انتشار نسخهٔ وب
`mp-web` روی هر push به `main` اجرا می‌شود و artifact `muscleparadise-web` تولید می‌کند.
برای میزبانی، پوشهٔ `build/web` را روی سرور استاتیک یا GitHub Pages قرار دهید.

## ۷. عیب‌یابی
- **`flutter pub get` شکست می‌خورد:** دسترسی به `pub.dev` را بررسی کنید.
- **`flutter build web` شکست می‌خورد:** خطا را در annotation همان job ببینید؛ ماژول‌هایی مثل `dart:io` در وب مجاز نیستند.
- **APK با خطای کلید:** مقدار `MP_ANDROID_CERT_SHA256` و رمزهای secret را دوباره بررسی کنید.
