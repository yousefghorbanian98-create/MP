# طراحی JP7، نمودارهای پیشرفت و QR صفحهٔ پایانی با بازیابی مستقیم نسخهٔ ساخت‌یافته

**وضعیت:** مشخصات طراحی و نمودار است؛ محاسبه/ذخیره‌سازی مشتق‌شده، QR برنامه و تولید PDF متصل به دادهٔ تازه در محصول پیاده‌سازی نشده‌اند. در کد فعلی `jp7_body_fat` عمداً قفل است. مربی قرائت خام وارد می‌کند؛ فعال‌سازی معادله نیازمند تأیید منبع، جمعیت، پروتکل، رضایت و رفع mismatch سایت‌هاست. یافتهٔ جدید: برای PDFهای تولیدشده توسط Muscle Paradise باید از QR به `ProgramVersion` و دادهٔ canonical برگردیم، نه PDF را OCR کنیم؛ OCR فقط مسیر fallback برای فایل بیرونی/قدیمیِ بی‌پیوند است.

**فلوچارت نهایی:** [QR → ProgramVersion canonical → سنجش/مقایسه → نمودارها → برنامهٔ بعد](athlete-jp7-program-qr-flow-v6-2026-11-23.png). این جزئیات به‌صورت شاخهٔ C02 و تحویل برنامهٔ خصوصی در [نمودار routing اصلی](open-source-question-routing-flow-v1-2026-11-23.png) هم آمده است.

**تعبیر فنی QR:** نیاز محصول این است که اسکن QR در انتهای PDF، کل محتوای همان برنامهٔ تأییدشده را باز و شناسایی کند. یک QR استاندارد نمی‌تواند یک PDF چندصفحه‌ای با محتوای نامحدود را در خودش جا بدهد؛ بنابراین QR باید فقط شناسهٔ مبهم و قابل‌ابطال داشته باشد و سرور پس از احراز هویت، آن را به نسخه و fingerprint بایگانی‌شده وصل کند تا PDF کامل را resolve کند. اگر شرط «تمام بایت‌های همهٔ صفحات داخل یک QR و بدون شبکه» الزام قطعی است، با یک QR استاندارد شدنی نیست.

**پاسخ مستقیم به سؤال «فرمول کجا بود؟»:** در نمودار/سند قبلی، فقط ذخیرهٔ خام و مقایسهٔ کلی آمده بود؛ خود معادله و مسیر تبدیل خودکار خروجی‌ها درج نشده بود. این بخش آن خلأ را جبران می‌کند.

## ۱) ورودی مربی: قرائت‌ها، نه محاسبات دستی

فرم C02 برای هفت site استاندارد این طراحی، هر مقدار را به میلی‌متر می‌گیرد:

`chest`, `midaxillary`, `triceps`, `subscapular`, `abdomen`, `suprailiac`, `thigh`.

مربی این موارد را وارد می‌کند؛ موتور سن را در روز اندازه‌گیری محاسبه می‌کند و مربی نباید مجموع، density، درصد یا توده‌ها را دستی حساب کند:

- هفت قرائت خام (ترجیحاً همراه با repeatهای ثبت‌شده و مقدار consensus که طبق SOP انتخاب شده)؛
- `assessment_date`, ارزیاب، caliper/model و calibration، site-map/protocol version، سمت/وضعیت بدن، شرایط و quality flag؛
- سن به سال در تاریخ اندازه‌گیری؛ برای معادلهٔ انتخابی، `equation_category` که صریحاً توسط ورزشکار/مربی طبق فرم رضایت‌دار تأیید شود؛ از gender profile حدس زده نشود؛
- وزن روز اندازه‌گیری به kg فقط برای مشتقات `fat_mass` و `fat_free_mass`؛ قد برای BMI اختیاری و جدا از JP7 است؛
- تکرارها و قاعدهٔ توافق/خطای مجاز از نسخهٔ پروتکل؛ اگر اختلاف قرائت از حد پروتکل بیشتر است، دوباره اندازه‌گیری شود و خروجی مشتق صادر نشود.

**سایت‌ها باید یکسان باشند:** فهرست کد فعلی در `validate_jp7_raw` شامل `calf` است و `midaxillary` ندارد. این طرح `calf` را به‌عنوان site هفتمِ JP7 جایگزین نمی‌پذیرد؛ فرم، validator، schema، protocol-map و تست‌ها باید در یک تصمیم مستقل هم‌راستا شوند. تا آن زمان محاسبهٔ معتبر انجام نمی‌شود.

## ۲) فرمول‌های پیشنهادی، صریح و versioned

`Σ7` = جمع هفت skinfold نهایی بر حسب mm؛ `age` = سن به سال در روز ارزیابی؛ `Db` = body density با واحد g/cm³. معادلهٔ density به equation category وابسته است:

**JP7 مردان (Jackson–Pollock 1978):**

`Db = 1.112 − 0.00043499×Σ7 + 0.00000055×(Σ7²) − 0.00028826×age`

**JP7 زنان (Jackson–Pollock, Ward 1980):**

`Db = 1.0970 − 0.00046971×Σ7 + 0.00000056×(Σ7²) − 0.00012828×age`

برای تبدیل density به درصد چربی، conversion زیر یک شناسه/نسخهٔ مستقل دارد:

**Siri 1961:** `body_fat_pct = (495 / Db) − 450`

`JP7 density equation` و `Siri conversion` دو رکورد جدا در `EquationRegistry` هستند. سیستم باید formula/equation IDs، ضرایب/منبع، نسخه، scope جمعیتی، approver و زمان تأیید را کنار هر نتیجه ثبت کند. خروجی درصد چربی، تخمین مدل دوزمانی است، نه اندازه‌گیری مستقیم یا تشخیص پزشکی. اگر category برای معادله معتبر/قابل‌اعمال/تأییدشده نیست، فقط دادهٔ خام ذخیره شود و `body_fat_pct` تهی بماند؛ سیستم category را حدس نمی‌زند.

**منابع اولیهٔ پیشنهادی برای review پیش از فعال‌سازی:** Jackson & Pollock (1978), “Generalized equations for predicting body density of men,” *British Journal of Nutrition*, 40, 497–504؛ Jackson, Pollock & Ward (1980), “Generalized equations for predicting body density of women,” *Medicine & Science in Sports & Exercise*, 12(3), 175–181؛ Siri (1961), “Body composition from fluid spaces and density,” در *Techniques for Measuring Body Composition*. این ارجاع‌ها باید توسط مسئول علمی تطبیق داده شوند با نسخهٔ protocol، جمعیت و حقوق استفاده؛ ثبت آن‌ها در سند به‌معنای آزادشدن قفل کد فعلی نیست.

## ۳) خروجی خودکار برای پروفایل و برنامهٔ خصوصی عضو

پس از validation و محاسبهٔ مجاز، سرویس به‌طور خودکار یک `AnthropometrySnapshot` immutable می‌سازد و در پروفایل همان عضو ذخیره می‌کند:

| خروجی | روش/منبع | نمایش |
|---|---|---|
| هر هفت raw site + repeatها | ورودی ثبت‌شدهٔ مربی | نمای خصوصی اندازه‌گیری برای عضو و مربی مجاز |
| `sum7_mm` | جمع همان هفت site پس از quality gate | کنار protocol/equation version |
| `Db_g_cm3` | فرمول JP7 متناسب با equation category و age | با فرمول/نسخه و scope |
| `body_fat_pct` | Siri conversion جداگانه | تخمین درصد چربی کلی + حدود/عدم‌قطعیت؛ نه رشد موضعی عضله |
| `fat_mass_kg` | `weight_kg × body_fat_pct / 100` | فقط اگر وزن همان ارزیابی معتبر موجود است |
| `fat_free_mass_kg` | `weight_kg − fat_mass_kg` | فقط با همان وزن؛ معادل muscle mass نیست |
| `BMI` (اختیاری) | `weight_kg / height_m²` | شاخص جدا و نه خروجی JP7؛ تفسیر جدا |
| quality/repeatability | SOP version، repeat spread/TEM در صورت تعریف و confidence | low quality ⇒ hold/re-measure؛ score با confidence پایین منتشر نشود |

مقادیر مشتق‌شده دوباره روی raw نمی‌نویسند. هر نتیجه، source reads، actor، تاریخ، equation/protocol version، status و consent دارد. نمودارهای پیشرفت فقط در گزارش/پروفایل خصوصی عضو و مربی مجاز نمایش داده می‌شوند؛ قرائت خام پوست‌چین یا درصد چربی به‌صورت پیش‌فرض داخل PDF اجرایی برنامه چاپ نمی‌شود.

## ۴) مقایسه با history همان عضو و نمودار روند

هر snapshot تازه با snapshot پیشین از `AthleteProfile → MeasurementHistory` match می‌شود؛ نام عضو join key نیست. مقایسهٔ درصد چربی/توده‌ها فقط وقتی معتبر است که مالک و پروفایل، site set، واحد، protocol/site-map، ابزار/کیفیت، equation category و `equation_id + conversion_id` همسان/قابل‌تبدیل و تاریخ/وزن لازم موجود باشد. در غیر این صورت:

- raw measurement جدید همچنان در history ذخیره می‌شود؛
- فیلد نامنطبق `not comparable / needs review` می‌شود و از delta مشترک کنار گذاشته می‌شود؛
- مربی/عضو درخواست تکرار پروتکل همسان می‌گیرند؛ مقدار baseline overwrite نمی‌شود.

برای هر ارزیابی، نمودار فردیِ زمانی می‌تواند `Σ7`, `Db`, `body_fat_pct`, `fat_mass_kg`, `fat_free_mass_kg` و وزن را جدا و با واحد/تاریخ/equation/source/quality نمایش دهد. trend برای عضو و مربی اختصاص‌یافته در پروفایل ذخیره می‌شود، با access control و audit. افزایش `fat_free_mass` یا تغییر درصد چربی به‌تنهایی اثبات رشد عضلهٔ موضعی یا اثر علّی یک حرکت نیست.

## ۵) یک QR در صفحهٔ پایانیِ PDF کامل هر برنامه

پس از تأیید مربی، برای **هر ورزشکار و هر نسخهٔ برنامه یک PDF کاملِ چندصفحه‌ای** تولید و بایگانی می‌شود. فقط **یک QR برنامه** در انتهای صفحهٔ آخر همان PDF قرار می‌گیرد. QR باید با اسکن، نسخهٔ دقیق را شناسایی کند و دسترسی به تمام صفحه‌های همان برنامه را فراهم کند.

### محدودیت فنیِ «همهٔ محتوا داخل QR»

یک QR استاندارد، ظرفیتی محدود دارد: در بیشترین حالتِ رایج (Version 40، تصحیح خطای L) حداکثر حدود ۲٬۹۵۳ بایت در حالت باینری می‌پذیرد؛ سطح تصحیح خطای بالاتر ظرفیت را کمتر می‌کند. یک PDF چندصفحه‌ای، به‌ویژه با متن/تصویر، معمولاً از این اندازه بسیار بزرگ‌تر است. پس **قرار دادن همهٔ بایت‌های PDF داخل یک QR استاندارد ممکن نیست**. فشرده‌سازی هم این محدودیت را برای همهٔ برنامه‌ها و تصاویر حل نمی‌کند.

راهکار پیشنهادی که نتیجهٔ موردنظر شما را حفظ می‌کند: QR در صفحهٔ آخر فقط یک شناسهٔ مبهم و غیرحساس داشته باشد؛ سرور آن را به `athlete + program_version_id`، دادهٔ canonical و fingerprint بایگانی‌شده map می‌کند. پس از ورود و کنترل مالکیت، سامانه **کل نسخهٔ ساخت‌یافته و همهٔ صفحه‌های PDF** را از بایگانی باز می‌کند. این شناسه مجوز دسترسی نیست، قابل‌ابطال است و QR دادهٔ حساس ندارد. اگر الزام شما این است که کل سند بدون شبکه و فقط از یک QR قابل‌بازیابی باشد، باید آن را به‌عنوان محدودیت/تغییر فنیِ جداگانه حل کنیم؛ یک QR استاندارد جواب نمی‌دهد.

QR برای هر عضو و هر نسخهٔ تأییدشده یکتاست، نه یک کد عمومی مشترک برای همه. `ProgramVersion` ساخت‌یافته منبع حقیقت است؛ PDF فقط render همان داده است و fingerprint/renderer/template version دارد. بنابراین PDF داخلی با QR معتبر **مستقیماً از نسخهٔ canonical بازیابی می‌شود، نه با OCR**؛ تغییرات بعدی برنامه و نسخه/PDF قبلی را دستکاری نمی‌کنند.

### بازیابی برنامهٔ قبلی: native fast path و fallback فایل بیرونی

- **برنامهٔ صادرشده از Muscle Paradise:** QR/reference یا انتخاب از تاریخچه → احراز هویت/مالکیت → resolve `ProgramVersion` و `content_hash` → بارگذاری مستقیم JSON ساخت‌یافته و PDF کامل. OCR لازم نیست؛ خواندن دوبارهٔ PDF فقط خطا و تأخیر اضافه می‌کند.
- **PDF بیرونی/قدیمی یا بدون reference قابل‌حل:** فایل اصلی خصوصی و immutable بارگذاری و hash می‌شود؛ اول text/layout extraction برای PDF دیجیتال؛ OCR فقط برای صفحهٔ تصویری/اسکن‌شده. خروجی به‌صورت `ImportCandidate` با متن خام، page/bounding-box، روش استخراج و confidence نگهداری می‌شود. نام حرکت‌ها به کاتالوگ canonical پیشنهاد می‌شوند؛ هیچ مقدار نامشخصی حدس زده یا وارد برنامهٔ اجرایی نمی‌شود.
- **تأیید:** مربی candidate را کنار صفحهٔ اصلی بازبینی می‌کند؛ هویت عضو، واحد، حرکت، set×rep، بار و progression مبهم را تأیید/اصلاح می‌کند. فقط پس از تأیید، یک `LegacyProgramVersion` immutable با hash فایل، schema/import version، provenance هر فیلد و reviewer ثبت می‌شود. فایل/دادهٔ قبلی overwrite نمی‌شود.

### مسیر اسکن تا ارزیابی و ساخت برنامهٔ جدید

1. اسکن QR، نسخهٔ قبلی و کل سند را resolve می‌کند؛ سپس login، نقش و مالکیت عضو/برنامه کنترل می‌شود. QR به‌تنهایی دسترسی خصوصی نمی‌دهد و اسکن به‌معنی انجام تمرین یا سنجش نیست.
2. دادهٔ خام جدید را **مربی** با تاریخ/پروتکل/کیفیت سنجش برای همان عضو ثبت می‌کند. رکورد قدیمی دست‌نخورده می‌ماند. لاگ اجرای واقعی، بازخورد ست، effort، درد/توقف، تعویض حرکت و جلسات ازدست‌رفته نیز از مسیر مستقل ثبت می‌شوند.
3. مقایسه فقط بین رکوردهای همان عضو و فیلدهای واقعاً قابل‌مقایسه انجام می‌شود. اگر site/protocol/tool/quality یا محدودهٔ معادله ناسازگار باشد، نتیجه `not comparable / needs review / re-measure` است.
4. نمودار **چربی/ترکیب بدن** فقط از سنجهٔ معتبر و مجاز ساخته می‌شود: اگر معادلهٔ JP7 تأیید و قابل‌اعمال باشد، می‌توان تخمین نسخه‌دار را همراه با عدم‌قطعیت نشان داد؛ وگرنه نمودار `Σ7` و/یا وزن/دور کمر با نام درست خودشان نمایش داده می‌شود، نه «درصد چربی» ساختگی.
5. نمودار **عضله‌سازی** از JP7 به‌تنهایی نتیجه نمی‌شود. برای هر گروه عضلانی، دادهٔ قابل‌دفاع مانند عملکرد حرکت‌های ثابت با بار/تکرار و effort یکسان، حجم تمرین انجام‌شده، adherence/recovery و در صورت دسترسی سنجهٔ موضعیِ استاندارد به‌کار می‌رود. محیط اندام شاخص کمکی است، نه اندازه‌گیری مستقیم عضله.
6. `ProgramComposer` نسخهٔ کامل قبلی، روندهای معتبر، لاگ‌های واقعی، هدف/محدودیت‌های تازه، کاتالوگ حرکتِ approved و گیت ایمنی را ترکیب می‌کند. برای هر عضله scorecard و دلیل تغییر/حفظ حرکت ثبت می‌شود؛ تغییر حرکت صرفاً به‌خاطر یک عدد JP7 یا اجبار به تعویض در هر چرخه نیست.
7. مربی نمودارها، scorecardها و تغییرات ساختار/حرکت را بازبینی و تأیید می‌کند. سپس `ProgramVersion n+1` و PDF کامل جدید ساخته می‌شود و QR نسخهٔ جدید در انتهای صفحهٔ آخر می‌آید. نسخهٔ قبلی همچنان در تاریخچه می‌ماند.

## ۶) stateها و توقف‌های الزامی

`prior_program_source → (native_QR/history_ref → auth+ownership+hash_check → direct_canonical_ProgramVersion_load; no_OCR) | (external_or_unlinked_PDF → private_quarantine+hash → text/layout_extract → OCR_scanned_pages_only → ImportCandidate+provenance → coach_side_by_side_confirm → immutable_LegacyProgramVersion) → resolved_prior_program → coach_raw_entry+actual_training_logs → site/protocol/quality_gate → equation_scope_and_consent_gate → jp7_calculation_or_raw_only → immutable_measurement_snapshot → comparability_gate → private_fat/performance_trends → per_muscle_scorecards → ProgramDraft n+1 → coach_review/approval → immutable_canonical_ProgramVersion n+1+content_hash → render_full_private_PDF → QR_on_final_page → next_cycle`.

شاخه‌های `invalid_site`, `missing_age/category`, `equation_locked/not_approved`, `repeat_quality_fail`, `not_comparable`, `unresolved_import_field`, `unauthorized_scan`, `no_new_measurement/logs`, `insufficient_muscle_metric` و `safety_hold` از استنتاج/تجویز خودکار خارج می‌شوند و اقدام بعدی می‌دهند؛ هیچکدام با صفر یا «بدون تغییر» جایگزین نمی‌شوند.

## ۷) مرز وضعیت فعلی کد و تصمیم‌های لازم

- [`equations.py`](../../../mp-app/backend/modules/assessment/equations.py) فعلاً `APPROVED_EQUATIONS` خالی دارد و `jp7_body_fat` را قفل می‌کند؛ در این تغییر کد/DB دست‌نخورده است.
- raw validator و schemas فعلی `calf` می‌خواهند، درحالی‌که این طراحی هفت‌سایت کلاسیک شامل `midaxillary` را مشخص می‌کند؛ پیش از implementation باید source/protocol و migration/API/UI/tests در یک ADR جدا تصویب شود.
- owner علمی باید equation scope، category eligibility، دقیق‌بودن روش اندازه‌گیری، repeats/TEM، body-fat conversion و خروجی مجاز را تأیید کند. اگر معادله برای عضو قابل‌اعمال نیست، raw-only حفظ می‌شود.
- endpoint و نمودار روندِ خام `Σ7` از قبل وجود دارند، اما معادلهٔ درصد چربی قفل است؛ مقایسهٔ پروتکل‌محور، snapshot مشتق‌شده، نمودارهای معتبر چربی/پیشرفت عضله، QR مخصوص PDF برنامه و resolver نسخهٔ کامل هنوز در این طراحی پیاده نشده‌اند. QR موجودِ check-in باشگاه با QR برنامه یکی نیست.
- برنامهٔ فعلی `WorkoutProgram`/week/exercise rows، تأیید مربی و بخشی از set feedback را دارد؛ اما `ProgramVersion` canonical immutable با content hash، resolver QR، تولید PDF از همان canonical record و مسیر OCR/import برای PDF بیرونی در این طراحی اضافه شده‌اند و هنوز پیاده‌سازی نشده‌اند. بنابراین مسیر native بدون OCR پس از ساخته‌شدن این زیرساخت قابل‌اجرا است.
