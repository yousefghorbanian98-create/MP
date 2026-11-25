# برنامهٔ تولید، اتوماسیون هوشمند و آمادگی انتشار Muscle Paradise

> **وضعیت:** پیش‌نویس مشورتی برای تأیید مالک؛ نه ADR پذیرفته‌شده، نه backlog میکرولوپ‌ها و نه مجوز پیاده‌سازی/استقرار. این سند مسیر کلان را طراحی می‌کند؛ پس از تأیید، می‌توان آن را طبق ۱۳ لایه به loopها و سپس micro-taskها تبدیل کرد.
>
> **دامنهٔ این کار:** طراحی برنامه با تکیه بر جریان‌ها و معماری همین مخزن و پروژه‌های متن‌باز GitHub. در این مرحله کد محصول، dependencyها، workflowها، زیرساخت یا داده تغییر نمی‌کند؛ هیچ پروژه‌ای نصب/اجرا نمی‌شود.

## ۱. نتیجه‌ای که برنامه باید به آن برسد

هدف، ساخت سامانه‌ای است که AI بتواند **کارهای مهندسیِ ازپیش‌محدودشده** را بدون نظارت روزمره پیش ببرد: هدف محصول را به کارهای کوچک تقسیم کند، در فضای ایزوله تغییر بدهد، تست و اشکال‌زدایی کند، مستندات مرتبط را به‌روز کند، بازبینی مستقل بگیرد، و فقط پس از عبور از گیت‌های قابل‌اندازه‌گیری تغییر را به مرحلهٔ بعد ببرد.

این هدف دو مسیر وابسته اما متفاوت دارد:

1. **تولید نرم‌افزار:** کیفیت و ایمنی فرایند ساخت با عامل‌های AI، کنترل‌های مرحله‌ای، اصلاح محدود و قابل‌ممیزی، و محدودیت اختیار.
2. **آماده‌سازی محصول برای استفادهٔ واقعی:** تکمیل جریان‌های اصلی عضو و کارکنان، داده، امنیت، بازیابی، مشاهده‌پذیری، استقرار و عملیات.

«بی‌نظارت» یعنی مالک مجبور نباشد هر تست و اصلاح معمول را تأیید کند؛ به معنی دسترسی نامحدود AI به secret، نقش‌ها، پول، دیتابیس یا production نیست. موفقیت با evidence سنجیده می‌شود، نه با گزارش عامل از کار خودش.

**مرز مهم:** عامل AI این برنامه برای مهندسی مخزن است؛ موتور تمرین/تغذیهٔ کاربر محصول مسئله‌ای جدا با قواعد، اعتبارسنجی، منبع داده و ارزیابی تخصصی خودش است. عامل کدنویس نباید دادهٔ سلامت عضو را بخواند یا تصمیم ورزشی/پزشکی/مالی را به مدل واگذار کند.

### تعریف پایان برنامه

پیش از پذیرش انتشار واقعی، هر جریان اصلی باید:

- از رابط واقعی تا API، مجوز، منطق دامنه، DB و بازخورد کاربر سرتاسری و با تست مربوط پوشش داده شود؛
- خطا، retry، قطع و وصل، درخواست تکراری و دسترسی غیرمجاز را امن مدیریت کند؛
- توضیح‌پذیر، قابل‌ممیزی و متناسب با حریم و مجوز داده باشد؛
- روی artifact مشخص و تغییرناپذیر به staging برسد؛
- backup و restore واقعی، rollback، هشدار و runbook آن آزموده شده باشد؛
- در CI همان commit/digest گیت‌های ثبت‌شده را پاس کند. گیت اجرا‌نشده، نتیجهٔ `UNKNOWN` است، نه `PASS`.

## ۲. مبنای پروژه و اسناد راهنما

این برنامه جریان‌های محصول را از نو طراحی نمی‌کند. پیش از شکستن آن به کارهای اجرایی، این اسناد باید کنار هم خوانده شوند:

- [فلوچارت یکپارچهٔ محصول و وضعیت current/target](muscle-paradise-full-program-flow-v1-2026-11-23.md) و [نقشهٔ کامل v2](muscle-paradise-combined-flow-v2-2026-11-23.png)
- [مقصد PWA و مدل دسترسی](muscle-paradise-final-pwa-access-flow-v1-2026-11-23.md)
- [معماری هدف و شکاف‌های زیرساخت](muscle-paradise-world-class-target-architecture-v1-2026-11-23.md)
- [چرخهٔ ورزشکار، نسخهٔ برنامه، JP7 و QR](athlete-program-lifecycle-v2-2026-11-23.md)، [فلوچارت QR/سنجش/برنامه](athlete-jp7-program-qr-flow-v6-2026-11-23.png) و [مشخصات canonical](athlete-jp7-program-qr-v6-2026-11-23.md)
- [مسیریابی سؤال‌ها به منابع](open-source-question-routing-and-layered-data-architecture-v1-2026-11-23.md)
- [طرح ابری/تولید](../PLAN-CLOUD-PRODUCTION.md)، [تصمیم‌های محصول/مالی/دسترسی](../TODO-CLOUD-FINANCE-ACCESS.md)، [runbook عملیات](../OPS-RUNBOOK.md)، [راهنمای استقرار](../DEPLOYMENT.md)، [release checklist](../RELEASE-CHECKLIST.md) و [ADR index](../adr/README.md)

> نمودارها نمای طراحی یا snapshot کد هستند؛ به‌تنهایی اثبات اجرای همهٔ پیکان‌ها، پذیرش محصول یا آمادگی production نیستند. وضعیت ادعا باید در بستهٔ کاری مربوط با route، کد، تست و CI همان revision تأیید شود. worktree این شاخه پیشاپیش تغییرات متعددِ commit‌نشده دارد؛ هر evidence تا تثبیت revision دقیق، فقط به همان worktree/آزمون محدود است.

### وضعیت مبنا از شواهد فعلی

| حوزه | آنچه اکنون در مخزن دیده می‌شود | پیامد برای برنامه |
|---|---|---|
| معماری برنامه | FastAPI به‌صورت modular monolith، Studio وب و Flutter/Android عضو | همین سادگی حفظ شود؛ microservices/Kubernetes هدف پیش‌فرض نیست. فایل‌های Android/Flutter حذف یا بازنویسی نشوند. |
| رابط/مسیر انتشار | TODO محصول، Android عضو + Studio وب را مسیر انتشار اول می‌داند؛ فلوچارت PWA یک رابط مشترک را به‌عنوان هدف طراحی ترسیم می‌کند. PWA هنوز پیاده نشده است. | تعارض صریح و حل‌نشده است؛ هیچ سندی صرفاً به‌خاطر جدیدتر بودن، تصمیم انتشار را supersede نمی‌کند. مالک باید در G0 با ADR دامنهٔ انتشار را انتخاب کند؛ Flutter/Android تا آن زمان حفظ می‌شود. |
| دسترسی | کد فعلی نقش‌های `member`, `coach`, `reception`, `manager`, `admin`, `super_admin` را می‌شناسد. | فلوچارت مقصد مدل `super_admin/admin/member` و اعطای نقش/مجوز ریز فقط توسط `super_admin` را ترسیم می‌کند. این مهاجرت تصمیم و نگاشت owner-signed می‌خواهد؛ `admin` نباید خودش یا دیگری را ارتقا دهد/مجوز بدهد و حق موجودی نباید خودکار گسترش یابد. |
| جریان محصول | مستندات، عضویت، تمرین، تغذیه، ارزیابی، کلاس/QR، چت و مسیرهای مالی/فروشگاه را پوشش می‌دهند؛ خود نمودارها محدودیت شاهد را تصریح می‌کنند. | هر دامنه به «جریان قابل‌آزمون» تبدیل شود؛ نمایش صفحه به‌تنهایی تکمیل نیست. محاسبهٔ پزشکی یا تصمیم مالی خودکار از مدل زبانی پذیرفته نیست. |
| خرید و پول | تصمیم محصول در TODO، فروشگاه نمایش‌محور/خرید حضوری و کارت‌به‌کارت با تطبیق انسانی را می‌خواهد؛ کارت‌به‌کارت فقط وقتی سرور محلی زنده/باشگاه باز است؛ سند Full Cloud قدیمی‌تر دربارهٔ درگاه متعارض است. | مبنای این طرح TODO محصول است: checkout آنلاین هدف انتشار اول نیست و فیش/تطبیق انسانی باید امن و تراکنشی باشد. وضعیت ساعات/آنلاین از سرور بیاید؛ خارج از آن درخواست غیرفعال و پیام واضح نمایش داده شود. پیش از تغییر/انتشار، سند درگاه باید با ADR صریحاً supersede یا به تصمیم جاری پیوند بخورد؛ mock یا sandbox در production راه‌حل نیست. |
| دادهٔ حساس | حوزه‌های حساب، مالی و سلامت/ارزیابی در محصول هستند؛ عکس پیشرفت بدن خارج از محدودهٔ تصمیم مالک است. | دادهٔ واقعی فقط پس از سیاست دسترسی، حداقل‌سازی، retention، حذف، audit و بررسی حقوقی؛ اطلاعات حساس وارد prompt، log یا telemetry نشود. |
| پایگاه داده | Compose تولیدی فعلی SQLite دارد؛ Valkey برای cache است. | PostgreSQL نه شرط مطلق و نه تصمیم اجراشده است. گیت بار، تعداد instance، تراکنش‌های مالی و RPO/RTO تعیین می‌کند SQLite کافی است یا مهاجرت لازم می‌شود. |
| زیرساخت/میزبانی | تصمیم ثبت‌شده در TODO محصول، یک سرور محلی باشگاه با ورودی HTTPS ارزان (VPS کوچک یا تونل) است؛ طرح قدیمی Full Cloud مسیر دیگری پیشنهاد می‌دهد. در مخزن Docker Compose، Caddy، Ansible، Prometheus و دو Compose هم‌پوشان اما متفاوت وجود دارند. | topology محلی/ingress در برابر Full Cloud و منبع حقیقت Compose باید با ADR هم‌راستا شوند. مرز Dokploy/Ansible هم باز است. وجود فایل workflow یا credential template، اتصال به میزبان و استقرار موفق را ثابت نمی‌کند. |
| backup و عملیات | archive محلی SQLite وجود دارد؛ Ansible هم Restic را زمان‌بندی می‌کند، ولی مسیر منبع، volume نام‌دار، repository خارج‌میزبان و restore واقعی نیازمند تأیید عملی‌اند. | نقطهٔ پذیرش production، restore اثبات‌شده از خارج میزبان است، نه صرفاً موفق‌شدن job backup. |
| CI و کیفیت | تست‌ها و گیت‌های کد/مستندات/secret و انتشار image در GHCR وجود دارند؛ Prometheus و چند alert هم تعریف شده‌اند. | از گیت‌های فعلی استفاده و آن‌ها را تقویت کنیم؛ ابزار تکراری اضافه نکنیم. Trivy، SBOM/امضا و alert/monitor مستقل فقط پس از طراحی و آزمون وارد شوند. |
| Ollama | container آن در Compose زیرساخت دیده می‌شود؛ مصرف end-to-end و مجوز مدل‌های انتخابی از پیکربندی بررسی‌شده ثابت نشده است. | مدل محلی فقط نامزد کاهش وابستگی API است؛ سخت‌افزار، کیفیت، مجوز weights و مسیر اتصال باید جدا تأیید شود. |

### یافته‌های مسیر که باید در baseline رسمی دوباره سنجیده شوند

این موارد از فلوچارت/گزارش تحلیل شاخهٔ کاری استخراج شده‌اند، نه از آزمون تازهٔ این سند. فلوچارت کل برنامه برخی وضعیت‌ها را پیش از اصلاحات موجود در worktree توصیف می‌کند. گزارش [تحلیل ۲۰۲۶-۱۱-۲۳](analysis-2026-11-23.md) چند اصلاح و شاهد TestClient را ثبت کرده، اما worktree هنوز dirty است و این برنامه آزمون‌های backend یا device را دوباره اجرا نکرده است؛ بنابراین وضعیت «اصلاح در worktree» را با «پذیرش نهایی» یکی نگیرید.

| مورد | آنچه در اسناد/شاخهٔ فعلی گزارش شده | کار لازم برای پذیرش |
|---|---|---|
| فرم Intake و `POST /population/gate-check` | فلوچارت قدیمی‌تر ۴۲۲ را نشان می‌دهد؛ تغییر کاری `GateCheckIn` بدنهٔ JSON را می‌خواند و گزارش تحلیل، پاسخ ۲۰۰ را در TestClient ثبت می‌کند. | قرارداد Flutter/OpenAPI، آزمون عضو و نقش‌های مجاز، گیت‌های جمعیتی/unknown و E2E روی build دقیق را دوباره بسنج؛ نمودار و route contract را پس از پذیرش هم‌نسخه کن. |
| ایمنی برنامهٔ تمرین | تغییرات کاری قیدهای profile+request را ادغام می‌کنند، شناسهٔ حرکت را با کاتالوگ نگاشت می‌کنند و ID بی‌نگاشت را `needs_review` می‌سازند؛ گزارش فعلی نمونهٔ `knee_injury` را `blocked` می‌داند. بااین‌حال `blocked/needs_review` هنوز در مسیر گزارش‌شده به‌شکل draft ساخته/نمایش داده می‌شود؛ واژگان فارسی فرم نیز با کلیدهای موتور/غربالگر کامل همسان نیست. | گیت سرور باید پیش از ساخت/نمایش draft ایمن fail-closed باشد، نه صرفاً flag ذخیره کند؛ قیود canonical و ترجمهٔ ورودی، پایداری پروفایل، safety cases، آزمون API/UI و نظر متخصص لازم است. هیچ ادعای بالینی از این تست‌ها نتیجه نمی‌شود. |
| تمرین روزانه و ثبت completion | گزارش تحلیل می‌گوید انتخاب روز/هفته محدودیت دارد و تیک انجام تمرین فقط state محلی است، نه ثبت پایدار API/DB. | روز استراحت، زمان/منطقه، تغییر برنامه و sync/retry را تعریف و تست کن؛ تکمیل فقط وقتی تأیید شود که قرارداد persistence و رفتار قطع شبکه روشن باشد. |
| تغذیه و وعده | طرح چرخه، `MealItem` را هدف می‌گیرد؛ گزارش کد شاخه می‌گوید generator فعلی `meals: []` می‌سازد. نمودار قدیمی دربارهٔ نبود `MealItem` با مدل جاری نیاز به reconcile دارد. | model/schema/API/Studio/Client را یک‌بار تطبیق بده؛ کالری/ماکرو را meal plan جا نزن؛ منبع غذا/داده و مجوز آن را قبل از ingest بررسی کن. تا آن زمان وعدهٔ تأییدشده، feature آماده نیست. |
| فروشگاه و رقابت موجودی | تصمیم محصول فروشگاه نمایش‌محور و خرید حضوری است؛ online checkout پیش‌فرض خاموش/fail-closed. تغییرات کاری transaction اتمیک‌تری را می‌آورند و تست‌های rollback/success گسترش یافته‌اند، اما race همزمانی stock هنوز اثبات نشده است. | API/UI خرید عضو fail-closed بماند؛ inventory concurrency جداگانه با DB/runtime منتخب بررسی شود. آزمون SQLite/TestClient به‌تنهایی گیت رقابت یا خرید واقعی نیست. |
| چرخهٔ نسخه‌دار، JP7، PDF و QR | lifecycle/Q01–Q11/C01–C11 و مسیر برنامهٔ نسخه‌دار، تأیید مربی، PDF و QR طراحی‌اند؛ JP7 خودکار و پیوند برنامه/PDF به دادهٔ واقعی هنوز هدف است. | منبع داده/مجوز/فرمول را تصویب، مسئول متخصص را مشخص و مسیر draft → coach approval → immutable version → PDF/QR را از API تا گوشی/چاپ آزمون کن؛ به‌عنوان runtime فعلی معرفی نکن. |
| چهره/حضور | گزارش شاخه می‌گوید `method=face` اکنون fail-closed و غیرقابل‌استفاده است؛ QR هدف جایگزین است، اما دستگاه/دوربین و replay روی تجهیزات واقعی آزموده نشده‌اند. | چهره را غیرفعال نگه‌دار مگر تصمیم/اجرا/حریم مستقل؛ QR، scope، انقضا و replay را با دستگاه فیزیکی و شبکهٔ واقعی (بدون دادهٔ شخصی) بیازما. |
| worker، backup و انتشار | تعریف scheduler/outbox, Restic, Compose و deploy workflow در مخزن به‌تنهایی ثابت نمی‌کند handler فعال است، backup خارج‌میزبان واقعاً نوشته/بازخوانی شده یا rollback اجرا شده است. | در topology انتخابی worker تک‌فعال/health، backup off-host، restore جدا، probe/alert مستقل و staging/rollback تمرین‌شده evidence لازم دارند. |

## ۳. اصول طراحی ثابت

1. **یک source of truth برای محصول و استقرار:** flowchartهای جاری، ADR پذیرفته‌شده، قرارداد API، DB و کد یکدیگر را پشتیبانی کنند؛ دیاگرام هدف جای تست runtime را نمی‌گیرد.
2. **Modular monolith تا وقتی شواهد خلافش را نشان دهد:** جداسازی سرویس تنها با نیاز اندازه‌گیری‌شده به scaling مستقل، محدودیت reliability یا مرز تیمی بررسی می‌شود.
3. **Online-first تا تعیین تکلیف آفلاین:** shell/دارایی کم‌حساس می‌تواند جداگانه بررسی شود؛ write آفلاین به مالی، عضویت، مجوز یا presence اضافه نمی‌شود مگر طراحی idempotency، conflict، انقضا و revoke تأیید شود.
4. **Security در سمت سرور:** default deny، مالکیت/branch scope، نقش و grant و audit در هر route، فایل، export، job و event اعمال شود؛ UI کنترل امنیتی محسوب نمی‌شود.
5. **دادهٔ حساس از prompt جدا:** AI با دادهٔ مصنوعی/حداقلی کار کند. ارسال source یا اطلاعات عضو به مدل/سرویس بیرونی فقط با اجازهٔ مستقل و سیاست دادهٔ مشخص؛ پیش‌فرض، ممنوع.
6. **آزمون را برای سبزشدن تضعیف نکن:** تغییر تست تنها با تغییر نیازمندی/fixture مستند و بازبینی انجام شود؛ `continue-on-error`, skip گیت، استثنای سراسری و allowlist بی‌مالک راه‌حل نیست.
7. **هر retry محدود و قابل‌توقف:** self-heal حداکثر سه دور اصلاح به‌عنوان پیش‌فرض پیشنهادی دارد؛ پس از آن کار متوقف، evidence ثبت و به صف review برگردد. سقف هزینه/زمان قبل از استفاده از inference تعیین می‌شود.
8. **Build once, promote by digest:** artifact یک‌بار ساخته، بررسی و امضا شود؛ همان digest به staging و سپس به انتشار برسد؛ tag به‌تنهایی immutable نیست.
9. **بازیابی عملیاتی است، نه فایل پیکربندی:** backup، آزمون restore، زمان واقعی بازیابی، محل خارج‌میزبان و مسئول هشدار باید ثبت شود.
10. **هزینهٔ نرم‌افزار با هزینهٔ اجرا یکی نیست:** پروژهٔ MIT/Apache/GPL می‌تواند رایگان باشد ولی VM، برق/GPU، storage، پیامک، دامنه و inference پولی نیستند. این plan «بدون subscription نرم‌افزار تا حد ممکن» را دنبال می‌کند، نه ادعای هزینهٔ کل صفر.
11. **کنترل تعاملی محصول از صفر ساخته نشود:** تصمیم Q11 حفظ شود؛ از کتابخانهٔ UI موجود با نسخه و مجوز بررسی‌شده استفاده شود، نه از کنترل دست‌ساز یا dependency موازی.
12. **مدل بیرونی پیش‌فرض نیست:** هیچ API مدل برای گیت‌های قطعی پروژه لازم نیست. اجرای عامل بدون inference موجود/مصوب `BLOCKED` می‌ماند؛ به API ابری یا ارسال کد/داده fallback نمی‌کند.

## ۴. معماری تولیدیِ هدف

مسیر کلان انتشار:

`تصمیم محصول/معیار پذیرش → task graph نسخه‌دار → عامل در workspace ایزوله → تست/اصلاح محدود → بازبینی مستقل + CI → image با digest/SBOM/امضا → staging با دادهٔ ساختگی → readiness و smoke → تصمیم انتشار طبق سیاست → پایش/rollback → بازخورد به task graph`

### مرزها

- **Client:** انتخاب نهایی انتشار در G0 است؛ TODO محصول Android عضو + Studio وب را می‌گوید و فلوچارت PWA یک مقصد طراحی جدا را نشان می‌دهد. هیچ‌کدام از نمودار به‌تنهایی تصمیم release نمی‌شود؛ Flutter/Android حفظ می‌شود.
- **Ingress و میزبان محصول:** مبنای ثبت‌شدهٔ TODO یک سرور محلیِ باشگاه با ورودی HTTPS ارزان از طریق VPS کوچک یا تونل است؛ topology دقیق، مالکیت و دسترس‌پذیری باید آزموده شود. Full Cloud گزینهٔ متفاوت و قدیمی‌تر است، نه پیش‌فرض این طرح. Caddy/TLS یا proxy تأییدشده فقط مسیرهای عمومی لازم را عرضه کند؛ metrics و admin/data services عمومی نشوند.
- **Application:** یک FastAPI modular monolith، policy/ownership server-side، transaction service، domain modules و event/outbox فقط در صورت نیاز واقعی.
- **Storage:** DB مرجع در توپولوژی مصوب، Valkey cache، فایل‌های private و backup جدا. SQLite فعلی است؛ PostgreSQL فقط با trigger، ADR و آزمون مهاجرت. پایداری مالی/مجوز روی cache تنها نباشد.
- **AI build plane:** task planner، orchestrator، agent runner، test harness و evidence store؛ از runtime محصول، دادهٔ اعضا و secrets production جدا. محل اجرا و نیاز به model/inference هنوز تصمیم نشده است.
- **Observability:** metrics/alerts موجود تقویت، probe بیرونی مستقل از سرور محصول، trace فقط با مقصد/retention/redaction مشخص.

این مرزبندی **مقصد طراحی** است؛ انتخاب client، reuse همین Composeها، انتخاب database، ingress و محل agent runner تا گیت تصمیم/آزمون قطعی نیست.

## ۵. نامزدهای ابزار متن‌باز برای ارزیابی مرحله‌ای

این جدول **فهرست نامزدها بر اساس قابلیت** است، نه طراحی ۱۳ لایه، انتخاب dependency یا مجوز نصب. نقطهٔ شروع، ابزارهای حاضر در مخزن است. هر adoption به تأیید دامنه، نسخهٔ pin‌شده، بررسی مجوز کل زنجیره و آزمون ارزش/هزینه نیاز دارد.

| قابلیت | وضعیت فعلی و نامزدهای OSS | شرط استفاده در MP |
|---|---|---|
| دانش، معماری و مدیریت کار | Markdown/ADR/نقشه‌های Git فعلی؛ [LikeC4](https://github.com/likec4) (MIT) یا [Beads](https://github.com/steveyegge/beads) (MIT) برای نیاز واقعی به مدل/وابستگی task. [OpenProject Community](https://github.com/opf/openproject) (GPL-3.0) فقط اگر UI برنامه‌ریزی لازم شود. | ابتدا از فایل‌های موجود استفاده کن. Beads/LikeC4 آزمایشی‌اند و جای TODO/ADR را نمی‌گیرند. OpenProject سرویس جداگانه و مرز Community/Enterprise دارد؛ قابلیت enterprise را رایگان فرض نکن. |
| orchestration کارهای عامل | [LangGraph](https://github.com/langchain-ai/langgraph) (MIT) برای state machine محدود؛ [Temporal](https://github.com/temporalio/temporal) (MIT) فقط اگر دوام اجرا/بازیابی پس از restart با شواهد لازم شد. | ابتدا POC بدون سرویس میزبان تجاری؛ LangSmith/Temporal Cloud و سایر hosted/enterprise features، مجوز و هزینهٔ جدا دارند و برای core flow اجباری نیستند. |
| sandbox و ابزارها | Docker/Compose موجود؛ [Podman](https://github.com/containers/podman) و [gVisor](https://github.com/google/gvisor) (Apache-2.0). | agent runner جدا از میزبان محصول، least-privilege/rootless، بدون secrets و با egress محدود. gVisor/Podman تنها پس از تست سازگاری؛ اجرای self-host منابع، patching و نگهداری می‌خواهد. |
| عامل کدنویس و ارزیابی | یک گزینه برای پایلوت: [Aider](https://github.com/Aider-AI/aider) (Apache-2.0) یا [SWE-agent](https://github.com/SWE-agent/SWE-agent) (MIT)؛ [Promptfoo](https://github.com/promptfoo/promptfoo) (MIT) برای evaluation/red-team روی fixture. | OSS runtime به معنی مدل رایگان نیست. هر hosted/enterprise feature، model provider، token billing و ارسال کد جداست؛ هیچ code/data egress پیش‌فرض مجاز نیست. |
| verification و supply chain | pytest/coverage/docs/route/security gates موجود؛ [Trivy](https://github.com/aquasecurity/trivy), [Syft](https://github.com/anchore/syft), [Cosign](https://github.com/sigstore/cosign), [OpenSSF Scorecard](https://github.com/ossf/scorecard) (عمدتاً Apache-2.0)؛ [Renovate](https://github.com/renovatebot/renovate) (AGPL-3.0-only) اختیاری. | Trivy اول report-only؛ SBOM/sign برای digest واقعی؛ Scorecard سلامت مخزن است نه گواه امنیت محصول؛ Renovate فقط PR، بدون auto-merge. Gitleaks/Semgrep/Bandit/pip-audit موجود دوباره نصب نشوند. نسخه و license فایل/بستهٔ دقیق بازبینی شود. |
| CI، registry، پایش و policy | GitHub Actions/GHCR و Prometheus موجود؛ [Uptime Kuma](https://github.com/louislam/uptime-kuma) (MIT), [OpenTelemetry Collector](https://github.com/open-telemetry/opentelemetry-collector) (Apache-2.0), [OPA](https://github.com/open-policy-agent/opa) (Apache-2.0), [OpenFGA](https://github.com/openfga/openfga) (Apache-2.0); [Woodpecker CI](https://github.com/woodpecker-ci/woodpecker)/[Harbor](https://github.com/goharbor/harbor) (Apache-2.0) صرفاً در سناریوی self-host. | اول ابزار موجود را harden کن؛ Kuma فقط روی host/network مستقل ارزش دارد؛ OTel فقط با مقصد/retention/redaction؛ OPA/OpenFGA فقط اگر قواعد موجود کافی نبودند؛ self-host CI/registry یعنی سرور و on-call اضافه. |
| مدیریت راز و inference | رازها از مسیر امن موجود/منتخب محیط؛ [SOPS](https://github.com/getsops/sops) (MPL-2.0) فقط اگر encrypted config در Git لازم شود. [Ollama](https://github.com/ollama/ollama) (MIT برای runtime) در Compose دیده شده است. | SOPS جای secret manager/کلید بازیابی نیست. مجوز weight، دیتاست، prompt و خروجی مدل جدا از Ollama است؛ سخت‌افزار/کیفیت و inference API هزینهٔ مستقل دارند. تا انتخاب مالک، هیچ model API یا inference بیرونی پیش‌فرض نیست. |
| کنترل‌های رابط محصول | تصمیم Q11: کنترل تعاملی از صفر نوشته نشود؛ از UI library رایگان/OSS موجود (Studio: Ant Design؛ Flutter: widgetهای SDK) استفاده شود. | قبل از تغییر، dependency موجود و مجوز exact version بررسی شود؛ UI library رایگان به معنی همهٔ خدمات/افزونه‌ها/آیکن‌ها/فونت‌ها یا assetهای آن رایگان و بازتوزیع‌پذیر نیست. ابزار/کتابخانهٔ موازی اضافه نکن. |

### معنای «رایگان» و هزینهٔ مالکیت

مجوز OSS (مثلاً MIT/Apache/GPL) هزینهٔ خرید کد را از دید خود آن مجوز مشخص می‌کند؛ این با هزینهٔ زیرساخت، نگهداری، پشتیبانی، امنیت، انرژی/GPU، storage و backup، دامنه/TLS، پیامک/push، ترافیک، inference API، hosted control plane و مجوز وزن مدل/داده/رسانه یکی نیست. Community/Open-core در کنار featureهای Enterprise/hosted می‌تواند مرز محصولی یا مجوزی داشته باشد؛ قبل از adoption همان release/tag، بخش‌های repository و service terms بررسی شود. رقم ماهانه تا تعیین topology و ارائه‌دهنده برآورد نمی‌شود.

## ۶. مسیر مرحله‌ای و گیت‌های عبور

ترتیب زیر macro-plan است، نه فهرست microtask. هر مرحله تا evidence آن PASS نشود گام وابسته را باز نمی‌کند. جریان‌های مستقلِ مستندسازی/ارزیابی ابزار می‌توانند موازی شوند، ولی تغییر محصول یا release از gate عبور می‌کند.

| فاز | هدف و تحویل | گیت خروج / توقف |
|---:|---|---|
| **G0 · تثبیت دامنه** | تصمیم جاری TODO را با طرح PWA متعارض روشن کن: baseline مستند Android عضو + Studio وب است؛ PWA فقط در صورت تصویب صریح جای آن را می‌گیرد. topology ثبت‌شده سرور محلی باشگاه + ورودی HTTPS ارزان baseline است؛ Full Cloud فقط با تصمیم تازه. نقش‌ها، تک‌باشگاه یا multi-tenant، خرید حضوری/کارت‌به‌کارت، offline boundaries و فهرست «همهٔ قابلیت‌های اصلی» نیز تثبیت شوند. | مالک تصمیم می‌گیرد آیا baselineهای فعلی را تأیید/تغییر می‌دهد؛ ADR و اسناد متعارض صریحاً link/supersede شوند. بدون آن، release scope و اجرای عامل روی محصول شروع نمی‌شود. Android/Flutter محفوظ. |
| **G1 · baseline و راهبری** | inventory از flows، route/roles, schema, CI, Compose, ingress/deploy/runbooks, backup, gaps؛ snapshot شاخه و worktree را non-destructive ثبت و evidence را به commit/diff hash/environment وصل کن. تصمیم‌های DB/Compose/ingress/inference/داده ثبت شوند. | برای هر جریان: current/target/unknown و آزمون مشخص؛ هر `UNKNOWN` صاحب و گام کشف دارد. هیچ PASS از نقشهٔ قدیمی یا تغییرات uncommitted بدون بازاجرای گیت‌ها صادر نمی‌شود. |
| **G2 · سیاست AI و محیط ایزوله** | تعیین انواع کار مجاز/ممنوع، GitHub token scope، sandbox، egress، سقف زمان/هزینه/درخواست، kill switch و دفاع prompt injection؛ POC فقط با fixture ساختگی و بدون inference بیرونی. | Agent نه secret/production/branch protection/نقش محصول را می‌خواند و نه تغییر می‌دهد؛ prompt injection و egress-denied به توقف امن ختم شوند. اگر مدل محلی/مصوب موجود نیست، POC `BLOCKED` می‌ماند و هزینه/اثر sandbox اندازه‌گیری می‌شود. |
| **G3 · POC task-to-PR کم‌ریسک** | یک مورد مستند/آزمون کوچک به task graph → agent → branch → targeted tests → reviewer → draft PR؛ system logs/evidence بدون کد حساس. | دو run پیاپی قابل‌بازتولید، تست regression ثابت، retry محدود، تغییر test gate ممنوع؛ اگر نتیجه تصادفی/هزینه نامعلوم است `BLOCKED`. هنوز auto-merge و deployment ندارد. |
| **G4 · هویت، API و مجوز محصول** | inventory تمام routeها با actor/permission/scope؛ پیاده‌سازی نگاشت نقشِ تصویب‌شده در G0 (اگر مدل سه‌نقشی انتخاب شد، مهاجرت از roleهای فعلی) و صفحهٔ owner grant؛ ممیزی endpointهای حساس. | `admin` نمی‌تواند grant/role تغییر دهد؛ عضو به دادهٔ دیگری دسترسی ندارد؛ تست منفی direct API، expiry/revoke و عدم ارتقای خود/دیگری پوشش دارد. هیچ role mapping اجرا نمی‌شود تا مالک آن را تأیید کند. |
| **G5 · vertical slice محصول** | جریان‌های انتخاب‌شدهٔ عضو/کادر بر مبنای نمودارها، هرکدام از UI تا DB/صندوق/خروجی؛ ترتیب اولیه پس از G0: ورود/عضویت → تمرین/ارزیابی/تغذیه → QR/کلاس → پیام/اعلان → مالی دستی/گزارش → فروشگاهِ نمایش‌محور. کنترل‌های UI مطابق Q11 از کتابخانهٔ OSS موجود باشند. | برای هر جریان ماتریس پذیرشِ قابل‌مشاهدهٔ مالک، خطا/قطع شبکه و role matrix؛ همهٔ قابلیت‌های اصلی در scope یا `BLOCKED` با دلیل. جریان هدف با رفتار runtime یا client تصمیم‌نگرفته اشتباه نشود. |
| **G6 · DB، topology و بازیابی** | ADR SQLite-vs-PostgreSQL با load/concurrency؛ topology سرور محلی + HTTPS ingress در برابر Full Cloud؛ Compose مرجع و مسئولیت Ansible/Dokploy؛ migration فقط با trigger؛ مسیر backup از DB/private files تا مقصد خارج میزبان. | migration/rollback روی scratch، restore واقعی روی میزبان جدا، retention و RPO/RTO مصوب؛ config نهایی با env ساختگی validate شود؛ بدون credential یا دادهٔ production. |
| **G7 · سخت‌سازی و زنجیرهٔ تأمین** | container hardening به‌ازای سرویس، Trivy و dependency policy، image یک‌بار ساخته‌شده، Syft SBOM و Cosign verification، Renovate PR-only. | digest از build تا staging ثابت، scan result با مالک/استثنا، signature verification در deploy؛ هیچ یافتهٔ بحرانی/بالا بدون تصمیم امنیتی و deadline. |
| **G8 · staging و عملیات** | استقرار واقعی فقط با مجوز staging جدا، دادهٔ ساختگی، smoke flows، rollback برنامه/DB، ingress/probe مستقل، alerts, runbooks, restore drill, incident & privacy review. | مسیر واقعی سرور محلی/HTTPS یا topology مصوب، readiness، تحویل alert، restore، device/browser و RTL/accessibility؛ latency/error baseline و مسئول پاسخ روشن؛ هیچ workflow از PR مستقیم production را trigger نکند. |
| **G9 · Go/No-Go و release** | release candidate مشخص، feature/status matrix، release notes، owner/support plan، migration/backup window و digest تثبیت‌شده. | تمام core flows و security/privacy gates PASS؛ عملیات و پشتیبانی آماده؛ تأیید صریح مالک برای عرضهٔ همهٔ باشگاه. طبق تصمیم جاری، استفادهٔ واقعیِ جزئی/pilot جای تکمیل همهٔ قابلیت‌های اصلی را نمی‌گیرد. هر gate باز، `NO-GO` برای production. |
| **G10 · بهبود عملیاتی** | پایش با SLI/SLO واقعی، restore drill دوره‌ای، dependency/security review، بازبینی هزینه و loop outcomes، policy update با ADR. | هر تغییر سیاست/مدل دسترسی یا گیت با تاریخچه و تست؛ self-heal هیچ‌وقت گیت را پنهان یا تضعیف نکند. |

> زمان‌بندی تقویمی در این سند تخمین زده نمی‌شود. حجم واقعی هر جریان، تصمیم client و topology، database، ظرفیت توسعه‌دهنده، دسترسی به دستگاه/staging و ظرفیت اپراتوری باید در G1 مشخص شوند؛ تخمین قبل از آن عددسازی است.

## ۷. مرز این سند و تبدیل اجرایی بعدی

این نسخه فقط **برنامهٔ کلان محصول تا آمادگی انتشار** را تعریف می‌کند. G0 تا G10 فاز و گیت برنامه‌اند، نه taskهای assign‌شده یا micro-loopهای قابل‌اجرا.

عمداً در این نسخه ساخته نشده‌اند: نگاشت این برنامه به ۱۳ لایه، شناسه‌های loop، microtaskها، dependency DAG اجرایی، فایل prompt/agent، issueهای Beads یا workflow/orchestrator config. هیچ دستور نصب یا اجرای agent هم در این سند صادر نمی‌شود.

فقط پس از تأیید صریح مالکِ همین برنامه و تعیین تصمیم‌های scope که اجرای آن‌ها را مسدود می‌کند، می‌توان در نسخه‌ای جداگانه آن را به ساختار ۱۳ لایه و micro-loopها تبدیل کرد. آن نسخه باید گیت‌ها و شواهد این plan را حفظ کند و اختیار تازه‌ای برای merge، inference بیرونی یا deploy ایجاد نکند.

## ۸. Autonomy ladder و گیت‌های مالک

| سطح | اختیار عامل | اجازهٔ این پیش‌نویس |
|---|---|---|
| **A0 — Analyze** | فقط خواندن، inventory، plan و gap report. | مجاز پس از تصویب scope و رعایت حفاظت داده. |
| **A1 — Test** | تست روی fixture، lint/build و گزارش، بدون تغییر مخزن. | مرحلهٔ نخست POC؛ no secret/no production. |
| **A2 — Draft** | تغییر در worktree/branch محدود، targeted tests و ساخت draft PR. | هدف پایلوت اصلی؛ هیچ merge خودکار. |
| **A3 — Low-risk merge** | merge فقط برای طبقات تغییر کم‌خطر، protected branch، review مستقل، تمام gates سبز و rollback مشخص. | هنوز فعال نشده؛ نیازمند تصمیم جداگانه و شواهد چند run پیاپی. |
| **A4 — Staging** | deploy staging با دادهٔ مصنوعی، readiness و rollback خودکار در failure طبق مجوز محدود. | پس از G6/G7؛ secrets staging با کمترین privilege و مجوز صریح. |
| **A5 — Production** | انتشار production طبق سیاست pre-authorized/owner approval، با digest و rollback. | این طرح مجوز production خودکار نمی‌دهد. پرداخت/DB destructive/RBAC/privacy/high-risk همیشه gate جداگانه دارند. |

### عملیات ممنوع برای agent بدون مجوز مستقل

- دسترسی به secretهای واقعی، account admin، GitHub rules، کلید انتشار یا دادهٔ واقعی؛
- تغییر نقش یا grant محصول، حذف/بازنویسی data، migration production، transaction واقعی، refund یا payment approval؛
- disable کردن تست/اسکن/coverage/backup، گسترده‌کردن allowlist یا تبدیل failure به success؛
- branch switching، force push، پاک‌کردن فایل‌های قبلی/untracked، انتشار log یا code به مدل بیرونی؛
- push/merge/release/deploy خارج از همان مجوز محدود و صریح؛ rollback هم اثر داده/DB دارد و خودکار کور اجرا نمی‌شود.

برای رسیدن به استقلال روزمره، policy و test باید اختیار کم‌خطر را **پیشاپیش، دقیق و قابل‌ابطال** بدهند. درخواست یک‌بارهٔ «خودکار باش» مجوز حذف حفاظ‌ها نیست. منبع کد، دیتاست، exercise/media، فونت/تصویر و خروجی مدل هم license gate مستقل دارد؛ مجوز یک ابزار به داده یا دارایی همراه آن تعمیم پیدا نمی‌کند.

## ۹. آزمون و معیار کیفیت مشترک

### پوشش تست

- **Unit:** محاسبهٔ مالی، permission policy، planner rules، validation و model mapping؛ boundary/rounding/تاریخ تهران.
- **Integration:** API واقعی با DB موقت، transaction/rollback، owner/scope، cache fallback و outbox/job؛ PostgreSQL اگر انتخاب شد.
- **Contract:** OpenAPI/API client و payload واقعی Studio/PWA/Flutter؛ هیچ response mock-only برای پذیرش flow.
- **UI/E2E:** نقش‌های مجاز و ممنوع، focus/keyboard، خطای شبکه، وضعیت empty/stale، فارسی/RTL، عدد و ریال؛ هر کلید مالی/direct route.
- **Device/network:** QR و دوربین، Android lifecycle و push در foreground/background، reconnect/offline، امضای release با دستگاه‌های مجاز.
- **Security:** Gitleaks، Semgrep و bandit/pip-audit موجود حفظ؛ Trivy برای image/config اضافه‌شدنش مشروط؛ test IDOR/prompt injection/egress/secret scope؛ OWASP ASVS را به requirement-evidence matrix تبدیل کنیم، نه ادعای certification.
- **Recovery/performance:** concurrent payment simulation، notification retries، queue overload، disk full، DB disconnect و restore؛ load profile با ۱۰۰ عضو اولیه و همزمانی واقعی پس از اندازه‌گیری تنظیم می‌شود.

### مرز گزارش

- Coverage gate موجود کاهش داده نشود. هیچ ratio ساختگی یا threshold جدید بدون baseline/ADR اضافه نشود.
- هر ادعا نشان دهد test دقیقاً کدام variant، role، platform، DB، code SHA و محیط را اجرا کرده است.
- Success در SQLite/TestClient تعمیم به PostgreSQL/device/prod نیست.
- SLO و RPO/RTO عدد آماده ندارند: baseline measure شود، owner پذیرش کند، بعد alert threshold تعیین شود.
- error/security exception باید owner، دلیل، جبران و تاریخ انقضا داشته باشد؛ دائمی و بی‌نام نماند.

## ۱۰. شاخص‌های عملیات و ارزیابی AI

| بُعد | سنجهٔ پیشنهادی | تفسیر و محدودیت |
|---|---|---|
| تحویل نرم‌افزار | سهم بسته‌های کاری/اجرای عامل با evidence کامل، lead time، reopen/revert، defect leak و flaky tests | تعداد commit یا lines-of-code معیار کیفیت نیست. |
| کیفیت agent | task acceptance rate در fixtureهای ثابت، patch-size، test failures، اصلاحات بعد از review، هزینه/زمان هر task و retry count | ارزیابی روی sample ثابت؛ model-as-judge به‌تنهایی معیار قطعی نیست. |
| امنیت اختیار | ابزارهای خارج allowlist، egress denied، scope violations، تلاش برای خواندن secret، unauthorized access tests | موفقیت آزمایش نباید privilege را برای agent گسترش دهد. |
| تجربهٔ محصول | login/member journey, program/PDF/QR, class/check-in, finance/manual transfer, shop display, chat/notifications | مسیرهای خارج از scope و مسیرهای هدف جدا لیست شوند. |
| عملیات | error rate/p95, readiness, backup age, restore duration, queue lag, disk, alert delivery | آستانه بعد از baseline؛ خود host نمی‌تواند تنها هشدار قطعی خرابی خودش باشد. |
| مالی و داده | duplicate financial events، reconciliation open items، orphan files، access audit و retention exceptions | هدف پیش‌نهادی صفر duplication/unauthorized access؛ نتیجه باید با fixture و لاگ قابل‌ممیزی باشد. |

### مدیریت رخداد

- **P0 security/data/financial incident:** توقف agent runner و deploy، حفظ logهای حداقلی و audit، revoke token/service credentials طبق policy، isolate میزبان، alert owner، برنامهٔ breach/privacy response.
- **P1 service impact:** pause feature flag/route/worker، حفظ DB، readiness/probe و runbook، rollback artifact فقط پس از بررسی schema/data.
- **شکست اجرای عامل:** توقف بعد از سقف تلاش؛ ثبت شناسهٔ prompt/input (بدون secret)، stdout پالایش‌شده، diff/test failure، نسخهٔ model/runtime در صورت استفاده، هزینه و علت احتمالی. کار به صف بازبینی برمی‌گردد؛ retry نامحدود خودکار ندارد.

## ۱۱. ریسک‌ها و کنترل‌ها

| ریسک | اثر | کنترل لازم پیش از عبور از gate |
|---|---|---|
| تعارض PWA با تصمیم Android+Studio در TODO | دو client/UX متفاوت و کار دوباره | baseline Android+Studio حفظ؛ ADR مالک در G0 اگر می‌خواهد PWA را جایگزین کند؛ Flutter محفوظ. |
| نقش‌های شش‌گانهٔ موجود با مدل سه‌گانه | privilege escalation، شکستن مسیر staff | ماتریس role/permission، migration mapping و منفی‌تست تمام routeها؛ `super_admin` فقط grant. |
| AI prompt injection از issue/README/کد | اجرای دستور خصمانه، نشت یا تغییر policy | محتوای repo ورودی غیرقابل‌اعتماد است؛ policy از بیرون sandbox، tool allowlist، no secret، egress controls، reviewer readonly. |
| self-heal بی‌پایان/تضعیف تست | هزینهٔ نامحدود و کیفیت ظاهری | سقف retry/time/request، deterministic gates، fail-closed، stop/quarantine و ممنوعیت تضعیف گیت. |
| AI مدل/وابستگی بی‌مجوز | ریسک حقوقی/هزینه/داده | license per code/data/model/asset؛ no external inference/data egress بدون تصمیم. |
| دوباره‌شماری یا race مالی | از دست‌رفتن پول/گزارش نادرست | atomic/idempotent transaction، ledger, reconciliation، concurrent tests، manual bank verification. |
| Backup در همان میزبان یا مسیر نامنطبق | نبود بازیابی هنگام خرابی host | volume mapping واضح، offsite repository، restore drill، alert و owner. |
| SQLite بدون load/backup کافی یا مهاجرت شتاب‌زده | lock, downtime, data loss | benchmark و ADR؛ migration/rollback/reconciliation قبل از تغییر. |
| دو Compose و دو مسیر deploy | drift بین staging/production و rollback ناقص | canonical contract، rendered config، pinned digest و staging rehearsal. |
| cache/offline هر client منتخب | نمایش دادهٔ منقضی یا نوشتن پس از revoke | online-first، API no-cache، cache کم‌حساس، offline writes فقط پس از design+tests؛ رفتار Flutter/PWA جداگانه سنجیده شود. |
| telemetry/logهای حساس | افشای سلامت/هویت/مالی | field-level redaction, data retention, role access, tests and separate telemetry endpoint. |
| rollout بدون پشتیبانی/اپراتور | incident طولانی و دادهٔ ناسازگار | owner on-call، runbooks، alert route، staging, restore, feature flags و Go/No-Go. |
| پذیرش کاذب ناشی از mock-only tests | تصور نادرست از bank/device/production | mock فقط boundary test؛ external/device/environment evidence صریح و جدا. |

## ۱۲. مسئولیت و تصمیم‌های در انتظار مالک

| نقش/مسئول | مسئولیت تصمیم/شاهد |
|---|---|
| مالک محصول (`super_admin` در سامانه) | تصویب scope/client، نقش‌ها و مجوز، سیاست پرداخت/فروشگاه، هزینه/پشتیبانی، انتشار و exceptionهای پرریسک. این نقش محصول با GitHub org admin یکی نیست. |
| عامل برنامه‌ریز | task graph، dependency و معیار؛ اختیارات محدود read/planning؛ هیچ تأیید عملیاتی. |
| عامل سازنده | patch در scope و branch ایزوله؛ بدون production/secret و بدون self-approval. |
| بازبین مستقل | architecture/security/test review readonly؛ اختلاف را مستند می‌کند؛ reviewer باید جدا از نویسنده باشد. |
| CI/verifier | deterministic tests/scans/build، artifact digest و evidence؛ خودکار و بدون تغییر محصول. |
| اپراتور/DevOps | میزبان، secret delivery، backup/restore، monitor/alert، staging و incident. تا تعیین نام/دسترسی، این مسئولیت `UNASSIGNED` است. |
| متخصص حقوق/مالی | privacy/retention، منشأ و مجوز داده، تعریف حسابداری و الزامات مالی. AI code review جایگزینش نیست. |

### تصمیم‌هایی که پیش از گیت G0 باید ثبت شوند

1. **Client scope:** TODO محصول Android عضو + Studio وب را مسیر انتشار اول می‌داند؛ فلوچارت PWA مشترک یک طراحی هدف متعارض است. آیا baseline فعلی را تأیید می‌کنید یا آن را با ADR به PWA تغییر می‌دهید؟ هیچ فایل Flutter حذف نمی‌شود.
2. **Topology و ingress:** TODO محصول سرور محلی باشگاه + ورودی HTTPS ارزان را می‌گوید؛ طرح Full Cloud قدیمی‌تر است. آیا همین baseline جاری است؟ اگر VPS/tunnel/روش دیگری انتخاب می‌شود، مالکیت، میزبان، راه‌اندازی و بودجه باید مشخص شوند.
3. **Payment source of truth:** TODO جاری کارت‌به‌کارت با تطبیق انسانی و فروشگاه نمایش‌محور/خرید حضوری را می‌گوید؛ سند Full Cloud هنوز Zarinpal را مطرح می‌کند. آیا متن قدیمی رسماً supersede و مسیر درگاه برای انتشار اول بسته بماند؟
4. **Data topology:** یک باشگاه/نصب مستقل baseline است؛ آیا multi-tenant واقعاً نزدیک‌مدت است؟ تا پاسخ مثبت، tenant architecture/DB مشترک اضافه نشود.
5. **Database trigger:** حداکثر load/concurrency، write contention، availability/restore expectations؛ معیار انتخاب SQLite/PG و صاحب ADR.
6. **Autonomy ceiling:** کدام تغییرها تا A2 (draft PR) می‌مانند و آیا بعداً A3 low-risk merge مجاز است؟ production همچنان gate جدا دارد.
7. **Model policy:** گیت‌های قطعی بدون API مدل اجرا می‌شوند و inference بیرونی پیش‌فرض ممنوع است. آیا برای پایلوت عامل، مدل محلیِ موجود/مجاز کافی است یا می‌خواهید provider بیرونی را با بودجه و مرز داده جداگانه تأیید کنید؟
8. **Operator & resilience:** میزبان/ingress و backup خارج‌میزبان، بودجه، on-call، RPO/RTO، ساعات پشتیبانی، uptime objective و probe مستقل.
9. **Security/privacy:** route/data/role matrix نهایی، retention و purge، notice/consent و مقررات حوزهٔ خدمت؛ متخصص/مالک تأیید.
10. **Scope of «همهٔ قابلیت‌های اصلی»:** feature flows دقیق از نمودارها، نسخهٔ زبان/RTL، دستگاه‌ها و این‌که client منتخب و notification push کدام در انتشار اول لازم‌اند.

## ۱۳. چک‌لیست تأیید همین برنامه

با تأیید این سند، فقط اجازهٔ **تبدیل macro-plan به ۱۳ لایه و loop plan** را می‌گیریم؛ خودبه‌خود مجوز نصب ابزار، تغییر محصول، push/merge، استفاده از مدل بیرونی، خرید، مهاجرت داده یا deploy صادر نمی‌شود.

- [ ] اصل معماری modular monolith و الزام تکمیل همهٔ قابلیت‌های اصلی پیش از انتشار واقعی را می‌پذیرم.
- [ ] مسیر انتشار Android عضو + Studio وب (طبق TODO) مبنا بماند؛ یا PWA مشترک با ADR مالک آن را جایگزین کند. فایل‌های Flutter/Android حذف نمی‌شوند.
- [ ] سرور محلی باشگاه + ورودی HTTPS ارزان (طبق TODO) مبنا بماند؛ Full Cloud یا تغییر ingress نیازمند تصمیم و بودجهٔ جداست.
- [ ] مدل نقش هدف `super_admin/admin/member` و owner-only grants را با نگاشت/مهاجرت امن از نقش‌های فعلی می‌پذیرم؛ یا قبل از تبدیل plan اصلاحش می‌کنم.
- [ ] فروشگاه نمایش‌محور/خرید حضوری و کارت‌به‌کارت با تطبیق انسانی مبنا بماند؛ سند قدیمی Zarinpal با تصمیم جدید به‌صورت ADR/مستند رسمی هم‌راستا شود.
- [ ] هیچ inference/API بیرونی پیش‌فرض نیست؛ مدل محلی هم فقط با مجوز weights، سخت‌افزار و تصمیم جدا به کار می‌رود.
- [ ] اختیار اولیهٔ عامل A0–A2 و draft PR باشد؛ auto-merge/deploy فقط با policy و مجوز جدا بررسی شود.
- [ ] پس از تأیید این macro-plan، آن را در مرحلهٔ بعد به ساختار ۱۳ لایه و micro-loopها تبدیل کنیم؛ این checkbox مجوز نصب ابزار، کدنویسی یا deployment نیست.

**فعلاً هیچ checklistی علامت‌خورده نیست.** پس از پاسخ/تأیید، نسخهٔ بعدی باید با تصمیم‌ها به‌روزرسانی و سپس تنها آن نسخه به loop plan تبدیل شود.

## ۱۴. منابع GitHub متن‌باز در این طرح

- [OpenProject](https://github.com/opf/openproject) (GPL-3، Community edition)، [LikeC4](https://github.com/likec4/likec4) (MIT)، [Beads](https://github.com/steveyegge/beads) (MIT).
- [LangGraph](https://github.com/langchain-ai/langgraph) (MIT)، [Temporal](https://github.com/temporalio/temporal) (MIT)، [Podman](https://github.com/containers/podman) و [gVisor](https://github.com/gvisor/gvisor) (Apache-2.0).
- [Aider](https://github.com/Aider-AI/aider) (Apache-2.0)، [SWE-agent](https://github.com/SWE-agent/SWE-agent) و [Promptfoo](https://github.com/promptfoo/promptfoo) (MIT).
- [Trivy](https://github.com/aquasecurity/trivy)، [Scorecard](https://github.com/ossf/scorecard)، [Woodpecker](https://github.com/woodpecker-ci/woodpecker)، [Harbor](https://github.com/goharbor/harbor)، [OPA](https://github.com/open-policy-agent/opa)، [OpenFGA](https://github.com/openfga/openfga)، [Syft](https://github.com/anchore/syft)، [Cosign](https://github.com/sigstore/cosign) و [OpenTelemetry Collector](https://github.com/open-telemetry/opentelemetry-collector) (مجوزهای آزاد در repositoryها؛ انتخاب نهایی و مجوز همهٔ اجزا قبل از adoption بازبینی شود).
- پروژه‌های repository رایگان‌اند؛ میزبانی، سخت‌افزار، انرژی، push provider، هزینهٔ پیامک، API مدل و مجوز weights بیرونی را رایگان فرض نکن.
