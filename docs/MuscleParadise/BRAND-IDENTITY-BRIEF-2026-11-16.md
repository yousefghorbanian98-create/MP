# بریف بازطراحی هویت برند Muscle Paradise — ۲۰۲۶-۱۱-۱۶

> خروجی **M100 / FINN**: بریف اجرایی برای بازطراحی نشان MP و حرکت آغاز برنامه؛ خود M100 لوگو را انتخاب نمی‌کرد. وضعیت جاری M103 در پایین آمده است: بستهٔ هویت ثابت تکمیل شده، اما این سند هیچ asset یا کد محصولی را تغییر نمی‌دهد.

## وضعیت تصمیم

- کاربر پیشنهادهای مربوط به ساده‌سازی نشان، تفکیک هویت ثابت از Splash سیستم‌عامل و reveal اختیاری کوتاه را تأیید کرده است.
- پس از دیدن مقایسهٔ A/B/C، کاربر **C — Progress Loop** را بهترین جهت انتخاب کرد؛ این تصمیم مسیر طراحی را مشخص می‌کند، نه artwork/فونت نهایی و نه تعویض آیکن فعلی.
- A و B برای مقایسه حفظ شده‌اند؛ ارزیابی heuristic پنج‌معیاره و انتخاب C در `brand/concepts/M101-CONCEPTS.md` است. تست بازار/کاربری ادعا نمی‌شود.
- در M100 فقط مستندات به‌روز شدند؛ در M101 conceptهای SVG/PNG زیر `docs/` ساخته شدند. `app_icon.png`، کد Flutter/Studio، dependencyها و تنظیمات اجرا دست‌نخورده‌اند.

## هدف و مرز کار

ساخت یک هویت دیداری منسجم برای **Muscle Paradise (MP)** که در app icon، نام/نشان Studio، محیط تاریک فعلی و در صورت توجیه، حرکت آغاز برنامه قابل استفاده باشد. «بازطراحی لوگو» و «طراحی launch experience» دو خروجی جدا هستند؛ یکی جایگزین دیگری نیست.

**خارج از scope فعلی:** تغییر سراسری UI یا رنگ‌بندی محصول، بازنویسی برند/نام شرکت، ادعای علمی/سلامتی، افزودن کتابخانهٔ افکت، تغییر رفتار احراز هویت یا انتشار build.

## وضعیت موجود — شواهد مخزن

| سطح | وضعیت دیده‌شده | نتیجه برای طراحی بعدی |
|---|---|---|
| آیکن فعلی | `mp-app/client/assets/logo/app_icon.png`، PNG با ابعاد ۱۰۲۴×۱۰۲۴؛ زمینهٔ تیرهٔ گرد، M برجسته با اشارهٔ وزنه و گرادیان سبز/طلایی | برای خوانایی در اندازهٔ کوچک، تست نسخهٔ ساده/تک‌رنگ لازم است؛ حرف P در نشان فعلی به‌سرعت قابل تشخیص نیست. این مشاهده دلیل بازطراحی است، نه حکم دربارهٔ پسند کاربر. |
| رنگ‌های محصول | `design-system.md`: زمینه `#0B0F14`، سبز `#00B86A`، طلایی `#FFD700`؛ تم تاریک پیش‌فرض و رابط فارسی RTL | پالت فعلی نقطهٔ شروع پیشنهادی است، نه قید اجباری برای لوگوی نهایی. |
| app icon | `pubspec.yaml`، `flutter_launcher_icons` را با همین تصویر و پس‌زمینهٔ adaptive `#0B0F14` تنظیم می‌کند؛ iOS فعلاً خاموش است | نشان، foreground و background آیکن باید جداگانه و با ماسک Android بررسی شوند؛ فایل فعلی تا تأیید جایگزین نشود. |
| Launch Android | `drawable/launch_background.xml` روشن سفید است؛ `drawable-v21` از `?android:colorBackground` استفاده می‌کند. `LaunchTheme` روز/شب جداست. | اختلاف روز/شب و رفتار Android 12+ در M104/105 روی دستگاه/نسخهٔ هدف بررسی شود؛ XML فعلی در این مرحله تغییر نکند. |
| startup Flutter | `main.dart` پیش از `runApp()`، `authProvider.notifier.restore()` را `await` می‌کند؛ زمان این مسیر اندازه‌گیری نشده است. این sandbox `flutter`/`dart`/`adb`، SDK یا دستگاه ندارد. | M104 `UNKNOWN`: run sheet در `finn/reports/m104-startup-measurement.md` است؛ runtime cold/warm start و restore باید روی emulator/دستگاه هدف سنجیده شود پیش از reveal؛ هیچ عددی حدس زده نشده است. |
| Studio | `Login.tsx` و `Sidebar.tsx` نشان متنی `MP` دارند؛ Sidebar نام `Muscle Paradise` را نیز نشان می‌دهد. | بستهٔ نهایی باید نشان مستقل، wordmark و lockup مشترک را تعریف کند، نه اینکه دو کلاینت نشانه‌های ناسازگار بسازند. |
| motion | `mp-app/shared/motion-spec.md` مقیاس ۱۵۰/۲۵۰/۴۵۰ms دارد و می‌گوید هیچ انیمیشنی بیش از ۵۰۰ms کاربر را معطل نکند؛ Flutter از `flutter_animate` استفاده می‌کند. | motion برند باید کوتاه، معنادار، قابل‌حذف و هم‌خوان با همین نظام باشد؛ dependency تازه بدون نیاز اثبات‌شده اضافه نشود. |

## معیارهای هویت ثابت

1. **شناخت‌پذیری:** MP باید در تست سریع و اندازهٔ کوچک خوانا/به‌یادماندنی باشد؛ جزئیات وزنه نباید فرم حروف را ببلعد.
2. **سادگی و مقیاس‌پذیری:** نشان در ۱۶، ۲۴، ۳۲ و ۴۸ پیکسل، تک‌رنگ، خاکستری، روی زمینهٔ روشن و تیره بررسی شود. گرادیان، برجستگی، سایه یا بافت نباید شرط تشخیص نشان باشند.
3. **هویت قابل ادامه:** سبز/طلایی/ذغالی به‌عنوان سرنخ‌های فعلی در گزینه‌ها حفظ شوند؛ تغییر پالت فقط با دلیل روشن و مقایسه انجام شود.
4. **کاربردهای مجزا:** mark، wordmark لاتین «Muscle Paradise»، lockup، app icon/adaptive icon و نسخه‌های روشن/تیره/تک‌رنگ جدا تعریف شوند. فارسی‌بودن رابط الزام نمی‌کند که نام برند لاتین به‌صورت آوایی ترجمه شود.
5. **پرهیز از کلیشه:** از هالتر آماده، بدنساز silhouette، افکت فلزی سنگین، نخل/ساحلِ کلیشه‌ای و جزئیات تزئینیِ غیرقابل‌خواندن پرهیز شود؛ هر استعاره باید برای MP دلیل داشته باشد.
6. **حرکت‌پذیری بدون وابستگی:** اگر انیمیشن انتخاب شد، فرم ایستا به‌تنهایی باید کامل باشد؛ حرکت فقط معنی یا رابطه‌ای را روشن کند، نه اینکه نقص خوانایی را بپوشاند.

## سه قلمرو بصری — همگی گزینه‌اند، نه تصمیم

### A. نشان هندسی MP — گزینهٔ پیشرو برای نمونه‌سازی

حروف M و P با فضای منفی/ساختار هندسی یکپارچه؛ اشارهٔ کوچک به قدرت یا تمرین فقط در صورت کمک به خوانایی. مزیت احتمالی: حفظ ارتباط با MP و مقیاس‌پذیری بهتر از آیکن برجستهٔ فعلی.

### B. Wordmark مینیمال و پریمیوم

تایپوگرافی اختصاصی/انتخاب آگاهانه برای «Muscle Paradise» با monogram کوچک و مستقل. مزیت احتمالی: هویت حرفه‌ای‌تر و کمتر وابسته به تصویر کلیشه‌ای وزنه؛ باید برای app icon یک mark محکم داشته باشد.

### C. نماد پیشرفت و حرکت

مسیر، قوس یا تکرارِ کنترل‌شده که پیشرفت را القا کند و در نسخهٔ ثابت به MP متصل بماند. مزیت احتمالی: قابلیت تبدیل به motion reveal؛ ریسک: انتزاع بیش از حد و کم‌شدن خوانایی حروف.

در M101 هر سه با کاربردهای هم‌اندازه و معیار یکسان ساخته می‌شوند؛ ترکیب آن‌ها فقط وقتی پذیرفته است که دلیل و بهبود قابل‌مشاهده داشته باشد.

## Launch و Motion — قاعدهٔ اجرایی

- **Launch Screen** باید سریع و هم‌خوان با اولین صفحه باشد، نه تبلیغ یا تایمر انتظار.
- Android 12+ گذار و splash سیستمی دارد؛ اگر آیکن متحرک استفاده شود، انیمیشن نباید از سقف توصیه‌شدهٔ Android (حدود ۱ ثانیه) فراتر برود.
- طبق راهنمای Apple، launch screen جای معرفی تبلیغاتی برند نیست؛ اگر معرفی اضافه لازم باشد، آن را در onboarding/پس از آماده‌شدن تجربه بسنج.
- برای MP، هر reveal اختیاری باید بعد از آماده‌شدن اولین فریم، کوتاه (هدف اولیه ۳۵۰–۴۵۰ms)، غیرمسدودکننده و قابل حذف با تنظیم کاهش حرکت باشد. پخش در هر startup تا وقتی دلیل UX ندارد، فرض نشود.
- هیچ delay مصنوعی برای «کامل‌کردن انیمیشن» مجاز نیست. اگر `restore()` کند است، آن را اندازه بگیر و خود مسیر startup را بررسی کن؛ انیمیشن راه‌حل performance نیست.

## تناسب منابع پیشنهادی

| منبع | استفادهٔ مناسب برای این کار | مرز استفاده |
|---|---|---|
| [UI UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | ساختاردهی brief، قواعد UI و بررسی design system | راهنمایی/تولید کمکی است؛ خروجی لوگو یا AI به‌تنهایی انتخاب نهایی MP نیست و هیچ API key یا dependency در این loop اضافه نمی‌شود. |
| [Particles by Casberry](https://particles.casberry.in/) | الهام برای یک demo وب/WebGL یا storyboard | راهکار پیش‌فرض Flutter/Splash نیست؛ ذره‌افشانی فقط اگر به معنا و کارایی کمک کند. |
| [OriginKit](https://www.originkit.dev/docs/components) | دیدن و نمونه‌سازی الگوهای React/Framer | کاتالوگ component وب است؛ کدش بی‌بررسی وارد اپ Flutter نشود. |
| [daisyUI](https://daisyui.com/docs/intro/?lang=en) | اجزای CSS/Tailwind در وب | ابزار طراحی لوگو یا موتور motion نیست و استک Studio را بدون نیاز تغییر نمی‌دهد. |
| [Design Motion Principles](https://github.com/kylezantos/design-motion-principles) | چک‌لیست خلق/بازبینی حرکت هدفمند، restraint، دسترس‌پذیری و کارایی | مرجع روش است؛ توصیه‌های skill باید با پلتفرم و motion-spec خود MP سنجیده شوند. |
| [Motion for React](https://motion.dev/docs/react) (نام کنونی Framer Motion) | حرکت‌های سطح Studio/وب React | پیاده‌سازی React است؛ کتابخانهٔ انیمیشن بومی Flutter محسوب نمی‌شود. |
| [21st.dev](https://21st.dev/community/components/s/animated) | ایده و نمونهٔ component وب | component، dependency و مجوز هر مورد جداگانه بررسی شود. |
| [Animmaster Lib](https://animmasterlib.dev/) | مرجع افکت‌های وب/۳بعدی | خرید/مجوز و هزینه باید برای مورد مشخص بررسی شود؛ گزینهٔ پیش‌فرض اپ بومی نیست. |
| [Skiper UI](https://skiper-ui.com/) | نمونهٔ preloader/reveal وب | زمان demo (مثلاً چند ثانیه) معیار انتظار مناسب در اپ نیست؛ کپی مستقیم ممنوع. |
| [Vengeance UI](https://github.com/Ashutoshx7/VengeanceUI) | الگوهای React/TypeScript/Tailwind | برای الهام/نمونه‌سازی وب؛ dependency یا مجوز هیچ جزء مفروض نیست. |
| [Material 3 Motion](https://m3.material.io/styles/motion/overview/how-it-works) | واژگان motion، easing و transition سازگار با Android | مرجع platform/design system؛ انیمیشن باید با کاهش حرکت و دسترسی‌پذیری سازگار باشد. |

## گیت M100

- مسیرهای موجود، رنگ‌ها، ابزارهای حاضر و launch/startup را از مخزن ثبت کردیم.
- «نشان ثابت»، «Splash سیستم‌عامل» و «reveal اختیاری» از هم تفکیک شدند.
- سه مسیر طراحی و معیار ارزیابی مستند شد؛ هیچ مسیر به‌عنوان logo نهایی ثبت نشده.
- ابزارهای وب به‌عنوان منبع الهام دسته‌بندی شدند؛ package جدید، کد یا assetی وارد نشد.
- نتیجهٔ M100: `PASS` مستنداتی؛ هیچ کد، dependency یا asset محصولی تغییر نکرد.

## خروجی M101/M102 — conceptها و انتخاب مسیر

سه برد مستقل و یک تصویر مقایسه‌ای در [M101-CONCEPTS.md](brand/concepts/M101-CONCEPTS.md) هستند؛ برای هر مسیر SVG قابل‌ویرایش و PNG preview وجود دارد. کاربر C / Progress Loop را انتخاب کرده و M102 `PASS` است. ارزیابی ۸۲/۱۰۰ برای C، ۸۱ برای A و ۶۵ برای B heuristic است، نه تست کاربری.

M103 بستهٔ هویت ثابت C را در `brand/selected-c/M103-C-PACKAGE.md` تکمیل کرد (`PASS`, static identity only): برش optical 16px طبق انتخاب کاربر و Vazirmatn موجود با OFL1.1 برای lockupها استفاده شد. M104 `UNKNOWN` است چون این sandbox ابزار/دستگاه Android ندارد؛ گزارش و run sheet در `finn/reports/m104-startup-measurement.md` است. `app_icon.png` تا M105 همچنان دست‌نخورده است.

## منابع پلتفرمی مرجع

- Apple Human Interface Guidelines — [Launching](https://developer.apple.com/design/human-interface-guidelines/launching)
- Android Developers — [Splash screens](https://developer.android.com/develop/ui/views/launch/splash-screen)
- Material 3 — [Motion](https://m3.material.io/styles/motion/overview/how-it-works)، [Easing and duration](https://m3.material.io/styles/motion/easing-and-duration/tokens-specs)، [Transitions](https://m3.material.io/styles/motion/transitions/applying-transitions)
- پروژهٔ MP — `design/design-system.md` و `mp-app/shared/motion-spec.md`
