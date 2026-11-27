# Architecture Atlas — نقشهٔ معماری

> این پوشه مرجع نمودارهای معماری است. از نو ترسیم نکن؛ ابتدا سند موجود را بخوان و اختلافش با کد را با شاهد ثبت کن.

## نقشه‌های موجود

| سطح | سند | چه چیزی را توضیح می‌دهد |
|---|---|---|
| **فلوچارت یکپارچهٔ کل برنامه** | [صفحهٔ اصلی](muscle-paradise-full-program-flow-v1-2026-11-23.md) · [نقشهٔ کامل PNG v2](muscle-paradise-combined-flow-v2-2026-11-23.png) · [SVG بزرگ‌نمایی‌پذیر](muscle-paradise-combined-flow-v2-2026-11-23.svg) · [ZIP نمودارها](muscle-paradise-architecture-diagrams-v1-2026-11-23.zip) · [DOT](muscle-paradise-combined-flow-v2-2026-11-23.dot) | مسیرهای جاری عضو/کادر و تراکنش‌ها به‌علاوهٔ چرخهٔ پیشنهادی برنامه، منبع‌ها، PDF/QR و بازخورد؛ تفاوت current/target مشخص است |
| **فلوچارت تاریخیِ مقصد PWA و دسترسی‌ها** | [شرح و محدودیت وضعیت](muscle-paradise-final-pwa-access-flow-v1-2026-11-23.md) · [PNG](muscle-paradise-final-pwa-access-flow-v1-2026-11-23.png) · [SVG](muscle-paradise-final-pwa-access-flow-v1-2026-11-23.svg) · [DOT](muscle-paradise-final-pwa-access-flow-v1-2026-11-23.dot) · [ZIP نمودارها](muscle-paradise-architecture-diagrams-v1-2026-11-23.zip) | تصویر target-only و snapshot قدیمیِ سه‌نقشی است، نه منبع تصمیم جاری. [ADR-007](../adr/007-pwa-primary-release.md) baseline جاری عضو/کادر را تعیین می‌کند و OQ-03 شش نقش را حفظ می‌کند؛ وضعیت و acceptance فقط از [TODO canonical](../TODO-2026-11-16.md#pwa-ui-ux-full-backlog-2026-11-23) و [tracker](../TODO-PWA-RELEASE-2026-11-23.fa.md) پیگیری می‌شوند. تصویر/منبع آن پیاده‌سازی یا QA را ثابت نمی‌کند؛ Flutter/Android حفظ می‌شود. |
| **Option 03 — LAB · مرجع طراحی UI/UX** | [سند فلو و محدودیت‌ها](frontend-ui-ux-flow-option-03-lab-v1-2026-11-23.md) · [ADR-007](../adr/007-pwa-primary-release.md) · [TODO canonical](../TODO-2026-11-16.md#pwa-ui-ux-full-backlog-2026-11-23) · [tracker](../TODO-PWA-RELEASE-2026-11-23.fa.md) · [دفتر وضعیت اجرا](../PWA-EXECUTION-STATE.md) | فقط visual direction/design reference؛ نمودارها و screenshotها شاهد پیاده‌سازی، پذیرش PWA یا QA نیستند. claims قدیمی Android/PWA در خود سند snapshot تاریخی‌اند. |
| **معماری هدف و شکاف‌های زیرساخت** | [تحلیل و اولویت‌ها](muscle-paradise-world-class-target-architecture-v1-2026-11-23.md) · [PNG](muscle-paradise-world-class-target-architecture-v1-2026-11-23.png) · [SVG بزرگ‌نمایی‌پذیر](muscle-paradise-world-class-target-architecture-v1-2026-11-23.svg) · [DOT](muscle-paradise-world-class-target-architecture-v1-2026-11-23.dot) · [ZIP نمودارها](muscle-paradise-architecture-diagrams-v1-2026-11-23.zip) | نقشهٔ هدف مرحله‌ای از وضعیت مشاهده‌شده؛ SQLite/PostgreSQL و ابزارهای اختیاری صریحاً مشروط‌اند و وضعیت فعلی با پیشنهاد اشتباه گرفته نشده است |
| **برنامهٔ کلان تولید و آمادگی انتشار با عامل‌های AI** | [پیش‌نویس نسخهٔ ۱](ai-autonomous-production-plan-v1-2026-11-23.md) | فازها، گیت‌های Go/No-Go و کنترل‌های اختیار؛ baseline محصول با OQ-01…10 هم‌راستا شده است، اما این سند به‌تنهایی ۱۳ لایه/micro-loop یا مجوز اجرا نیست |
| **پیش‌نویس خردسازی Finn-loop** | [پیش‌نویس مستقل تاریخی](finn-loop-microtask-backlog-draft-v1-2026-11-23.md) | کارت‌های D-01…D-11 snapshot پیش از OQ-01…10 هستند؛ برای صف اجرا ملاک نیستند. هیچ issue یا مجوز اجرای Finn ایجاد نمی‌شود. |
| **Motion/reduced-motion — crosswalk و handoff** | [فهرست sandbox/Codespace و گیت‌های بیرونی](motion-pwa-availability-matrix-2026-11-23.fa.md) · [crosswalk ایستای current-tree و browser evidence](studio-motion-current-tree-static-crosswalk-2026-11-23.fa.md) · [صف canonical](../TODO-2026-11-16.md#pwa-ui-ux-full-backlog-2026-11-23) · [tracker](../TODO-PWA-RELEASE-2026-11-23.fa.md) · [دفتر اجرا](../PWA-EXECUTION-STATE.md) | synthetic browser evidence محدود؛ سه follow-up همچنان PARTIAL، device/OS، screen reader و reviewer مستقل جدا هستند |
| **System Atlas** | [system-atlas.md](system-atlas.md) | تصویر README، گراف متنی، وضعیت ادعاها و مسیرهای کد مرتبط |
| **C4 — Context** | [c4.md](c4.md) | نقش‌های عضو، مربی، پذیرش و مدیر؛ مرز محصول و سامانه‌های بیرونی |
| **C4 — Container** | [c4.md](c4.md) | Client، Studio، API، پایگاه داده، cache، jobها و مرزهای شبکه |
| **C4 — Component** | [c4.md](c4.md) | مسئولیت ماژول‌های FastAPI و ارتباط‌های دامنه |
| **Code / Module** | [c4.md](c4.md) · [module-map.md](module-map.md) | الگوی درونی هر ماژول، وابستگی‌ها و جریان‌های مهم؛ هر دو snapshot اولیه |
| **هدف ابری، مالی و دسترسی** | [cloud-finance-access.md](cloud-finance-access.md) | وضعیت موجود در برابر هدف، پرداخت انسانی و QA هر میکرولوپ؛ نه تأیید پیاده‌سازی |
| **جریان‌های بازبینی PR** | [pr-review-flows-2026-11-18.md](pr-review-flows-2026-11-18.md) | بازگشت وجه، QR و checkpoint؛ یافته‌ها و مرز هر شاهد |
| **RepoWise snapshot بازبینی** | [گراف DSL](repowise-pr-review-2026-11-18.dsl) · [فهرست ورودی](repowise-pr-review-scope-2026-11-18.txt) | snapshot انتخابی از commit بازبینی‌شده؛ نه index کامل یا اثبات runtime |
| **مسیر کامل ورزشکار و بازطراحی چرخهٔ بعد** | [سند lifecycle](athlete-program-lifecycle-v2-2026-11-23.md) · [فلوچارت برگشت v3](athlete-program-return-workflow-v3-2026-11-23.png) · [scorecard و ساختار v3](athlete-program-component-score-rebuild-v3-2026-11-23.png) · [مشخصات JP7/QR canonical v6](athlete-jp7-program-qr-v6-2026-11-23.md) · [فلوچارت نهایی QR/سنجش/برنامه](athlete-jp7-program-qr-flow-v6-2026-11-23.png) | طرح محصول؛ نه قابلیت runtime |
| **فلوهای مستقل عضو / Studio / تراکنش** | [راهنمای نمودارها](member-studio-dataflow-v1-2026-11-23.md) · [Flutter عضو (DOT)](member-app-dataflow-v1-2026-11-23.dot) · [Studio (DOT)](studio-dataflow-v1-2026-11-23.dot) · [یافته‌های تراکنشی (DOT)](transaction-findings-flow-v1-2026-11-23.dot) | route/service/DB از کد ردیابی شده؛ تصویرها جدا و بازتولیدپذیرند؛ نمودارها به‌تنهایی شاهد E2E یا production نیستند |
| **مسیریابی منابع ورزشی** | [سند سؤال→منبع→لایه](open-source-question-routing-and-layered-data-architecture-v1-2026-11-23.md) · [Graphviz DOT flow](open-source-question-routing-flow-v1-2026-11-23.dot) · [درخت source registry](open-source-source-registry-tree-v1-2026-11-23.dot) | منبع‌ها جدا و license-gated؛ Graphviz imageها از DOT بازتولید می‌شوند، نه دادهٔ زنده |

### چهار سطح C4 در این مخزن

1. **Context:** بازیگران و سامانه‌های بیرونی؛
2. **Container:** اپ عضو، پنل تیم باشگاه، API و زیرساخت داده؛
3. **Component:** router/service/repository و ماژول‌های دامنهٔ backend؛
4. **Code:** فایل‌ها و مرزهای import در یک ماژول.

سندهای C4 و نقشهٔ ماژول‌ها، نقشهٔ قابل‌خواندن‌اند؛ آن‌ها به‌تنهایی اثبات نمی‌کنند یک مسیر end-to-end در runtime کامل است. وضعیت هر جریان را در TODO جاری، کد و تست همان مسیر تأیید کن.

## مسیرهای مستندشده

`module-map.md` جریان‌های حیاتی را نام‌گذاری می‌کند، از جمله ثبت‌نام/پرداخت/check-in، پیشنهاد و تأیید برنامه، و check-in چهره/QR. پیش از ادعای «کامل»، route، policy مالکیت/نقش و تست/شاهد جاری را در `mp-app/backend/` و مصرف‌کنندهٔ واقعی در `mp-app/client/` یا `mp-app/studio/` بررسی کن.

## صفحه‌های ماژول (یک زیرسیستم = یک صفحه)

| دامنه | صفحه | وضعیت ادعاها |
|---|---|---|
| Shop — کاتالوگ/سبد/سفارش/رسید | [modules/shop.md](modules/shop.md) | مسیرها verified؛ runtime عضو `unknown`؛ چاپ و inventory race `target`/`unknown` |

قرارداد این صفحه‌ها (DX-REP-01، بند ۳): مسئولیت، مسیر کد/API/مدل داده، یک Mermaid flow، جدول «ادعا ↔ برچسب ↔ چرا» و پیوند به تست همان مسیر. نقشهٔ `c4.md`/`module-map.md` بازتولید نمی‌شود. `scripts/docs_gate.py` هر `modules/*.md` را خودکار به چک لینک اضافه می‌کند، پس صفحهٔ تازه بدون ویرایش اسکریپت هم تحت گیت می‌افتد؛ ادعای بدون شاهد با برچسب `target`/`unknown` می‌ماند.

## چه زمانی باید این نقشه‌ها به‌روز شوند؟

- افزوده/حذف‌شدن container، سرویس بیرونی یا مسیر شبکه؛
- جابه‌جایی مرز ماژول، وابستگی بین ماژول‌ها یا الگوی لایه‌بندی؛
- تغییر قرارداد API، مدل داده یا جریان end-to-end؛
- تغییر مرز امنیت/حریم خصوصی، پرداخت، check-in یا deployment.

برای انتخاب معماری جدید، ابتدا [ADR index](../adr/README.md) و [قالب ADR](../adr/TEMPLATE.md) را ببین. توضیحِ یک وضعیت موجود را در C4 به‌روز کن؛ تصمیم تازه را به‌صورت ADR جدید ثبت کن.

## قرارداد صحت و نمایش

- پیش‌فرض دیاگرام‌های مستندات Mermaid متنی است تا diff/review ساده بماند؛ برای گراف متراکمِ منبع‌ها/routeهای چندبه‌چند، درخواست کاربر با Graphviz DOT اجرا شده و فایل `.dot` کنار PNG/SVG حفظ می‌شود تا خروجی بازتولیدپذیر بماند.
- پیکانِ هدف یا آینده‌نگر را با برچسب **هدف/پیشنهادی** و خط‌چین نشان بده؛ جریان تأییدشده را بدون شاهد، خط پیوسته نکش.
- کنار هر claim مهم، مسیر کد/تست را بنویس. شمارهٔ خط را فقط اگر لازم است اضافه کن و در تغییر بعدی دوباره بررسی‌اش کن.
- «آزموده‌نشده/نامعلوم» از «پیاده‌نشده» متفاوت است؛ در صورت نبود شاهد، `UNKNOWN` ثبت کن.
- جزئیات آزمون جاری، محدودیت‌ها و کارهای باز در [صف جاری](../TODO-2026-11-16.md) است؛ نسخهٔ قدیمی C4 را بر صف جدید مقدم ندان.


## افزونهٔ جریان‌های ارزش نامزد

[نقشهٔ هدف تمرین، حضور و فیش](oss-value-flows.md) با سرنخ RepoWise روی mirror ایزوله و تطبیق دستی source ساخته شد؛ پیکان‌های هدف، شاهد E2E یا تأیید امنیت نیستند.
