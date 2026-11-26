# فهرست راهنمای جامع Muscle Paradise

> **سند یکپارچه:** برای خواندن همهٔ پنج فصل در یک فایل، از [PROJECT_GUIDE.fa.md](../PROJECT_GUIDE.fa.md) شروع کنید. فصل‌های این پوشه منبع ماژولار نگهداری آن سند هستند؛ پس از تغییر فصل‌ها `python3 scripts/assemble_project_guide.py` را اجرا و سپس `python3 scripts/assemble_project_guide.py --check` را بررسی کنید.
>
> **هدف:** خواننده‌ای که هیچ پیش‌زمینه‌ای ندارد بتواند محصول، اجزای فنی، جریان‌های کاری، داده، API، اجرا، آزمون، محدودیت‌ها و اسناد تصمیم را با یک مسیر مطالعهٔ پیوسته بفهمد.
>
> **مبنای این نسخه:** checkout شاخهٔ `arena/5e0f64cf-mp`؛ HEAD پیش از افزودن این راهنما `a30e6bff01dee6153cf1cff2521c71e6b9c14b07` بود و working tree از قبل تغییرات محلی داشت. بنابراین این راهنما snapshot **کد و اسناد موجود در همان working tree** را توصیف می‌کند، نه ادعای این‌که همهٔ تغییرات آن commit یا منتشر شده‌اند. برای حقیقت فعلی همیشه `git status`، کد و تست همان مسیر را بررسی کنید.
>
> در این مستندسازی، فایل پایگاه‌دادهٔ ریشه و محتوای رسیدهای خصوصی بازبینی نشدند؛ محتوای محرمانه، دادهٔ شخصی یا کلید واقعی در سندها نقل نشده است.
>
> **حد دامنه:** این نخستین راهنمای معماری/عملیات و onboarding است، نه توضیح لفظ‌به‌لفظ همهٔ چندصد فایل source یا تأیید کامل featureها. فهرست فایل/مدل/route و پیوندهای تست برای ادامهٔ ممیزی آمده‌اند؛ پایان‌دادن مرور semantic هر route/فایل همچنان کار باز است و در [بخش دامنهٔ بازبینی](05-security-status-glossary.md) صریح شده است.

## مسیر مطالعه

1. [نقشهٔ پروژه و معماری](01-project-map.md) — محصول چیست، چه نقش‌هایی دارد، مخزن چگونه تقسیم شده و چه چیزی هدف در برابر پیاده‌سازی است.
2. [Backend، API و داده](02-backend-and-data.md) — چرخهٔ درخواست، ماژول‌های FastAPI، مدل‌ها، مهاجرت‌ها، امنیت مسیرها و سرویس‌های پس‌زمینه.
3. [Clientها و سفرهای کاربر](03-clients-and-workflows.md) — Flutter، Studio/PWA، نشست، ویژگی‌ها و جریان‌های واقعی/ناتمام.
4. [توسعه، آزمون و عملیات](04-development-testing-operations.md) — پیش‌نیازها، اجرای محلی، متغیرهای محیطی، گیت‌های CI، Docker، پشتیبان و استقرار.
5. [امنیت، وضعیت و واژه‌نامه](05-security-status-glossary.md) — مرزهای حریم/امنیت، ادعاهای اثبات‌شده در برابر باز، تناقض‌های اسناد و اصطلاحات.

## نقشه‌های مرجع تکمیلی

| نیاز | مرجع |
|---|---|
| آشنایی کوتاه و quickstart | [README ریشه](../../../README.md) · [راهنمای مستندات](../../README.md) |
| توضیح architecture و نمودارها | [Architecture Atlas](../architecture/README.md) · [System Atlas](../architecture/system-atlas.md) · [C4 تاریخی](../architecture/c4.md) |
| تصمیم پذیرفته‌شدهٔ baseline PWA انتشار اول | [ADR-007](../adr/007-pwa-primary-release.md) · [فهرست ADRها](../adr/README.md) |
| route inventory و سیاست دسترسی | [`routes.json`](../../../mp-app/backend/api/routes.json) · [`export_routes.py`](../../../mp-app/backend/scripts/export_routes.py) · [کاتالوگ خوانای ۱۶۳ عملیات (snapshot کاری)](../architecture/session-decisions-2026-11-23/API-ROUTE-CATALOG.md) |
| زنجیرهٔ UI→API→DB، سفرها و شواهد سناریو | [Wiring ledger (بستهٔ بازبینی کاری)](../architecture/session-decisions-2026-11-23/WIRING-LEDGER.md) · [تحلیل ۲۰۲۶-۱۱-۲۳](../architecture/analysis-2026-11-23.md) |
| صف محصول و پاسخ تصمیم‌گیرنده | [TODO جاری/تصمیم‌های مالک](../TODO-CLOUD-FINANCE-ACCESS.md) · [ADRها](../adr/README.md) |
| اجرا و release | [Deployment](../DEPLOYMENT.md) · [Ops runbook](../OPS-RUNBOOK.md) · [Release checklist](../RELEASE-CHECKLIST.md) |
| حریم داده | [سیاست نگهداری داده](../DATA-RETENTION.md) · [`modules/privacy/retention.py`](../../../mp-app/backend/modules/privacy/retention.py) |
| استانداردهای مشارکت | [`AGENTS.md`](../../../AGENTS.md) · [راهنمای مخزن](../../../README.md) |

> **دربارهٔ snapshotهای کاری:** برخی سندهای داخل `architecture/session-decisions-2026-11-23/` و خود ADR-007 در checkout دیده می‌شوند اما در وضعیت Git این بررسی untracked بودند. آن‌ها در working tree موجودند، ولی تا وقتی همراه تغییرشان در Git ثبت نشوند، clone تمیز الزاماً آن‌ها را ندارد. route JSON و سورس برنامه مرجع پایدارترند.

## اصل راهنما: چهار وضعیت را قاطی نکنید

- **در کد:** ساختار یا منطق در فایل جاری دیده می‌شود.
- **آزموده:** فقط همان سناریو و همان محیطی که تست/CI واقعاً اجرا کرده.
- **تصمیم محصول:** انتخابی که در ADR یا پاسخ مالک ثبت شده؛ به‌تنهایی اجرای فنی نیست.
- **هدف/نامعلوم:** طرح آینده یا چیزی که شواهد کافی برای آن نداریم.

وجود endpoint، صفحه، تست، Compose یا دیاگرام به‌تنهایی اثبات اجرای end-to-end، اتصال سرویس بیرونی، استقرار production یا آمادگی انتشار نیست. هر وقت این راهنما با source یا تست جاری اختلاف پیدا کرد، source/test را مقدم بگیرید و سند را اصلاح کنید.
