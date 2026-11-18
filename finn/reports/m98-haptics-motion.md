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
| `flutter analyze` / `flutter test` / build | **اجرا‌نشده** (SDK نیست؛ `dl.google.com` هم از این sandbox در دسترس نیست) |
| CI | پس از push بستهٔ نهایی (D-047) در `client-flutter` سنجیده می‌شود؛ نتیجه در `LOOP-PLAN-M63-M99.md` ثبت می‌شود |

## محدودیت‌ها (بدون ادعای polish فراگیر)

- «۷۲ فایل / ۰ یافته» فقط نحو + سیاست‌های `dart_gate` است؛ جایگزین analyzer (type errors، unused imports، deprecations) نیست. همان‌جا که CI می‌گوید.
- پالس‌ها روی **هیچ دستگاه واقعی** حس نشده‌اند: نه شدت، نه تأخیر، نه رفتار روی iOS/Android متفاوت. این loop فقط «فراخوانی درست به messenger می‌رود» را ثابت می‌کند.
- `disableAnimations` سیگنال انیمیشن است؛ **لرزش از آن پیروی نمی‌کند** و صریحاً هم این‌گونه طراحی شد (یک کاربر reduced-motion ممکن است لرزش را برای «ثبت شد» بخواهد). اگر روزی toggle جداگانهٔ کاربر لازم شد، `SystemMpHaptics.enabled` همان نقطه است — ولی تنظیمات App-Settings هنوز ساخته نشده و وانمود به داشتنش نکردیم.
- بقیهٔ صفحات (checkin، progress، nutrition، …) عمداً پالس نگرفتند؛ هدف loop «کارکردی‌های پس از کارکرد» بود، نه پوشش سراسری. ادعای «اپ حالا haptics دارد» نمی‌کنیم — سه جریان عملیاتی دارد.
- `SemanticsBinding.instance.accessibleNavigation` برای «فقط‌خواندن‌شدن» اضافه نشد؛ اگر بازخورد لمسی برای کاربری با Accessible Navigation آزارنده باشد، نیاز به تنظیمات کاربر دارد (خارج از این loop).
- ECC/REA: هیچ subagent اجرا نشد (کلید API/`claude`/REA در این sandbox نیست). چک‌لیست `flutter-reviewer.md` و `a11y-*` به‌صورت دستی اعمال شد؛ به‌عنوان اجرای ایجنت ثبت نمی‌شود.

## بازگشت

حذف `core/haptics.dart`, `core/motion.dart`, `test/motion_haptics_test.dart`, `test/haptics_recorder.dart` و برگرداندن آن چهار فایل UI و دو فایل تست، رفتار قبلی (بدون پالس، با duration ثابت) را برمی‌گرداند. هیچ API/schema/dependency درگیر نیست.
