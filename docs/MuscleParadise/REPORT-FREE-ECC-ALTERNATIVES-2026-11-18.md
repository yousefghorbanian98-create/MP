# ارزیابی عملی گزینه‌های رایگان جایگزین ECC

**تاریخ مرجع:** ۲۰۲۶-۱۱-۱۸ · **نوع:** پژوهش و smoke ایزوله، نه پذیرش یا نصب روی پروژه<br>
**تصمیم فعلی:** جایگزینی کامل ECC هنوز اثبات نشده است. **Superpowers + نقش‌های منتخب Agency Agents روی OpenCode** نامزد امیدوارکننده است؛ اجرای مکانیکی فراخوانی skill و ساخت child session با مدل ساختگی پاس شد، ولی کیفیت و خودمختاری AI با مدل واقعی هنوز `NOT RUN` است.

## ۱. سؤال و معیار

آیا ترکیبی رایگان می‌تواند نقش‌ها، گردش کار و زیراجنت‌های ECC را برای FINN و QA پروژه جایگزین کند، بدون تعارض با خواستهٔ مالک، ایمنی فایل‌ها و هزینهٔ نامعلوم؟ معیارها: مجوز، سازگاری میزبان، بارگذاری نقش/skill، child واقعی با شاهد، رگرسیون‌های هر loop، TDD، امنیت، کیفیت خروجی مدل، هزینه و حفاظت workspace. مهارت متنی، نتیجهٔ QA و قدرت مدل یکی نیستند.

## ۲. محیط و ایمنی

- شاخهٔ فعلی `arena/b0e55b62-mp`، HEAD `5482930`، ۶۲ تغییر dirty/untracked و صفر فایل staged در آغاز سنجش. هیچ pull/reset/merge/push یا تغییر محصولی انجام نشد.
- سیستم: Python 3.11، Node 22، حدود ۳٫۸ GiB حافظهٔ گزارش‌شده؛ GPU، Docker، Ollama و CLIهای OpenCode/Claude/Codex در PATH اولیه وجود نداشتند. متغیرهای رایج کلید مدل در محیط subprocess خالی بودند؛ مقدار credential نمایش داده نشد.
- آرشیوهای pinned عمومی به یک مسیر زیر `/tmp`، خارج از workspace پروژه دانلود شدند. OpenCode در prefix موقت، با `npm install --ignore-scripts` نصب شد. wrapper بدون postinstall اجرا نشد؛ به‌جای اجرای script نصب، binary بستهٔ اختیاری Linux مستقیم اجرا شد. HOME، cwd و agent/config مربوط به OpenCode موقت و جدا بودند؛ **هیچ کد یا دادهٔ پروژه عمداً به این آزمایش داده نشد**. این جداسازی cwd/HOME به‌تنهایی sandbox امنیتیِ سطح سیستم‌عامل یا اثبات ممانعت از خواندن فایل‌های خارج نیست.
- subprocess با `env -i` و بدون credential، با غیرفعال‌کردن auto-update و model-fetch راه‌اندازی شد؛ stub فقط روی loopback و دادهٔ ساختگی بود. هیچ فراخوانی مدل ابری/واقعی یا تراکنش پولی مشاهده نشد. `opencode.ai`، `api.anthropic.com` و `huggingface.co` از این sandbox برای درخواست HEAD قابل دسترسی نبودند؛ این مشاهده را به نشست یا شبکهٔ دیگر تعمیم نده.
- آزمایش از branch و Git repo اصلی در حافظه/محیط دیگر استفاده نکرد؛ هیچ branch/worktree پروژه یا تنظیمات MCP/hook پروژه ساخته نشد. فایل‌های خروجی این گزارش و metadata تنها آثار جدید عمدی در workspace هستند؛ بسته‌های موقت بین نشست‌ها ماندگار نیستند.

## ۳. نسخه‌ها و مجوزها

| نامزد | نسخه یا commit سنجیده‌شده | مجوز / ارزیابی |
|---|---|---|
| ECC | نسخهٔ `ecc-universal 2.2.3` و [آزمایش پیشین](REPORT-ECC-SUBAGENT-SMOKE.md) | هسته MIT و رایگان؛ زیراجنت پیشین در همان محیط به دلیل auth اجرا نشد. رفتار ECC در سنجش امروز تکرار نشده است. |
| Superpowers | [v7.0.2 / commit 22f0b463](https://github.com/obra/superpowers/tree/22f0b463e7a5e579904dd6211a520321035526f7) | MIT؛ روش برنامه‌ریزی، TDD، بازبینی و زیرعامل؛ نه جایگزین یک‌به‌یک همهٔ agentها و hookهای ECC. |
| Agency Agents | [commit 8ae61646](https://github.com/msitarzewski/agency-agents/tree/8ae6164602c95ca78828b148b9052460ee426885) | MIT؛ کتابخانهٔ نقش؛ ۲۸۳ نقش در خروجی installer همان snapshot، نه ۲۸۳ مدل یا عامل اجرایی. |
| OpenCode | بستهٔ npm `opencode-ai@1.19.6`، [مخزن](https://github.com/anomalyco/opencode) | MIT؛ runtime عامل و زیراجنت. عدد `v2.3.2` در release مخزن به `opencode-ai@2.3.2` در npm تطبیق نداشت؛ نصب آن نسخه 404 بود و معادل بودن releaseها ادعا نمی‌شود. |
| Oh My OpenAgent | [مجوز مخزن](https://github.com/code-yeongyu/oh-my-openagent/blob/9a2e4dec0decb589dc3d6d80a2a10208e1cb9d59/LICENSE.md) | Sustainable Use License و محدودیت توزیع؛ ارزیابی حقوقی استفادهٔ تجاری اختصاصی لازم است؛ نصب/تست اجرایی نشد. |

بررسی مجوزهای بالا مربوط به متن/metadata مخزن در snapshot است، نه بررسی کامل وابستگی‌ها، مدل، weights، سرویس و وضعیت حقوقی هر کاربرد. ورود کد/پرامپت به مخزن یا محصول نیازمند attribution و بررسی جداگانه است.

## ۴. آزمایش‌های واقعاً انجام‌شده

### ۴.۱ تست مستقل بسته‌ها

در آرشیو Superpowers، پنج test script بالادستی با `bash` موفق شدند:

1. `tests/opencode/test-skill-registration.sh`: در میزبان **شبیه‌سازی‌شدهٔ** V2، ۱۵ skill ثبت شدند و rejection عمدی یک skill بررسی شد؛ پیام خطای شبیه‌سازی‌شدهٔ stderr انتظار تست بود.
2. `tests/opencode/test-hook-registration.sh`: ثبت hookهای context/compaction/generate در mock موفق.
3. `tests/opencode/test-session-bootstrap.sh`: طبقه‌بندی child، recovery و cache در mock موفق؛ هشدارهای عمدی تست، خرابی اثبات‌شدهٔ محیط واقعی نیستند.
4. `tests/skill-layout/test-no-dev-files-in-skills.sh`: موفق.
5. `tests/sdd-helper-paths/test-sdd-helper-paths.sh`: موفق.

در آرشیو Agency Agents، سه test script موفق شدند: `scripts/test-agent-selection.sh`، `scripts/test-lint-fences.sh` و `scripts/test-convert-frontmatter.sh`. فقط این تست‌ها اجرا شدند؛ هیچ‌یک کیفیت مدل یا سلامت کل پروژهٔ upstream را اثبات نمی‌کند.

### ۴.۲ بارگذاری واقعی در OpenCode با نقش ساختگی/محدود

در cwd موقت، installer مربوط به Agency با انتخاب فقط `testing-api-tester` اجرا شد و فایل agent را صرفاً در آن cwd تولید کرد. برای Superpowers پلاگین pinned از طریق symlink در HOME موقت ثبت شد. `opencode agent list` واقعاً `API Tester (subagent)` را نشان داد. مشاهدهٔ فهرست به‌تنهایی اجرای child نیست.

در یک subprocess جدا، با مدل HTTP محلی **اسکریپت‌شده، غیرهوشمند**:

- **Skill:** پاسخ ساختگی provider، فراخوانی `skill(name="test-driven-development")` را تحمیل کرد. خروجی واقعی ابزار OpenCode `completed`، طول ۹۸۷۹ کاراکتر و شامل RED/GREEN بود. این شاهد بارگذاری متن است، نه اجرای TDD یا تبعیت مدل از آن.
- **Delegation:** provider ساختگی فراخوانی `task` به نقش `API Tester` را تحمیل کرد. OpenCode واقعاً یک **session فرزند جدا** ساخت؛ رویداد ابزار وضعیت `completed`، شناسه‌های متفاوت parent/child و marker ساختگی `CHILD_API_4` را گزارش کرد. متن نقش Agency در درخواست child و bootstrap Superpowers در درخواست parent مشاهده شد. خروجی provider عمداً از قبل نوشته شده بود؛ هیچ مدل هوش مصنوعی تصمیم نگرفت agent را صدا بزند یا پاسخ را تولید کند. اجرای واقعی مکانیزم session، اثبات کیفیت یا تفکر زیراجنت نیست.
- پیکربندی آزمون در cwd موقت دارای `permission` برابر `* = deny` به‌جز `task` و `skill` بود؛ تنها همین طرح و فعالیت مشاهده‌شده گزارش می‌شود، نه گواهی کامل امنیت permission یا انزوای فرایند.

[شاهد metadata پالایش‌شده](../../finn/reports/rea/free-ecc-alternatives-smoke-metadata.json) شامل شناسه‌های ساختگی session، وضعیت ابزار و revisionهاست. این فایل را agent اصلی ساخت؛ **REA در این سنجش اجرا نشد**. متن کامل پاسخ‌ها، provider config یا log خام منتشر نشده است.

### ۴.۳ آنچه هنوز انجام نشده

`NOT RUN/BLOCKED`: مدل واقعی رایگان یا محلی، تصمیم خودکار مدل برای فراخوانی زیراجنت، تولید/بازبینی کد، TDD RED→GREEN→REFACTOR، مقایسهٔ A/B با ECC، امنیت واقعی، QA محصول، runtime Flutter و یکپارچه‌سازی native با Arena. در این نشست مکانیسم بومی delegation برای این عامل در دسترس/اثبات‌شده نبود. تجربهٔ موفق کاربر در نشست‌های قبلی را رد نمی‌کنیم و عملکرد نشست دیگر می‌تواند متفاوت باشد.

## ۵. خطرهای مهم قبل از هر نصب واقعی

1. در Superpowers، `using-git-worktrees` می‌تواند ساخت branch/worktree و تغییر `.gitignore`/commit را پیشنهاد کند؛ `finishing-a-development-branch` مسیر checkout/merge/push دارد. در پروژهٔ ما این کارها فقط در چارچوب پیام branch فعلی و مجوز صریح ممکن‌اند. برای این نشست تغییر branch، ساخت branch جدید و overwrite آثار قبلی ممنوع است.
2. `test-driven-development` صراحتاً حذف کد پیش از تست را تجویز می‌کند. **هرگز آثار کاربر یا کد قبلی را بر اساس این دستور حذف نکن**. اجازهٔ صریح و محدود کاربر، دستور سطح بالاتر و حفظ آثار موجود مقدم‌اند. دستور upstream به معنی اجبار قابل اجرا بر مخزن نیست.
3. API Tester دارای ادعاها و هدف‌های کلی است؛ نقش `Reality Checker` حتی فرمان‌های ثابت وابسته به Laravel، مسیر فرضی localhost و screenshot script دارد که بر پروژهٔ ما منطبق نیست. نقش‌ها باید با حداقل مجوز و بررسی موردی اقتباس شوند؛ ادعا یا دستور عمومی به‌صورت خودکار اجرا نشود.
4. OpenCode در `agent list` در برخی نقش‌ها permission گسترده نشان داد؛ defaults را امن فرض نکن. قبل از هر کار واقعی، مجوز خواندن/نوشتن/اجرای دستور/شبکه و لاگ‌ها باید با تست جداگانه و مطابق sandbox بررسی شود. ثبت نقش به‌تنهایی کنترل دسترسی نیست.
5. نرم‌افزار رایگان الزاماً inference رایگان یا باکیفیت نیست. گزینهٔ مدل محلی به RAM/CPU/GPU، مجوز weights و ابزار نیاز دارد؛ برای بار واقعی پروژه در این محیط هیچ عملکرد قابل قبول یا مدل مناسب اثبات نشده. سهمیهٔ رایگان ابری، دسترسی منطقه‌ای، داده و هزینه ممکن است تغییر کنند.

## ۶. نتیجه و توصیه

**رتبه‌بندی فعلی فقط برای بررسی بیشتر، نه تأیید برتری:**

1. **Superpowers + Agency + OpenCode:** عبور از smoke مکانیکی بارگذاری مهارت و ساخت child؛ مناسب‌ترین نامزد سنجیده‌شده برای تداوم FINN/QA. مقایسهٔ کیفی و امنیتی باز است.
2. **ECC:** از نظر گسترهٔ نقش‌ها و skills همچنان گزینهٔ مهم است؛ اجرای واقعی زیراجنت در آزمایش قبلی این sandbox به auth برخورد و در محیط دیگر ممکن است کار کند. نبود child در آن تست به معنی بی‌کیفیت‌بودن ECC نیست.
3. **Oh My OpenAgent:** قابلیت‌های هماهنگی جذاب اما به دلیل مجوز، مدل و محدودیت‌ها بدون بررسی بیشتر انتخاب نمی‌شود.

**گام بعدی پیشنهادشده:** در یک sandbox واقعاً ایزوله و میزبان/مدل مجاز، همان سه تمرین مصنوعی و هم‌سطح را با ECC و ترکیب جدید تکرار کن: (۱) اجرای parent/child با شاهد، (۲) باگ کوچک با تست واقعاً RED/GREEN، (۳) review مستقل امنیت/QA و بررسی حفظ فایل. تعداد موفقیت، failures، زمان، مدل، هزینه، مجوز و خروجی را ثبت کن. برای خدمت ابری، پیش از ارسال هر کد حتی عمومیِ پروژه، تأیید provider، داده و هزینه لازم است؛ می‌توان ابتدا فقط fixture ساختگی استفاده کرد. تا مشاهدهٔ نتایج، هیچ تغییر در انتخاب رسمی، hook، پروژه یا برنامهٔ QF انجام نشود.
