# FINN Decisions — ثبت تصمیم‌های خودمختار (ADR سبک)
> هرگاه لوپ بدون نظارت انسان تصمیمی گرفت، اینجا ثبت می‌کند: زمینه، گزینه‌ها، انتخاب، دلیل.

---

## D-001 — تاریخ 2026-11-14 — حفاظت حافظهٔ لوپ در برابر پاک‌شدن سندباکس
- **زمینه:** کاربر صریحاً خواسته «بعد از هر میکرو-چرخه ساخته‌ها در گیت‌هاب ذخیره شوند تا در سندباکس پاک نشوند». چک‌لیست ۳.۵ می‌گوید `.finn/` و `.claude/` در `.gitignore` باشند.
- **گزینه‌ها:** (الف) پیروی کورکورانه از چک‌لیست و gitignore کردن کل `.finn/` و `.claude/` (خطر: از‌دست‌رفتن LEDGER/DECISIONS/REGRESSIONS با wipe سندباکس)؛ (ب) commit کردن فایل‌های کوچک وضعیت و نقش‌آفرینی ایجنت‌ها، ignore کردن کلون ECC.
- **انتخاب:** (ب) — `.finn/state/` + `.finn/ecc-commit.txt` + `.claude/` (مجموعاً < ۴۰۰KB) در git commit می‌شوند؛ فقط `.finn/ecc/` (کلون، بازتولیدپذیر با کامیت پین‌شده) ignore است.
- **دلیل:** اولویت صریح کاربر (حفظ در گیت‌هاب) + بازتولیدپذیری (G10): کامیت ECC در `ecc-commit.txt` ثبت است و کلون هر لحظه بازسازی می‌شود؛ اما حافظهٔ لوپ (درس‌ها/تصمیم‌ها/رگریشن‌ها) غیرقابل‌بازسازی است.

## D-002 — تاریخ 2026-11-14 — نبود Flutter/Dart SDK در محیط اجرا
- **زمینه:** محیط سندباکس فقط به github.com، npmjs، pypi دسترسی دارد؛ دانلود Flutter SDK (storage.googleapis.com) ممکن نیست.
- **گزینه‌ها:** (الف) حذف MP Client از scope؛ (ب) نوشتن کامل پروژهٔ Flutter + تست‌ها و انتقال گیت‌های اجرایی (`flutter analyze/test`) به CI گیت‌هاب؛ (ج) بازنویسی Client با React (انحراف از طرح).
- **انتخاب:** (ب) — پروژهٔ Flutter کامل (lib/ + test/ + pubspec) نوشته و commit می‌شود؛ گیت‌های اجرایی آن در `.github/workflows/ci.yml` تعریف می‌شوند.
- **دلیل:** طرح ۱۶ لایه تکنولوژی Client را Flutter تثبیت کرده؛ انحراف به React ممنوع (دام لایهٔ ۶). خطای محیطی = مسیر جایگزین + ثبت (پروتکل بخش ۸).

## D-003 — تاریخ 2026-11-14 — نبود Docker در محیط اجرا
- **زمینه:** Docker در سندباکس نصب نیست؛ لایهٔ ۱۱ نیازمند docker-compose است.
- **گزینه‌ها:** (الف) حذف زیرساخت؛ (ب) نوشتن docker-compose + Caddyfile + Ansible به‌عنوان artifact و اعتبارسنجی YAML/سینتکس، اجرای استک در CI/سرور هدف.
- **انتخاب:** (ب).
- **دلیل:** خروجی لایهٔ ۱۱ فایل‌های provisioning هستند؛ اجرای استک در محیط هدف (CI با Docker) انجام می‌شود.

## D-004 — تاریخ 2026-11-14 — اسکرین‌شات UI در نبود مرورگر headless
- **زمینه:** کاربر خواسته «قبل از ساخت UI/UX اول اسکرین‌شات بده». مرورگر headless قابل نصب نیست (CDN مرورگرها مسدود).
- **گزینه‌ها:** (الف) موکاپ‌های باکیفیت تولیدشده با مدل تصویر + نمایش به کاربر قبل از ساخت؛ (ب) Live Preview اپ واقعی پس از ساخت؛ (ج) اسکرین‌شات‌های Playwright در CI.
- **انتخاب:** هر سه — موکاپ در آغاز M06/M07 نمایش داده می‌شود (بازرسی کاربر)، سپس UI مطابق موکاپ ساخته و با Live Preview نمایش داده می‌شود؛ اسکرین‌شات‌های خودکار به CI منتقل می‌شوند.
- **دلیل:** تأمین حداکثری خواستهٔ کاربر با ابزار در دسترس.

## D-005 — تاریخ 2026-11-14 — انتخاب shadcn/ui به‌عنوان تنها سیستم کامپوننت Studio
- **زمینه:** لایهٔ ۷ می‌گوید shadcn/ui **یا** DaisyUI، هرگز هر دو.
- **گزینه‌ها:** shadcn/ui (کامل‌تر، سازگار با Framer Motion و Origin UI) | DaisyUI (ساده‌تر).
- **انتخاب:** shadcn/ui + Tailwind + Framer Motion.
- **دلیل:** سازگاری با اکوسیستم انیمیشن (Framer Motion/Skiper UI) و کیفیت کلاس جهانی خواسته‌شده؛ Tailwind برای هر دو گزینه مشترک است.

## D-006. (M14) endpoint خروجی موتور: `POST /programs/from-engine`
شکاف محصول: سرویس `create_program_from_engine_output` بدون مسیر HTTP بود. مسیر اضافه شد تا M15 (موتور هوش مصنوعی) خروجی قواعد را مستقیم ثبت کند. قواعد G8 حفظ شد: `llm_explanation` فقط متن.

## D-007. (M15) معماری هوش مصنوعی: موتور قواعد قطعی + توضیح متنی
اعداد تمرین/تغذیه فقط از `engine/workout.py` + `engine/nutrition.py` (جدول‌های قطعی + Mifflin-St Jeor) می‌آیند؛ `llm_explanation` فقط متن قالبی/LLM است (G8). اسلات Ollama برای آینده با fallback قالبی — هیچ عددی از LLM خوانده نمی‌شود.

## D-008. (M16) الگوی درگاه پرداخت + قرارداد کیف‌پول
`GatewayAdapter` (Protocol) + `MockGateway` (قطعی برای dev/e2e) + `ZarinpalAdapter` (سند اجرا با sandbox). مبالغ کیف‌پول همیشه مثبت + `kind` تعیین‌کنندهٔ علامت. `wallet_pay` اتمیک (بررسی موجودی + debit + payment در یک commit) و double-spend رد می‌شود. توکن HMAC برای callback جلوی جعل مبلغ را می‌گیرد.

## D-009. (M17) جایگزینی PyJWT با python-jose
pip-audit سه آسیب بدون نسخهٔ رفع در python-jose/ecdsa گزارش کرد (مسیر ECDSA استفاده نمی‌شد اما وابستگی وجود داشت). با جایگزینی PyJWT (HS256 فقط، بدون ecdsa) اسکن به «No known vulnerabilities» رسید. ۱۴۱ تست بدون تغییر سبز ماند.

## D-010. (M18) مالکیت سطری در لایهٔ سرویس (نه فقط RBAC)
RBAC مسیر/متد را چک می‌کند؛ مالکیت (عضو فقط دادهٔ خودش) با `app/security/ownership.py` در سرویس‌ها اعمال می‌شود (user از روتر عبور می‌کند؛ فراخوانی داخلی با user=None). ورود پیکرسنجی فقط staff (سیاست POST ندارد برای member)؛ خواندن نتایج/سوابق/کیف پول برای عضو با مالکیت آزاد شد.

## D-011. (M20) معماری آپدیت تفاضلی
endpoint عمومی `GET /updates/manifest` (بدون auth — پیش از ورود) + `registry.json` (پچ‌ها با sha256/size). نسخه‌یابی semver-simplified در سه لایه یکسان (backend/ts/dart). وب: SW با SKIP_WAITING؛ موبایل: دانلود patch با تأیید هش + fallback به full. حالت `force` وقتی نسخه < min_supported.

## D-012. (consult-1) Jackson–Pollock: پروتکل ۷ نقطه انتخاب شد — ضرایب تا مرجع مستقل قفل
کاربر پروتکل ۷ نقطه‌ای (سینه/زیربغل/پشت‌بازو/زیرکتف/شکم/بالای‌لگن/ران) را انتخاب کرد. اما معادله/ویرایش/ضرایب اجرا نمی‌شوند تا مرجع مستقل (نه حافظهٔ LLM) + حقوق + تناسب جمعیتی بررسی و تصویب شود (E07). ذخیرهٔ خام mm/ارزیاب/تاریخ/کیفیت همچنان تنها رفتار فعال؛ مدل فعلی ۳ فیلد mm باید در زمان اجرا به ۷ محل تعمیم یابد.

## D-013. (consult-1) اجرای TODO بستهٔ fitness-handoff فعلاً متوقف
کاربر «فعلاً هیچ‌کدام» را انتخاب کرد: تا روشن‌شدن تصمیم‌های ۱۱ تا ۱۵ (مجوز/دامنهٔ جمعیتی/تغذیه و خروجی/محیط اجرا) هیچ موردی از لیست کارها به لوپ اضافه یا اجرا نمی‌شود. رفع فوری (MpColors.info و CORS) هم در همین توقف است تا اجازهٔ صریح.

## D-014. (consult-1) Face-ID: فقط اثبات و مستند — ادغام بعداً
اثبات زنده PASS (face_recognition/dlib — MIT/Boost، آفلاین) در `finn/reports/faceid-evidence/` ماندگار شد؛ ادغام محصول به تصمیم بعدی موکول شد.

## D-015. (consult-1) LICENSE اپ فعلاً ثبت نشود
کاربر «فعلاً بدون مجوز» را انتخاب کرد. وضعیت فعلی (بدون LICENSE = همهٔ حقوق محفوظ/مبهم) آگاهانه ادامه می‌یابد تا تصمیم نهایی؛ ورود هر OSS به محصول قبل از آن ممنوع است (E12/E08).

## D-016. (consult-2) دامنهٔ جمعیتی فاز اول: بزرگسال + سالمند سالم
فاز اول = بزرگسالان (۱۸+) و سالمندان سالم با پروتکل ایمنی ساده (بار کمتر، گرم‌کردن بیشتر، معیار توقف درد/تنفس، بدون تست بیشینهٔ اجباری). مسیرهای کودک/نوجوان، بارداری/پس از زایمان، معلولیت، بیماری و بازگشت از آسیب پشت **گیت صریح توقف تولید خودکار** می‌مانند (E05) — مرحله‌بندی است نه محدودیت دائمی. مرجع بازبین حرفه‌ای: طبق پاسخ، مربی/پژوهشگر (کاربر) تا معرفی مرجع دیگر.

## D-017. (consult-2) حدود تغذیه: درشت‌مغذی/کالری پایه + مشاورهٔ عمومی؛ بالینی فقط ارجاع
ردیابی/پیشنهاد ماکرو و کالری پایه + راهنمای عمومی غذا مجاز است. هر رژیم بالینی/بیماری/دارویی فقط **مسیر ارجاع به متخصص** با ثبت علائم — بدون تولید خودکار (هم‌سو با §۴ بسته).

## D-018. (consult-2) محیط اجرا: اندروید (گوشی/تبلت شاگرد و مربی) + سرور محلی
کلاینت Flutter هدف = اندروید؛ بک‌اند روی سرور محلی باشگاه؛ معماری آفلاین‌محور (M10/M20) اولویت دارد. مشخصات RAM/GPU هنوز اعلام نشده — برای اجرای محلی مدل/پردازش سنگین (مثل Face-ID) باید روی دستگاه سبک بماند (یافتهٔ OOM اثبات face-id همین را تأیید می‌کند).

## D-019. (consult-3) اجرا فعلاً متوقف — تا اطلاع بعدی
کاربر «هنوز صبر کن» را انتخاب کرد. هیچ موردی از TODO (حتی فوری‌ها) اجرا نمی‌شود تا پیام صریح «شروع کن». نقشهٔ اجرایی آماده است.

## D-020. (consult-3) فرمت خروجی گزارش محرمانه: HTML چاپی + JSON
خروجی اصلی = HTML راست‌چین چاپ‌پذیر + JSON ماشین‌خوان؛ PDF فارسی (WeasyPrint) در CI فقط در صورت نیاز. تکمیل‌کنندهٔ D-017.

## D-021. (loop-plan) تصویب نقشهٔ لوپ M22–M31 با ایجنت‌های ECC و مراحل کیفی S1–S9
کاربر همهٔ موارد صف + ۲۱ کمبود جدید را به لوپ اضافه کرد و خواستار طرح‌ریزی دقیق با مأموریت مرحله‌به‌مرحلهٔ ایجنت‌های ECC + مراحل کیفی از منابع تحقیق‌شده شد. منابع واقعاً بررسی شدند: ادغام (Vercel guidelines، DESIGN.md، Finn-loop، Hermes، scientific-skills الگویی، find-skills، Dokploy، Strix/Browser-use اختیاری)، مرجع (Skiper/Vengeance/21st.dev/vgpu/Casberry/Originkit/AgentMemory/OmniRoute/n8n)، رد (Animaster=پولی، DaisyUI=تعارض با shadcn)، نامعلوم (Soup). فرایند از Finn-loop (spec→build→review→merge) + Hermes (L0–L5 + بازرس) پیروی می‌کند. سطح استقلال فعلی: L2.



## D-022. (consult-3) LICENSE: مالکیتی (Proprietary) — جایگزین D-015
کاربر در تاریخ ۲۰۲۶-۱۱-۱۴ «مالکیتی (Proprietary)» را انتخاب کرد. D-015 (بدون مجوز) منسوخ است.
- `LICENSE` در ریشهٔ مخزن: حقوق محفوظ + اجازهٔ غیرانحصاری/غیرقابل‌انتقال به سازمان مشتری برای بهره‌برداری داخلی.
- `NOTICE-THIRD-PARTY.md`: فهرست اجزای OSS با مجوزها (E12).
- اثر بر model_lock (D-008): مانع مجوز توزیع رفع شد؛ مانع باقی‌مانده = تأمین وزن مدل از منبع معتبر + تأیید جمعیتی — تا آن زمان قفل پابرجاست.
- E12/E08: ورود هر OSS جدید قبل از بررسی مجوز به محصول ممنوع (همان قاعده، حالا با مرجع مجوز صریح).

## D-023. (consult-4) بازچینش صف ساخت — «ارزیابی اول»
کاربر در ۲۰۲۶-۱۱-۱۴ انتخاب را به عهدهٔ عامل گذاشت؛ انتخاب: «تأیید بازچینش + شروع از هارنس ارزیابی (G4)».
- استدلال: گرفتن «عدد پایه» از موتور فعلی، روایت کمّی قبل/بعد را برای دفاع ممکن می‌کند.
- ترتیب جدید: G4 ارزیابی ← G1 بازخورد ست‌به‌ست ← G2 نشانگرهای حجم ← G5/G3 تغذیه ← G6 روندنمای JP7 ← Q4/G7 صف آفلاین/سنک ← بقیه.
- درگاه پرداخت (gap-24) به انتهای صف منتقل شد (پروژهٔ پژوهشیِ بدون درآمد).
- وضعیت: G4 اجرا شد (finn/reports/eval/2026-11-14-EVAL-SUMMARY.md).

## D-024. (consult-5) دامنهٔ نهایی پایان‌نامه — حذف/نگه‌داشت/جایگزین
کاربر در ۲۰۲۶-۱۱-۱۴: «گزینه دو و چهار را حذف کن چون به‌جای نسخهٔ iOS، نسخهٔ وب کارمان را راه می‌اندازد».
- ❌ حذف: (۲) تماس ویدیویی؛ (۴) نسخهٔ iOS.
- ✅ نگه‌داشته شد: (۱) کتابخانهٔ ویدیو/تصویر حرکات (مسیر پایگاه‌های آزاد)؛ (۳) آنالیز سگمنتال با مسیر نرم‌افزاریِ بدون سخت‌افزار (اندازه‌گیری‌های محیطی/پوست‌چین چندنقطه‌ای — نه ادعای InBody).
- ➕ افزوده شد: **نسخهٔ وب** به‌عنوان جایگزین چندسکویی iOS (احتمالاً PWA روی همان API محلی).

## D-025. منبع رسمی ECC = `affaan-m/ECC` (فورک WorldFlowAI منسوخ شد)
نصب قبلی (Phase-0، ۲۰۲۶-۱۱-۱۴) از `WorldFlowAI/everything-claude-code@432485ba` بود: ۹ ایجنت، ۱۱ اسکیل،
آخرین کامیت ۲۰۲۶-۰۱-۲۳ — یعنی **۱۰ ماه عقب‌تر** از بالادستی که کاربر معرفی کرد.
- **منبع رسمی جدید:** `github.com/affaan-m/ECC` @ `d2ef2680` (v2.2.3) — ۷۱ ایجنت، ۳۱۴ اسکیل، ۹۸ فرمان، ۲۳ بستهٔ قوانین.
- `install-toolchain.sh` جای `install-ecc.sh` را گرفت (دومی برای سازگاری می‌ماند، اما منبعش قدیمی است).
- ایجنت‌های قرارداد FINN (۹ مورد) همه در نسخهٔ جدید هستند و محتوایشان **غنی‌تر** است (مثلاً `planner` از ۳۰ خط به ۲۲۱ خط، با Prompt Defense Baseline).
- **درس:** پین‌کردن کامیت برای بازتولیدپذیری درست است، اما پین‌کردن روی یک فورک ثالثِ رهاشده = قفل‌شدن روی نسخهٔ کهنه. منبع باید بالادست رسمی باشد.

## D-026. REA واقعی نصب شد — «بازبینی REA» قبلی نقش‌آفرینی متنی بود
`REA-REVIEW-2026-11-15.md` در زمانی نوشته شد که REA نصب نبود؛ عامل نقشش را بازی کرد و شاهدها
خروجی `pytest`/`ruff` خودمان بودند. نتیجه مفید بود (۵ باگ واقعی) اما فاقد شاهد ماشینیِ مستقل،
تحلیل باینری، و مقایسهٔ رفتاری با رقبا.
- اکنون REA v6.9.0 نصب است؛ شاهدها `evidence_id` + `digest` دارند و در `finn/reports/rea/` بایگانی می‌شوند.
- **قاعدهٔ جدید (G11):** هر ادعای «بازبینی/باگ‌یابی» در گزارش‌های آینده باید یا `evidence_id` REA داشته باشد یا صریحاً «بازبینی دستی (بدون REA)» برچسب بخورد. ادعای REA بدون ابزار ممنوع.
- REA فقط برای اهداف **خودمان** و **رقبای متن‌باز/عمومی** — دیکامپایل رقبای بسته ممنوع (D-022/E12/D-024 پابرجاست).

## D-027. موتور native نصب نمی‌شود
Ghidra/Hopper/IDA/Kuna/JADX نصب نمی‌شوند: (۱) سورس کامل محصول را داریم، (۲) تحلیل رقبای بسته ممنوع است،
(۳) ~۲GB+ حجم و وابستگی Java برای ارزش صفر در این پروژه. ابزارهای بدون provider
(Flutter build ID، APK signature، JS/Electron، SQLite، archive، HAR) کافی‌اند.

## D-028. تأیید پرداخت درگاهی فقط با پاسخ امضاشدهٔ درگاه
مسیر `POST /payments/{id}/verify` تنها برای نقدی/کارت‌خوان (پذیرش) است.
پرداخت `zarinpal` فقط با `gateway_authority` ثبت‌شده و پاسخ امضاشدهٔ
`/callback` تأیید می‌شود. دلیل: semgrep نشان داد تأیید دستی روی پرداخت
درگاهی، هر دارندهٔ توکن را قادر می‌کرد پول را «وصول‌شده» اعلام کند.
همچنین درگاه بی‌حالت شد (اعتبار از HMAC داخل authority، نه حافظهٔ
پروسه) چون با `--workers 4` تأیید پرداخت معتبر شکست می‌خورد.

## D-030 (M61) — «ثبت چهره» از اپ عضو حذف شد، نه اینکه تعمیر شود
انتخاب: به‌جای ساختن تشخیص چهرهٔ سمت کلاینت (embedding از دوربین)، دکمهٔ
«ثبت چهره» از `checkin_page.dart` **حذف** شد و یک جمله گفت که ثبت چهره در
باشگاه و توسط پذیرش انجام می‌شود.

چرا: `POST /face/enroll` ورودی‌اش `embedding_b64` است (خروجی مدل SFace)، نه
تصویر خام. ساخت این embedding نیازمند مدل روی دستگاه است که در این نسخه نیست.
با ماندن دکمه، سه انتخاب بد داشتیم: (۱) ۴۰۳ که رفع شد ولی بعد رضایت می‌خواست،
(۲) دکمه‌ای که همیشه پیام «انجام نمی‌شود» می‌دهد، (۳) ادعای «تشخیص چهره» که
صادق نبود. قاعدهٔ R3 می‌گوید هیچ‌کدام. حذف دکمه + توضیح صادقانه تنها گزینه‌ای
بود که کاربر را به مسیری که کار نمی‌کند نمی‌فرستد.

مسیر ثبت چهره برای کیوسک/پذیرش باز است و برای member هم اکنون **با رضایت**
کار می‌کند (اثبات زنده: ۴۰۳ → رضایت → ۲۰۰). یعنی API آماده است؛ فقط سطح اپ
عضو آن را ارائه نمی‌دهد.

## D-031 (M63) — n8n فقط اعلان CI read-only و backup خصوصیِ مشروط
مصوبهٔ کاربر در `docs/MuscleParadise/adr/005-n8n-boundary.md` ثبت شد.
- مجاز: اعلان حداقلی از metadata وضعیت GitHub Actions با دسترسی read-only؛ backup
  workflowهای خود n8n فقط اگر instance واقعاً راه‌اندازی شود، در مخزن خصوصی و پس از
  بازرسی/پاک‌سازی export و محدودسازی credential.
- ممنوع: منطق محصول، پرداخت، هویت/RBAC، داده/یادآوری عضو، deploy/release یا تغییر
  خودکار repo. فعلاً instance، credential و ادغام وجود ندارد.
- Sustainable Use License مجوز MIT/OSI نیست؛ استفادهٔ تجاری/self-host باید پیش از
  هر نصب جدا بررسی شود. هیچ package یا سرویس نصب/فعال نشد.

## D-032 (M63) — شروع صریح M63–M99
درخواست اخیر کاربر شروع اجرای نقشهٔ M63–M99 را صریحاً مجاز می‌کند و برای همین بازه
D-019 قدیمیِ «تا اطلاع بعدی متوقف» را supersede می‌کند. مرجع دامنه و وضعیت:
`docs/MuscleParadise/LOOP-PLAN-M63-M99.md`؛ اجرا روی شاخهٔ جاری می‌ماند، بدون push،
release، deploy، پرداخت واقعی یا تغییر DB تولید. BLOCKED/UNKNOWN فقط loop وابسته را
متوقف می‌کند؛ آثار موجود/untracked حفظ می‌شوند.

## D-033 (سیاست سراسری TODO، ۲۰۲۶-۱۱-۱۶) — ادامهٔ خودمختار، بدون نظارت روتین

درخواست صریح کاربر این سیاست را به **همهٔ micro-loopهای مشتق از TODO** تعمیم می‌دهد،
نه فقط M63–M99 یا مسیر برند. دامنهٔ مستنداتی که باید با این قاعده همسو باشند:
M00–M17 (`FINN_LOOP.md`)، M22–M31، M33–M40، M63–M99 و M100–M106.

- فقط صف/نقشهٔ مرجع جاری تعیین می‌کند کدام loop فعال است؛ ذکر یا ویرایش نقشهٔ
  تاریخی/آرشیوی به‌تنهایی آن را دوباره `READY` یا مجاز به اجرا نمی‌کند.
- هر loop فعال با وضعیت `READY` بدون مکث برای نظارت یا تأیید روتین پیش می‌رود.
  تصمیم فنی/طراحیِ محدود، برگشت‌پذیر و درون‌دامنه‌ای با پیش‌فرض امن گرفته و
  دلیل، شاهد و اثر بازگشت در همین دفتر و گزارش loop ثبت می‌شود؛ سؤال روتین
  از کاربر یا `WAITING_FOR_REVIEW` برای گرفتن نظر او گیت اجرا نیست.
- پیش‌نیاز واقعیِ بیرونی، حقوقی، امنیتی/ایمنی، مالکیت/credential، دستگاه، مجوز
  یا تصمیم تجاری/حقوقیِ غیرقابل‌حدس را جعل یا حدس نمی‌زنیم. فقط loop وابسته
  `BLOCKED`/`UNKNOWN` می‌شود؛ loopهای مستقل ادامه می‌یابند و از کاربر سؤال نمی‌شود.
- هیچ گیت، معیار، تست یا شاهدی حذف/تضعیف نمی‌شود و `PASS` فقط با مدرک ثبت
  می‌شود. این سیاست مجوز push، release، deploy/rollback، پرداخت واقعی، تغییر
  DB تولید، استفاده از credential/دادهٔ واقعی یا عملیات مخرب روی تاریخچه/فایل‌های
  موجود نیست. تصمیم‌های توقف اختصاصی مانند D-013 و گیت‌های صریح ایمنی/حقوقی
  همچنان پابرجا هستند.
- D-019 در حد توقف کلیِ TODO و L2/تأیید روتینِ ذکرشده در D-021 و نقشه‌های قدیمی، فقط برای loopهای صریحاً فعال و `READY` با این سیاست supersede می‌شوند؛ D-013 و توقف‌ها/محدودیت‌های اختصاصی هر تصمیم یا محصول تغییر نمی‌کنند.

## D-034 (M72) — نمایش تاریخچهٔ واقعی اشتراک و رفتار امن در مرز انقضا

- **انتخاب:** بنر خانه از `GET /members/{member_id}/memberships` و فیلد واقعی `expires_at` بخواند؛ `days_remaining` سمت کلاینت با گردکردن رو به بالا محاسبه شود چون قرارداد API آن را ندارد. انقضا مرز انحصاری است: در `expires_at` یا بعد از آن، active نیست. تاریخ بدون offset مطابق رفتار backend/SQLite به UTC تعبیر می‌شود. تاریخ/وضعیت ناقص یا نامعتبر `unknown` است، نه «بدون اشتراک» یا صفر. اگر چند رکورد active معتبر برگشت، معتبرترین تا دورترین تاریخ آینده نشان داده می‌شود.
- **دلیل:** endpoint موجود member-scoped است و `MembershipOut` تاریخ/status را دارد؛ بنر قبلی تاریخ پایان نداشت و fixture قبلی `days_remaining` خارج از قرارداد API داشت. رفتار مرز با مقایسهٔ backend (`expires > now`) همسو است.
- **اثر بازگشت:** فقط helper، provider UI و تست‌های Client؛ dependency، schema، endpoint و DB تغییر نکردند. می‌توان همان hunks را بازگرداند.
- **وضعیت شاهد:** static Dart gate پاک، اما Flutter/Dart test/analyze اجرا نشده‌اند؛ M72 در نقشه `UNKNOWN` می‌ماند. جزئیات: `finn/reports/m72-membership-display.md`.

## D-035 (M73) — ثبت غذای عضو با حداقل مجوز و نمایش صادقانهٔ منبع

- **انتخاب:** از سه API و کاتالوگ موجود استفاده شود؛ ثبت وزن بر حسب گرم و وعده به زبان فارسی باشد. به role `member` فقط POST دقیق `/nutrition/food-logs` افزوده شود؛ `ensure_member_scope` در service مرز مالکیت است و باید بماند. هیچ wildcard نوشتن nutrition اضافه نشود. مقدار چربی از dataset مستقیم نیست/تخمینی است، پس در دفتر Client نمایش داده نشود و محدودیت منبع اعلام شود.
- **دلیل:** تست پیش از تغییر policy، self-log واقعی عضو را 403 بازتولید کرد؛ endpoint فعلی service-level ownership دارد. منبع `soooolag/food-finder` با MIT در فایل موجود ثبت شده و ۳ غذای ایرانیِ category `غذای ایرانی` دارد. API values per 100g است؛ انتخاب portion توسط عضو لازم است.
- **اثر بازگشت:** یک policy دقیق + provider/UI و تست؛ endpoint/schema/DB/dependency/catalog تغییر نکردند. حذف همان hunks این گپ مجوزی را برمی‌گرداند.
- **وضعیت شاهد:** 25 تست backend/data و ruff/py_compile سبز؛ 44 فایل Dart در static gate بدون یافته، اما Flutter widget test/analyze/build اجرا نشدند؛ M73 `UNKNOWN`. گزارش: `finn/reports/m73-food-logging.md`.

## D-036 (M74) — رزرو کلاس member-scoped؛ نمایش وضعیت خود عضو

- **انتخاب:** `GET /classes` برای role member فقط status رزرو خود همان member را همراه هر class بدهد؛ service برای `book` و `cancel` `ensure_member_scope` اجرا کند. UI فقط در وضعیت `confirmed`/`waitlisted` دکمهٔ لغو نشان می‌دهد و پس از هر پاسخ API فهرست را تازه می‌کند.
- **دلیل:** پیش از fix، تست دو عضو مصنوعی نشان داد عضو دیگر می‌توانست reservation را cancel کند و نیز می‌توانست به نام قربانی رزرو بسازد؛ هر دو 200. این دو endpoint از همان `member_id` caller-controlled استفاده می‌کردند، پس بستن هر دو حداقل اصلاح امن است. staff با `user=None`/نقش غیرعضو behavior قبلی را حفظ می‌کنند.
- **اثر بازگشت:** route/service/UI/test hunks؛ migration/schema/dependency جدیدی ندارد. Rollback، گیت مالکیت را حذف می‌کند و باید آگاهانه باشد.
- **وضعیت شاهد:** 46 backend/RBAC integration tests، py_compile و ruff سبز؛ static Dart gate 45/0، اما Client widget test/analyze/build اجرا نشده؛ M74 `UNKNOWN`. گزارش: `finn/reports/m74-class-cancel.md`.

## D-037 (M75) — inbox اعلان فقط از API عضو و read مالک‌محور

- **انتخاب:** از `GET /notifications/member/{member_id}` و `POST /notifications/{notification_id}/read` موجود استفاده شود؛ `ensure_member_scope` در service برای فهرست و mutation لازم است. Client فقط member_id نشست را به GET می‌دهد، unread را از `read_at` محاسبه می‌کند، پس از mark دوباره fetch می‌کند و inbox را از خانه قابل‌دسترسی می‌سازد.
- **دلیل:** دو تست pre-fix نشان داد member دیگر توانست فهرست عضو را ببیند و notification او را read کند؛ هر دو 200 بودند. قرارداد API کافی است و نیاز به scheduler، push/local notification، مدل، migration یا dependency تازه نیست.
- **اثر بازگشت:** service/router ownership guard، provider، صفحه/route، دکمهٔ خانه و تست‌ها. هیچ DB/schema یا endpoint تازه اضافه نشده؛ rollback همان هانک‌ها دسترسی متقاطع را دوباره باز می‌کند.
- **وضعیت شاهد:** 65 تست backend notification/reminder/chat/RBAC، py_compile و ruff سبز؛ static Dart gate 47 فایل/0 یافته؛ Flutter widget test/analyze/build به‌دلیل نبود SDK اجرا نشد؛ M75 `UNKNOWN`. گزارش: `finn/reports/m75-notifications.md`.

## D-038 (M76) — نمایش readiness به‌عنوان برآورد مبتنی بر بازخورد، نه واقعیت بالینی

- **انتخاب:** endpoint موجود `/programs/member/{member_id}/readiness` مصرف شود؛ owner از نشست تعیین و ساختار report/signals اعتبارسنجی شود. اگر `readiness` null باشد، فقط reason واقعی API نمایش یابد. امتیاز، band، recommendation، signals/missing و شمارش واقعی بازخوردها نشان داده می‌شوند و متن صریح می‌گوید این برآورد تمرینی است، نه تشخیص پزشکی. پس از ثبت feedback، provider invalidate شود.
- **دلیل:** backend و Studio از قبل گزارش قابل توضیح با score، reason و data_counts دارند؛ endpoint ownership gate و تست‌های readiness دارد. جبران نبودن داده با عدد mock یا توصیهٔ بالینی مجاز نیست.
- **اثر بازگشت:** provider، Today card/page، invalidation feedback و Client widget tests؛ backend/API/schema/DB/dependency تغییر نکرد.
- **وضعیت شاهد:** readiness unit/integration 22 passed و 7 deselected با فیلتر، static Dart 49/0؛ Flutter widget/analyze/build اجرا نشده، پس M76 `UNKNOWN`. گزارش: `finn/reports/m76-readiness.md`.

## D-039 (M77) — نمایش volume از منبع و level واقعی API

- **انتخاب:** API موجود و member-scoped را با level انتخابی مصرف کن؛ chart/bar و اعداد planned و reported جدا بمانند. `effective_sets` با `source_of_number`, `data_state`, hard/soft/unknown RIR، جدول landmarks و suggestion/reason از پاسخ واقعی نمایش داده شوند. پاسخ بدون برنامه empty است؛ پاسخ خراب/network error عدد صفر نمی‌شود.
- **دلیل:** endpoint از قبل `weekly_volume_report`، مالکیت و تست planned-vs-feedback دارد. `Israetel/RP` source و bands، حد راهنمای مربی‌گری است، نه آزمون/تشخیص پزشکی؛ نباید planned را به‌عنوان completed جا زد.
- **اثر بازگشت:** Client provider/card/Today/test؛ API/DB/schema/dependency دست‌نخورده.
- **وضعیت شاهد:** volume integration/unit 13 passed، static Dart 51/0؛ Flutter widget/analyze/build اجرا نشده؛ M77 `UNKNOWN`. گزارش: `finn/reports/m77-weekly-volume.md`.

## D-040 (M78) — TDEE تطبیقی و self weigh-in از endpoint موجود

- **انتخاب:** از GET adaptive و POST weight-logs موجود استفاده شود. عضو باید بتواند وزن خودش را وارد کند، پس policy فقط روی `POST /nutrition/weight-logs` باز می‌شود؛ `ensure_member_scope` در service، cross-member را رد می‌کند. Target/TDEE/delta سمت Client محاسبه نمی‌شوند؛ اگر API داده ناکافی بدهد، UI `null` و action none را صادقانه نشان می‌دهد.
- **دلیل:** pre-fix test نشان داد self weigh-in با 403 بسته بود، در حالی که موتور adaptation برای TDEE هم به وزن و هم روزهای غذای ثبت‌شده نیاز دارد. هیچ wildcard یا write برنامه/کاتالوگ مجاز نشد.
- **اثر بازگشت:** policy دقیق، testها، provider/card و NutritionPage؛ schema/service/DB/dependency تغییر نکرد. rollback policy self log را می‌بندد، service owner check مستقل باقی می‌ماند.
- **وضعیت شاهد:** 74 تست adaptive/RBAC/unit سبز، py_compile/ruff سبز، static Dart 53/0؛ Flutter widget/analyze/build اجرا نشده، پس M78 `UNKNOWN`. گزارش: `finn/reports/m78-adaptive-nutrition-client.md`.

## D-041 (M79) — reuse مسیر/دادهٔ JP7؛ فقط نمودار عضو گپ داشت

- **انتخاب:** M5 و D4/M62 به route `/bodycomp`، `jp7TrendProvider` و `GET /assessments/jp7/member/{id}/trend` می‌رسند؛ endpoint/provider/page موازی ساخته نشود. تفاوت acceptance: M62 دادهٔ واقعی، حالت ناکافی، تفسیر و history را آورد، اما نمودار خطی member در BodyCompPage نبود. M79 همان نمودار را فقط از `measurements[].sum_mm` و تاریخ‌های سرور، روی همان صفحه، اضافه می‌کند؛ زیر دو نقطه نمودار نمی‌سازد. `Assessment14Page` مستقل است: AppShell tab «توانایی‌ها» و API `/axis-assessments/*`; ۱۴محور با محورهای خام JP7 یکی نیست.
- **دلیل:** crosswalk سورس/route/provider/testها را با TODO مقایسه کرد. grep قدیمی پیش از M62 دیگر شاهد «API مصرف نمی‌شود» نیست، اما نبود chart از مقایسهٔ خود UI با acceptance عضو M5 مشخص شد.
- **اثر بازگشت:** chart و regression widget assertions در Client؛ هیچ API, route, provider یا dependency جدیدی نیست. `_dateFa` رقم/جداکننده را نیز امن تبدیل می‌کند تا تاریخ‌های واقعیِ نمودار/history نمایش‌پذیر باشند.
- **وضعیت شاهد:** Dart static gate 53 فایل/0 یافته؛ `bodycomp_real_data_test.dart` و `assessment14_page_test.dart` به‌دلیل نبود Flutter executable اجرا نشدند؛ M79 `UNKNOWN` برای runtime. گزارش: `finn/reports/m79-jp7-crosswalk.md`.

## D-042 (M80) — تاریخچهٔ حضور از هویت نشست جاری

- **انتخاب:** `GET /members/me/checkins` شناسهٔ عضو را از `user.id` نشست پیدا می‌کند و هیچ ID ورودی را برای انتخاب داده مصرف نمی‌کند؛ وجود `member_id` در query همین مسیر صریحاً 403 می‌گیرد. مسیر IDدار پروفایل عضو دیگر هم برای role=member با 403 بسته است. فقط role=member مجاز است؛ رکوردها با `member_id` همان profile، تازه‌ترین اول و با pagination برمی‌گردند. تلاش‌های denied هم در تاریخچهٔ خود فرد می‌مانند. مسیر staff `/admin/checkins` تغییر نمی‌کند و member=403 می‌ماند.
- **دلیل:** endpoint اداری دادهٔ چند عضو و نام‌شان را برمی‌گرداند و برای اپ عضو مناسب نیست؛ مسیر self-scoped از نشت ناشی از شناسهٔ دست‌کاری‌شده جلوگیری می‌کند و paging حد upper-bound دارد.
- **اثر بازگشت:** endpoint/service/tests، RBAC regression assertion، artifact مسیرهای API `api/routes.json` و تب «سوابق» با loading/empty/error/retry/older در صفحهٔ checkin Client. DB/schema/dependency و admin feed تغییر نکردند.
- **وضعیت شاهد:** کل backend: 811 passed, 1 skipped؛ Ruff check/format و py_compile سبز؛ Dart static gate 55 فایل/0 یافته. Flutter widget/analyze/build به‌دلیل نبود SDK و مسدودی شبکه اجرا نشده، پس M80 `UNKNOWN`. گزارش‌ها: `finn/reports/m80-member-checkin-history.md` و `finn/reports/flutter-sdk-provisioning.md`.

## D-043 (M81) — چت عضو از نشست و گفتگوی موجود

- **انتخاب:** فهرست `GET /chat/conversations` بدون `member_id` خوانده شود؛ پاسخ در Client باید با `memberId` نشست تطبیق کند. پیام‌ها و mark-read فقط روی شناسهٔ گفتگوی انتخاب‌شدهٔ همان فهرست انجام شوند و مالکیت server-side همچنان مرجع نهایی بماند. پیام ارسالی فقط پس از موفقیت پاک شود؛ شکست draft را حفظ کند.
- **دلیل:** member coach assignment ندارد و هیچ مسیر موجودی برای resolve مربی واقعی در Client نیست. در `chat_service.open_conversation`، نبود `coach_id` به `user.id` caller fallback می‌شود؛ برای member ساخت thread بی‌طرف مقابل ممکن است. پس empty state مربی را به شروع گفتگو از Studio دعوت می‌کند و Client `POST /chat/conversations` را صدا نمی‌زند.
- **اثر بازگشت:** صفحه/provider/testهای Client و route/home entry؛ API، backend و dependency تغییر نکردند. برای افزودن start flow ابتدا قرارداد معتبرِ تعیین مربی لازم است.
- **وضعیت شاهد:** backend contract regression 13 passed؛ Dart static 58/0؛ API coverage 4 passed، Studio suite 217 passed/9 skipped و build موفق. Flutter widget/analyze/full Client/APK gates اجرا نشدند؛ M81 `UNKNOWN`. گزارش: `finn/reports/m81-member-chat.md`.

## D-044 (M81، کشف رگرسیون M71) — پوشش API باید زنجیرهٔ Riverpod را بشناسد

- **انتخاب:** tokenizer دارت در `studio/tests/apiCoverage.test.ts` callهای واقعی `ref.read/watch(apiClientProvider).get/post/...` را بشناسد؛ probe رگرسیون اضافه شد. exceptionهای classes/cancel و notification list/read که اکنون مصرف واقعی دارند به evidence واقعی ارتقا یافتند.
- **دلیل:** اجرای gate روی سورس جاری ابتدا `/api/v1/classes/book` را uncovered گزارش کرد، هرچند Client آن را از provider فراخوانی می‌کند؛ alias-only tokenizer منفی کاذب می‌ساخت. اضافه‌کردن TODO یا پذیرش بی‌شاهد، قاعدهٔ M71 را دور می‌زد.
- **اثر بازگشت:** فقط test gate و evidence استثناها؛ feature code کلاس/اعلان/Studio تغییر نکرد. این اصلاح M81 در M71 را به‌صورت targeted regression محافظت می‌کند.
- **وضعیت شاهد:** gate targeted 4 passed؛ کل Studio 217 passed/9 skipped؛ `npm run build` موفق. گزارش اصلاح و زمینه: `finn/reports/m81-member-chat.md`.

## D-045 (M82؛ 2026-11-16) — تغییر شماره با دو OTP ترتیبی و ابطال کامل نسخهٔ نشست

- **انتخاب:** نشست معتبر حساب، شمارهٔ جدید را درخواست می‌کند؛ کد اول فقط به شمارهٔ فعلی فرستاده می‌شود. پس از اثبات شمارهٔ فعلی، کد مستقل به شمارهٔ جدید ارسال می‌شود؛ فقط پس از اثبات هر دو، شمارهٔ یکتای `User.phone` تغییر می‌کند. هر challenge تصادفی به یک user و زوج شماره bind است، کدها فقط salted-hash دارند، TTL/تعداد تلاش دارند و challenge تکمیل‌شده/منقضی/لغوشده قابل استفادهٔ مجدد نیست.
- **ابطال نشست‌ها:** هنگام تغییر، همهٔ refreshها revoke و `users.auth_version` اتمیک یک واحد زیاد می‌شود. JWTهای جدید claim نسخه دارند؛ auth dependency نسخه را بررسی می‌کند تا access JWTهای قدیمیِ session-bound و legacy بدون `sid` هم با تغییر شماره رد شوند. ورود با شمارهٔ جدید همان user را می‌گیرد.
- **خطای OTP:** کد نادرست `400 invalid_otp` است، نه `401`; Studio/Client برای 401 نشست را refresh و درخواست را retry می‌کنند و این می‌توانست یک OTP اشتباه را دوبار بشمارد. 401 فقط برای احراز هویت/نشست باقی می‌ماند.
- **بازیابی بدون شمارهٔ قدیم:** عمداً هیچ bypass خودکار یا پشتیبانی مبتنی بر اطلاعات حدسی ساخته نشد. اگر فرد به شمارهٔ قدیم دسترسی ندارد، بازیابی انسانی با سیاست احراز هویت مصوبِ مالک لازم است؛ scope این M82 آن مسیر بیرونی را جعل نمی‌کند.
- **migration:** `users.phone` از قبل unique بود؛ migration فقط `auth_version` و جدول challenge را می‌افزاید، نه قید تکراری. برگشت: downgrade migration و بازگرداندن UI/service/dependency hunks؛ این کار قابلیت را حذف می‌کند و نباید روی production اجرا شود.
- **وضعیت شاهد:** backend full **810 passed / 2 skipped**، شامل تست race که رقیب را پس از preflight و پیش از UPDATE وارد می‌کند؛ Ruff check/format سبز. migration scratch `upgrade head` + `alembic check` بدون drift، head `d9e0f1a2b3c4` و route artifact **118** مسیر است. Studio full **219 passed / 9 skipped** + `npm run build` موفق؛ Dart static **60 files / 0 findings**. Flutter/Dart/Java/Android SDK در sandbox موجود نیست؛ widget/analyze/pub-get/APK اجرا نشده‌اند، پس M82 `UNKNOWN` برای Client runtime. هیچ SMS واقعی، production DB، push یا commit استفاده نشد. گزارش: `finn/reports/m82-phone-change.md`.

## D-046 (2026-11-16) — مجوز محدود برای commit و push این checkpoint

کاربر صریحاً اجرای پیشنهاد بازبینی، stage انتخابی، commit و push را خواست. این تصمیم فقط اختیار no-push عمومی D-033 را برای یک commit/push بازبینی‌شده به شاخهٔ جاری `arena/4f336f66-mp` مستثنا می‌کند؛ push به branch دیگر، tag/release، deploy/rollback، پرداخت واقعی یا تغییر DB تولید مجاز نیست. فایل‌های signing/private، APKهای buildشده و شواهد face-ID محلی در Git قرار نمی‌گیرند؛ آثار محلی حفظ می‌شوند.

## D-047 (2026-11-17) — ادامهٔ loopهای آماده و push بستهٔ نهاییِ Codespaces

کاربر دستور داد loopهای ساخت ادامه یابند، پیش‌نیازهای GitHub Codespaces آماده شوند و بستهٔ نهایی به همان شاخهٔ فعال `arena/4f336f66-mp` push شود. این مجوز، no-push عمومی D-033 را فقط برای commit/push انتخابیِ بستهٔ نهایی و اصلاح‌های لازم همان کار مستثنا می‌کند؛ شاخهٔ دیگری ساخته/استفاده نمی‌شود. این دستور مجوز release/deploy، تغییر DB تولید، پرداخت/SMS واقعی، استفاده از credential/دادهٔ واقعی یا انتشار کلید signing/APK/شواهد خصوصی نیست. `evidence/` و `finn/` untracked فعلی حفظ و فقط فایل‌های لازم پس از بازبینی انتخاب می‌شوند. Codespaces config/handoff آماده می‌شود؛ ایجاد ماشین ابری واقعی جدا از push است و تا روشن‌شدن نیاز/هزینه اجرا نمی‌شود.

## D-048 (M97؛ 2026-11-18) — صفرکردن drift با parity تست‌شده و restore بدون لمس فایل زنده

- **انتخاب:** به‌جای «اعتماد به `alembic check`»، drift روی هر دو provisioning path سنجیده می‌شود: یک تست، schema ساخته‌شده با `Base.metadata.create_all` را با schema مهاجرت‌کرده مقایسه می‌کند. نتیجهٔ اجرا: ۵۲ جدول، صفر اختلاف → **هیچ migration اصلاحی لازم نشد** و هیچ schema محصولی تغییر نکرد (معیار M97 «اصلاح schema فقط با baseline و migration آزموده» را باز می‌کند: اگر diff می‌بود، اول baseline و migration، نه ALTER دستی).
- **تاریخچه:** گیت «یک head + گراف کامل» افزوده شد (۲۶ revision، head `f9b0c1d2e3f4` که خودش merge point است). دلیل ماندن: تاریخچهٔ همین پروژه یک‌بار دو سر شده است و `upgrade head` با دو head در استقرار می‌شکند.
- **ابزار عملیاتی:** `restore` فایل‌های الحاقی را در مسیر اصلی می‌نوشت → حالت `verify` (فقط خواندن) و `--extras-to DIR` افزوده شد؛ رفتار پیش‌فرض بدون flag عمداً عوض نشد تا دستورهای مستندشده و restore تولیدی نشکنند، و تست M30 به scratch منتقل شد.
- **راستی‌آزمایی:** حساسیت دو گیت جدید با تزریق خرابی (ایندکس/ستون جعلی، revision موازی/parent گم‌شده) ثابت شد؛ سبزها «score review» دستی نیستند.
- **اثر بازگشت:** حذف دو قابلیت CLI و فایل تست جدید، رفتار قبلی را برمی‌گرداند؛ هیچ داده/جدولی درگیر نیست. گزارش: `finn/reports/m97-migration-drift.md`.

## D-049 (M90؛ 2026-11-18) — رسید عضو از endpoint موجود، با نگهبان مالکیت در کلاینت و بدون dependency چاپ

- **انتخاب:** به‌جای ساخت «رسید PDF» یا مسیر تازهٔ backend، کلاینت همان `GET /shop/orders/{id}/receipt` را می‌خواند که از M60/R5 وجود داشت و Studio مصرفش می‌کرد. هیچ مبلغی از کلاینت نمی‌رود (فقط GET) و جمع‌ها از همان پاسخ خوانده می‌شود.
- **نگهبان کلاینت (fail closed):** اگر `order_id` پاسخ با سفارش درخواستی یا `member_id` با عضو نشست نخواند، رسید نمایش داده نمی‌شود و خطای روشن می‌آید — حتی اگر سرور اشتباه کند. اگر `items_total_rial` با `total_rial` نخواند، عدد تصحیح نمی‌شود؛ هر دو نمایش داده می‌شوند با یک یادداشت.
- **چرا `target: 0` و `SelectionArea` نه پرینت/PDF:** افزودن `printing`/`pdf` dependency فقط برای «چاپ» بدون نیاز اثبات‌شده، هم APK را سنگین می‌کند هم سطح حمله؛ acceptance «رسید از endpoint مالک‌محور» بود.
- **اثر بازگشت:** حذف سه فایل جدید + provider و برگرداندن `shop_page.dart`؛ هیچ داده/schema/API تغییر نکرده.
- **وضعیت شاهد:** Dart static gate ۶۸ فایل/۰ یافته؛ `apiCoverage` 4 passed و Studio 219 passed/9 skipped؛ `flutter analyze`/`flutter test` در sandbox ممکن نبود (SDK نیست)، پس `UNKNOWN` تا CI.

## D-050 (M98؛ 2026-11-18) — لایهٔ `MpHaptics`/`MpMotion` به‌جای فراخوانی مستقیم در ویجت‌ها

- **انتخاب:** رابط تزریق‌پذیر (`hapticsProvider`) + helper کاهش حرکت روی `MediaQuery.disableAnimations`؛ تست با `setMockMethodCallHandler(SystemChannels.platform, …)` می‌سنجد پالس واقعاً به messenger می‌رود و `enabled: false` صفر فراخوانی است. دلیل: رفتار نام کانال با نسخهٔ SDK عوض می‌شود (`VibrationEffect` در برابر `HapticFeedback.vibrate`) و تست وابسته به آن شکننده می‌شد.
- **قاعدهٔ معنا:** موفق = `success`، صف آفلاین و خطا = `warning`، تغییر اسلایدر = `select`؛ پالس پس از `await` سرویس می‌آید تا «ثبت شد» لمسی زودتر از نتیجهٔ سرور نباشد. خطای پلتفرم بلعهیده می‌شود: لرزش نباید عملیات را بشکند.
- **کاهش حرکت = skip، نه حذف:** `MpMotion.dur → Duration.zero` و `animate(target: 0)`؛ بقیهٔ صفحات عمداً دست‌نخورده‌اند تا ادعای polish فراگیر نشود.
- **shared-element/Hero ساخته نشد:** ارزش اثبات‌شده نداشت و ریسک می‌کرد؛ معیار loop «فقط در صورت سود» بود.
- **اثر بازگشت:** حذف دو فایل core و دو فایل تست، برگرداندن چهار فایل UI/دو فایل تست؛ بدون API/schema/dependency.
- **وضعیت شاهد:** Dart static gate ۷۲ فایل/۰ یافته؛ Studio 219/9 بدون رگرسیون؛ هیچ پالسی روی دستگاه واقعی حس نشده و Flutter test/analyze محلی اجرا نشده → `UNKNOWN` تا CI.

## D-051 (M98؛ 2026-11-18) — بازخورد لمسی fire-and-forget است: رابط `void`، نه `Future<void>`

- **انتخاب:** `MpHaptics.select/success/warning` سه متد **`void`**‌اند. `SystemMpHaptics` خودش با `unawaited(pulse().catchError(…))` شلیک می‌کند؛ هیچ call-site ای پالس را `await` نمی‌کند و پالس بعد از `mounted` check می‌آید.
- **چرا (شاهد CI، نه سلیقه):** run `44293699567` در `set_feedback_sheet_test.dart:100` متن «اعمال شد» را گم کرد — `await haptics.success()` بین نتیجهٔ سرویس و `setState` نشسته بود و در محیطی که کانال پلتفرم پاسخ نمی‌دهد آن future resolve نمی‌شد. یعنی یک «polish» می‌توانست نمایش نتیجهٔ درست را بلوکه کند.
- **قاعدهٔ کلی که از این می‌ماند:** هر چیز اختیاری (haptics، sound، analytics، toast) باید بعد از state-update و بدون await مسیر باشد؛ «اول پیام، بعد لرزش» هم از نظر UX و هم از نظر invariants.
- **همراه با تست همان کانال:** چون API دیگر awaitable نیست، `motion_haptics_test.dart` بعد از پالس‌ها صف رویداد را با `tester.runAsync(() => Future.delayed(Duration.zero))` + یک `pump()` تخلیه می‌کند (نه `pumpEventQueue()` — آن زیر FakeAsyncِ `testWidgets` برنمی‌گردد و دو تست را ۱۰ دقیقه نخ می‌کرد، شاهد run `44295081645`) و `debugDefaultTargetPlatformOverride = TargetPlatform.android` را pin می‌کند — روی لینوکس CI `HapticFeedback` no-op است و بدون آن، هم red و هم green هر دو توخالی می‌شدند.
- **اثر بازگشت:** اگر روزی await لازم شد (مثلاً ترتیب دقیق پالس/حس‌گر)، باید با `Timeout` و بعد از `setState` باشد؛ برگرداندن رابط به `Future<void>` به‌تنهایی همان باگ را برمی‌گرداند.

## D-052 (M107؛ 2026-11-18) — گیت‌های خارج از sandbox به runbook مرحله‌ای split شدند

- **انتخاب:** به‌جای اینکه agent «تقریب» بزند یا وضعیت loopها را با استدلال عوض کند، یک دستور کار اجرا‌شدنی نوشته شد: `docs/MuscleParadise/runbooks/codespaces-execution.md` (مرحله ۰ تا ۸) + `.devcontainer/provision-android-sdk.sh` (اختیاری). کاربر اجرا می‌کند، لاگ می‌فرستد، و **بعد از دیدن لاگ** وضعیت عوض می‌شود.
- **تقسیم واقعی کار:** Codespace سه گیتِ Flutter/Android-compile/pip-audit را حل می‌کند؛ قدم‌های «دستگاه» (M104 startup، M105/M106 mask، حس haptics، outbox روی restart، QR فیزیکی) **در مرورگر شدنی نیستند** — Codespaces USB و KVM ندارد؛ پس آن‌ها روی لپ‌تاپ با `adb` برنامه‌ریزی شدند، نه در container.
- **قاعدهٔ provisioning:** نصب Android SDK بیرون از build تصویر می‌ماند، چون `sdkmanager --licenses` یعنی پذیرفتن یک توافق حقوقی از طرف هر سازندهٔ container؛ اسکریپت با `ACCEPT_ANDROID_LICENSES=1` صریح باز می‌شود و بدون `SDK_SHA256` (یا `SDK_ALLOW_UNPINNED=1`) **خروج می‌کند** — ساختن hash حدسی بدتر از نبودش است.
- **مرز SEC-01:** `apk.yml` trigger نشد؛ همان workflow با keystore موجود در مخزن امضا می‌کند. در runbook هم این هشدار جلوی دستور آمده: خروجی‌اش «شاهد کامپایل» است نه artifact نصب/توزیع.
- **اثر بازگشت:** سند اختیاری است؛ حذفش هیچ گیت موجودی را نمی‌شکند. تنها تغییر کدِ این loop، cwd-independence در `test_monitoring.py` است.

## D-053 (M108؛ 2026-11-18) — «در sandbox نمی‌شود» ≠ «باید دستی انجام شود»: گیت را به CI ببر

- **انتخاب:** به‌جای واگذاشتن شاهد به کاربر/Codespace، جاب `client-pinned` اضافه شد که همان گیت‌ها را روی **همان SDK پین‌شدهٔ devcontainer** اجرا می‌کند و عددها را در `::notice` می‌گذارد تا از API خوانده شوند. `flutter build apk --debug` عمداً بدون keystore است؛ `apk.yml` (که با keystore مخزن امضا می‌کند) trigger نشد.
- **چرا نه «دسترسی به Codespace کاربر»:** توکن این نشست `X-OAuth-Scopes` خالی دارد (App token)؛ `gh codespace ssh` لازم است، ولی نه permit می‌دهد نه token کاربر در گفتگو درخواست/ذخیره می‌شود. پس «انجام دادنِ من» فقط با تغییر معماری گیت ممکن بود، نه با گرفتن دسترسی.
- **قاعدهٔ چیدن گیت‌ها (از شکست خودم):** یک گیت تازه **هرگز** نباید قبل از گیت‌هایی که برایش شاهد می‌سازد قرار بگیرد — در `bash -e` CI، یک failure در میانه، بقیه را skip می‌کند و خروجی‌اش «سبزیِ بدون شاهد» است. گیتِ نو یا آخر چیده می‌شود یا (اگر بدهیِ کهنه دارد) غیربلاکینگ با شمارشِ ثبت‌شده، تا when پرداخت شد کشنده شود.
- **صداقتِ ادعا:** `pip-audit` را «هرگز اجرا‌نشده» نوشته بودم؛ اشتباه بود (در job `backend` بلاکینگ و سبز). سند اصلاح شد + لینک به همین گزارش. عدد 151MB برای **debug universal APK** است و «سایز اپ» گزارش نمی‌شود.

## D-054 (M109؛ 2026-11-19) — «کار انسانی» را دوباره طبقاتی کن: دسترسی ≠ ابزار، و ابزار ≠ اجازهٔ commit

- **انتخاب:** یک commitِ مکانیکیِ پرخطا (فرمت ۶۶ فایل) را CI تولید کرد و **از راه PR** وارد شد، نه با commit رباتی روی شاخه. `git add -u -- '*.dart'` و مقایسهٔ blobهای staged جزو تعریفِ کار است، نه جزئیات اجرا.
- **چرا دوباره پرسیدم:** جواب قبلی‌ام («به Codespace تو دسترسی ندارم») درست بود ولی **کافی نبود** — لایه‌های مجزا بودند: (۱) ساختن codespace: مجاز، (۲) ورود SSH: غیرمجاز (نمی‌توان کلید مجاز کرد) و مسدودِ شبکه، (۳) dispatch/PR/merge: مجاز. کاری که در لایهٔ ۱ و ۲ «نشدنی» بود، در لایهٔ ۳ شدنی بود. هر بار که «نمی‌شود» می‌گویم، باید **هر لایه را جدا** بسنجم و پاسخ را با همان تفکیع بدهم.
- **چرا PR و نه push مستقیم:** چون `permissions: contents: write` روی `ci.yml` (که هر push اجرا می‌شود) یعنی هر کسی که یک commit می‌فرستد یک رباتِ writer هم ساخته است. workflow جدا + dispatch-only + PR، همان قدرت را با یک نقطهٔ بازبینی می‌دهد. پس از بازبینی، من merge کردم — و بازبینی **واقعی** بود: همین‌جا diff را دوباره بایت‌به‌بایت سنجیدم و سه فایلِ بی‌ربط را که CI می‌خواست وارد کند، بیرون کشیدم.
- **قاعدهٔ «commit مکانیکی»:** یک commit فقط-فرمت باید ثابت کند *هیچ چیز دیگری* در آن نیست: نه فایل جدید، نه تزریق خودکار ابزار. اثبات را **بعد از** همهٔ گام‌های ابزار و **روی blobهای staged** بنویس؛ اثبات روی درختِ پیش از `pub get`، چیزی را که commit می‌شود تأیید نمی‌کند.
- **کاماها را انکار نکن:** اولین versionِ proof فقط-whitespace می‌خواست و ۶۵ از ۶۶ فایل را رد کرد. درست نه «شل کردن چک» که «شمردنِ جداگانهٔ تغییرِ مجاز» — تا اگر روزی formatter بیش از چیدمان عوض کرد، عددش دیده شود.


## D-055 (M110؛ 2026-11-20) — ادعای «کامل» بیرون از شناسهٔ تاجر: فیکِ stateful، نه mock بی‌حالت
وقتی مالک می‌گوید «تکمیل باشد ولی با درگاه واقعی خودم بعداً تست می‌کنم»، تعریفِ درستِ «تکمیل»
این است که **قرارداد بیرونی** محلی و رایگان آزموده شود: سرویس مستقلِ HTTP با حالتِ واقعیِ تراکنش
(بازگشت امضاشده، verify یک‌بارمصرف، انصراف، موجودی ناکافی، مهلت انقضا، بازگشت وجه). mockِ
درون‌پروسه فقط logic خودی را می‌سنجد، نه هم‌خوانی با بانک. دو ضمیمهٔ الزامی: (۱) مسیرِ بازگشت
مرورگر باید وجود داشته باشد و در گیتِ public-routes با **دلیل** ثبت شود، نه quiet-skip؛
(۲) production دو لایه قفل شود (validatorِ استارت + getterِ رانتایم) تا «شبیه‌ساز» هیچ‌وقت
جای درگاه واقعی نزند.

## D-058 — تاریخ 2026-11-19 — حذف کامل ECC از مخزن

- **زمینه:** هیچ زیراجنتی از ECC اجرا نشد؛ در Arena ابزار واگذاری و credential مدل وجود ندارد. مالک گفت ECC «قطع» شود و ترجیح داد پروژه به API مدل نیاز نداشته باشد.
- **گزینه‌ها:** (الف) نگه‌داشتن ECC به‌عنوان کتابخانهٔ پرامپت؛ (ب) حذف کامل و آوردن نقش‌های متنی از یک کتابخانهٔ رایگان؛ (ج) ساختن نقش‌ها از صفر.
- **انتخاب:** (ب) — حذف کامل؛ نقش‌ها از کتابخانهٔ رایگان نقش گرفته می‌شوند تا چرخ دوباره اختراع نشود، و تأیید واقعی از ابزارهای قطعی (pytest/ruff/semgrep/gitleaks/route-guard/CI) می‌آید.
- **دلیل:** ۹۳۱ فایل tracked (۸٫۳MB) فقط پرامپت بود و هیچ‌کدام در CI اجرا نمی‌شد؛ نگه‌داشتنش وابستگی و ادعای «agent اجرا شد» می‌ساخت. نقش متنی بدون مدل هم قابل استفاده است و با نیاز «بدون API» سازگار است.
