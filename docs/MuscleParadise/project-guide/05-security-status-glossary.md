# ۵. امنیت، وضعیت اثبات‌ها و واژه‌نامه

[بازگشت به راهنما](README.md) · [Backend/API](02-backend-and-data.md) · [Release checklist](../RELEASE-CHECKLIST.md) · [TODO مالک/محصول](../TODO-CLOUD-FINANCE-ACCESS.md)

## ۵.۱ شیوهٔ خواندن شواهد

هر ادعا را با یکی از وضعیت‌های زیر بخوانید:

| وضعیت | معنا |
|---|---|
| **CODE** | در فایل‌های همان checkout منطق/ساختار قابل مشاهده است. به‌تنهایی اثبات runtime نیست. |
| **TEST-REPORTED** | یک گزارش/CI اجرای سناریوی معین را نوشته است؛ اگر این نوبت اجرا نشده، آن را نتیجهٔ امروز نخوانید. |
| **TEST-RUN** | همین SHA و همین محیط فرمان آزمون شده و خروجی واقعی ثبت شده است. در این نوبت آزمون محصول اجرا نشده است. |
| **OWNER-RECORDED / ADR** | انتخاب محصولی از طرف مالک ثبت شده؛ پیاده‌سازی، اثر امنیتی یا پذیرش انتشار را به‌تنهایی ثابت نمی‌کند. |
| **PARTIAL** | بخشی از قرارداد/flow در کد یا آزمون هست، اما دامنهٔ کامل تأیید نشده. |
| **TARGET / PROPOSED** | هدف طراحی یا کار پیشنهادی؛ کد موجود فرض نشود. |
| **OPEN / UNKNOWN / NOT_RUN** | شاهد/تصمیم/آزمون لازم در دسترس نیست. نبود شاهد را «امن»، «نمی‌تواند» یا «قطعاً پیاده نشده» تفسیر نکنید. |
| **BLOCKED / NO-GO** | گیت صریح مانع عبور است؛ پیش‌فرض یا حدس آن را باز نمی‌کند. |

`routes.json`, diagram, mockup, source comment, historical test report، CI سبزِ commit قدیمی و وجود provider class هرکدام نوع شاهد متفاوت‌اند. برای ادعای «کار می‌کند»، source → integration test → build/runtime/device متناسب با آن ادعا لازم است.

## ۵.۲ مرزهای امنیتی موجود در source

### احراز هویت و مجوز

- OTP با محدودیت نرخ و تلاش، `access_token` و `refresh_token`، rotation/session tracking، خروج از session و افزایش `auth_version` در کد وجود دارند.
- access token در API با `Authorization: Bearer` می‌آید؛ role/method/path با Casbin کنترل می‌شود؛ موارد حساس ممکن است به grant جدا و زمان‌دار نیاز داشته باشند.
- مالکیت عضو باید در backend/service enforce شود، نه صرفاً با مخفی‌کردن صفحه یا گذاشتن `member_id` در کلاینت.
- Google/SSO/MFA را فقط به‌خاطر وجود JWT یا OTP فرض نکنید؛ معیار فعلی/کامل بودن آن‌ها را در route/schema/ADR بررسی کنید.
- Studio از localStorage برای token استفاده می‌کند؛ source آن را HttpOnly-cookie یا XSS-proof نمی‌خواند.
- Client tokenها را در `SharedPreferences` نگه می‌دارد؛ این مستندسازی evidence رمزگذاری اختصاصی محلی یا jailbreak/root resistance ندارد.

### OTP و SMS

`app/sms.py` الگوی adapter `dev`, `webmagfa`, `kavenegar` دارد. Dev provider SMS واقعی نمی‌فرستد؛ API response echo نیز به تنظیم dev وابسته است. providerهای وب، HTTPS را اجباری می‌کنند و متن exception شامل credential/URL را در log پنهان می‌کنند. برای production، `config.py` provider غیر-dev، URL HTTPS و فیلدهای secret لازم را validate می‌کند. وجود adapter/test به‌تنهایی اتصال به provider، اعتبار حساب یا deliverability را نمی‌سنجد.

### رمز/کلید و transport

- production validation حداقل ۳۲ بایت برای `MP_SECRET_KEY`, کلید پیش‌فرض ممنوع و `MP_BIOMETRIC_KEY` برابر Base64 از دقیقاً ۳۲ بایت و جدا از secret را می‌خواهد.
- production CORS originها باید allowlist HTTPS واقعی باشند؛ `MP_TRUSTED_PROXIES` معتبر و non-empty؛ `MP_VALKEY_URL` به مقصد قابل‌دسترسی غیر-loopback اشاره کند.
- `SecurityHeadersMiddleware` و تنظیم proxy در کد موجودند. دامنهٔ TLS، رفتار header در هر مسیر/ingress، CDN، trusted proxy واقعی و firewall باید روی topology هدف آزمایش شود.
- Android `network_security_config` و `ApiClient` سیاست HTTP محدود به loopback/private RFC1918 دارند؛ build/manifest compiled را با سورس یکی ندانید.
- logهای ساختاریافته و correlation id برای ردیابی هستند؛ OTP، access token، کلید یا embedding خام نباید ثبت/منتشر شود.

### بیومتریک و QR

- consent version، revoke/delete FaceTemplate و رمزنگاری template/embedding با کلید زیست‌سنجی اختصاصی در سرویس‌ها دیده می‌شوند.
- `MP_BIOMETRIC_KEY` در production الزامی است. کلید گمشده/غلط باید fail closed بماند؛ backup/rotation key و دادهٔ رمز‌شده نیازمند فرایند جدا هستند.
- QR عضو با امضای JWT کوتاه‌عمر و `jti` تصادفی ساخته می‌شود؛ در check-in digest آن ذخیره و unique index در DB همزمانی redemption تکراری را می‌بندد. QR bearer خام در hash column قرار نمی‌گیرد.
- مسیر `method=face` در گزارش تحلیل با 409 رد شده و check-in جدید نمی‌سازد؛ نباید از تصمیم قبلی YuNet/SFace یا کد `deep-status` نتیجه گرفت که تشخیص چهره در انتشار فعال است.
- هیچ آزمون دوربین، اسکنر، کیوسک یا device QA در این مستندسازی اجرا نشده؛ liveness/anti-spoofing و کلید محلی گوشی به‌تنهایی حضور server-verified را ثابت نمی‌کنند.

### فیش/دادهٔ خصوصی

رسید پرداخت و receipt هزینه فایل‌های خصوصی‌اند. endpoint باید auth/scope داشته باشد؛ نام فایل تصادفی، محدودیت حجم، اعتبارسنجی محتوا، retention و access audit را از router/service/تست دنبال کنید. در این کار محتوای `mp-app/backend/var/receipts/` **عمداً باز، فهرست، کپی، screenshot یا در سند درج نشده است**. مسیر خصوصی را در مرور بعدی نیز از inventoryهای ناامن حذف کنید.

## ۵.۳ مالی و خطر دوباره‌شماری

- رفتار `Payment`, `PaymentReceipt`, `WalletTransaction`, `LedgerEntry`, `Expense` و `ExpenseRevision` جداست؛ تعادل کیف‌پول/ledger با درآمد شناسایی‌شده و سود عملیاتی یکی نیست.
- ledger دارای الگوی append-only/reversal است؛ اصلاح مالی را با دستکاری ردیف پیشین یا نمایش عدد حدسی توصیف نکنید.
- تصمیم مالک برای انتشار اول کارت‌به‌کارت + فیش خصوصی + تطبیق انسانی با منبع بانکی مستقل است؛ بارگذاری عکس، واریز واقعی را اثبات نمی‌کند.
- تست sandbox/mock، callback route یا adapter به معنی بانک/merchant live نیست.
- فروشگاه عضو نمایش‌محور است؛ `shop_online_purchase_enabled=False` پیش‌فرض و مسیر سرویس در این وضعیت fail-closed گزارش شده. کد سبد/سفارش تاریخی باقی است و تصمیم محصولی را خودبه‌خود تغییر نمی‌دهد.
- Refund / Commission / report / expense exports از سطح route، role، grant، ownership، completeness، تاریخ refund و CSV escaping بررسی شوند. inventory «role allowed» را مجوز مؤثر ندانید.
- definition of revenue, refund period, inventory cost, tax, profit و گزارش رسمی هنوز به مالک/حسابدار نیاز دارند. بدون سیاست حسابداری، وضعیت ناقص باید `unknown/incomplete` باشد، نه صفر یا سود قطعی.

## ۵.۴ Health، resilience و عملیات

- `health` liveness ساده است؛ readiness DB/storage/rate-limit/pool و بسته به config heartbeat worker را می‌سنجد.
- `require_worker` default false است؛ اگر worker جدا دارد باید در Compose/Deployment و readiness به‌طور عمدی فعال شود.
- outbox relay retry/backoff/dead-letter دارد، اما handler نمونه log-only است؛ presence منطق صف به معنی push/SMS handler واقعی یا running worker نیست.
- Valkey cache fallback درون‌حافظه دارد؛ fallback بین processها مشترک نیست. Production rate limiting نیز نباید به cache fallback عمومی تقلیل یابد.
- Backup script archive/manifest/hash و SQLite integrity را بررسی می‌کند؛ این نه رمزگذاری خودکار backup، نه offsite retention، نه restore drill production است.
- Prometheus ruleها در مخزن‌اند، اما Alertmanager receiver/notification عملیاتی باید جدا راه‌اندازی/آزموده شود.
- خطای اتصال DB، scheduler process، worker heartbeat، migration drift، queue age، disk/cert expiry و backup freshness باید alert/incident owner داشته باشند؛ فقط endpoint readiness تمام عملیات را پوشش نمی‌دهد.

## ۵.۵ حریم خصوصی و retention

منبع‌های کلیدی: `docs/MuscleParadise/DATA-RETENTION.md`, `modules/privacy/retention.py`, `modules/face_id/privacy.py`, grant/audit services و routeهای admin retention.

- سیاست retention در `DATA-RETENTION.md` با وضعیت «پیش‌نویس مصوب مهندسی — اجرا پیش از دادهٔ واقعی الزامی» ارائه شده؛ جدول آن مدت‌هایی برای هویت، اندازه‌گیری، مالی، حضور و consent چهره پیشنهاد/ثبت می‌کند.
- کد پاک‌سازی allowlist محدود دیگری دارد: `audit_logs`، `inbox_messages`، اعلان‌های خوانده‌شده و `report_runs`؛ route پیش‌نمایش/run فقط `super_admin` است و هر run audit می‌شود.
- کد retention صریحاً برخی داده‌های مالی و outbox dead-letter را دست‌نخورده می‌گذارد تا تأیید حقوقی/مالی. همسانی جدول سند با سیاست کد، backup purge و حذف کاربر باید تصمیم/آزمون جدا داشته باشند.
- consent، حذف FaceTemplate و privacy notice وجود کد دارد، اما الزام حقوقی/فرم رضایت، دسترسی audit به دادهٔ حساس، retention backup و exercise حذف در production مستقل/قانونی تأیید نشده‌اند.
- ذخیرهٔ عکس پیشرفت بدن خارج از scope انتشار اول است؛ فیش پرداخت و عکس محصول categoryهای متفاوت‌اند.
- در این نشست reviewer مستقل حقوقی، پزشکی یا مالی در دسترس/تأییدشده نیست؛ گیت‌هایی که چنین review می‌خواهند `UNKNOWN/BLOCKED` می‌مانند.

## ۵.۶ safety و هوش مصنوعی

- موتور `engine/workout.py` / `modules/ai_engine/` قاعده‌ای و قطعی برای عددهای برنامه است؛ source comment و ADR-003 می‌گوید بار/ست/تکرار از موتور قواعد بیاید، نه از LLM.
- موجودبودن adapter یا URL مدل داخلی، فعال بودن مدل محلی، داشتن license وزن‌ها، صحت نتیجه، یا اجازهٔ inference را ثابت نمی‌کند. طبق پاسخ مالک/ADR-007، API/inference بیرونی و ارسال کد/داده به آن ممنوع است؛ capability متکی به مدل تا انتخاب/مجوز مدل محلی مجاز `BLOCKED` بماند.
- `blocked`/`needs_review` safety result در گزارش جاری ممکن است هنوز draft ایجاد/نمایش دهد؛ پس fail-closed کامل محصولی را ادعا نکنید. UI باید این را مسدود/نیازمند مربی نشان دهد؛ مسیر دقیق پذیرش باز است.
- سرویس‌ها و rule tests جایگزین ارزیابی حرفه‌ای/بالینی، تشخیص یا ضمانت عدم آسیب نیستند. محصول راهنمای تمرین است و نباید ادعای پزشکی بسازد.
- مجوز تجاری dataset، sourceهای exercise/food، تصویر و model weights باید componentبه‌component و artifactبه‌artifact بررسی شود.

## ۵.۷ وضعیت تصمیم و انتشار

### پذیرفته‌شده یا فعلی بر اساس اسناد تصمیم مالک

- baseline انتشار اول: shared React PWA برای عضو و کادر؛ Flutter/Android حفظ؛ Android Chrome عضو و Chrome/Edge دسکتاپ کادر target browser، نه QA پاس‌شده.
- single-club و حفظ شش role جاری؛ SQLite موقتاً انتخاب‌شده؛ سرور محلی باشگاه + HTTPS جهت استقرار.
- کارت‌به‌کارت با تأیید انسانی؛ فروشگاه نمایش‌محور؛ حضور QR بدون تشخیص چهرهٔ server-side؛ بدون عکس پیشرفت بدن در انتشار اول؛ بدون ادعای پزشکی؛ inference/API بیرونی ممنوع.

### هنوز باز یا `NOT_RUN`

- پیاده‌سازی و پذیرش جریان‌های کامل عضو/کادر در PWA، install/offline/update، parity و تست Android Chrome/Chrome/Edge روی device/version مشخص.
- full route × role × grant × ownership/scope matrix، test-driven privilege/access review و اثبات مسیرهای ممنوع.
- adoption/payment reconciliation انسانی، finance accounting definition، prod config و provider decision سازگار با source فعلی.
- migration/trigger SQLite→Postgres benchmark (مالک فعلاً SQLite را انتخاب کرده؛ production migration تصویب نشده).
- worker/scheduler startup, notification delivery, service integrations, hosting domain/operator, DNS/TLS, backup offsite, restore, RPO/RTO, monitoring receiver.
- reviewer مستقل حقوقی/پزشکی/مالی و OS/device/accessibility review.

### NO-GO

ADR-007 وضعیت `NO-GO` انتشار را تا تکمیل جریان‌های اصلی و پذیرش گیت‌های امنیت/حریم/عملیات/device با شاهد روی artifact دقیق اعلام می‌کند. وجود manifest، Compose، green CI قدیمی، route inventory یا تست unit این NO-GO را برنمی‌دارد. Android signing key تاریخی افشاشده نیز در اسناد ثبت شده؛ گفتهٔ مالک مبنی بر این‌که APK release به کاربر تحویل نشده، کلید را امن/rotate‌شده ثابت نمی‌کند.

## ۵.۸ Glossary

| اصطلاح | معنی در این پروژه |
|---|---|
| **API** | قرارداد HTTP؛ در Backend زیر `/api/v1`. |
| **RBAC** | مجوز مبتنی بر role، در اینجا Casbin و guardهای route. |
| **ABAC / scope** | محدودکردن دسترسی با ویژگی رکورد/مالکیت/branch؛ فراتر از نقش. |
| **OTP** | رمز یک‌بارمصرف؛ در پروژه مسیر SMS/توسعه دارد. |
| **Access token** | توکن کوتاه‌عمر برای درخواست‌های محافظت‌شده. |
| **Refresh token** | اعتبار بلندتر برای گرفتن token pair تازه و لغو نشست. |
| **Migration** | تغییر نسخه‌دار schema DB با Alembic؛ با `create_all` یکی نیست. |
| **ORM** | نگاشت شیء Python به جدول SQL با SQLAlchemy. |
| **Outbox** | ثبت رویداد هم‌زمان با تغییر دامنه و relay/retry بعدی. |
| **Inbox/idempotency** | جلوگیری از تکرار اثر رویدادی هنگام تحویل at-least-once. |
| **Dead letter** | eventی که retryها را تمام کرده/برای بررسی نگه داشته شده. |
| **PWA** | وب‌اپ installable با manifest/service worker؛ نصب‌پذیری runtime نیازمند browser/device test است. |
| **Service Worker** | worker browser که درخواست‌ها/cache/update را کنترل می‌کند؛ API نباید از cache قدیمی پاسخ داده شود. |
| **Liveness** | پاسخ‌گویی فرایند؛ dependencyها الزاماً سالم نیستند. |
| **Readiness** | آمادگی سرویس برای دریافت کار واقعی؛ در این پروژه `/api/v1/health/ready`. |
| **E2E** | آزمون flow از UI/client تا server/data در سطح تعریف‌شده؛ integration API تنها browser/device E2E نیست. |
| **SLO** | هدف کیفیت سرویس؛ وجود نام/metric یا threshold به معنی تحقق روی production نیست. |
| **Fail-closed** | در نبود config/رضایت/مجوز یا حالت امن، عملیات منع می‌شود نه این‌که پیش‌فرض مجاز شود. |
| **ADR** | Architecture Decision Record؛ چرایی تصمیم و دامنهٔ آن. |
| **Artifact/SHA** | نسخهٔ مشخص build/source؛ شواهد باید به همان artifact/SHA نسبت داده شوند. |
| **RPO / RTO** | هدف حداکثر ازدست‌رفتن داده / زمان بازیابی؛ این‌ها باید با اپراتور تعیین و drill شوند. |

## اختلاف و کهنگی مستندات

در این checkout چند منبع هم‌زمان یک ادعای واحد ندارند؛ برای رفع تناقض به ترتیبِ مالک/ADR جاری → source/test جاری → runbook/README تاریخی رجوع کنید. ابهام را بدون شاهد حذف نکنید.

| موضوع | اختلاف مشاهده‌شده | روش برخورد |
|---|---|---|
| Baseline PWA | root `README.md`, `ADR-007`, ADR index و TODO جاری PWA مشترک عضو/کادر را کلاینت اصلی انتشار اول می‌دانند؛ ADR-006 با clarification تاریخ‌دار جهت قبلی و وضعیت D-01/D-10 را جدا می‌کند. | `D-01` از نظر baseline کلاینت با ADR-007 پاسخ دارد؛ `D-10`/Go-No-Go همچنان باز است. PWA عضو هنوز پیاده‌سازی/parity/QA نشده؛ Flutter/Android حفظ می‌شود. status و پذیرش را در [backlog canonical](../TODO-2026-11-16.md#pwa-ui-ux-full-backlog-2026-11-23)، [tracker](../TODO-PWA-RELEASE-2026-11-23.fa.md) و [دفتر اجرا](../PWA-EXECUTION-STATE.md) دنبال کنید. |
| PWA و نقش هدف | بخشی از `architecture/README.md`/نقشه‌های قدیمی دربارهٔ PWA اجرا‌نشده، نقش target سه‌گانه و baseline قدیمی است؛ ADR-007 و پاسخ مالک شش role و baseline جدیدتر را می‌گویند. | آن صفحات را snapshot/هدف بخوانید؛ role source جاری و ADR-007 را برای تصمیم جاری دنبال کنید. |
| پرداخت production | `docs/MuscleParadise/DEPLOYMENT.md` و `OPS-RUNBOOK.md` هنوز نمونهٔ `MP_PAYMENT_GATEWAY=zarinpal`/merchant می‌گویند؛ `app/config.py` فعلی فقط `manual`, `mock`, `sandbox` را قبول می‌کند و production mock/sandbox را رد و `manual + sandbox=true` را هم رد می‌کند؛ `.env.example` manual/false دارد. | این یک conflict اجرایی است: دستور Zarinpal در وضعیت source فعلی config validation را پاس نمی‌کند. **قبل از deploy، owner و maintainer باید تصمیم/کد/runbook را همسو کنند.** این مستندسازی integration واقعی را فعال یا آزموده نمی‌کند. |
| Quickstart env | root README فرمان `uvicorn` را بدون `MP_ENVIRONMENT` می‌آورد؛ `app/main.py` اجرای ضمنی را رد می‌کند مگر محیط صریح یا override تست. | از command این guide که `MP_ENVIRONMENT=development` صریح دارد استفاده کنید؛ `MP_ALLOW_IMPLICIT_DEV` را برای dev نگذارید. |
| App shell | comment در `client/lib/features/shell/app_shell.dart` از ۴ tab می‌گوید؛ `static _tabs` و UI پنج tab دارد. | count واقعی را از children/list و test بخوانید؛ comment را مرجع runtime ندانید. |
| Service worker manifest | comment `sw.js` می‌گوید API و manifest شبکه هستند؛ branch کد فقط `/api/` را bypass می‌کند و درخواست‌های دیگر به fallback کلی می‌رسند. | ادعای cache policy manifest را از اجرای دقیق branch بسنجید؛ PWA runtime هنوز test مستقل لازم دارد. |
| Retention | `DATA-RETENTION.md` جدول عمومی retention دارد؛ `modules/privacy/retention.py` allowlist پاک‌سازی محدودتر/متفاوت دارد و برخی مالی/outbox را نگه می‌دارد. | مدت‌ها را سیاست قطعی قانونی یا cleanup کامل فرض نکنید؛ reconcile با privacy/legal/finance و backup purge لازم است. |
| Master Map و handoff | فایل‌های `MASTER_MAP.md`, `SESSION_HANDOFF.md`, reportهای تاریخ‌دار شامل branch/SHA/شمارش/پشتهٔ تاریخی هستند و گاهی ساختار قدیمی‌تر از source امروز را توصیف می‌کنند. | آن‌ها snapshotهای زمان‌دارند، نه «وضعیت خودکار امروز». زمان/branch/SHA و آخرین بخش status را همراه code/test چک کنید. |
| Interaction map | artifact تعداد surface/operation و تست‌های match‌شده را ثبت می‌کند؛ برخی `tests: []` هستند. | این خروجی test matcher است؛ نبودن `tests` در artifact اثبات قطعی نبودن هر آزمون/سناریو نیست. |

## دامنهٔ بازبینی این راهنما و ادامهٔ مستندسازی

این بسته نقشهٔ سیستم، قرارداد API، مدل‌های اصلی، جریان‌های سطح بالا، تصمیم‌ها، عملیات و گیت‌ها را برای onboarding پوشش می‌دهد؛ **ممیزی semantic خط‌به‌خط تمام فایل‌های repository نیست**. مخزن چندصد فایل کد، test، migration و دارایی دارد. `WIRING-LEDGER`, route catalog و model inventory ابزارهای جهت‌یاب‌اند؛ برای «خط‌به‌خط» شدن باید هر ماژول/route به source، guard، schema، service، جدول migration، مصرف‌کنندهٔ UI، تست دقیق و edge case وصل و بازبینی شود.

در نوبت حاضر:

- کد/اسناد چندلایهٔ Backend، PWA/Client، route inventory، models/migrations و CI به‌صورت نمونه‌گیری/ردیابی‌شده بررسی شدند؛ نه تمام فایل‌ها.
- آزمون محصول، build، CI تازه، browser/device، production، بانک/پیامک، backup restore یا migration واقعی اجرا نشد.
- رسیدهای خصوصی خوانده/فهرست/کپی نشدند.
- فایل‌های جدید این راهنما در working tree ایجاد شده‌اند؛ اسناد companion که untracked بودند ممکن است در clone تمیز موجود نباشند تا جداگانه در Git ثبت شوند.
- هیچ commit/push/PR/merge/release/deploy انجام نشده است.

برای تکمیل واقعی مرور «از صفر تا صد»، گام بعدی باید route-by-route و feature-by-feature در [Wiring ledger](../architecture/session-decisions-2026-11-23/WIRING-LEDGER.md) انجام شود: هر ادعای `CODE`, `TEST-REPORTED`, `OPEN` را به line/fixture/test دقیق همان snapshot وصل، route × role × scope matrix را جمع‌بندی، migration graph را روی scratch بررسی و هر تضاد تصمیمی را با owner حل کند. تا آن زمان برچسب `PARTIAL/UNKNOWN` حفظ شود.
