# دفتر تصمیم‌ها و پرسش‌های باز — ۲۰۲۶-۱۱-۲۳

> این دفتر **تصمیم‌های قبلیِ ثبت‌شده** را از برداشت کد و پیشنهادهای معماری جدا می‌کند. این فایل تصمیم تازه‌ای از جانب مالک نمی‌گیرد و هنوز به ADR رسمی تبدیل نشده است.

## ۱. وضعیت‌نامه

| برچسب | معنای دقیق |
|---|---|
| `OWNER-RECORDED` | مالک پیش‌تر در سند تصمیم/صف کار تصمیم را صریح ثبت کرده است؛ تأیید نمودار حاضر نیست. |
| `CODE` | در source/config جاری قابل مشاهده است؛ تضمین runtime یا پذیرش محصول نیست. |
| `TEST-REPORTED` | گزارش تحلیل ۲۰۲۶-۱۱-۲۳ اجرای سناریوی مشخص را ثبت می‌کند؛ suite در این نشست دوباره اجرا نشده است. |
| `PARTIAL` | کد/تست بخشی از رفتار را ثابت می‌کند، اما scope کامل یا E2E را نه. |
| `OPEN` | پاسخ/گزینهٔ انتخاب‌شده در شواهد نیست؛ برای تصمیم نهایی از مالک بپرسید. |
| `NOT-APPROVED` | سند قدیمی آن را پیشنهاد کرده، اما تأیید مالک برای جایگزینی محصول جاری وجود ندارد. |

## ۲. تصمیم‌هایی که قبلاً به مالک نسبت داده شده‌اند

| ID | موضوع و تصمیم ثبت‌شده | وضعیت اجرا/شواهد | شاهد و مرز ادعا |
|---|---|---|---|
| D-01 | **ثبت تاریخی baseline انتشار نخست (پیش از OQ-01):** Android برای عضو و پنل وب برای کارکنان؛ اپ کادر یا دسکتاپ اختصاصی لازم نیست. | `OWNER-RECORDED` + `CODE`; `SUPERSEDED_FOR_RELEASE_BASELINE_BY_OQ-01` | [TODO-CLOUD-FINANCE-ACCESS](../../TODO-CLOUD-FINANCE-ACCESS.md) و [ADR-007](../../adr/007-pwa-primary-release.md). از ۲۰۲۶-۱۱-۲۳ کلاینت اصلی انتشار اول PWA مشترک است؛ native حفظ می‌شود. این سابقه پیاده‌سازی PWA/مهاجرت را ثابت نمی‌کند. |
| D-02 | **محل اجرا:** سرور همان سرور محلی باشگاه؛ برای دسترسی عضو از بیرون یک ورودی HTTPS ارزان (VPS کوچک/tunnel) مدنظر است، نه «Full Cloud» به‌عنوان تصمیم انتشار اول. عملیات server-side در قطعی انجام نشود. | `OWNER-RECORDED`; provider/deployment باز | [TODO-CLOUD-FINANCE-ACCESS](../../TODO-CLOUD-FINANCE-ACCESS.md). دامنه، میزبان، TLS/tunnel، trusted proxy، HA، backup خارجی، restore و بار واقعی هنوز با اجرای production ثابت نشده‌اند. |
| D-03 | **فروشگاه عضو نمایش‌محور:** محصول/قیمت/موجودی برای اطلاع؛ خرید حضوری است؛ cart/checkout عضو در انتشار اول غیرفعال و API fail-closed باشد. | `OWNER-RECORDED` + `CODE`؛ تست محدود در گزارش | config جاری `shop_online_purchase_enabled=False` در [`config.py`](../../../../mp-app/backend/app/config.py) و سیاست [TODO](../../TODO-CLOUD-FINANCE-ACCESS.md). تحلیل شاخه regressionهای wallet checkout را در تنظیم آزمایشی ثبت کرده؛ این شاهد، مجوز روشن‌کردن checkout در production نیست. |
| D-04 | **پرداخت انتشار اول:** کارت‌به‌کارت (`card_to_card`) + بارگذاری فیش خصوصی + بازبینی انسانی و تطبیق با منبع بانکی مستقل؛ فعال‌سازی اشتراک بعد از تأیید، یک‌بار و تراکنشی. روش تاریخی `card` (کارت‌خوان) با کارت‌به‌کارت یکی نیست. | `OWNER-RECORDED`; پرداخت بانکی live اثبات نشده | [TODO](../../TODO-CLOUD-FINANCE-ACCESS.md) و [OWNER-DECISIONS، بخش پرداخت](../../OWNER-DECISIONS.md). `payment_gateway` پیش‌فرض کد جاری `manual` است؛ mock/sandbox وجود دارد. عکس فیش به‌تنهایی رسیدن پول را ثابت نمی‌کند. |
| D-05 | **Sandbox مالی:** بانک صندباکس محلی برای آزمون بدون پول واقعی پذیرفته شده؛ مالک در آینده اتصال/شناسهٔ merchant واقعی خودش را شخصاً آزمایش می‌کند. | `OWNER-RECORDED`; فقط Sandbox | [OWNER-DECISIONS](../../OWNER-DECISIONS.md)، بخش پرداخت؛ کد `mp-app/backend/devtools/sandbox_bank.py` و تست‌های `test_sandbox_bank.py`. این محیط، درگاه زنده، تسویهٔ واقعی یا اجازهٔ انتشار را ثابت نمی‌کند. محرمانهٔ تاجر/secret را در سند/چت وارد نکنید. |
| D-06 | **حضور:** QR کوتاه‌عمر + احراز/قفل محلی دستگاه عضو؛ تشخیص چهرهٔ سروری فعلاً ساخته/وعده نشود. | `OWNER-RECORDED`؛ `PARTIAL` | [OWNER-DECISIONS، بخش ورود باشگاه](../../OWNER-DECISIONS.md)، routeهای `/face/qr-token`, `/face/checkin-qr`. گزارش تحلیل، `method=face` را با ۴۰۹ fail-closed و بدون ایجاد check-in ثبت کرده است؛ هنوز آزمون دستگاه/پذیرش و production نیست. قفل دستگاه امنیت QR سمت سرور را جایگزین نمی‌کند. |
| D-07 | **راهنمای سلامت:** محصول راهنمای سادهٔ تمرین باشد؛ ادعای تشخیص پزشکی/جایگزینی پزشک اضافه نشود. اگر متخصص بالینی وارد شد، تصمیم از نو باز شود. | `OWNER-RECORDED`; ارزیابی حرفه‌ای انجام‌نشده | [OWNER-DECISIONS، بخش غربالگری سلامت](../../OWNER-DECISIONS.md). تست rule-engine اثربخشی/ایمنی بالینی را تأیید نمی‌کند. `blocked/needs_review` هنوز ممکن است draft ساخته/نمایش داده شود؛ fail-closed محصولی کامل نیست. |
| D-08 | **عکس پیشرفت بدن:** قابلیت ذخیرهٔ عکس بدن در scope انتشار اول نیست. اگر در آینده ساخته شد، مدت نگهداری را عضو خودش انتخاب کند و حذف فوری/حذف با حذف حساب وجود داشته باشد. این سیاست شامل فیش پرداخت یا عکس محصول نیست. | `OWNER-RECORDED`; قابلیت عکس بدن را اجراشده فرض نکنید | [TODO](../../TODO-CLOUD-FINANCE-ACCESS.md) و [OWNER-DECISIONS، بخش عکس‌ها](../../OWNER-DECISIONS.md). retention در DB/backup، UI انتخاب بازه، رضایت و پاک‌سازی هنوز به طراحی/بازبینی حقوقی نیاز دارد. فایل‌های موجود را بدون inventory و مجوز پاک نکنید. |
| D-09 | **نقش و grant:** اعطا/تغییر/ابطال role فقط برای `super_admin`; ordinary admin از ساخت/ارتقای role محروم؛ second super-admin از API عادی ممنوع. دسترسی‌های شخصیِ admin برای حوزه‌های حساس (خواندن/نوشتن جدا و قابل‌انقضا) طبق سیاست مالک تنظیم شود. | `OWNER-RECORDED`; `PARTIAL` | [TODO، نقش و مجوز](../../TODO-CLOUD-FINANCE-ACCESS.md). کد فعلی ۶ role (`member`, `coach`, `reception`, `manager`, `admin`, `super_admin`) دارد؛ طرح قدیمی نقش‌های مقصد سه‌گانه با آن‌ها یکسان نیست. TODO خودش می‌گوید route matrix، منع admin و default finance access نیازمند کار است؛ از وجود Casbin/منوی مخفی نتیجه نگیرید که همهٔ routeها هم‌راستا شده‌اند. |
| D-10 | **گزارش مالی/مجوزها:** گزارش پیش‌فرض برای admin و manager خاموش، super_admin دسترسی کامل؛ اختیار شخصی به admin قابل اعطا/لغو؛ گزارش سرپرست بدون مجوز شخصی جدید باز نشود. | `OWNER-RECORDED`; پیاده‌سازی کامل/همگرا ثابت نشده | [TODO، تصمیم‌های مالک](../../TODO-CLOUD-FINANCE-ACCESS.md). در کد جاری نقش‌نامه و Casbin/گاردهای route ترکیبی‌اند؛ ماتریس API+export+فایل باید جداگانه آزموده شود. هر گزارش ناقص، سود قطعی/صفر نیست و طبق رفتار موجود «نامعلوم» است. |
| D-11 | **کنترل UI:** برای کنترل‌های تعاملی از کتابخانه/ویجت OSS رایگان با مجوز OSI استفاده شود؛ برای Studio کنترل‌های Ant Design و تقویم جلالی مجازند؛ Flutter از ویجت SDK استفاده کند؛ کنترل تعاملی دست‌ساز هدف نیست. | `OWNER-RECORDED`; مهاجرت همهٔ کنترل‌ها یک ادعای جداست | [TODO بخش J](../../TODO-CLOUD-FINANCE-ACCESS.md) و [Option 03](../frontend-ui-ux-flow-option-03-lab-v1-2026-11-23.md). در شاخه، توکن‌ها و بخشی از کنترل‌ها/آزمون‌ها موجودند؛ وجود این تصمیم به‌تنهایی inventory/جایگزینی کامل همهٔ کنترل‌های Studio را ثابت نمی‌کند. |
| D-12 | **توزیع Android:** اپ خصوصی است، Play Store در scope نیست؛ فایل مستقیم مدنظر است. رسیدگی به secret/keyهای واقعی تاریخی باید موردی و امن انجام شود؛ allowlist سراسری برای دورزدن secret scan مجاز نیست. | `OWNER-RECORDED`; signing/release مستقل | [OWNER-DECISIONS، بخش کلید Android](../../OWNER-DECISIONS.md). این تصمیم PASS گیت secret، صحت signing، آماده‌بودن APK یا انتشار را ثابت نمی‌کند. این بسته هیچ credential/key/fingerprintی را بازگو نمی‌کند. |

## ۳. برداشت‌های کد/تست که «تصمیم مالک» نیستند

| موضوع | وضعیت قابل مشاهده | نباید چه نتیجه‌ای گرفت؟ |
|---|---|---|
| API | [`routes.json`](../../../../mp-app/backend/api/routes.json): ۱۶۳ operation و ۱۴۱ الگوی path؛ `interaction_map.py --check` در snapshot جاری ۳۱ سطح و ۱۶۳ مسیر قراردادی را PASS کرده است. | PASS inventory معادل پوشش E2E، پوشش همهٔ دکمه‌ها، صحت business logic یا اتصال هر DB table نیست. پنج surface دارای endpoint در artifact تست مرتبط خالی دارند؛ این یعنی generator تستی را match نکرده، نه اثبات نبود هر آزمون دیگری. |
| دیتابیس | `sqlite:///./mp.db` مقدار پیش‌فرض `Settings.database_url` است. | «SQLite برای production مناسب است» یا «همین حالا PostgreSQL انتخاب شده» از این مقدار نتیجه نمی‌شود. |
| Worker/scheduler | `build_scheduler()` و outbox logic در سورس/تست دیده می‌شوند؛ `main.py` scheduler را در lifespan start نمی‌کند. | تعریف job/تست `run_once` اثبات اجرای زمان‌بندی‌شده، worker فعال، retry واقعی یا exactly-once در deployment نیست. |
| وب‌هوک/درگاه | مسیرهای callback/return در router/قراردادند و gatewayهای manual/mock/sandbox شناخته شده‌اند. | وجود `/gateway-return` یعنی merchant واقعی/بانک وصل است، نه. |
| AI | موتور قاعده‌ای و adapterهای اختیاری وجود دارند. | تصویر نمودار یا موفقیت یک تست، hallucination-free بودن، ایمنی پزشکی یا فعال بودن provider خارجی نیست. |
| اقامت/میزبانی | فایل Compose و کد Caddy/health/metrics وجود دارند. | وجود فایل deployment معادل استقرار موفق، TLS عمومی، backup خارج از سرور یا تمرین restore نیست. |

## ۴. موارد باز/نیازمند تأیید — خارج از تصمیم‌های قطعی

این موارد از نمودار جدا نگه داشته شده‌اند. هیچ‌یک در `OWNER-RECORDED` بالا جای داده نمی‌شوند مگر مالک گزینه را صریح انتخاب کند.

| ID | پرسش باز | دلیل بازماندن / گزینه‌های نیازمند تأیید |
|---|---|---|
| O-01 | baseline کلاینت اصلی انتشار اول چیست و آیا native کنار گذاشته می‌شود؟ | برای baseline انتشار اول پاسخ داده شد: PWA مشترک عضو/کادر (OQ-01، [ADR-007](../../adr/007-pwa-primary-release.md)). Flutter/Android حفظ می‌شود؛ parity و سرنوشت بلندمدت native تصمیم جدا/باز است. |
| O-02 | آیا مدل نقش به ۳ role کاهش یابد یا ۶ role حفظ شود؟ | مالک تک‌باشگاه و حفظ شش role فعلی را انتخاب کرد (OQ-03). تغییر/کاهش role یا grant تصویب نشده؛ route matrix server-side هنوز باید بررسی/تست شود. |
| O-03 | جزئیات سرور محلی و ورودی HTTPS چیست؟ | جهت «سرور محلی باشگاه + HTTPS» پاسخ داده شد (OQ-02). نام میزبان/دامنه، اپراتور، budget, firewall/trusted proxy, staging, backup/restore و RPO/RTO همچنان `OPEN/NOT_RUN`; هیچ deploy مجاز نیست. |
| O-04 | SQLite بماند یا PostgreSQL در چه آستانه‌ای مهاجرت کند؟ | مالک SQLite را فعلاً انتخاب کرد (OQ-04). معیار benchmark/trigger مهاجرت هنوز باز است؛ PostgreSQL و migration تولیدی تصویب نشده‌اند. |
| O-05 | رفتار آیندهٔ عکس پیشرفت بدن چگونه رضایت/retention/delete/backup را اجرا کند؟ | مالک تأیید کرد ذخیرهٔ عکس پیشرفت بدن در انتشار اول خارج از scope است (OQ-07). سیاست آینده، دادهٔ احتمالی موجود، backup purge و مرور حقوقی هنوز بازند؛ هیچ عکس موجودی بدون inventory/مجوز حذف یا باز نمی‌شود. |
| O-06 | جدول نهایی route × role × permission × record scope چیست؟ | سیاست مالک برای role/grant/مالی ثبت شده، اما TODO implementation work باقی می‌گذارد. نهایی‌سازی باید تمام endpointها، exportها، فایل‌ها، member ownership، denyها و مسیرهای جایگزین را پوشش دهد. |
| O-07 | تعریف حسابداری «درآمد/هزینه/سود» و بازهٔ report چیست؟ | refund ناقص اکنون سود را نامعلوم می‌کند؛ تعریف شناسایی درآمد، دوره، بهای کالا، مالیات و هزینه با حسابدار/مالک لازم است. |
| O-08 | کدام push provider و چه SLA عملیاتی پذیرفته شود؟ | اعلان داخلی با push یکی نیست؛ دسترسی Android/GMS، شبکهٔ هدف، هزینه، زمان‌بندی، worker heartbeat و fallback به تصمیم/آزمون نیاز دارند. |
| O-09 | آیا پاسخ platform جدید باید به ADR/TODO رسمی منتقل شود؟ | انجام شد: [ADR-007](../../adr/007-pwa-primary-release.md)، [ADR index](../../adr/README.md) و [TODO واحد](../../TODO-2026-11-16.md). این ثبت، تأیید design diagrams یا QA محصول نیست. |

## ۵. تغییرات ممنوع تا پاسخ مالک

- baseline جاری انتشار اول را طبق OQ-01 و ADR-007، PWA مشترک عضو/کادر ثبت کنید؛ آن را منتشرشده/QA‌شده یا جایگزین Flutter/Android در repository و CI معرفی نکنید.
- نقش‌ها را به سه‌تایی هدف تقلیل ندهید و routeهای فعلی را براساس آن rename نکنید.
- Full Cloud، PostgreSQL، gateway بانکی زنده یا push provider را «انتخاب‌شده/فعال» ننویسید مگر منبع جدیدی تصمیم/تست را ثابت کند.
- مدت ثابت نگهداری عکس بدن را انتخاب نکنید؛ در عین حال، قابلیت ذخیرهٔ عکس بدن را برای انتشار اول اضافه نکنید.
- پشت pass شدن interaction-map، grant یا permission را برای کاربر مجاز فرض نکنید.
- هیچ رسید خصوصی/تصویر شخصی را در نمودار، screenshot، سند یا archive کپی نکنید.


## ۶. الحاقیهٔ پاسخ‌های مستقیم مالک — ۲۰۲۶-۱۱-۲۳

> منبع: پاسخ‌های صریح OQ-01…OQ-10 در question boxهای همین گفتگو؛ متن پاسخ‌ها در [دفتر پاسخ مالک](../owner-decision-questionnaire-2026-11-23.fa.md) ثبت شده است. این الحاقیه وضعیت قدیمی D-01/پرسش‌های قبل را پنهان نمی‌کند؛ فقط تصمیم جاری و scope supersession را ردیابی می‌کند.

| OQ | پاسخ مالک | ثبت/گیت باقیمانده |
|---|---|---|
| OQ-01 | PWA مشترک React عضو و کادر رابط اصلی انتشار اول؛ Flutter/Android حفظ شود. | ADR-007 پذیرفته؛ implementation/QA/PWA installability `NOT_RUN`. فقط baseline قدیمی superseded است. |
| OQ-02 | سرور محلی باشگاه + HTTPS. | host/operator/budget/backup/restore/RPO/RTO باز؛ deployment مجاز نیست. |
| OQ-03 | تک‌باشگاه؛ شش role فعلی حفظ شوند. | role/grant mutation یا model سه‌نقشی مجاز نشده؛ امنیت API گیت جداست. |
| OQ-04 | SQLite فعلاً؛ benchmark و trigger مهاجرت لازم‌اند. | هیچ migration production مجاز نشده است. |
| OQ-05 | کار محلی کد/تست/docs روی branch جاری بدون تأییدهای روتین. | commit/push/PR/merge/release/deploy و production بیرون scope است. |
| OQ-06 | API/inference بیرونی ممنوع؛ قابلیت وابسته به مدل تا مدل محلیِ مجاز `BLOCKED`. | هیچ کد یا داده‌ای به inference بیرونی ارسال نشود. |
| OQ-07 | تأیید تطبیق انسانی کارت‌به‌کارت، فروشگاه نمایش‌محور، QR بدون چهره، راهنمای غیرپزشکی، بدون عکس بدن در انتشار اول. | هیچ payment live/face detection/medical claim/body-photo workflow از پاسخ استنتاج نشود. |
| OQ-08 | تمام جریان‌های اصلی TODO پیش از release؛ هدف Android Chrome برای عضو و Chrome/Edge دسکتاپ برای کادر. | browser versions/device models pin نشده‌اند؛ physical test `UNKNOWN/NOT_RUN`. |
| OQ-09 | APK release به کاربر نرسیده است. | این وضعیت، signing key تاریخیِ افشاشده را پاک/امن نمی‌کند؛ rotation و secret gates لازم‌اند. |
| OQ-10 | reviewer مستقل حقوقی/پزشکی/مالی فعلاً موجود نیست. | هر گیت مستقل بی‌شاهد `UNKNOWN/BLOCKED`; مالک محصول، reviewer مستقل نیست. |

**عدم‌تضعیف:** انتخاب PWA اجازهٔ role/DB/payment/offline changes، device/independent review claim یا release نمی‌دهد. TODO canonical و status هر micro-loop مرجع اجرای محلی‌اند؛ هیچ کار خصوصی/receipt باز یا وارد سند نمی‌شود.
