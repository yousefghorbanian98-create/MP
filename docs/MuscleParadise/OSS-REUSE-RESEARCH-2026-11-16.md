# گزارش بررسی منابع OSS برای TODO — با روش REA

- تاریخ بررسی: ۲۰۲۶-۱۱-۱۶ (UTC)
- شاخه: `arena/4f336f66-mp`
- دامنهٔ مرجع: `docs/MuscleParadise/TODO-2026-11-16.md`
- نوع کار: پژوهش و بازبینی ایستا؛ **هیچ feature، dependency، migration، test، build یا تنظیمی اجرا/اعمال نشد.**

## ۱. محدودیت پوشش و روش

منظور از «کل نت» در این محیط به‌معنای واقعی قابل‌اجرا نیست: دسترسی خروجی فقط به GitHub (`github.com`/`api.github.com`/`codeload.github.com`)، npm و PyPI محدود است. در نتیجه این گزارش، جست‌وجوی نظام‌مند در همین مخازن مجاز است؛ نه ادعای جست‌وجوی همهٔ وب. به `pub.dev`، Codeberg، سایت‌های ناشر، مخزن‌های دادهٔ خارج از GitHub و وب عمومی دسترسی نداشتم. برای Flutter، metadata و sourceهای GitHub بررسی شدند، نه امتیاز/صفحهٔ package در pub.dev.

طبق `docs/MuscleParadise/REA-OPERATIONS.md`، فقط source رقبا/پروژه‌های متن‌باز مجاز بود؛ APK یا باینری رقیب بسته بررسی/دیکامپایل نشد. آن راهنما هم برای source یک پروژهٔ OSS، بررسی کد معمول را به‌جای reverse engineering باینری توصیه می‌کند. در این sandbox فایل اجرایی REA و Node پرتابلِ معرفی‌شده در آن راهنما حاضر نبودند؛ پس **هیچ REA CLI run یا Evidence ID ماشینی تولید نشده است**. این یک desk audit از README، درخت فایل، manifest/pubspec، license و metadataهای مجاز است؛ «اجرای REA» یا «اعتبارسنجی integration» ادعا نمی‌شود.

## ۲. قید تعیین‌کنندهٔ مجوز

مجوز ریشهٔ MP در `LICENSE`، نرم‌افزار را proprietary و بازتوزیع source/binary را محدود می‌کند. بنابراین «رایگان» به‌تنهایی به‌معنی «مجاز برای واردکردن در MP» نیست:

- **نامزد مناسب برای بررسیِ افزودن dependency یا اقتباس محدود:** MIT، BSD-2/3، Apache-2.0 و Unlicense؛ با حفظ notice/copyright، ثبت در `NOTICE-THIRD-PARTY.md` و بررسی مجوز dependencyهای تو‌در‌تو.
- **مستقیماً وارد proprietary نکن:** GPL/AGPL. می‌توان رفتار و نیازمندی محصول را مطالعه کرد، ولی کپی/ادغام source یا وابستگی آن برای محصولی با این مجوز نیازمند تصمیم حقوقی و تغییر مجوز است.
- **داده، عکس و model weights مجوز مستقل دارند.** MIT بودن برنامهٔ میزبان، مجوز دیتاست یا وزن مدل را MIT نمی‌کند. نامشخص/بدون مجوز = فعلاً وارد نشود.

## ۳. نتیجهٔ اجراییِ جست‌وجو: چه چیزی واقعاً آمادهٔ reuse است؟

### نامزدهای محدود و مشخص

| موضوع | منبع و مجوز مشاهده‌شده | تصمیم، بدون اجرا |
|---|---|---|
| اسکن QR برای S5 | [`mobile_scanner`](https://github.com/juliansteenbakker/mobile_scanner)، BSD-3-Clause؛ manifest فعلی v7.5.0، Flutter ≥3.29 و Dart ≥3.7 | **بهترین نامزد dependency مستقیم** برای camera/QR UI؛ فقط QR را می‌خواند. احراز actor، عضویت، مالکیت، expiry، replay و ثبت خروج را حل نمی‌کند. باید با mirror/CI روی نسخهٔ دقیق Flutter تأیید شود. |
| اعلان محلی S3 | [`flutter_local_notifications`](https://github.com/MaikuB/flutter_local_notifications)، license فایل package از نوع BSD-3؛ v23.0.2 در source نیازمند Flutter ≥3.44 است | گزینهٔ واقعی برای زمان‌بندی/نمایش اعلان روی دستگاه، نه صفحهٔ inbox، دریافت `/notifications/member/{id}`، read-state یا push server. نسخهٔ دقیق با Flutter CI پروژه تطبیق داده نشده؛ compatibility را پیش از انتخاب بررسی کنید. |
| نمودارهای عضو M1/M2/M3/M5 | [`fl_chart`](https://github.com/imaNNeo/fl_chart)، MIT؛ v1.3.1، Dart ≥3.6.2 و Flutter ≥3.27.4 | dependency مناسب برای line/bar/radar/chart در Flutter. **فقط rendering** است؛ readiness، حجم، TDEE، دسترسی API، متن توضیحی و دادهٔ JP7 همچنان از MP می‌آیند. |
| رسید M6 | [`pdf`](https://github.com/DavBfr/dart_pdf)، Apache-2.0؛ v3.13.1 نیازمند Dart ≥3.12 | موتور ساخت PDF نامزد مناسبی است؛ endpoint، ownership، قالب رسید ریالی، فونت فارسی/RTL، ذخیره/اشتراک/چاپ و تست UI را آماده نمی‌کند. rendering فارسی باید جداگانه بررسی شود. |
| ثبت عکس پروفایل/پیشرفت G5/G9 | dependency فعلی MP یعنی `image_picker` از قبل در `mp-app/client/pubspec.yaml` هست | **نیازی به افزودن package انتخاب عکس نیست.** این فقط انتخاب عکس است؛ upload امن، سقف اندازه، رضایت، storage، حذف، URL غیرقابل‌حدس و سیاست نگهداری باید از MP بیایند. |
| haptic UX-G3 | `HapticFeedback` داخل Flutter SDK (`services.dart`) است | package دیگری لازم نیست؛ مورد، چند فراخوانی محدود + تست method-channel است، نه کد آمادهٔ بیرونی. |
| persistence برای Q4 | [`drift`](https://github.com/simolus3/drift)، MIT، SQLite محلی | می‌تواند **لایهٔ محلی/outbox** باشد، نه sync/conflict solution. خود پروژه آن را قبلاً از `pubspec` حذف کرده چون مصرفی نداشت؛ فقط اگر طرح Q4 و schema/test روشن شد دوباره بررسی شود. |
| full sync برای Q4/Q8 | [PowerSync Dart SDK](https://github.com/powersync-ja/powersync.dart) و [PowerSync Service](https://github.com/powersync-ja/powersync-service) مجوز Apache-2.0 دارند؛ service README منبع‌های PostgreSQL، MongoDB، MySQL و SQL Server را معرفی می‌کند | OSS واقعی و ارزشمند برای **مطالعهٔ معماری**، اما drop-in نیست: MP روی SQLite/SQLAlchemy و API/LWW خودش است؛ PowerSync منبع SQLite فعلی را به‌عنوان upstream نشان نمی‌دهد و به service/config و تغییر مسیر sync نیاز دارد. مهاجرت DB/بازطراحی از دامنهٔ «فقط افزودن dependency» بیرون است. «کاملاً رایگان» بودن deployment/hosting در این بررسی ارزیابی نشد؛ self-host هم هزینهٔ زیرساخت دارد. |
| اسکن secret برای SEC-01 | [`gitleaks`](https://github.com/gitleaks/gitleaks)، MIT | ابزار متن‌باز مناسبی برای گیت/CI و کشف secret در history است؛ **secret را revoke/rotate نمی‌کند** و پاک‌کردن یک فایل از HEAD، تاریخچهٔ عمومی را بی‌اثر نمی‌کند. |
| تست دستگاهی Q3/S5 | [`Maestro`](https://github.com/mobile-dev-inc/Maestro)، Apache-2.0؛ [Appium](https://github.com/appium/appium)، Apache-2.0 | می‌توانند سناریوی UI را خودکار کنند، اما گوشی/دوربین واقعی را فراهم نمی‌کنند و یک تست روی emulator اثبات عملکرد دوربین دستگاه واقعی نیست. این‌ها ابزار تست‌اند، نه feature قابل‌ادغام در اپ. |
| آزمون قرارداد API/S1 | [`Schemathesis`](https://github.com/schemathesis/schemathesis)، MIT | برای تولید آزمون از OpenAPI مفید است؛ **جایگزین گیت «endpoint واقعاً از UI مصرف می‌شود» نیست**. Source-map چندزبانهٔ Flutter/Studio و دنبال‌کردن call واقعی هنوز به گیت/AST پروژه نیاز دارد. |
| OTP برای D8 | [`react-otp-input`](https://www.npmjs.com/package/react-otp-input)، MIT، npm metadata نسخهٔ 3.1.1 و آخرین تغییر ۲۰۲۳-۱۲-۱۲ را نشان می‌دهد | فقط کنترل ورودی رقم OTP است، نه صفحهٔ ورود، درخواست OTP، خطاها، token storage، refresh یا RBAC. چون کنترل ساده است و dependency نسبتاً قدیمی است، نامزد مستقیم قوی نیست. |
| مدیریت کاربر FastAPI | [`fastapi-users`](https://github.com/fastapi-users/fastapi-users)، MIT | به‌دلیل مدل auth/session خودش، با OTP، مدل User/Member، Casbin، scope مالکیت و tokenهای MP یکی نیست؛ واردکردنش می‌تواند به‌جای حل D8/D9/D10، تعویض معماری auth شود. |
| تست API backend | [`Schemathesis`](https://github.com/schemathesis/schemathesis)، MIT | ممکن است در آینده برای contract/fuzz سمت سرور مفید باشد؛ به مصرف‌کنندهٔ Flutter/Studio و gate استثناهای API وصل نمی‌شود. این پیشنهاد فعلاً فقط ارزیابی است. |

### رقبای متن‌باز مجاز برای مطالعهٔ source

| پروژه | آنچه از GitHub خوانده شد | حکم reuse |
|---|---|---|
| [`wger`](https://github.com/wger-project/wger) | self-hosted؛ تمرین، غذا/وزن، عکس پیشرفت، API و قابلیت‌های پایهٔ باشگاه؛ مجوز **AGPL-3.0** | مرجع غنی برای جریان محصول/واژگان و آزمون نیازمندی؛ **source آن را به MP proprietary کپی/لینک نکنید**. دادهٔ Open Food Facts هم مجوز جدا دارد. |
| [`FitTrackee`](https://github.com/SamR1/FitTrackee) | mirror مجاز GitHub از پروژهٔ Codeberg؛ tracker فعالیت بیرونی، media و تاریخچهٔ امنیت/JWT؛ مجوز **AGPL-3.0**. changelog mirror نسخهٔ 1.3.7 در ۲۰۲۶-۱۰-۳۱ را نشان می‌دهد. | فقط مطالعهٔ الگوها؛ محصول باشگاه نیست و AGPL با واردکردن source به MP سازگارِ بی‌قید نیست. دسترسی مستقیم به Codeberg در این محیط نداشتم. |
| [`GymOS`](https://github.com/maxlevels-ae/gymos) | ERP باشگاه با عضویت/تمدید/QR/دسترسی و چند PWA؛ Express/SQLite؛ مجوز **GPL-3.0** | از نظر فهرست قابلیت، مرجع خوبی برای G6/G10/S5 است؛ **کد قابل‌کپی برای MP نیست** به‌علت GPL، علاوه بر تفاوت stack. |
| [`Fitness360 / Gymkhana`](https://github.com/gymkhana-fitness-360/gymkhana) | Apache-2.0؛ Next.js/Prisma/PostgreSQL؛ README/parity شامل members, renewals, payment, attendance/QR و profile photos؛ changelog نسخهٔ 0.2.0 در ۲۰۲۶-۰۷-۱۲ | مناسب‌ترین مرجع مدیریتی permissive در نتایج این بررسی؛ **کل سامانه drop-in نیست** (Node/Prisma، tenant model و routeهای خودش). می‌توان ایده/ماژول جدا را فقط پس از بررسی وابستگی، مرز license و ثبت NOTICE اقتباس کرد. این بررسی کیفیت/اجرای release را تأیید نکرد. |
| [`FitBook`](https://github.com/brandonp2412/FitBook) | اپ Flutter MIT با food diary، macro graphs، barcode، offline mode، Drift و test/integration-test؛ README می‌گوید دیتای ۷هزار غذا از CORGIS است. | **بهترین مرجع UI/flow برای M4** و شاید اجزای مستقل MIT؛ ولی app خودش backend MP نیست و معماری Drift/دادهٔ محلی متفاوت است. source آن را بدون dependency/data audit wholesale ادغام نکنید. |
| [`CORGIS`](https://github.com/corgis-edu/corgis) | GitHub API مجوز repository را **GPL-3.0** گزارش می‌کند؛ FitBook دیتای غذا را به این پروژه نسبت می‌دهد. | مجوز MIT کد FitBook، مجوز دیتای آن را تعیین نمی‌کند. فایل غذا را فعلاً به دیتابیس proprietary MP کپی نکنید؛ مجوز دقیق خود dataset لازم است. دیتای آمریکایی آن نیز جای پایگاه غذای ایرانی را نمی‌گیرد. |
| [`Open Food Facts server`](https://github.com/openfoodfacts/openfoodfacts-server) | کد سرور **AGPL-3.0**؛ پایگاه داده/داده مجوز مستقل دارد. | کد سرور برای ادغام در MP مناسب نیست. مجوز دقیق و شرایط استخراج dataset در این بررسیِ محدود به GitHub به‌طور مستقل تثبیت نشد؛ داده را هم بی‌بررسی وارد نکنید. این دیتابیس عمدتاً محصول/barcode است، نه جایگزین دستور/غذای ایرانی. |
| `GymOps` با همان نام | جست‌وجوی GitHub چند prototype کوچک/قدیمی یا بی‌مجوز روشن داد؛ یک نتیجهٔ MIT کم‌حجم، اما repoهای هم‌نام پراکنده‌اند. | نتایج به‌قدر کافی شناخته‌شده/مجزا نبودند تا «ماژول آماده» اعلام شوند. `GymOS` در ردیف جداست و نباید نام‌ها را یکی فرض کرد. |

## ۴. بررسی جداگانهٔ موضوع‌های TODO

در وضعیت، **جدول آغازین «پس از M61/M62» را مرجع فعلی** گرفته‌ام. بخش‌های تفصیلی پایین‌تر و صف هفته‌ای خود سند قدیمی‌اند؛ موارد D3–D7، S2 و D4/M5 چند تناقض/هم‌پوشانی دارند. هرجا اختلاف هست، آن را زیر «نیاز به تطبیق» گذاشته‌ام؛ از متن قدیمی وضعیت قطعی نمی‌سازم.

| شناسه و موضوع | وضعیت مرجعِ فعلی در TODO | نتیجهٔ جست‌وجوی OSS و حکم «قابل واردکردن؟» |
|---|---|---|
| **SEC-01 — Android signing key در history** | TODO آن را release blocker می‌نامد. | Gitleaks (MIT) فقط ابزار کشف/گیت است. هیچ OSS ابزاری نمی‌تواند کلید انتشار افشاشده را معتبر کند یا به‌جای مالک rotate کند. rotation/release strategy و history cleanup عملیاتی/محصولی‌اند؛ مقدار secret را در گزارش/خروجی بازنشر نکنید. |
| **SEC-02 — مالکیت/عضویت/replay در QR** | TODO شامل ادعای نتیجهٔ TestClient است، اما با قید کاربر تا بازتولید شاهد، یافته را قطعی نمی‌گیرم. | هیچ scanner/auth package‌ای semantics MP را حل نمی‌کند. Casbin در پروژه هست؛ actor↔subject، عضویت فعال، نقش پذیرش، nonce/replay و atomic idempotency باید با policy و regression tests خاص دامنه تعیین شوند. در این جست‌وجو تست/کد اجرا نشد. |
| **D1 — ثبت چهره/دکمهٔ 403** | وضعیت بالایی: دکمهٔ بی‌مصرف حذف/مجوز اصلاح شده؛ ثبت چهرهٔ واقعی هنوز ساخته نشده. | هیچ consent widgetی تشخیص/ثبت را حل نمی‌کند. برای مسیر QR از mobile_scanner استفاده می‌شود؛ اگر face واقعی انتخاب شد، باید model/runtime و data license جداگانه تأیید شوند. |
| **D2 — payload چهره/تشخیص واقعی** | بدنهٔ درخواست اصلاح شده؛ پاسخ 200 با `membership_expired` را نباید به face-match تعبیر کرد؛ خود تشخیص هنوز نیست. | `DeepFace` (MIT code), `CompreFace` (Apache-2.0), `face_recognition` (MIT) و InsightFace را دیدم. هیچ‌کدام را drop-in توصیه نمی‌کنم: runtime/embedding pipeline با Flutter و flow فعلی فرق دارد؛ weights/data/liveness/privacy جداگانه‌اند. InsightFace README صریحاً می‌گوید داده/مدل‌های آموزش‌دیده برای non-commercial research هستند و برای برخی recognition weights مجوز جدا می‌خواهد؛ برای استفادهٔ تجاری MP **رد** است مگر مجوز کتبی مدل گرفته شود. CompreFace آخرین pushی که API نشان داد ۲۰۲۴-۱۰-۰۵ است و مدل‌ها/عملیاتش باید جدا vet شوند. |
| **D3 — logout** | فعلی: logout در Flutter اضافه/تست شده، ولی Studio هنوز logout ندارد. شرح قدیمی پایین TODO می‌گوید هیچ‌جا نیست و superseded است. | ماژول آماده لازم نیست؛ UI/clear local tokens و فراخوانی مسیر موجود از معماری فعلی ساده‌تر و کم‌ریسک‌تر است. FastAPI Users را برای همین کار وارد نکنید. |
| **D4 — صفحهٔ body-composition/دادهٔ ساختگی** | جدول بالایی می‌گوید در M62 به endpoint روند JP7 وصل و تست کمبود داده اضافه شد. متن تشریحی پایین‌تر هنوز می‌گوید ۱۰۰٪ mock است. | برای rendering می‌توان از fl_chart استفاده کرد؛ package فرمول JP7، کیفیت اندازه‌گیری، API ownership یا صحت داده را نمی‌دهد. این D4 را «باز» اعلام نمی‌کنم؛ **تعارض متن قدیمی با وضعیت M62 باید در خود TODO اصلاح شود**. |
| **D5 — بنر تخفیف تولد/کوپن** | فعلی: بنر ساختگی با وضعیت واقعی عضویت جایگزین شده؛ S2 مرزی‌ها را بازبینی می‌خواهد. | کنترل بنر dependency نمی‌خواهد. Coupon (UX-G2) یک domain جداست؛ در search مجاز، ماژول آمادهٔ mature و license-compatible پیدا نشد. آزمون per-user/expiry/price freeze باید با مدل shop MP باشد. |
| **D6 — استثناهای API coverage** | فعلی: شاهد واقعی برای استثناها و تست منفی gate در M61 ثبت شده؛ شرح قبلی کاذب قدیمی است. | Schemathesis فقط API سرور را از OpenAPI آزمون می‌کند؛ گیت «source واقعی UI call می‌زند» را جایگزین نمی‌کند. برای S1 AST/call-graph مشخص پروژه لازم است. |
| **D7 — VolumePanel عضو انتخاب‌شده** | فعلی: در M61 از عضو انتخاب‌شده استفاده می‌کند و تست صفحه ثبت شده. | بستهٔ عمومی لازم نیست؛ state/selection متعلق به Studio است. این موضوع را از M2 (نمای حجم برای عضو اپ) جدا نگه دارید. |
| **D8 — ورود OTP در Studio** | باز. | React OTP input فقط رقم‌ها را نمایش می‌دهد؛ auth flow، اتصال endpoint، lockout، نقش‌ها و token lifecycle را نمی‌سازد. فرم با UI فعلی و API موجود، اقتباس کوچک است؛ dependency مستقل ارزش آشکاری ندارد. |
| **D9 — refresh نشست Studio** | باز. | FastAPI Users/کتابخانهٔ JWT موجود نمی‌تواند refresh route و سیاست revoke MP را بی‌هزینه جایگزین کند. استفاده از client/session موجود و تست هم‌زمانی refresh، راه fitتری است؛ این فقط ارزیابی است، نه پیشنهاد اجراشده. |
| **D10 — 401→refresh در Flutter** | پیاده‌سازی M62 اعلام شده، اما کد اصلاح‌شده هنوز mirror/CI validation می‌خواهد. | package تازه‌ای لازم نیست؛ `http` و client MP موجودند. آزمون را با mirror تأییدشده یا CI انجام دهید؛ این گزارش آن را اجرا نکرده و فقدان executable محلی را blocker محصول نمی‌نامد. |
| **S1 — گیت API consumption** | گیت فعلی برای جلوگیری از comment/string false-positive نیاز به گیت ساختاری دارد. | Schemathesis نامزد server contract است، نه این مسئله. AST/تحلیل call واقعی بین TS/Dart و `routes.json` باید در پروژه تعریف شود؛ package عمومی plug-in برای این قرارداد خاص پیدا نشد. |
| **S2 — تاریخ/وضعیت انقضای عضویت** | با D5 هم‌پوشان است: D5 می‌گوید وضعیت واقعی عضویت جای بنر آمده، S2 هنوز می‌گوید تاریخ انقضا دیده نمی‌شود. | library ندارد. پیش از انتخاب کد، معیار را دقیق کنید: «وضعیت فعال/منقضی» یا «تاریخ پایان و روزهای باقی‌مانده»؛ API/عضو فعلی خودش منبع است. |
| **S3 — اعلان‌های دیده‌نشده** | backend/Studio و `engine/reminders.py` هست؛ صفحه/مصرف عضو باز است. | flutter_local_notifications فقط لایهٔ local display/schedule است. inbox، unread count، mark-as-read و اتصال به API را باید MP بسازد. Push نیازمند provider/زیرساخت جداست و این plugin به‌تنهایی push server نیست. |
| **S4 — رضایت بیومتریک** | فعلی: متن/گرفتن رضایت در M61 نیمه‌پیاده؛ تولید embedding و مسیر چهره هنوز بسته است. متن قدیمی «هیچ مصرف‌کننده» را به‌روز کنید. | فرم رضایت قابل‌اقتباس از کد فعلی است؛ هیچ package عمومی جای متن consent، هدف استفاده، revoke، حذف بیومتریک و تصمیم حقوقی را نمی‌گیرد. |
| **S5 — scanner/exit کیوسک** | QR نمایش داده می‌شود، scanner/exit flow در TODO باز است. | `mobile_scanner` BSD-3 نامزد dependency مستقیم برای camera barcode/QR است؛ `/face/checkin-qr` باید سمت سرور امن شود و `/exit`/مدت حضور business logic خود MP است. |
| **M1 — readiness/fatigue در اپ عضو** | engine/API و `ReadinessPanel` در Studio؛ عضو مصرف ندارد. | fl_chart فقط نمودار است. trackerهای عمومی readiness که GitHub search نشان دادند بر دادهٔ ساعت/HRV/اپل/گارمین یا مدل دیگر تکیه دارند؛ معادل الگوریتم MP نیستند. چون خود MP engine دارد، واردکردن مدل بیرونی توجیه ندارد. |
| **M2 — weekly muscle volume در اپ عضو** | API و VolumePanel در Studio موجودند؛ نمایش عضو باز است؛ D7 اصلاح شده، این جداست. | fl_chart برای chart؛ محاسبه و متن «چرا» از API MP. ماژول کامل compatible پیدا نشد. |
| **M3 — adaptive nutrition در اپ عضو** | engine و Studio panel موجود؛ مصرف عضو باز است. | UI از FitBook می‌تواند الگو بگیرد، اما FitBook الگوریتم/TDEE MP نیست؛ fl_chart فقط graph. کد adaptive فعلی را تکرار نکنید. |
| **M4 — ثبت غذای عضو** | endpoints و Studio هست؛ عضو مصرف ندارد. | FitBook MIT بهترین مورد برای مشاهدهٔ flow و برخی widget patterns است، نه backend-ready integration. دیتای CORGIS را به‌دلیل مجوز GPL-3 repository و license مستقلِ نامعلومِ فایل data وارد نکنید. جست‌وجوی GitHub برای «Iranian/Persian nutrition database» دیتاست عددیِ تازه، معتبر و permissive نشان نداد؛ دیتای ایرانی موجود MP باید منبع باشد. |
| **M5 — نمودار روند JP7 عضو** | در جدول فعلی TODO هنوز باز است؛ D4 می‌گوید صفحه‌ای دادهٔ real می‌خواند. احتمالاً endpoint/صفحهٔ D4 با نمودار عضو M5 یکی نیست، اما متن crosswalk روشن نیست. | fl_chart مناسب rendering است. **پیش از reuse باید مشخص شود M5 چه چیزی اضافه می‌کند نسبت به D4/M62**؛ در غیر این صورت دوباره‌کاری مستند رخ می‌دهد. |
| **M6 — رسید سفارش عضو** | receipt endpoint ساخته شده، ولی مصرف‌کنندهٔ اپ در TODO باز است. | `pdf` Apache-2.0 نامزد generator؛ endpoint و permission را فراخوانی کنید، نه منطق رسید/قیمت را دوباره. فارسی/RTL/فونت و اشتراک‌گذاری، نیاز به تست جدا دارد. |
| **UX-G3 — haptics** | open در TODO. | Flutter SDK کافی است؛ reuse package اضافه ندارد. |
| **UX-G6 — attendance history عضو** | endpoint member-scoped و صفحه باز است؛ `/admin/checkins` جایگزین امنی برای آن نیست. | Fitness360/Gymkhana و GymOS برای الگوی حضور مرجع‌اند؛ no drop-in endpoint. Gymkhana permissive است ولی Next/Prisma؛ GymOS GPL-3. پیاده‌سازی باید scope عضو را در API MP enforce کند. |
| **UX-G7 — تغییر شماره/بازیابی حساب** | open؛ OTP دو شماره و باطل‌کردن نشست‌ها نیاز است. | FastAPI Users با auth مدل دیگری می‌آید؛ هیچ package آماده‌ای ownership OTP دو مرحله‌ای/phone uniqueness/refresh revocation MP را حل نمی‌کند. کد domain-specific. |
| **UX-G2 — coupon/discount** | open؛ Campaign/Offer قبلی مرده است. | در نمونه‌های gym OSS مورد بررسی featureها بیشتر campaign/reminder/renewal هستند؛ coupon engine سازگار با MP و gateway فعلی پیدا نشد. قیمت قفل‌شده و سقف per-user باید با shop MP تست شوند. |
| **UX-G5 — avatar** | open؛ آیکون ثابت. | `image_picker` از قبل موجود است؛ Gymkhana نمونهٔ profile-photo با Apache-2.0 دارد، ولی backend و storage Next/Prisma قابل‌کپی مستقیم نیستند. |
| **UX-G8 — personal record (PR)** | open. | FitTrackee در source mirror تاریخچه/رکورد ورزشی دارد، ولی AGPL-3 و outdoor semantics؛ نتایج 1RM trackerهای GitHub کوچک/بدون license روشن بودند. چون MP ست‌ها را ثبت می‌کند، PR قدرتی را نباید از رکورد عمومی دوچرخه/دویدن قرض گرفت. |
| **UX-G9 — progress photos** | open؛ تصمیم storage/retention لازم است. | wger gallery (AGPL-3) فقط مرجع رفتار است. `image_picker` در MP موجود است؛ import عکس/گالری wger نکنید. policy حذف، consent، access و log را باید MP تعیین کند. |
| **UX-G10 — auto-renew/renewal** | reminderها هست، خودکارسازی پرداخت/failed→past_due و idempotency open؛ gateway زنده merchant می‌خواهد. | GymOS GPL-3 و Gymkhana Apache-2.0 الگوی lifecycle می‌دهند، اما سرویس‌های payment/tenant مدل متفاوت دارند. هیچ package OSS merchant ID/Zarinpal recurring authorization فراهم نمی‌کند. Reminder ≠ auto-renew. |
| **N1 — لغو رزرو کلاس** | endpoint cancel در بک‌اند هست؛ مصرف‌کنندهٔ Flutter باز است. | package لازم نیست؛ call, confirmation, optimistic/error handling و invalidation باید به مسیر موجود وصل شوند. Gym management systems فقط flow مرجع‌اند. |
| **N2 — چت عضو** | API و Chat Studio هست؛ اپ عضو مصرف ندارد. | SDK چت جدید تکرار backend خواهد بود و به مدل MP نمی‌خورد. UI Flutter مصرف‌کنندهٔ API فعلی باید باشد؛ package لازم قطعی شناسایی نشد. |
| **P4 — R7, R9–R15, R17, R19** | متن اصلی در مخزن موجود نیست و خود TODO آن را نامعلوم می‌نامد. | تا توضیح هر شناسه را نداشته باشیم، جست‌وجوی feature-specific ممکن نیست؛ **حدس نمی‌زنم و موردی را حذف/ادغام نمی‌کنم**. |
| **P5 — JADX** | ابزار بررسی APK خودمان؛ JDK در shell نیست. | [`jadx`](https://github.com/skylot/jadx) مجوز Apache-2.0 دارد و source آزاد است؛ decompiler/tool است، نه کد MP. این گزارش آن را نصب/اجرا نکرد. مطابق D-022، برای binary رقیب بسته استفاده نمی‌شود. |
| **P5 — binary رقیب** | محدودیت صریح REA. | no reuse/search on proprietary APKs. فقط GitHub source رقبا در scope بود. |
| **P5 — APK/دوربین روی دستگاه واقعی** | سخت‌افزار واقعی در sandbox نیست. | Maestro/Appium test code را می‌دهند، نه device. این گزارش هیچ test اجرا نکرد؛ emulator/physical proof باید در مرحلهٔ مجاز و جدا باشد. |
| **P5 — Alembic روی mp.db** | مسئله به همان فایل DB و وضعیت migration آن وابسته است. | Alembic از قبل dependency MP است. هیچ external code آن DB را بی‌خطر migrate نمی‌کند؛ backup/DB identity/plan لازم است. من هیچ DB یا migration را باز/تغییر ندادم. |
| **P5 — درگاه live** | adapter MP و sandbox وجود دارد؛ merchant ID واقعی مانع بیرونی است. | PyPI نتیجه‌های `zarinpal`/`python-zarinpal` مجوز LGPLv3 اعلام می‌کردند؛ افزون بر حساسیت سازگاری مجوز، package جدید merchant credential تأمین نمی‌کند و adapter MP از قبل هست. واردکردن توجیه ندارد. |
| **P5 — مقایسهٔ LLM محلی** | adapter موجود؛ runtime/model در sandbox نیست. | [`Ollama`](https://github.com/ollama/ollama) code MIT دارد، اما weights هر مدل مجوز جدا دارند و بعضی research/non-commercial‌اند. runtime رایگان به‌معنی مدل آزاد/تجاری نیست؛ پیش از انتخاب باید مدل و مجوزش جداگانه غربال شود. |

## ۵. تناقض‌هایی که پیش از تصمیم reuse باید حل شوند

1. سرآغاز وضعیت پس از M61/M62، D3 تا D7 را به‌روز می‌کند؛ بخش قدیمی P0 پایین‌تر هنوز بعضی از همان‌ها را شکسته می‌خواند. صف اجرای هفتگی خود TODO هم صریحاً قدیمی است. این report وضعیت جدیدتر را ملاک گرفته و هیچ کار قدیمی را دوباره «باز» یا «تمام» اعلام نکرده است.
2. D4 می‌گوید صفحهٔ M62 از JP7 واقعی می‌خواند، درحالی‌که M5 هنوز می‌گوید هیچ API مصرف نمی‌شود. قبل از انتخاب chart package باید acceptance/route/صفحهٔ هر دو را جدا نام‌گذاری کرد.
3. D5 می‌گوید بنر به وضعیت واقعی عضویت وصل شد؛ S2 هنوز می‌گوید انقضا به عضو نمایش داده نمی‌شود. وضعیت فعال و تاریخ دقیق پایان دو معیار متفاوت‌اند.
4. شماره‌های G موجود در بنچمارک و ممیزی UX، موضوع‌های متفاوتی هستند. این گزارش از عنوان کامل موضوع استفاده می‌کند، نه شماره به‌تنهایی.
5. نام «open source» برای یک repo کافی نیست: license داده‌های FitBook/CORGIS، وزن مدل چهره و dependencyهای پروژهٔ Fitness360 جدا از مجوز source اصلی‌اند.

## ۶. حکم نهایی

- **چند dependency کوچک واقعاً قابل‌بررسی برای افزودن‌اند:** `mobile_scanner` برای S5، `fl_chart` برای نمودارهای عضو، `pdf` برای M6 و احتمالاً `flutter_local_notifications` برای نمایش local در S3. این‌ها فقط لایهٔ فنی‌اند؛ هیچ‌کدام business logic یا endpoint مصرف عضو را آماده نمی‌کنند.
- **برای M4 بهترین reuse کم‌ریسک، مطالعه/اقتباس محدود UI از FitBook است؛ نه واردکردن app/data کامل آن.** دیتاست غذا را جداگانه license-check کنید.
- **برای Q4/Q8**، Drift یک ذخیره‌ساز local است؛ PowerSync یک گزینهٔ معماریِ کامل‌تر ولی ناسازگار با SQLite/API فعلی بدون تغییر بزرگ است. هیچ‌کدام را «صف آماده» تلقی نکنید.
- **کد gym OSS پرقابلیت هم لزوماً قابل‌کپی نیست:** wger/FitTrackee AGPL و GymOS GPL هستند. Fitness360/Gymkhana Apache-2.0 permissive است، اما stack آن drop-in نیست.
- **برای face recognition، coupon, phone recovery, access/ownership/replay, auto-renew, class cancel, attendance scope و member chat، کد آمادهٔ مجاز و drop-in پیدا نشد.** در این موارد reuse یک library عمومی فقط بخش فنی کوچک را پوشش می‌دهد؛ منطق و تست باید متعلق به MP باشد.

### کارهای انجام‌نشده در این بررسی

- هیچ package نصب یا clone نشد؛ هیچ build/test/CI/curl/API زنده اجرا نشد.
- هیچ فایل کد، dependency manifest، TODO یا LICENSE تغییر نکرد؛ فقط همین گزارش جدید نوشته شد.
- GitHub/npm/PyPI نتیجه‌های metadata/source بودند؛ وجود repo/package به‌تنهایی کیفیت، امنیت، release fitness یا compatibility را اثبات نمی‌کند.
- قبل از هر استفادهٔ واقعی: license تمام فایل‌های کپی‌شده و assets/data/models، transitive dependencies، Flutter SDK توافق‌شده و CI/mirror، privacy/retention و تست integration باید جداگانه بررسی شوند.
