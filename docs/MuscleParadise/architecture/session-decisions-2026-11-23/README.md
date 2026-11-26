# بستهٔ یکپارچهٔ فلو و تصمیم‌ها — پیش‌نویس برای بازبینی مالک

این بسته حاصل ادغام نقشه‌های موجودِ محصول، UI/UX، Flutter، Studio، API، backend، داده، تراکنش‌ها و چرخهٔ برنامه است. هدفش این است که «چه چیزی اکنون در کد/آزمون قابل ردیابی است؟»، «مالک قبلاً دقیقاً چه چیزی را تصویب کرده؟» و «چه چیزی هنوز باید تصمیم/اثبات شود؟» از هم جدا بمانند.

> **این بسته هنوز سند رسمی/ADR نیست.** برای رعایت دستور مالک، هیچ تصمیم باز یا طرح آینده در فهرست تصمیم‌های قطعی قرار نگرفته و این بسته به `architecture/README.md` اضافه نشده است. لطفاً فایل [APPROVAL-CHECKLIST](APPROVAL-CHECKLIST.md) را مرور کنید؛ فقط بندهایی که صریحاً تأیید می‌کنید به Architecture Atlas/ADR رسمی منتقل می‌شوند.

## مسیر خواندن

1. **[نقشهٔ یکپارچه + PNG/SVG/DOT](../system-integrated-flow-v1-2026-11-23.md)** — نمای اصلی مکانیزم و راهنمای رنگ/شواهد.
2. **[DECISION-LOG](DECISION-LOG.md)** — تصمیم‌های ثبت‌شدهٔ قبلی مالک، تفاوت آن‌ها با پیاده‌سازی، موارد باز/متعارض.
3. **[WIRING-LEDGER](WIRING-LEDGER.md)** — زنجیرهٔ UI → intent/state → API → route/guard → service → persistence، سفرهای دامنه و گپ‌های اثبات.
4. **[API-ROUTE-CATALOG](API-ROUTE-CATALOG.md)** — همهٔ ۱۶۳ operation موجود در قرارداد JSON (۱۴۱ path template یکتا).
5. **[APPROVAL-CHECKLIST](APPROVAL-CHECKLIST.md)** — چک‌لیست تأیید/اصلاح/عدم‌تأیید.

## برچسب‌های وضعیت

- **تصویب‌شدهٔ مالک (ثبت‌شده در سند قبلی):** تصمیمی که در `OWNER-DECISIONS.md` یا `TODO-CLOUD-FINANCE-ACCESS.md` به‌عنوان تصمیم مالک ثبت شده است. این برچسب، تأیید همین نمودار یا اجرای همهٔ جزئیات را معنی نمی‌دهد.
- **کد جاری:** مسیر/مدل/تنظیمی که در snapshot کاری قابل خواندن است؛ به‌تنهایی اجرای موفق را ثابت نمی‌کند.
- **تست‌شده در گزارش پیوست:** گزارش تحلیل همین شاخه یک سناریوی مشخص TestClient/unit/UI را ثبت کرده؛ این نشست آن suite را دوباره اجرا نکرده است.
- **مشاهدهٔ کد / design:** ردگیری استاتیک یا سند UX؛ رفتار runtime تضمین نشده.
- **پیکربندی‌وابسته / اثبات‌نشده:** برای فعال‌شدن به secret/محیط/دستگاه/زیرساخت نیاز دارد یا شواهد deployment ندارد.
- **گپ:** رفتار ناقص یا مسیر مسدودشده‌ای که نباید موفقیت فرض شود.
- **پیشنهاد / نیازمند تأیید:** طرح آینده؛ تا تأیید صریح، تصمیم قطعی نیست.

## مبنای snapshot و حفظ workspace

- شاخهٔ فعال: `arena/5e0f64cf-mp`; HEAD پایهٔ snapshot: `35d4b35184b4148c658b415bd009fc076bf24e00`.
- Worktree از قبل تغییرهای متعدد داشته است؛ آن‌ها حفظ شده‌اند. هیچ stage، commit، reset یا تغییر شاخه‌ای انجام نشده است.
- مسیر `mp-app/backend/var/receipts/` عمداً باز یا منتشر نشده؛ نه محتوای رسیدها و نه اطلاعات فردی از آن‌ها در این بسته وارد نشده است.
- فایل‌های `routes.json` و `interaction-map.json` از همین worktree خوانده شده‌اند؛ با تغییر کد، اعداد و کاتالوگ باید دوباره تولید/بازبینی شوند.

## اسناد مبنای merge/review

خوانده‌شده و با هم مقایسه‌شده:

- نمودارهای یکپارچه/هدف: `muscle-paradise-combined-flow-v2`, `muscle-paradise-full-program-flow-v1`, `muscle-paradise-overview-flow-v1`, PWA/access، target architecture.
- نمودارهای تفصیلی: `member-app-dataflow`, `studio-dataflow`, `transaction-findings-flow`, UI/UX overview/member/Studio/control wiring.
- چرخهٔ آینده: athlete/program lifecycle، JP7/QR، source-routing/source registry، training-program-builder، intake decision tree.
- تحلیل و اطلس: `analysis-2026-11-23.md`, `system-atlas.md`, `c4.md`, `module-map.md`, `member-studio-dataflow-v1.md`.
- قرارداد و شواهد: `mp-app/backend/api/routes.json`, `interaction-map.json`, `scripts/interaction_map.py` و sourceهای Client/Studio/FastAPI.
- تصمیم محصول: `OWNER-DECISIONS.md`, `TODO-CLOUD-FINANCE-ACCESS.md`, `SESSION_HANDOFF.md`.

## تعارض‌های منبع که عمداً پنهان نشده‌اند

1. چند سند/نمودار قدیمی `gate-check` را با قرارداد query و ۴۲۲ توصیف می‌کنند؛ گزارش جدیدتر و route/test فعلی JSON body را می‌خوانند و آزمون `{path: adult}` را موفق ثبت کرده‌اند. در اسناد تازه ادعای ۴۲۲ به‌عنوان وضعیت فعلی تکرار نشده است.
2. فایل route فعلی ۱۶۳ operation و ۱۴۱ template path دارد. برخی متن‌های تحلیل/interaction قدیمی هنوز شمارش‌های snapshot پیشین (مانند ۹۵ route یکتا) را می‌گویند. برای تعداد جاری، کاتالوگ همراه از `routes.json` فعلی تولید شده است.
3. `TODO-CLOUD-FINANCE-ACCESS.md` انتشار نخست را Android عضو + Studio وب و سرور محلی باشگاه با ورودی HTTPS می‌داند؛ برخی طرح‌های قدیمی‌تر Full Cloud/PWA را هدف می‌گذارند. این طرح‌های قدیمی در نمودار تازه کهربایی و «تأییدنشده» هستند.
4. برخی route metadata مجوز را خلاصه می‌کند؛ guardهای عمیق‌تر، scope مالکیت، denyها و `finance.write` ممکن است دسترسی مؤثر را محدودتر کنند. کاتالوگ route خودِ ممیزی RBAC نیست.
5. کد/تعریف worker یا scheduler، به‌تنهایی اثبات راه‌اندازی/اجرای production آن نیست. نمودار این مرز را حفظ می‌کند.
