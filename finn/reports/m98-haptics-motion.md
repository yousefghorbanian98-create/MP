# M98 — UX-G3 بازخورد لمسی و Q5 مایکرو-انترکشن (با کاهش حرکت)

- تاریخ ثبت: ۲۰۲۶-۱۱-۱۸ (UTC)
- شاخه: `arena/4f336f66-mp`، پایه `d64e3b008d1c6c20c65c5ebfa4816277d4d23ce0`
- نتیجهٔ loop: **`UNKNOWN` برای runtime Flutter** — کد و تست نوشته شد، گیت ایستا سبز است؛ `flutter analyze`/`flutter test` در این sandbox اجرا نمی‌شود (SDK نصب نیست) و داوری نهایی به جاب `client-flutter` در CI موکول است.

## آنچه loop خواست و آنچه ساخته شد

معیار پذیرش: «haptics test با messenger، reduced-motion/accessibility، shared-element فقط در صورت سود و test؛ بدون ادعای polish فراگیر».

| بند | اجرا |
|---|---|
| haptics با test روی messenger | `lib/core/haptics.dart`: رابط `MpHaptics` (`select`/`success`/`warning`) + `SystemMpHaptics` روی `HapticFeedback`، با `enabled` و بلعیدن خطای پلتفرم (دسکتاپ/PWA موتور لرزشی ندارد). تست `test/motion_haptics_test.dart` با `setMockMethodCallHandler(SystemChannels.platform, …)` می‌سنجد **هر سه پالس دقیقاً یک فراخوانی پلتفرم می‌فرستند**، نام‌شان `HapticFeedback`/`Vibration` است و آرگومان‌شان با هم فرق دارد (یعنی «موفق» و «انتخاب» یکی نیستند)؛ با `enabled: false` صفر فراخوانی |
| reduced-motion | `lib/core/motion.dart`: `MpMotion.reduced/dur/target` روی `MediaQuery…disableAnimations` (همان سیگنالی که Android «animations off» و iOS «Reduce Motion» را می‌دهد). سه test: `dur → Duration.zero`، `target → 0`، و fallback امن وقتی MediaQuery نیست |
| جای اتصال | سه نقطهٔ عمل‌محور، نه کل اپ: **فرم بازخورد ست** (پالس موفق پس از اعمال پیشنهاد، پالس هشدار در صف آفلاین و در خطا، `select` روی هر گام اسلایدر RIR/درد)، **کلاس‌ها** (پالس پس از رزرو/لغو موفق، هشدار در خطا) و **فروشگاه** (پالس پس از افزودن به سبد و پس از پرداخت کیف‌پول، هشدار در خطا). ترنزیشن تب‌های `app_shell` و `fadeIn/slideY` لیست کلاس‌ها هم از `MpMotion` می‌خوانند |
| shared-element | **انجام نشد** — Hero بین صفحه‌ها در این سه جریان ارزش اثبات‌شده‌ای نداشت و ریسک شکستن navigation stack در تست داشت؛ معیار loop هم «فقط در صورت سود» بود |

## رفتارهایی که عمداً این‌گونه انتخاب شدند

- **پالس بعد از `await` سرویس، قبل از `setState`.** اگر برعکس می‌شد، لرزش می‌توانست پیش از معلوم‌شدن نتیجهٔ سرور «ثبت شد» را اعلام کند.
- **صف آفلاین = `warning`، نه `success`.** بازخورد ذخیره شده ولی به سرور نرسیده؛ پالس «موفق» کاربر را به اشتباه مطمئن می‌کرد.
- **`MpHaptics` خطا می‌بلعد.** لرزش نباید ثبت بازخورد/لغو رزرو را بشکند؛ برای همین `_run` در `try/catch` است.
- **کاهش حرکت = skip، نه حذف انیمیشن.** `target: 0` در `flutter_animate` همان ظاهر نهایی را می‌دهد؛ کد دو شاخه نشد و حالت «بدون انیمیشن» همان چیزی است که تست می‌بیند.
- **بدون dependency تازه.** نه `haptic_feedback` plugin، نه `motion_preference` — هر دو در `HapticFeedback`/`MediaQuery` فلاتر هست (`pubspec.yaml` دست‌نخورده).

## فایل‌ها

جدید: `lib/core/haptics.dart`, `lib/core/motion.dart`, `test/motion_haptics_test.dart`, `test/haptics_recorder.dart`
ویرایش (چهار فایل UI و دو فایل تست): `lib/features/feedback/set_feedback_sheet.dart`, `lib/features/classes/classes_page.dart`, `lib/features/shop/shop_page.dart`, `lib/features/shell/app_shell.dart`, `test/set_feedback_sheet_test.dart` (+۱ تست خطا، ۲ ادعای پالس), `test/classes_cancel_test.dart` (۲ ادعای پالس)

## شواهد

| گیت | نتیجه |
|---|---|
| `dart_gate.py --include-tests` (Tree-sitter) | **۷۲ فایل Dart، ۰ یافته** (پس از آخرین ویرایش) |
| `npm test` در Studio | **219 passed / 9 skipped** — طراحی/دیزاین‌توکن و coverage API تحت‌تأثیر این تغییرات Client قرار نگرفتند |
| backend | بدون تغییر در این loop؛ baseline M97: کل suite **861 passed / 1 skipped** + یک شکست cwd-sensitive مستندشده |
| `flutter analyze` / `flutter test` / build | **محلی اجرا‌نشده** (SDK نیست؛ `dl.google.com` هم از این sandbox در دسترس نیست) |
| **CI `client-flutter` روی `776ca6f`** | **✓ سبز** — analyze (گیت error+warning) + `flutter test` + manifest gate؛ پس از ۴ run قرمز با علل متفاوت (`44293699567`, `44295081645`, `44298469682`, `44299228685`) |

## محدودیت‌ها (بدون ادعای polish فراگیر)

- «۷۲ فایل / ۰ یافته» فقط نحو + سیاست‌های `dart_gate` است؛ جایگزین analyzer (type errors، unused imports، deprecations) نیست. همان‌جا که CI می‌گوید.
- پالس‌ها روی **هیچ دستگاه واقعی** حس نشده‌اند: نه شدت، نه تأخیر، نه رفتار روی iOS/Android متفاوت. این loop فقط «فراخوانی درست به messenger می‌رود» را ثابت می‌کند.
- `disableAnimations` سیگنال انیمیشن است؛ **لرزش از آن پیروی نمی‌کند** و صریحاً هم این‌گونه طراحی شد (یک کاربر reduced-motion ممکن است لرزش را برای «ثبت شد» بخواهد). اگر روزی toggle جداگانهٔ کاربر لازم شد، `SystemMpHaptics.enabled` همان نقطه است — ولی تنظیمات App-Settings هنوز ساخته نشده و وانمود به داشتنش نکردیم.
- بقیهٔ صفحات (checkin، progress، nutrition، …) عمداً پالس نگرفتند؛ هدف loop «کارکردی‌های پس از کارکرد» بود، نه پوشش سراسری. ادعای «اپ حالا haptics دارد» نمی‌کنیم — سه جریان عملیاتی دارد.
- `SemanticsBinding.instance.accessibleNavigation` برای «فقط‌خواندن‌شدن» اضافه نشد؛ اگر بازخورد لمسی برای کاربری با Accessible Navigation آزارنده باشد، نیاز به تنظیمات کاربر دارد (خارج از این loop).
- ECC/REA: هیچ subagent اجرا نشد (کلید API/`claude`/REA در این sandbox نیست). چک‌لیست `flutter-reviewer.md` و `a11y-*` به‌صورت دستی اعمال شد؛ به‌عنوان اجرای ایجنت ثبت نمی‌شود.

## اجرا در CI — بازداشت اول و طراحی مجدد API (۲۰۲۶-۱۱-۱۸)

اولین run واقعی پس از push بسته (run `44293699567`، job `client-flutter`): **146 passed / 4 failed** — و هر چهار شکست به همین loop برمی‌گشت:

| شکست CI | تشخیص | رفع |
|---|---|---|
| `motion_haptics_test.dart` — خطای کامپایل در خط ۸۶ | `setMockMethodCallHandler<void>` نوشته شده بود، ولی این متد در SDK نسخهٔ CI **ژنریک نیست** (`WRONG_NUMBER_OF_TYPE_ARGUMENTS_ELEMENT`)؛ `dart_gate` (Tree-sitter) این را نمی‌بیند | حذف پارامتر نوع + بالا کشیدن messenger به یک `local`؛ کامنت همان‌جا که «چرا بدون type argument» |
| `set_feedback_sheet_test.dart:100` — متن «اعمال شد» غیب شد | پالس موفق **بین** نتیجهٔ سرویس و `setState` با `await` بود؛ در تست ویجت (و روی دستگاهی که کانال پاسخ نمی‌دهد) آن future resolve نمی‌شود، پس `setState` هرگز اجرا نمی‌شد | قرارداد جدید: `MpHaptics` سه متد **`void`** است؛ `SystemMpHaptics` با `unawaited(...catchError)` شلیک می‌کند و پالس‌ها بعد از `mounted` check قرار گرفتند — بازخورد دیگر هرگز مسیر درستیِ UI را گیت نمی‌کند |

دو شکست دیگر (`shop_orders_receipt_test.dart`) در گزارش M90 ثبت شده‌اند.

**چرا این یک تغییر رفتار است، نه فقط رفع تست:** ادعای loop «پالس وقتی نتیجه معلوم شد» بود؛ نسخهٔ اول ناخواسته «پالس می‌تواند نمایش نتیجه را برای همیشه نخواباند» شد. حالا قرارداد همان چیزی است که بالای `lib/core/haptics.dart` نوشته شده و `motion_haptics_test.dart` با `pumpEventQueue()` ثابت می‌کند پیام **بدون await کردنِ مسیر UI** به messenger می‌رسد (سه فراخوانی با آرگومان‌های افتراقی؛ `enabled: false` → صفر فراخوانی).

### round دوم CI — رفع‌ها سبز، ولی خودِ تستِ من آویزان می‌شد

run `44295081645`: **154 passed / 2 failed**، زمان job ≈ ۲۱ دقیقه (قبلاً ۸ دقیقه). دو شکست، همان دو تست messenger بودند و هیچ‌کدام assertion معمولی نبود: هرکدام **timeout ده‌دقیقه‌ای** خورد. علت: برای دیدنِ پیام‌های fire-and-forget صف رویداد را با `pumpEventQueue()` تخلیه می‌کردم — آن تابع روی `Future.delayed` واقعی منتظر می‌ماند، ولی داخل `testWidgets` زمان فقط با `pump()` جلو می‌رود، پس هیچ‌وقت برنمی‌گشت.

رفع (`c672737`): `drain(tester)` = `await tester.runAsync(() => Future.delayed(Duration.zero))` و یک `pump()`. با همین تغییر، تست «سه فراخوانی» دیگر به زمان fake وابسته نیست و تست «`enabled: false` → صفر فراخوانی» هم معنا دارد (قبلاً روی لینوکس CI بی‌صدا سبز می‌شد؛ برای همین `debugDefaultTargetPlatformOverride = TargetPlatform.android` هم در `41ae143` اضافه شد).

### دورهای ۳ تا ۵ — harness، نه assertion

| run | sha | نتیجه | تشخیص و رفع |
|---|---|---|---|
| `44298469682` | `c672737` | 154 passed / **2 failed** (سریع، بی‌timeout) | هر دو تست messenger بودند، **از جمله تستی که فقط «صفر فراخوانی» را می‌سنجد** — پس مشکل شمارش پالس نبود، خودِ environment `testWidgets` بود (FakeAsync + تغییر `debugDefaultTargetPlatformOverride` داخل بدنه که با invariant بایندینگ درگیر می‌شود). رفع: گروه haptics از `testWidgets` به `test()` معمولی با `TestWidgetsFlutterBinding.ensureInitialized()` و mock روی `defaultBinaryMessenger` منتقل شد؛ override داخل تست و با `addTearDown` برگردانده می‌شود؛ event loop واقعی است و یک `Future.delayed(Duration.zero)` برای دیدنِ پیام در mock کافی است |
| `44299228685` | `a3b03e0` | `flutter analyze` **قرمز**، `flutter test` skip شد | `UNNECESSARY_CAST` (warning) روی `… as TestDefaultBinaryMessenger`؛ این گیت فقط `--no-fatal-infos` می‌دهد پس warningها کشنده‌اند. رفع (`776ca6f`): حذف کست زائد، با کامنت «چرا اینجا cast برای وضوح مجاز نیست» |
| `44300167991` | `776ca6f` | **client-flutter ✓ سبز** | `pub get` ✓ · `flutter analyze` ✓ · `flutter test` ✓ · manifest gate ✓ |

### یک ادعای صادقانه دربارهٔ «سبز بودن»

سبزیِ این جاب به‌تنهایی ثابت نمی‌کرد probe اجرا شده: اگر `HapticFeedback` روی runner پیامی نمی‌فرستاد، تست اول `markTestSkipped` می‌خورد و جاب سبز می‌ماند. برای همین `--summary` به `tools/ci_test_failures.py` اضافه شد (شمارش pass/fail/**skip** در step summary، بدون هیچ مقدار assertion) و رگرسیون `mp-app/backend/tests/regression/test_ci_test_failures.py` (۵ تست) رفتارش را — از جمله «متن error/stack به خروجی نرود» — قفل می‌کند. شمارش همین run از artifact/summary خوانده می‌شود؛ ادعای «صفر skip» فقط وقتی نوشته می‌شود که همان عدد دیده شده باشد.

**وضعیت نهایی:** برای دامنه‌ای که CI می‌سنجد (analyzer + widget/unit test) این loop **PASS** است؛ «شدت/تأخیر/احساس واقعی روی گوشی» همچنان سنجیده نشده و ادعا نمی‌شود. تا ثبت همان عدد، M98 `UNKNOWN` می‌ماند — «۷۲ فایل / ۰ یافته» و «تست‌ها منطقی‌اند» جایگزین pass نیستند.
## بازگشت

حذف `core/haptics.dart`, `core/motion.dart`, `test/motion_haptics_test.dart`, `test/haptics_recorder.dart` و برگرداندن آن چهار فایل UI و دو فایل تست، رفتار قبلی (بدون پالس، با duration ثابت) را برمی‌گرداند. هیچ API/schema/dependency درگیر نیست.
