# آزمایش ایزولهٔ اجرای زیراجنت ECC

**تاریخ مرجع نشست:** ۲۰۲۶-۱۱-۱۸ · **شاخه:** `arena/b0e55b62-mp` · **نتیجه:** `BLOCKED`؛ تعریف role و tool میزبان شناسایی شدند، اما هیچ زیراجنتی اجرا نشد.

## هدف و ایزوله‌سازی

در ادامهٔ [تحقیق REA/ECC](REPORT-REA-ECC-SUBAGENTS.md)، با اجازهٔ مالک یک smoke test برای سؤال ساختگی «۲ + ۲» انجام شد. CLI کش‌شدهٔ Claude Code `2.1.328` در یک cwd و `HOME` موقتِ خالی اجرا شد. محیط subprocess فقط چند متغیر عمومی داشت و **هیچ credential، تنظیمات کاربر، فایل محصول، MCP پروژه، دادهٔ واقعی یا کد محصول** به آن داده نشد. prompt نقش از فایل عمومیِ پین‌شدهٔ ECC (`agents/planner.md`) گرفته و به JSON گزینهٔ `--agents` تبدیل شد؛ نام موقت `ecc-planner-smoke` بود و فهرست ابزارهای آن خالی تعیین شد. این مسیر، **فراخوانی پلاگین `ecc@ecc` نیست**. `--strict-mcp-config`, `--no-session-persistence`, `--disable-slash-commands`, `--permission-mode plan` و `--tools Task` استفاده شدند؛ bypass-permissions یا allowlist سراسری استفاده نشد. سقف `--max-budget-usd 0.01` صرفاً حد محافظه‌کارانهٔ خود CLI بود، نه ادعای هزینه؛ subprocess بدون credential بود و هیچ model call تأییدشده یا مصرفی مشاهده نشد.

## نتایج دقیق

1. `claude auth status --json` در context جاری، فقط با خروجی metadata، `loggedIn: false`, `authMethod: none` و exit 1 را نشان داد؛ این نتیجه دربارهٔ سایر نشست‌ها یا حساب کاربر حکمی نمی‌دهد.
2. در حالت `--bare --restricted`، نقش سفارشی در پیام `init.agents` دیده شد ولی ابزار `Agent` یا `Task` با انتخاب صریح در `init.tools` ظاهر نشد. با `--tools default` فقط `Edit` و `Read` دیده شد. [شاهد metadata آزمایش نخست](../../finn/reports/rea/ecc-isolated-smoke-metadata.json).
3. آزمایش‌های تفکیکی نشان دادند که در این CLI و context ایزوله، حالت `--bare` با `--tools Agent` یا `--tools Task` فهرست ابزار خالی می‌دهد؛ **بدون `--bare`**، هر دو انتخاب در init به نام `Task` دیده شدند. این نتیجه مختص همین تنظیمات و نسخه است؛ علت داخلی دقیق آن مشخص نشده است. این آزمایش‌ها نیز به دلیل خطا مدل/agent اجرا نکردند.
4. آزمایش اصلی را بدون `--bare` و با **فقط** `--tools Task` تکرار کردیم: `init.tools` شامل `Task` بود و نقش `ecc-planner-smoke` در `init.agents` ثبت شد؛ اما process exit 1، و result با `is_error: true` و نشانهٔ خطای ورود/API key داشت. subtype نتیجه در همان خروجی `success` بود، ولی به‌سبب `is_error: true` و exit 1 موفقیت محسوب نمی‌شود. هیچ block از نوع tool-use برای Task/Agent و هیچ پیام با parent tool-use ID و خروجی child مشاهده نشد. [شاهد metadata](../../finn/reports/rea/ecc-task-only-smoke-metadata.json).
5. چون credential و کد MP عمداً کنار گذاشته شد، این آزمایش صرفاً discovery و تلاش بی‌خطر را نشان می‌دهد؛ نه اثبات عملکرد plugin، کیفیت خروجی planner، موفقیت model provider، یا شرایط پس از ورود. فرض نمی‌کنیم `tools: []` در هر میزبان همان اثر sandbox امنیتی را دارد؛ در این آزمایش مدل اصلاً اجرا نشد. جزئیات خام جریان خروجی و اطلاعات احتمالی ورود ذخیره یا منتشر نشدند.

## قدم بعدی قابل اجرا

- برای واقعی‌شدن فراخوانی child، به **یک میزبان واقعاً پشتیبانی‌شده و مجاز** نیاز است: یا Arena ابزاری برای delegation ارائه کند، یا Claude Code در محیطی که کاربر به‌صورت امن به سرویس آن دسترسی داده است. هیچ پسورد، کلید یا token نباید در چت فرستاده شود.
- تکرار با همان سؤال ساختگی، HOME/cwd مناسب میزبان، عدم دسترسی به کد MP، محدودیت ابزار و بودجهٔ تأییدشده؛ ثبت پیام واقعی `tool_use` برای `Task/Agent`، شناسهٔ parent/child و خروجی child و جمع‌آوری نتیجه. فقط بعد از این گیت، «زیراجنت ECC واقعاً اجرا شد» گفته شود.
- بارگذاری خود plugin با نام `ecc:planner` و بررسی هم‌زمان `enabled:true` / `projectEnabled:false`، restart و وابستگی‌ها یک آزمون جداست؛ موفقیت ثبت نقش دستی فوق آن را اثبات نمی‌کند. قبل از ارسال هر کد پروژه به سرویس بیرونی، provider، هزینه، مرز داده و اجازهٔ صریح لازم‌اند.

گیت مستندات و یکپارچگی JSON پس از ایجاد این گزارش اجرا می‌شوند. محصول، credential، hooks، سرویس پرداخت یا زیرساخت تغییری نکرده است.
