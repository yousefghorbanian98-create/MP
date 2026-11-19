# گزارش تکمیلی REA و RepoWise برای ارزش‌های نامزد

**وضعیت این نوبت:** پژوهش هدفمند و برنامه‌ریزی انجام شده؛ قابلیت‌های محصول پیاده یا پذیرفته نشده‌اند. [برنامهٔ برش‌ها و نقش‌ها](PLAN-OSS-VALUE-MICROLOOPS-2026-11-18.md) · [نقشهٔ هدف](architecture/oss-value-flows.md).

## خلاصهٔ عملی

1. جایگزینی backend یا اپ MP با هیچ‌یک از شش نامزد توصیه نمی‌شود. بررسی دقیق‌تر نشان داد خود MP از قبل بخش‌هایی از QR، تمرین، تغذیه و چت دارد؛ اول باید این اجزا تکمیل و آزمایش شوند.
2. سازوکار QR موجود MP از Gymkhana به‌صورت ظاهری ساده‌تر نیست: مسیر MP شناسهٔ تصادفی را هش و بازپخش و خطای رقابت DB را بررسی می‌کند؛ جایگزینی با کد نامزد بدون آزمون ممکن است این حفاظت را حذف کند.
3. صفحهٔ تمرین Open-Fit که بررسی شد دادهٔ نمونه و callback خالی دارد؛ نباید به‌عنوان ثبت تمرین عملیاتی وارد شود. تایمر Workout.cool بر شمارش تیک interval متکی است و قبل از استفاده باید drift و lifecycle آن بررسی شود.
4. مقداردهی، snapshot و savepoint در Lyftr الگوی خوبی برای بررسی race است، اما lookup ناموفق سابقه در مسیر موردنظر مانند «بدون سابقه» نمایش داده می‌شود؛ نیاز به آزمون و تصمیم مستقل دارد. انتقال الگوریتم بدون بررسی این تفاوت و قواعد MP نادرست است.
5. policy پرداخت انسان‌محور، نقش‌های مالک، محافظت از اطلاعات سلامت و حذف عکس پیشرفت بدن حفظ می‌شوند؛ OCR فقط می‌تواند متن پیشنهادی بدهد و تأیید بانکی نیست.

## REA: اجراهای واقعی و مرز پوشش

در شروع شاخه `arena/b0e55b62-mp`، HEAD `4571908c1fdc8dca6a2ba700f8f99f3b52329ab0` و ۴۶ مسیر dirty/untracked و staged صفر بود. REA واقعی **6.9.0** در محیط موقت اجرا شد؛ همهٔ sourceها pinned و mirror شده در `/tmp` و بدون اجرای کد نامزد بودند. `import-reference-source --detail summary` روی ۲۲ فایل منتخب با مجموع ۳۱۷۶ خط و شش مرجع اجرا شد:

| مرجع | SHA | فایل/خط ورودی منتخب | خروجی |
|---|---|---:|---|
| Gymkhana | `8197e4434fe152abb383ebc46c176e12aea06f10` | ۴ / ۵۲۳ | exit 0، `partial` |
| Lyftr | `21f63dc3ccdde65150d317077e5ae9d2b54edbad` | ۵ / ۷۲۷ | exit 0، `partial` |
| Workout.cool | `d52f9f62d2a5fcbb78d67a95dc8763f9a34dbf9e` | ۳ / ۱۴۸ | exit 0، `partial` |
| Open-Fit | `77c74a53ef729efa3c813ad087db97bdbd7d582e` | ۳ / ۲۶۶ | exit 0، `partial` |
| Fitness-Flutter-App | `2266460297aa3db6438384a58abfae3f1cb9a704` | ۳ / ۳۳۲ | exit 0، `partial` |
| MuscleMap | `d53ddf4d480b65979f1008b203e6b6eda0e67e54` | ۴ / ۱۱۸۰ | exit 0، `partial` |

تعداد خط فقط اندازهٔ ورودی است، نه تعداد خطوطی که REA معنای آن را فهمیده یا بازبین انسانی مستقل ممیزی کرده است. این فرمان فایل‌ها را به‌عنوان **historical reference** فهرست/هش می‌کند و ممیزی خط‌به‌خط معنایی، تست یا تأیید امنیت نیست؛ REA در اجراهای قبلی برای Dart رابطهٔ معنایی استخراج نکرد. بنابراین درخواست «بررسی موشکافانهٔ خط‌به‌خط همهٔ پروژه‌ها با REA» **تکمیل نشده و نباید چنین ادعایی شود**.

علاوه بر آن، `analyze-javascript-application` واقعاً روی شش فایل منتخب QR از Gymkhana، پنج فایل تایمر/sync Workout.cool و شش فایل منتخب Studio MP اجرا شد، هر سه exit 0. به‌ترتیب ۸۳۹، ۶۰۲ و ۴۸ فایل inventoried بیرون دامنهٔ تحلیل انتخابی ماندند. Static analysis و `complete-within-view` به معنی کامل‌بودن کل برنامه نیست. خروجی خام موقت است و پیش از هر انتشار باید مستقل از نظر دادهٔ حساس بررسی شود. فایل‌های منتخب و یافته‌های زیر با مشاهدهٔ دستی عامل اصلی نیز تطبیق شدند، نه QA مستقل.

## یافته‌های قابل پیگیری با مسیر و خط

| موضوع | شواهد و معنای عملی | تصمیم / برش |
|---|---|---|
| QR MP | `mp-app/backend/modules/face_id/router.py:70-117` token، بررسی scope، هش jti، خطای بازپخش و رسیدگی به IntegrityError را نشان می‌دهد؛ `service.py:203-229` وضعیت عضویت و ثبت DB را بررسی می‌کند. این مشاهده جای تست E2E/هم‌زمانی نیست. | حفظ و آزمون واقعی؛ OV-02. |
| QR Gymkhana | [adapter:219-265](https://github.com/gymkhana-fitness-360/gymkhana/blob/8197e4434fe152abb383ebc46c176e12aea06f10/src/domains/attendance/adapters/attendance-adapter.ts#L219-L265) payload امضاشده و کنترل بیش‌ازپنج‌دقیقه دارد؛ [adapter:288-300](https://github.com/gymkhana-fitness-360/gymkhana/blob/8197e4434fe152abb383ebc46c176e12aea06f10/src/domains/attendance/adapters/attendance-adapter.ts#L288-L300) جست‌وجوی حضور باز را نشان می‌دهد. این مرجع به‌تنهایی اثبات تک‌بارمصرفی یا مالکیت کامل نیست؛ timestamp نامعتبر/آینده و رقابت باید جداگانه تست شود. | الگوی سناریو، نه جایگزین ضدبازپخش MP؛ OV-01/02. |
| جلسه و پیشرفت | `mp-app/client/lib/features/today/today_controller.dart:8-35` پیشرفت را به‌صورت set از index در state و برنامه را از provider می‌گیرد؛ پایداری این state با همین مشاهده اثبات نمی‌شود. [Lyftr workout_progression.go:46-96](https://github.com/Cawlumm/lyftr/blob/21f63dc3ccdde65150d317077e5ae9d2b54edbad/backend/stores/workout_progression.go#L46-L96) snapshot و savepoint دارد؛ [خطوط 102-117](https://github.com/Cawlumm/lyftr/blob/21f63dc3ccdde65150d317077e5ae9d2b54edbad/backend/stores/workout_progression.go#L102-L117) خطای lookup را به nil تبدیل می‌کند. | هویت پایدار جلسه، تست crash/retry و مشخص‌کردن خطا در برابر سابقهٔ خالی؛ OV-03/05. |
| صفحهٔ Open-Fit | [active_workout_screen.dart:65-82](https://github.com/synthalorian/Open-Fit/blob/77c74a53ef729efa3c813ad087db97bdbd7d582e/lib/features/workouts/presentation/active_workout_screen.dart#L65-L82) تعداد نمونه و callback خالی، [خطوط 120-181](https://github.com/synthalorian/Open-Fit/blob/77c74a53ef729efa3c813ad087db97bdbd7d582e/lib/features/workouts/presentation/active_workout_screen.dart#L120-L181) ردیف‌ها و checkbox نمونه دارند. finish بررسی‌شده فقط dialog و خروج از صفحه را نشان می‌دهد، نه اثبات ذخیره. | الهام UI؛ پیاده‌سازی واقعی/تست اختصاصی؛ OV-03/04. |
| تایمر | [Workout.cool timer.tsx:21-35](https://github.com/Snouzy/workout-cool/blob/d52f9f62d2a5fcbb78d67a95dc8763f9a34dbf9e/src/components/ui/timer.tsx#L21-L35) بر `setInterval` و افزایش یک ثانیه‌ای متکی است. throttling/background ممکن است به drift منجر شود؛ این خطر نیازمند آزمون واقعی است. | طراحی و تست lifecycle/clock، نه کپی بدون تغییر؛ OV-04. |
| تغذیه | `mp-app/backend/modules/nutrition/router.py` و `service.py` جست‌وجو، ثبت غذا و summary را دارند؛ providers Open-Fit به repositoryهای Isar وابسته‌اند. | روی API موجود و محاسبه با fixture مجاز کار شود؛ OV-06. |
| چت و نقش | `mp-app/client/lib/features/chat/member_chat_page.dart:64-118` ارسال و read به مسیر گفت‌وگو دارد. در Fitness-Flutter-App مسیر `routes/auth.py:24` fallback مقایسهٔ خام و `routes/users.py:166` تغییر نقش توسط admin را نشان می‌دهد؛ پیش‌فرض کلید آن نیز برای تولید مناسب نیست. | نگه‌داشتن مدل امنیت MP و تطبیق UI؛ کپی auth ممنوع؛ OV-07. |
| عضله و رسانه | MuscleMap در فایل‌های `Sources/MuscleMap/Data/{MaleFrontPaths,FemaleFrontPaths,Muscle}.swift` هدر MIT دارد ولی provenance تمام هندسه/دارایی و تبدیل Flutter/web مستقلاً تأیید نشده است. `mp-app/backend/modules/exercises/router.py` تصویر/GIF را نمایش می‌دهد. | نقشه و رسانه فقط با ممیزی کامل asset و دسترس‌پذیری؛ OV-08/10. |
| تناقض مستندات رسانه | `backend/data/external/free_exercise_db/SOURCE.md` دربارهٔ تصاویر آن کاتالوگ می‌گوید vendored نیستند؛ در tree فعلی `git ls-files mp-app/backend/static/exercises` تعداد ۵۱ فایل tracked را نشان داد. این شمارش **به‌تنهایی منشأ، نوع، شباهت یا حق استفادهٔ آن ۵۱ فایل را اثبات نمی‌کند** و لزوماً جملهٔ سند را نقض نمی‌کند. | قبل از انتشار هر media inventory و digest و نسبت آن با کاتالوگ را مشخص کنید؛ OV-10. |

GitHub نامزدها و مجوز سطح کد: [Gymkhana/Apache-2.0](https://github.com/gymkhana-fitness-360/gymkhana/tree/8197e4434fe152abb383ebc46c176e12aea06f10)، [Lyftr/MIT](https://github.com/Cawlumm/lyftr/tree/21f63dc3ccdde65150d317077e5ae9d2b54edbad)، [Workout.cool/MIT](https://github.com/Snouzy/workout-cool/tree/d52f9f62d2a5fcbb78d67a95dc8763f9a34dbf9e)، [Open-Fit/Apache-2.0](https://github.com/synthalorian/Open-Fit/tree/77c74a53ef729efa3c813ad087db97bdbd7d582e)، [Fitness-Flutter-App/MIT](https://github.com/Mounib-Chandoul/Fitness-Flutter-App/tree/2266460297aa3db6438384a58abfae3f1cb9a704)، [MuscleMap/MIT](https://github.com/melihcolpan/MuscleMap/tree/d53ddf4d480b65979f1008b203e6b6eda0e67e54). مجوز root حق خودکار استفادهٔ همهٔ داده‌ها و دارایی‌ها نیست. [RepDB](https://huggingface.co/datasets/RepDB/exercise-dataset/blob/main/LICENSE.md) مجوز سفارشی، انتساب و محدودیت dataset/API دارد؛ حل حقوق و پین نسخه قبل از استفاده ضروری است. OCR فیش خارجی بررسی‌شده مربوط به ایران نیست و راستی‌آزمایی بانکی محسوب نمی‌شود.

## RepoWise: اجرای واقعی، نه اتصال ادعایی

- `repowise 0.61.0` از wheel در virtualenv موقت نصب و اجرا شد. نسخه و CLI مشاهده شد؛ `--no-prose`, `--no-editor-setup`, `--no-hook`, `--no-distill-hook`, `--no-agents`, `--no-codex`, `--no-claude-md`, `--no-save-key`, `--no-workspace` و محیط `REPOWISE_OFFLINE=1` و بدون کلید استفاده شدند. هیچ مدل یا embeddings واقعی یا اتصال MCP به Arena اجرا نشد.
- برای حفاظت داده، ۵۳۰ فایل mirror گزینشی نوبت قبل گردآوری شد؛ اسکن Gitleaks یک فایل دارای یک finding را از mirror کنار گذاشت و اسکن مجدد mirror exit 0 بود. اسکن کشف همهٔ اسرار را تضمین نمی‌کند. از ۵۲۹ فایل باقی‌مانده RepoWise گزارش **۵۱۷ فایل index‌شده، ۳۵۶۲ symbol، ۱۲۱۴۲ edge و ۳۶۲ صفحهٔ code-derived** داد؛ جست‌وجو full-text است. تفاوت ۵۲۹/۵۱۷ یعنی هم‌ارزی کل mirror با index فرض نمی‌شود. گزارش status مقدار `indexed_files: 648` را نیز در بخش mapping نشان می‌دهد که با `working_tree_files: 517` تفاوت دارد؛ تفسیر آنها به‌عنوان فایل یکتای منبع ممکن نیست.
- برای جلوگیری از خواندن تاریخچهٔ دارای اسرار، داخل همان mirror یک Git repository مصنوعی با یک commit محلی ساخته شد. SHA آن مربوط به **mirror مصنوعی** است نه commit MP، و تحلیل تاریخچه/ownership واقعی MP در آن ممکن نیست. index واقعی ریشهٔ پروژه ساخته یا به‌روز نشد؛ `.repowise/` خام در مخزن یا GitHub وارد نشده و موقت است.
- `repowise context --include symbols` برای QR، برنامه، تغذیه، `today_controller.dart` و `ExerciseLibrary.tsx` اجرا شد. خروجی Dart، نام `TodayState` و `TodayController` و رابطه با صفحه/تست را نشان داد و با خواندن source مقایسه شد. یک `export --format structurizr --standalone --components --no-externals` در `/tmp` خروجی ۲ container، ۲۱ component و ۹۸ relation ساخت؛ چون دامنه محدود است و Flutter را به‌صورت container جدا گزارش نکرد، **نقشهٔ کامل MP نیست**. نمودار نسخه‌شدهٔ این گزارش بر پایهٔ همان سرنخ‌ها و تطبیق دستی ساخته شده، نه رونویسی بی‌بررسی خروجی ابزار.
- پس از ساخت اسناد، ۱۰ فایل مستنداتیِ جداگانه اسکن و به mirror مصنوعی کپی شدند؛ `repowise update --index-only --defer-docs --no-agents` واقعاً exit 0 داد و ۱۰ فایل تغییرکرده، ۴۷۳۹ node و ۱۲۲۰۴ edge گزارش کرد. این به‌روزرسانی نیز فقط روی mirror موقت بود؛ بازنویسی صفحات تعمداً defer شد و index ریشهٔ پروژه به‌روزرسانی نشد. یادداشت حاضر بعد از snapshot به گزارش افزوده شد و خودِ این جمله داخل همان snapshot نیست. یک تلاش قبلی برای اسکن مجدد کل mirror پس از ساخته‌شدن cache ابزار exit 1 داد و پیش از update متوقف شد؛ در تلاش موفق فقط ۱۰ سندِ جداگانه اسکن و صریحاً به Git مصنوعی افزوده شدند، نه cache `.repowise`.
- هشدارهای heuristic RepoWise از جمله نمرهٔ سلامت و dead-code، شاهد ایمنی یا مجوز حذف نیستند؛ هیچ فایلی بر اساس آنها حذف نشد. شماره‌ها و زمان اجرای ابزار ممکن است تحت تأثیر snapshot و ساعت sandbox باشند.

## وضعیت اجرا و باقی‌مانده

برنامهٔ OV-01..11 و نقش‌های موازی در سند همراه نوشته شده‌اند. هیچ dependency یا کد/تصویر/دادهٔ خارجی به محصول اضافه، هیچ QF/OV بسته، هیچ subagent مستقل اجرا و هیچ تست Flutter، امنیت مستقل یا E2E در این نوبت PASS اعلام نشده است. Flutter/Dart محلی موجود نبود و ECC/QA مستقل پیش‌تر در میزبان فعلی اثبات نشده است. محدودیت‌های مجوز RepDB و صحت داده‌های ایرانی نیز بازند. CI موفق تاریخی برای `4571908...` شاهد tree جدید نیست. برای ورود واقعی ارزش‌ها باید loopهای مربوط با گیت‌های سند برنامه و شواهد جدید اجرا شوند.
