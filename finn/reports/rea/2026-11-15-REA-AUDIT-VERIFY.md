# REA — M53 / بازبینی ابزار و تأیید ممیزی قبلی

- تاریخ: ۲۰۲۶-۱۱-۱۵
- ابزار: REA **v6.9.0** (npm `rea-agents`)، Node پرتابل ۲۴.۲۲.۳
- هدف: `mp-app/client/release/app-arm64-v8a-release.apk`
- sha256 هدف: `2ab56399ad4a6d82edf0880593a08fc210afb4e96f72d368becd7500f6c04098`
- پروندهٔ کامل شاهد: `finn/reports/rea/2026-11-15-studio-js-analysis.json` و `apk-inventory.json`

---

## ۰. یک ناسازگاری مهم در شواهد قبلی

`finn/reports/rea/identify-flutter-build.json` (کامیت‌شده) هش APK را
`fba3e666526942ebfce98a1d83672038613e9cd3ed7e5b2a4655d671b5dee479` ثبت کرده،
در حالی که APK موجود در مخزن (و در ریلیز `v0.2.0-client3`) هش
`2ab56399ad4a6d82edf0880593a08fc210afb4e96f72d368becd7500f6c04098` دارد.

**تفسیر (inference):** APK پس از آن ممیزی دوباره ساخته شده (build `edfa16c` / run `43690917759`)
و شاهد قدیمی روی نسخهٔ قبل است. **نادانسته:** آیا رفع R1/R2/R3 در نسخهٔ *منتشرشده* هست یا نه.

→ بنابراین ادعای «R1/R2/R3 رفع‌شده» بدون بررسی مجدد، قابل اتکا نبود؛ در بخش ۲ دوباره سنجیده شد.

---

## ۱. مشاهدات (observation) — روی APK واقعی

| # | مشاهده | Evidence |
|---|---|---|
| 1 | `flutter_detected: true` · ABI: `arm64-v8a` · `dart_version: 3.14.0 (stable)` · `libapp.so` ۶٬۴۸۹٬۰۴۸ بایت · `coverage: partial` | `ev_2177d1bb…` |
| 2 | امضای APK خوانده شد؛ فهرست طرح‌ها (v1/v2/v3) و اثر انگشت گواهی موجود است | `ev_c3690c04…` |
| 3 | موجودی آرتیفکت: ۳۲۷ گره، ۳۷۸ عضو، ۳۷۷ یال، `integrity_contradictions: 0`، `source_complete: true` | `ev_d9ff046c…` → `ev_ec3f3a79…` |
| 4 | بدون هیچ موتور native هم تحلیل انجام می‌شود (بدون Ghidra/Hopper/IDA) | — |

## ۲. تأیید ممیزی قبلی روی APK فعلی (با پارسر مستقل)

پارسر مانیفست دودویی (`pyaxmlparser` در venv جدا) روی همان APK:

| ادعای `REA-AUDIT.md` | نتیجهٔ واقعی روی APK فعلی | حکم |
|---|---|---|
| R1: `INTERNET` به مانیفست release اضافه شد | `permissions: [...INTERNET]` — **موجود** | ✅ تأیید شد |
| R2: `networkSecurityConfig` اضافه شد | `networkSecurityConfig: @7F100001` (رفرنس منبع XML) + فایل `network_security_config.xml` در سورس | ✅ تأیید شد |
| R3: `allowBackup="false"` | `allowBackup: false` | ✅ تأیید شد |
| سخت‌شدگی: `debuggable=false` | `debuggable: None` — یعنی صفت در مانیفست نیست. مقدار پیش‌فرض AAPT/AGP در build release `false` است اما **در مانیفست اثبات نشده** | ⚠️ **inference، نه observation** |
| بسته/نسخه | `ir.muscleparadise.mp_client` · `versionName 0.1.0` · `versionCode 2021` · minSdk 24 · targetSdk 36 | ✅ |

**یافتهٔ جدید (گپ واقعی):** `versionName = 0.1.0` در حالی که گیت‌هاب ریلیز `v0.2.0-client3` است.
شمارهٔ نسخهٔ داخلی APK با نسخهٔ ریلیز هم‌خوان نیست → برای کاربر و برای پشتیبانی، نسخهٔ نصب‌شده قابل تشخیص نیست.
→ پیشنهاد: `version:` در `pubspec.yaml` با تگ ریلیز همگام شود (در `ci_apk.sh` یا workflow `apk.yml`).

**یافتهٔ جدید ۲:** `usesCleartextTraffic` صریحاً ست نشده؛ سیاست از `networkSecurityConfig` می‌آید که
`base-config cleartextTrafficPermitted="true"` دارد — یعنی **تمام** ترافیک HTTP مجاز است، نه فقط LAN.
ادعای کامنت فایل («فقط سرور محلی») با محتوای واقعی فایل هم‌خوان نیست.
→ پیشنهاد: `domain-config` برای بازه‌های LAN (`192.168.0.0/16`, `10.0.0.0/8`, `172.16.0.0/12`, `localhost`) و `base-config` روی `false`.

## ۳. تحلیل استودیو (JavaScript/Electron)

`analyze-javascript-application mp-app/studio` → ۳۹ فایل، باندل کامل:

| مشاهده | مقدار |
|---|---|
| پنجرهٔ مرورگر / preload / context bridge | ۱ / ۱ / ۱ |
| ارجاع‌های IPC (renderer↔main) | **۰** |
| APIهای افشاشده روی `window` | فقط `mpStudio.version` |
| `nodeIntegration` / `contextIsolation` | `false` / `true` (از سورس `main.cjs`) |

**استنباط:** معماری امنیتی درست است (contextIsolation روشن، nodeIntegration خاموش، سطح افشا حداقلی).
**نادانسته:** هیچ مسیر IPC وجود ندارد، پس هر قابلیت «بومی» آینده (پرینتر، فایل، آپدیت) باید کانال جدید بسازد — با `sender` validation.

---

## ۴. اقدام‌های پیشنهادی (برای M45/M46)

- [ ] همگام‌سازی `versionName` با تگ ریلیز در `apk.yml`
- [ ] محدودکردن `cleartextTrafficPermitted` به بازه‌های LAN با `domain-config`
- [ ] `android:debuggable="false"` را صریح در مانیفست release بنویس (تا observation شود، نه inference)
- [ ] افزودن `audit-release-exposure` روی APK به چک‌لیست انتشار (بررسی نبود source map / symbol / secret)
- [ ] بازسازی `finn/reports/rea/*.json` قدیمی روی APK فعلی (هش‌ها به نسخهٔ قبل تعلق دارند)
