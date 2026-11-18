# کارِ کاربر در GitHub Codespaces — یادآوریِ پایان FINN

- ثبت بر اساس درخواست مستقیم کاربر: 2026-11-17؛ مرز مجوز D-047
- شاخهٔ مجاز: `arena/4f336f66-mp` (active)
- **SUPERSEDED (M108، ۲۰۲۶-۱۱-۱۸):** گیت‌های Client/Android به جاب `client-pinned` رفتند و شاهد گرفتند؛ مسیر انسانیِ باقی‌مانده در `docs/MuscleParadise/runbooks/codespaces-execution.md` است (M109 + §۶ دستگاه). این فایل به‌عنوان تاریخچهٔ تصمیم نگه داشته شده.
- وضعیت یادآوری: **PENDING — Codespace ساخته نشده؛ handoff پایانی M99 نهایی شد (`finn/reports/m99-closeout-report.md`)، ولی ماشین ابری بدون نیاز/هزینه‌ی روشن ساخته نمی‌شود. اگر CI `client-flutter` پس از push سبز باشد، اجرای Codespaces فقط برای device/mask (M104–M106) لازم است، نه برای تکرار suite.**
- trigger: پس از ثبت loopهای محلیِ قابل‌اجرا تا M98 و پیش از بستن گزارش M99؛ یا اگر M99 برای اجرای Client به شاهد نیاز داشت، در handoff نهایی M99.

## زیرساخت آماده‌شده

- `.devcontainer/devcontainer.json`, `.devcontainer/Dockerfile` و `.devcontainer/post-create.sh` آماده‌اند.
- از تصویر نگه‌داری‌شده و MIT-licensed `mcr.microsoft.com/devcontainers/base:ubuntu24.04` استفاده می‌شود؛ Flutter از آرشیو رسمی، نسخهٔ `3.50.0`, revision `ab2912035e160d9cad6306df307576da6128ebdb` و SHA-256 برابر `6ea2d806fd57269ae783e6788e2a81fc26eaad782f1e0d0ff38623bb765ff9f5` دریافت و در build پیش از extract بررسی می‌شود. هیچ image از Cirrus Labs استفاده نمی‌شود.
- تصویر Codespaces برای Flutter/Dart analyze/test و OpenJDK 17 است؛ Android SDK نصب نمی‌کند، license قبول نمی‌کند و APK/signing تولید نمی‌کند. Codespaces config در این sandbox build نشده و Codespace واقعی ایجاد/هزینه نشده است.
- پیش‌نیازهای Flutter SDK در گزارش `finn/reports/flutter-sdk-provisioning.md` ثبت شده‌اند؛ TLS/egress همین sandbox قبلاً اجازهٔ دریافت SDK یا Pub packages را نداد.

## وضعیت شواهد و حدود ادعا

- M84 تغییر UI/API رزرو نام را دارد؛ backend targeted booking/cancel/finance/sync **20 passed**، full backend **853 passed / 2 skipped** با coverage **86.30%**، Ruff سبز و تست Flutter widget نوشته شده است. CI `44202586219` analyzer را پاس کرد و full Flutter suite را اجرا کرد (**101 passed / 13 failed**); در `44247416109` 13 test failure شمرده شد، اما M84-specific result از annotations قابل‌تأیید نیست؛ `UNKNOWN`.
- M85 `UNKNOWN` می‌ماند؛ source/معیار بالینی مصوب و reviewer qualified ثبت نشده و در این بسته ادعای پزشکی اضافه نشده است.
- M86 قرارداد outbox و backend API contract **12 passed** دارد؛ این `PASS` فقط قرارداد/backend است، نه Client.
- M87 Dart static gate **64 files / 0 findings**، Kotlin syntax parse **2 / 0** (نه compile) و Android manifest gate **1 / 0** پاس شدند؛ full backend checks نیز سبزند. CI analyzer در `44202586219` و `44247416109` پاس شد، اما suite **13 test failure** داشت؛ outbox-specific result هنوز نامعلوم است چون 4 نام در annotations جا افتاد. Kotlin/Gradle compile، Android DB restart/persistence و دستگاه واقعی هنوز اجرا نشده‌اند؛ پس `UNKNOWN` می‌ماند و feature flag پیش‌فرض خاموش است.
- CI `44194271168` روی commit `6475455` فایل‌های M84–M87 را دربر نمی‌گرفت. CI `44198198864` روی `b7cd7f1` شامل آن‌ها شد؛ backend/API jobs پاس، client analyzer و Studio API coverage fail شدند و client tests skip شدند. Fixهای analyzer/Studio در `0ace8fe` push شدند؛ `44200381791` analyzer را با یک warning در outbox fail کرد؛ تست `network: false` در `01a7177` آن را رفع کرد. در `44202586219` analyzer پاس شد و suite **101 passed / 13 failed**؛ run `44247416109` analyzer را هم پاس کرد و 13 failure شمرد، اما فقط 9 نام (از 5 فایل) به‌دلیل annotation cap نمایان شد و چهار نام هنوز مشخص نیست. Worktree helper را به single aggregate annotation تغییر می‌دهد تا نام همهٔ failureها دیده شود؛ CI بعدی لازم است. Gitleaks همچنان به‌دلیل matchهای تاریخی fail است. جزئیات redacted: `finn/reports/ci-follow-up-441922-441942.md`; Secret-scan failure را با heuristic یا allowlist broad نباید پنهان کرد.

## دستور نهایی اجرا

1. پس از push انتخابیِ بستهٔ بازبینی‌شده، Codespace را فقط از `arena/4f336f66-mp` بساز. مطمئن شو branch همان commit مورد انتظار را دارد؛ `main` یا شاخهٔ دیگر شاهد این بسته نیست.
2. پس از آماده‌شدن container، در terminal Codespaces اجرا کن:

   ```bash
   cd "$(git rev-parse --show-toplevel)/mp-app/client"
   flutter --version --machine
   dart --version
   flutter pub get
   flutter analyze --no-fatal-infos
   flutter test test/session_refresh_test.dart
   flutter test test/classes_cancel_test.dart
   flutter test test/set_feedback_sheet_test.dart
   flutter test test/shop_orders_receipt_test.dart
   flutter test test/motion_haptics_test.dart
   flutter test
   ```

3a. **تمرکز این بسته (M90/M98):** دو فایل اخیر، شیت رسید/«سفارش‌های من» و لایهٔ `MpHaptics`/`MpMotion` را می‌سنجند؛ اگر `flutter analyze` در این‌ها warning بدهد، همان‌جا ثبت شود و ادعای pass نکنیم (sandbox محلی فقط Tree-sitter gate داشت: ۷۲ فایل / ۰ یافته).

3. اگر M87 در بستهٔ جاری شامل تست‌های outbox بود، همهٔ آن‌ها نیز با full `flutter test` اجرا شوند. خروجی کامل، exit code هر دستور، نسخهٔ Flutter/Dart، مقدار `frameworkRevision`, نتیجهٔ `pub get` و تعداد تست‌ها ذخیره/ارسال شود. فایل `pubspec.lock` در baseline وجود ندارد؛ هر lockfile که ایجاد شود باید جداگانه بازبینی شود و به‌صورت خودکار commit نشود.
4. Runtime testهای Widget به Android SDK نیاز ندارند. در این container Android SDK نصب نشده؛ APK build، signing، قبول Android licenses یا استفاده از فایل‌های keystore جزو این handoff نیست و کلیدهای شناخته‌شدهٔ repository نباید لمس/ارسال شوند.
5. پس از logها، فقط همان gateهایی که واقعاً اجرا شده‌اند به‌روزرسانی شوند؛ شکست با test/fix/rerun مناسب پیگیری شود. نبود log، اجرای ناقص یا static Dart gate معادل `PASS` نیست.

## مرز اتصال و هزینه

Codespaces شبکه و filesystem جداگانه دارد و ایجادش دسترسی خودکار به این agent نمی‌دهد. اگر کاربر بعداً بخواهد عامل تلاش کند از `gh codespace ssh` استفاده کند، این کار به نام Codespace غیرمحرمانه و مجوز مستقل نیاز دارد؛ هیچ credential/token در گفتگو درخواست نمی‌شود. fallback قطعی: کاربر دستورات را در Codespace اجرا و logها را در گفتگو می‌فرستد. ساخت Codespace، مصرف ماشین و هر هزینهٔ احتمالی از commit/push این branch جداست.
