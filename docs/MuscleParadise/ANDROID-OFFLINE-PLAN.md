# برنامهٔ اندروید/آفلاین (M28) — مشخصات صف آفلاین و APK

وضعیت: **طرح مصوب + اسکریپت CI** — پیاده‌سازی Flutter در این سند (Flutter در سندباکس نصب‌نشدنی — D-002).
قرارداد API همین بک‌اند است (delta update از M20: همهٔ ماژول‌ها PATCH ساختاری می‌پذیرند).

## ۱. صف آفلاین (Offline-First Queue)

### ۱.۱ اصول
- **هر عمل کاربر** (ثبت عضو، ورود دادهٔ ترکیب بدن، رزرو کلاس، ثبت وعدهٔ غذایی…) ابتدا در SQLite محلی نوشته می‌شود (`status=pending`) — UI هرگز منتظر شبکه نمی‌ماند.
- **همگام‌سازی** در دو محرک: اتصال شبکه + هر ۶۰ ثانیه.
- **دلتا**: فقط رکوردهای `pending/failed` ارسال می‌شوند؛ درخواست‌ها `Idempotency-Key` (UUID محلی رکورد) دارند تا تکرار بی‌خطر باشد.
- **تعارض**: `updated_at` سرور > `updated_at` محلی ← سرور برنده؛ نسخهٔ محلی در `conflicts` جدول می‌ماند و به کاربر نمایش داده می‌شود (هرگز بی‌صدا حذف نشود).

### ۱.۲ طرح جدول (drift محلی)
```dart
// sync_queue(id INTEGER PK, entity TEXT, entity_id TEXT, method TEXT,
//            payload TEXT, idempotency_key TEXT UNIQUE,
//            status TEXT DEFAULT 'pending', attempts INT DEFAULT 0,
//            last_error TEXT, created_at, synced_at)
```
- `attempts ≥ 5` → `status=failed` + نمایش در «در انتظار همگام‌سازی» (UI) با دکمهٔ «تلاش دوباره».
- حذف داده: فقط soft-delete (`deleted=1`) همگام می‌شود؛ حذف فیزیکی از هر دو سو با تأیید صریح کاربر.

### ۱.۳ ترتیب همگام‌سازی
1. entity های مستقل (members, assessments) → 2. وابسته‌ها (programs) → 3. عملیات مالی (فقط آنلاین — در آفلاین disabled).
- پرداخت/شارژ کیف‌پول **هرگز صف نمی‌شود** (عملیات پولی حساس؛ فقط آنلاین).

## ۲. ساخت APK (CI)
اسکریپت `mp-app/client/ci_apk.sh`:
- `flutter pub get` → `flutter analyze --no-fatal-infos` → `flutter test` → `flutter build apk --release --split-per-abi`
- نسخه از `pubspec.yaml` + شمارهٔ build از متغیر CI (`BUILD_NUMBER`)
- artifact: `build/app/outputs/flutter-apk/app-arm64-v8a-release.apk` (دلتا: `flutter build appbundle` برای Play)

## ۳. ادغام در CI موجود
- job جدید در GitHub Actions: نیازمند `subosito/flutter-action` — در زمان فعال‌سازی به WORKFLOW اضافه می‌شود (کار ناتمام مستندشده).
- خروجی: APK در release + SHA256 در یادداشت انتشار (مانند handoff zip).

## ۴. پیامک (M28 — انجام‌شده در بک‌اند)
- `app/sms.py`: Adapter با ارائه‌دهندگان `dev | webmagfa | kavenegar` (تنظیم `sms_provider`).
- پاسخ OTP فقط در حالت `dev` شامل `dev_code` است؛ خرابی ارسال → خطا `sms_failed` (هرگز بی‌صدا قورت داده نشود).
