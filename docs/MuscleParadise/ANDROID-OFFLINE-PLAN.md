# برنامهٔ اندروید/آفلاین (M86–M88) — قرارداد outbox و APK

وضعیت: **M86 قرارداد محدود و fail-closed؛ M87 پیاده‌سازی کلاینت جداگانه**. M28 سند تاریخیِ طرح کلی بود و ادعای پیاده‌سازی صف برای همهٔ عملیات نداشت.

## ۱. Offline outbox — دامنهٔ مجاز

### ۱.۱ فقط بازخورد ساختاریافتهٔ تمرین

صف فقط برای `POST /programs/sync/set-feedback` است؛ این endpoint از قبل مالکیت عضو و LWW را سمت سرور بررسی می‌کند. در M87 فقط این فیلدها قابل صف‌اند: `program_id`, `movement_id`, `weight`, `target_reps`, `reps_done`, `rir`, `updated_at`, `device_id`, `client_id`.

- `member_id` فقط از نشست احرازشدهٔ جاری می‌آید؛ هر آیتم با همان owner ذخیره و فقط در همان نشست ارسال می‌شود. کلاینت حق انتساب آیتم به شناسهٔ عضو آزاد را ندارد.
- `device_id` تصادفی و پایدار برای نصب؛ `client_id` شناسهٔ یکتا برای همان رکورد. هر retry باید دقیقاً همان شناسه‌ها و `updated_at` را نگه دارد تا retry روی سرور قابل تشخیص باشد.
- note آزاد (`notes`)، soreness/درد، ارزیابی پزشکی و هر دادهٔ زیستی/چهره در outbox آفلاین قرار نمی‌گیرد. این محدودیت فقط مسیر آفلاین است و قرارداد آنلاین API را تغییر نمی‌دهد.
- **هیچ عملیات عمومی دیگری صف نمی‌شود:** ثبت/ویرایش عضو، ترکیب بدن، رزرو کلاس، check-in/QR/face، غذا، چت، پروفایل/OTP، عکس/رسانه و همهٔ پرداخت/کیف‌پول فقط آنلاین‌اند. HTTP 200 یا optimistic UI بدون رکورد پایدار و server ack موفقیت محسوب نمی‌شود.
- fallback به outbox فقط وقتی Android نبودِ شبکهٔ فعالِ دارای `NET_CAPABILITY_INTERNET` را گزارش کند مجاز است. اگر شبکه هست اما درخواست API timeout/5xx می‌دهد، نتیجه ممکن است پس از commit گم شده باشد؛ کلاینت آن را خودکار دوباره صف نمی‌کند و هشدارِ نتیجهٔ نامشخص می‌دهد تا رکورد تکراری نسازد.

### ۱.۲ ذخیره، ترتیب و پاک‌سازی

ذخیره‌ساز فقط برای Android در DB خصوصی برنامه و با `android:allowBackup="false"` است؛ web/PWA فقط online است. رمزنگاری application-layer/SQLCipher نداریم و کد این پروژه سیاست encryption خود دستگاه را اندازه‌گیری/تضمین نمی‌کند. بنابراین `MP_ANDROID_OFFLINE_FEEDBACK_ENABLED` در build پیش‌فرض `false` است؛ فقط build آزمون/مدیریت‌شده‌ای که سیاست رمزنگاری دستگاه جداگانه احراز شده باشد می‌تواند آن را صریحاً فعال کند. access/refresh token هرگز در صف ذخیره نمی‌شود. payload فقط allowlist بالا را دارد؛ response خام، متن free-form و credential در DB/log ذخیره نمی‌شود.

```sql
CREATE TABLE sync_queue (
  id INTEGER PRIMARY KEY,
  owner_member_id INTEGER NOT NULL,
  client_id TEXT NOT NULL,
  device_id TEXT NOT NULL,
  program_id INTEGER,
  movement_id TEXT NOT NULL,
  weight REAL NOT NULL,
  target_reps INTEGER NOT NULL,
  reps_done INTEGER NOT NULL,
  rir REAL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  status TEXT NOT NULL, -- pending | retry | conflict | failed | synced
  attempts INTEGER NOT NULL DEFAULT 0,
  next_attempt_at TEXT,
  last_error_code TEXT,
  synced_at TEXT,
  UNIQUE(owner_member_id, device_id, client_id)
);
```

آیتم‌ها با `created_at,id` FIFO و حداکثر 100تایی ارسال می‌شوند (API سقف 500 دارد). هیچ آیتمی پیش از ack معتبر server حذف نمی‌شود؛ `synced`های قدیمی را می‌توان پس از 30 روز پاک کرد. هر تلاش foreground برای sync، خطای شبکه/5xx را با backoff نمایی (شروع 30 ثانیه، سقف 6 ساعت) ثبت می‌کند؛ ارسال بعدی فقط با اقدام کاربر از دکمهٔ sync و پس از `next_attempt_at` ممکن است. پس از 5 شکست، وضعیت `failed` می‌شود و کاربر می‌تواند retry دستی بزند. worker/background sync وجود ندارد؛ با بازگشت شبکه، کاربر از دکمهٔ آشکار «همگام‌سازی با سرور» اقدام می‌کند.

### ۱.۳ پاسخ، تعارض و هویت نشست

- `accept`/winner=client و پاسخ صریح `unchanged_keys` یعنی ack قابل ثبت؛ فقط آن آیتم‌ها `synced` می‌شوند.
- `reject_stale`, `reject_clock_skew`, winner=server یا پاسخ نامفهوم به `conflict` می‌رود؛ payload محلی نگه‌داری و علت/کد محدود به کاربر نمایش داده می‌شود. هیچ نسخه‌ای بی‌صدا دور ریخته نمی‌شود و retry کلید/زمان تازه نمی‌سازد.
- 401/403 sync را متوقف و ورود/مالکیت را دوباره می‌خواهد؛ هرگز با account دیگر ارسال نمی‌شود. خروج/تغییر شماره در صورت وجود صفِ حل‌نشده نیازمند انتخاب صریح است: نگه‌داشتن صفِ همان owner برای ورود مجدد، یا حذف صریح و برگشت‌ناپذیر همان صف؛ حساب دیگر صف را نمی‌بیند و نمی‌تواند ارسالش کند. هیچ payload به owner تازه منتقل نمی‌شود.
- UI وضعیت pending/conflict/failed و «تلاش دوباره» را نشان می‌دهد؛ پیام «همگام شد» فقط پس از ack سرور.

### ۱.۴ آزمون‌های اجباری

- M87: write→restart→read، retry پس از قطع/وصل، duplicate با همان idempotency identity، خطای auth بدون ارسال به owner دیگر، server ack/conflict و logout/delete با تأیید.
- M88: دو outbox/device با یک member و رکورد مشترک، ترتیب timestamp و tie-break واقعی `sync_lww.py`; conflict در هر دو client قابل مشاهده، بدون ادعای sync دو دستگاه از API-only.
- اگر SQLite/plugin unavailable باشد، queue feature disabled/error صریح می‌شود؛ عملیات آنلاین موجود ادامه دارد.

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
