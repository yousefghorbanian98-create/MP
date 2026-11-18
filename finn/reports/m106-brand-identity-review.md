# M106 — بازبینی نهایی track برند (M100–M106): چه چیزی سنجیده شد و چه چیزی نه

- تاریخ: ۲۰۲۶-۱۱-۱۸ (UTC) | شاخه: `arena/4f336f66-mp` (`active`)
- نتیجهٔ loop: **`PARTIAL-CLOSED` — بازبینی static انجام شد؛ گیت‌های دستگاه‌محور اجرا نشدند و M105 همچنان `BLOCKED` است.** هیچ آیکن محصول، launch config یا UI استودیو در این بازه تغییر نکرد.

## ۱) تطبیق مسیرها (یک ابهام واقعی در سند plan رفع شد)

`LOOP-PLAN-M100-M106.md` به «`brand/...`» ارجاع می‌دهد و ریشهٔ مخزن چنین پوشه‌ای ندارد. بررسی واقعی:

- `find . -maxdepth 2 -type d -name brand` → تنها `./docs/MuscleParadise/brand`
- محتوای آن: `concepts/` (بریف M101 + سه concept + مقایسه) و `selected-c/` (بستهٔ M103 با ۱۲ جفت SVG/PNG و `M103-C-PACKAGE.md`).

پس همهٔ ارجاع‌های `brand/…` در آن نقشه **نسبت به `docs/MuscleParadise/`** درست‌اند؛ ادعاهای `PASS` M100–M103 به فایل‌های موجود اشاره می‌کنند، نه فایل‌های گم‌شده. لینک‌های داخل `M103-C-PACKAGE.md` (از جمله `../../../../mp-app/client/assets/fonts/OFL-Vazirmatn.txt`) با `scripts/docs_gate.py` بررسی شدند: **سبز (۷ فایل، ۹۹ لینک، ۳ Mermaid)**.

## ۲) آنچه واقعاً بازبینی شد

| مورد | شاهد |
|---|---|
| تداوم concept → بسته | `m101-c-progress-loop.svg` و `mp-progress-mark.svg` یک خانوادهٔ هندسی‌اند (بررسی بصری + diff بردارها در `M103-C-PACKAGE.md`) |
| ابعاد رستر | `file`/`identify` روی PNGها: mark، foreground/background، lockupهای dark/light/mono و `mp-progress-mark-16px.png` دقیقاً ۱۶×۱۶؛ cut جدا از master است (ادعای minimum-size پشتوانهٔ رستری دارد) |
| contrast | نسبت‌های محاسبه‌شده در بسته: green/dark 7.38:1، gold/dark 13.70:1، light-green/light 5.07:1؛ طلایی `#A17B00` فقط گرافیکی، نه متن ریز |
| license/منبع | Vazirmatn از قبل در `mp-app/client/assets/fonts` با `OFL-Vazirmatn.txt`؛ هیچ فونت/dependency تازه‌ای اضافه نشد |
| جدا بودن آیکن محصول | `git status --short mp-app/client/assets/logo/` → بدون تغییر؛ `app_icon.png` همان baseline است |
| راهنمای بازتولید | بخش‌های «گیت‌های جدا از M103» در `M103-C-PACKAGE.md` صریح‌اند: mask واقعی، startup و reduced-motion به M104–M106 موکول شده‌اند |

## ۳) آنچه انجام **نشد** (و چرا جعل نشد)

1. **adaptive mask واقعی (M106 acceptance)** — نیاز به Android launcher/`adaptive-icon` preview یا دستگاه دارد؛ نه Android SDK بود، نه emulator، نه `adb`. foreground موجود «حاشیهٔ محافظه‌کارانه» دارد اما این جای تست واقعی نیست.
2. **سرد/گرم startup و `restore()` (M104)** — `finn/reports/m104-startup-measurement.md` پروتکل و run sheet را دارد و جدولش **خالی** است. بدون Flutter/device هیچ عددی ثبت نشد و عددسازی نکردیم.
3. **reduced-motion** — این مورد در M98 (مسیر محصول) حل شد: `mp-app/client/lib/core/motion.dart` از `MediaQuery.disableAnimations` می‌خواند و `MpMotion.dur → Duration.zero` / `animate(target: 0)` می‌دهد. اگر روزی reveal برند ساخته شود، باید از همان helper استفاده کند — ولی چون M105 ادغام را شروع نکرده، هیچ reveal ای وجود ندارد و تست دستگاه‌محورش هم معنا ندارد.
4. **تصمیم reveal** — معلق؛ مبنای آن اعداد M104 بود که وجود ندارند.
5. **M105 ادغام** — `BLOCKED`؛ package ثابت پاس شده ولی شواهد runtime لازم (M104) و گیت device در دسترس نبود.

## ۴) اگر اجرای واقعی لازم است

- Codespaces (config حاضر در `.devcontainer/`؛ نسخهٔ Flutter پین‌شده و SHA-256 چک می‌شود): `flutter test`, `flutter run` روی emulator برای mask و startup. **ماشین ابری ساخته نشده** — هزینه/مجوز جدا از این بسته است.
- یا دستگاه واقعی + `adb`: `adb shell cmd uimode night yes|no` برای شب/روز، screenshot آیکن در ۴ اندازه، و `flutter run --profile` + capture timeline برای جدول M104.
- دستور ثبت در `finn/reports/codespaces-user-handoff.md` به‌روز شده و همین‌جا تکرار نشده است.

## ۵) وضعیت نهایی track

| Loop | وضعیت |
|---|---|
| M100 brief | `PASS` |
| M101 concepts | `PASS` (کاربر C را انتخاب کرد) |
| M102 selection | `PASS` (C منتخب) |
| M103 static package | `PASS` (static identity only) |
| M104 startup measurement | `UNKNOWN` — بدون ابزار/دستگاه؛ پروتکل و run sheet آماده |
| M105 integration + launch/motion | `BLOCKED` — پیش‌نیازهای M104/device و گیت ادغام |
| M106 final review | `PARTIAL-CLOSED` — بازبینی static + تطبیق مسیرها انجام شد؛ گیت‌های device/launch/mask اجرا نشدند |
