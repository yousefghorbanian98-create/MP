# وضعیت M60 — بستن آیتم‌ها با شاهد

- تاریخ: ۲۰۲۶-۱۱-۱۶
- شاخه: `arena/86fc9529-mp`
- قاعده: هر ادعا یا شاهد دارد (تست/CI/curl) یا برچسب **«بازبینی دستی»** می‌خورد.

## جدول

| # | آیتم | وضعیت | شاهد |
|---|---|---|---|
| R3 | پنهان‌کردن کارهای غیرمجاز از نقش | **انجام شد** | `security/rbac.py` (DENY برای reception روی مالی)، `lib/roleNav.ts`، ۱۳ تست studio + ۱۴ تست parity بک‌اند، اثبات زنده: ۴۰۳ |
| R4 | تسویهٔ سفارش پس از پرداخت درگاه | **انجام شد** | `payments/service._settle_shop_order`، ۳ تست idempotency/بدون‌احیای لغو‌شده، CI سبز |
| R5 | رسید سفارش | **انجام شد** | `GET /shop/orders/{id}/receipt`، ۴۵ تست shop، اثبات زنده (۲۰۰ صاحب / ۴۰۳ عضو دیگر / ۲۰۰ کارمند) |
| R6 | انیمیشن حرکت (GIF) | **انجام شد** | ۱۷ GIF از دو فریم، `gif_url` در API، مصرف‌کننده در ExerciseLibrary، ۳ تست studio + ۲ تست بک‌اند، اثبات زنده (۲۰۰ `image/gif`) |
| R8 | گیت استقرار ایستا | **انجام شد** | `deploy_gate.py` ۹ بررسی/۰ تناقض + باگ واقعی `MP_JWT_SECRET`→`MP_SECRET_KEY` |
| R18 | DAST | **انجام شد** | `evidence/m60/dast.json` — ۱۰۲۴ درخواست، ۱۲۸ عملیات، ۰ یافته |
| — | بازرسی APK با apktool | **از «مسدود» به «انجام شد»** | `res-*.json` برای ۳ ABI، `coverage: complete`، ۴۷۳ فایل |
| — | بازرسی APK در CI | **انجام شد** | اجرای ۴۳۸۲۹۶۷۱۰۵۰: مرحلهٔ `Deep APK audit (apktool)` سبز، APK تحویل داده شد |
| — | JADX (`inspect-android-package`) | **مسدود (دقیق)** | JAR پیدا شد؛ مانع `jdk.compiler` است و `jdk4py` فقط JRE است؛ همهٔ میزبان‌های JDK مسدود |

## دو باگ تولیدی که در همین بازبینی پیدا شد

**۱) `android:debuggable="false"` در سورس مانیفست.** من در M45 اضافه کرده بودم
تا یک مشاهدهٔ REA («debuggable صریح نیست») را ببندم. Android Lint آن را
`HardcodedDebugMode` می‌داند و `lintVitalRelease` بیلد release را می‌شکند.
اجرای ۴۳۸۲۸۴۵۴۰۲۱ به همین دلیل شکست. یعنی آن «سخت‌کردن» اپ را امن‌تر نمی‌کرد،
انتشار را متوقف می‌کرد. حذف شد؛ صحت روی **مانیفست کامپایل‌شده** بررسی می‌شود
(`apk_deep_audit.py` + `apk_audit.py`)، نه روی سورس.

**۲) ابزار بازرسی خودم دروغ می‌گفت.** `exported_activities` خالی برمی‌گشت
در حالی که `exported_components = 2` بود؛ regex فرض داشت `android:name` پیش از
`android:exported` می‌آید و در مانیفست واقعی برعکس است. حالا با پارس XML و
بدون فرض ترتیب، و علاوه بر فهرست، «exported بدون `android:permission`» را
یافته می‌داند (به‌جز activity لانچر).

## سرمایه‌گذاری روی گیت‌ها (تا این باگ‌ها برنگردند)

| گیت | چه چیزی را نگه می‌دارد | تست |
|---|---|---|
| `deploy_gate.py` | پورت/env تکراری، نام متغیر ناهم‌خوان با Settings | ۴ |
| `manifest_gate.py` | `debuggable`/`testOnly` در سورس، `allowBackup`، `--` در کامنت XML | ۶ |
| `apk_deep_audit.py` | مانیفست کامپایل‌شده، راز/URL عمومی در `libapp.so`، exported بی‌محافظ | ۱۹ |
| `dart_gate.py` | الگوهای خطرناک دارت | ۷ |
| `roleNav` + parity | هم‌خوانی منوی استودیو با RBAC سرور | ۲۷ |

## آمار نهایی گیت‌ها

- بک‌اند: **۷۷۸ passed / ۱ skipped** (`-p no:randomly`)، `ruff check` و `ruff format --check` پاک (۲۹۴ فایل)
- استودیو: **۱۷۹ passed / ۹ skipped**، `tsc --noEmit` بدون خطا
- CI: `a14ca52` → همهٔ ۶ جاب سبز
- APK: `43829671050` → بیلد + بازرسی + تحویل، همه سبز
