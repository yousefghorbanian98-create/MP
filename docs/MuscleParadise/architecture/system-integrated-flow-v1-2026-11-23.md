# نقشهٔ یکپارچهٔ مکانیزم Muscle Paradise — پیش‌نویس برای بازبینی مالک

> **وضعیت:** نسخهٔ جامعِ یکپارچه برای بازبینی شما؛ تا تأیید شما «تصمیم رسمی»، ADR یا مرجعِ منتشرشده در Architecture Atlas نیست. مطابق خواسته‌تان، به فهرست رسمی معماری/ADR اضافه نشده است. پیکان‌های فعلی، قابل‌ردیابی در کد/قراردادند؛ پیکان‌های خط‌چین کهربایی فقط طرح/هدف‌اند.
>
> **مبنای snapshot:** worktree شاخهٔ `arena/5e0f64cf-mp` با HEAD `35d4b35184b4148c658b415bd009fc076bf24e00`؛ تغییرهای محلی قبلی حفظ شده‌اند. وضعیت staging/production از روی این نمودار تأیید نمی‌شود.

## فایل‌ها

- **نمای اصلی برای دیدن:** [PNG با وضوح بالا](system-integrated-flow-v1-2026-11-23.png)
- **نمای بزرگ‌نمایی‌پذیر:** [SVG](system-integrated-flow-v1-2026-11-23.svg)
- **منبع قابل‌ویرایش و بازتولید:** [Graphviz DOT](system-integrated-flow-v1-2026-11-23.dot)
- **دفتر تصمیم‌های این نشست (پیش‌نویس):** [README مجموعه](session-decisions-2026-11-23/README.md) · [Decision log](session-decisions-2026-11-23/DECISION-LOG.md)
- **جزئیات wiring و شکاف‌ها:** [WIRING-LEDGER](session-decisions-2026-11-23/WIRING-LEDGER.md)
- **همهٔ عملیات route فعلی:** [API-ROUTE-CATALOG](session-decisions-2026-11-23/API-ROUTE-CATALOG.md)
- **برگهٔ تأیید:** [APPROVAL-CHECKLIST](session-decisions-2026-11-23/APPROVAL-CHECKLIST.md)

## چگونه این نمودار را بخوانید

1. **چپ به راست:** نقش/کلاینت → صفحه/کنترل → درخواست API → احراز هویت و مجوز سمت سرور → router/service → داده/فایل/اتصال جانبی → پاسخ و حالت UI.
2. **سبز/آبی و خط پیوسته:** وضعیت یا wiring قابل‌ردیابی در کد/قرارداد فعلی. این رنگ‌ها به‌تنهایی تست E2E، اجرای دستگاه یا آمادگی production را ثابت نمی‌کنند.
3. **قرمز:** گپ/رفتار ناقص یا مسیر fail-closed که باید درست به کاربر توضیح داده شود.
4. **کهربایی و خط‌چین:** proposal/هدف آینده، یا مسیر وابسته به تنظیم/تصمیم. عمدی است که آن را به مسیر فعلی نچسبانیم.
5. برای روان‌ماندن خواندنِ تصویر، تمام ۱۶۳ operation به‌صورت کارت جدا داخل PNG نیامده‌اند؛ **فهرست مکانیکی تک‌تک متدها/مسیرها/guardها/نقش‌ها** در API-ROUTE-CATALOG قرار دارد. نمودارهای جزئی‌تر نیز از همان گره‌های دامنه لینک شده‌اند.

## گسترهٔ مکانیزم در یک نگاه

| لایه | آنچه در نمودار و اسناد پیوست پوشش داده شده |
|---|---|
| نقش و پلتفرم | نقش‌های فعلی `member/coach/reception/manager/admin/super_admin`؛ اپ عضو Flutter/Android و پنل کارکنان React/Vite؛ PWA یکپارچه جدا و تصویب‌نشده است. |
| تعامل UI | ورود/نشست، shell و صفحه‌ها، form/query/mutation، loading/empty/error/offline/conflict، حفظ ورودی، جلوگیری از ارسال دوباره، reduced-motion و مرزهای دسترس‌پذیری. |
| امنیت درخواست | OTP/access/refresh، احراز هویت، role، permission/grant و ownership/scope در backend؛ گیت منو فقط UX است. |
| جریان دامنه | پروفایل/اشتراک، intake و برنامه، ارزیابی، nutrition و food logs، کلاس/waitlist، QR check-in، کیف‌پول/پرداخت/بازپرداخت، فروشگاه، هزینه/گزارش، chat/notification، settings/audit. |
| Backend و داده | FastAPI `/api/v1`، router → service، SQLAlchemy/SQLite پیش‌فرض، مدل‌های دامنه، فایل فیش خصوصی، cache، audit/outbox و سرویس‌های زمانی. وضعیت runtime هر job/اتصال جدا ذکر شده است. |
| اتصال و عملیات | SMS و پرداخت وابسته به پیکربندی، دادهٔ مالی انسانی، health/metrics، proxy/Compose؛ وجود config/route به معنی سرویس زنده یا استقرار نیست. |
| چرخهٔ هدف | سؤال/منبع مجاز → گیت کیفیت/ایمنی → برنامهٔ نسخه‌دار → تأیید مربی → PDF/QR خصوصی → لاگ/سنجش → چرخهٔ بعد؛ کل این شاخه هنوز proposal است. |

## نمودارها و اسنادی که برای ادغام باز و خوانده شدند

**جریان‌های فعلی و اتصال کد/داده:**

- [فلوچارت یکپارچهٔ قبلی v2 و یادداشت محدودیت‌ها](muscle-paradise-full-program-flow-v1-2026-11-23.md) و source آن [DOT](muscle-paradise-combined-flow-v2-2026-11-23.dot)؛
- [اپ عضو: Flutter → API → service → data](member-app-dataflow-v1-2026-11-23.dot)؛ [Studio → endpoint → service → data](studio-dataflow-v1-2026-11-23.dot)؛ [checkout/class/refund](transaction-findings-flow-v1-2026-11-23.dot)؛
- [UI/UX نمای کلی](frontend-ui-ux-overview-option-03-v1-2026-11-23.dot)، [عضو](frontend-ui-ux-member-option-03-v1-2026-11-23.dot)، [Studio](frontend-ui-ux-studio-option-03-v1-2026-11-23.dot) و [قرارداد wiring کنترل‌ها](frontend-ui-ux-control-wiring-option-03-v1-2026-11-23.dot)؛
- [API route artifact](../../../mp-app/backend/api/routes.json)، [تعامل صفحه→endpoint→تست](interaction-map.json) و generator/gate آن [`scripts/interaction_map.py`](../../../scripts/interaction_map.py)؛
- [تحلیل code/test و محدودیت‌ها](analysis-2026-11-23.md)، [نقشهٔ فعلی سیستم](system-atlas.md)، [C4](c4.md) و [module map](module-map.md).

**هدف/طرح‌های آینده که در نمودار کهربایی مانده‌اند:**

- [PWA و access target](muscle-paradise-final-pwa-access-flow-v1-2026-11-23.md)، [target infrastructure](muscle-paradise-world-class-target-architecture-v1-2026-11-23.md)؛
- [چرخهٔ ورزشکار و program lifecycle](athlete-program-lifecycle-v2-2026-11-23.md)، [JP7/ProgramVersion/QR](athlete-jp7-program-qr-v6-2026-11-23.md)، [routing منابع سؤال‌به‌منبع](open-source-question-routing-and-layered-data-architecture-v1-2026-11-23.md)، [برنامه‌ساز/PDF](training-program-builder-design-2026-11-23.md).

> **تعارض‌هایی که برای جلوگیری از ادغام ادعاهای کهنه حل‌نشده نگه داشته شدند:** `TODO-CLOUD-FINANCE-ACCESS.md` رابط انتشار را Android عضو + Studio وب می‌داند؛ پس PWA target را current نخواندم. `analysis-2026-11-23.md` می‌گوید body contractِ `gate-check` اصلاح و در TestClient موفق شده؛ متن قدیمی‌تر فلوچارت overview/full-flow هنوز 422 می‌گوید، بنابراین در نمودار تازه ادعای قدیمی تکرار نشده است. route artifact، سند تعامل و این نمودار هر کدام snapshot/محدودیت خود را دارند؛ catalog همراه برای عدد دقیق متدها منبع مستقیم JSON است.

## اعداد پوشش و محدودیت مهندسی

در snapshot خوانده‌شده، `routes.json` شامل **۱۶۳ رکورد operation** و **۱۴۱ الگوی path یکتا** است. نقشهٔ interaction، **۳۱ سطح** (۱۳ صفحهٔ Studio + ۱۸ گروه feature در Flutter) دارد و gate آن رانش قرارداد را صفر گزارش می‌کند. پنج سطح دارای endpoint در خروجی interaction-map با تست صفحه‌ایِ قابل‌تشخیص توسط generator match نشده‌اند: `Members`, `auth`, `intake`, `progress`, `core`. این یعنی «فایل تست در regex map تشخیص داده نشد»، نه اثبات قطعی نبود هر نوع آزمون؛ و PASS نقشه نیز اتصال هر control به جدول DB یا E2E را ثابت نمی‌کند.

همین‌طور:

- نمودارهای فعلی route→service→model نقشهٔ کدند، نه اجرای موفق همهٔ endpointها؛
- SQLite مقدار پیش‌فرض تنظیمات است؛ Valkey/SMS/worker/Ollama/درگاه به محیط وابسته‌اند؛
- `build_scheduler` و outbox در کد تعریف‌اند، اما جست‌وجوی راه‌اندازی در app startup به‌تنهایی runtime فعال آن‌ها را ثابت نکرد؛
- پرداخت واقعی بانکی، notification delivery، دستگاه QR واقعی، مرورگر responsive E2E، production restore و device E2E از این worktree/تست‌های اشاره‌شده نتیجه‌گیری نمی‌شوند؛
- گیت چهره fail-closed است؛ تصویر اسکن در صفحهٔ Studio، استفادهٔ دوربین/face matching را ثابت نمی‌کند؛
- PDF نسخه‌دار با QR برنامه و چرخهٔ source registry هنوز طرح آینده است و با QR حضور باشگاه یکی نیست.

## بازتولید

```bash
cd tools/graphviz-renderer
npm run render -- ../../docs/MuscleParadise/architecture/system-integrated-flow-v1-2026-11-23.dot ../../docs/MuscleParadise/architecture/system-integrated-flow-v1-2026-11-23.png 12000
```

**تصمیم برای ورود به فهرست رسمی:** بعد از بررسی شما، مواردی را که صریحاً تأیید می‌کنید به Architecture Atlas/ADR مناسب منتقل می‌کنم؛ وضعیت chart را هم از «پیش‌نویس» به «تأییدشده» تغییر می‌دهم. تا آن زمان هیچ طرح PWA، scorecard/JP7، QR برنامه یا معماری آینده به‌عنوان توافق قطعی ثبت نشده است.
