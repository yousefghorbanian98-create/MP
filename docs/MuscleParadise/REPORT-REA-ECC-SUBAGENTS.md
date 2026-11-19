# بررسی محلی REA برای یافتن مسیر اجرای زیراجنت‌های ECC

**تاریخ مرجع نشست:** ۲۰۲۶-۱۱-۱۸ · **شاخه:** `arena/b0e55b62-mp` · **هدف:** فهم راه واقعی استفاده از ECC، نه اجرای توسعه یا انتشار.<br>
**نتیجهٔ کوتاه:** تعریف نقش‌های ECC و CLI میزبان سازگار موجودند؛ اما در این نشست، ابزار مستقیم اجرای زیراجنت از سوی Arena دیده نمی‌شود و `claude auth status` برای CLI موقت `loggedIn: false` گزارش کرد. بنابراین اجرای مستقل در این نشست **هنوز اثبات نشده**، نه اینکه استفاده در نشست‌های قبلی ناممکن بوده باشد.

## ۱. دامنهٔ مطالعه و شواهد REA

- ابتدا وضعیت ابزار، Git و sandbox بررسی شد: Git `2.39.5`، Python `3.11.2`، Node پرتابل `24.22.3`، REA `6.9.0`، ECC `2.2.3`؛ ۴۸ ورودی dirty، HEAD پروژه `5482930587ce18e14f136d78296542a2de5af091` به‌علاوهٔ تغییرات موجود؛ ECC checkout روی `d2ef2680594f9a17526a6e1a2e18b3d242c5d17b`. روی همین شاخه کار شد؛ هیچ pull/reset یا تغییر runtime محصول صورت نگرفت.
- برای جلوگیری از دربرگیری فایل‌های حساس/حجیم، از فایل‌های متنی مجازِ Git tracked و untracked غیرignored یک mirror موقت در `/tmp` تهیه شد. شامل بخش‌های اصلی backend، client، Studio، docs، workflows، state و agentهای پروژه، و نیز skill/command/rule/hookهای `.claude` بود. فایل‌های محیطی، نام‌های مشکوک به credential/secret/token، keystore، داده و DB، دارایی‌های باینری، lockfile، مسیرهای generated، vendor، symlink و فایل‌های بزرگ و مسیرهای `finn/reports`/`evidence` در mirror وارد نشدند. نام‌پایهٔ filter ممکن است برخی فایل‌های کد با نام حساس را نیز عمداً حذف کند. فایل‌های ignored خارج از انتخاب‌اند؛ این یک تصویر کامل همهٔ فایل‌های repo نیست.
- `rea import-reference-source <temporary-project-mirror> --detail summary --outline-depth 1 --format json`: **۱۵۰۰ فایل متنی، ۵۳۶ directory، ۳۴۴ relationship و صفر parse failure گزارش‌شده، `inventory_state: partial`**؛ manifest `hsm_7b526b794caa9cddb95f7dd2712855ccae80ace203bedabf3018b9f4fea2b7bf`. ۷۳ فایل Dart در mirror شمارش شدند ولی Dart در فهرست زبان‌های تشخیص‌داده‌شدهٔ این خروجی نیامد؛ آن‌ها hashed/inventoried هستند، نه اینکه تحلیل معنایی Dart انجام شده باشد. مجوز، رفتار و امنیت از این آمار نتیجه نمی‌شود.
- برای فهم خود ECC نیز mirror دیگری از متن `agents/`, `scripts/`, `docs/`, `.claude-plugin/`, `commands/`, `skills/` و rootهای مشخص checkout تهیه شد؛ همان REA command: **۲۵۷۰ فایل، ۱۰۳۴ directory، ۱۲۷۵ relationship، صفر parse failure، `partial`**، manifest `hsm_2ac4c1ba7b21f5569fde551be3aac82ccc7e3c54ecb325eff92fa8e095364403`. چند target پویای CommonJS نامشخص ماند. mirrorها تاریخی‌اند و Git metadata ندارند، نه تحلیل مستقیم تاریخچه یا دیتای کامل workspace.
- REA `analyze-javascript-application` با انتخاب صریح سه فایل ECC (`scripts/ecc.js`, `scripts/setup.js`, `scripts/consult.js`) و به‌طور جدا سه فایل Studio (`src/lib/api.ts`, `src/components/RoleManager.tsx`, `src/components/PaymentPanel.tsx`) هر دو exit 0 دادند. فقط همین فایل‌ها بررسی static شدند؛ خروجی graph و semantic برای هر دو **partial** است، نه اجرای برنامه. `complete-within-view` صرفاً صفحهٔ view را توصیف می‌کند؛ در ECC ۳۹۵ و در Studio ۸۶ فایل artifact از انتخاب بیرون بودند. این تحلیل نه همهٔ کد پروژه است و نه آزمون runtime.
- [خلاصهٔ ماشین‌خوان پالایش‌شده](../../finn/reports/rea/project-ecc-orchestration-summary.json) شامل تعداد، manifestها، شناسه‌های evidence و محدودیت‌هاست. REA output کامل ممکن است کد/مسیر داشته باشد؛ فقط در sandbox موقت نگهداری شد و در مخزن ذخیره نشد. mirrorهای `/tmp` بین نشست‌ها تضمین بقا ندارند. نتیجهٔ این کار مطالعهٔ ساختار گسترده به همراه تحلیل هدفمند است، **نه ادعای مطالعهٔ خط‌به‌خط کل پروژه یا audit امنیتی کامل**.

## ۲. یافته‌های دقیق دربارهٔ اجرای واقعی

| لایه | شاهد واقعی | تفسیر |
|---|---|---|
| تعریف نقش‌ها | در `.finn/ecc/agents/` و `.claude/agents/` نقش‌های `planner`, `architect`, `tdd-guide`, `code-reviewer`, `security-reviewer`, `e2e-runner`, `refactor-cleaner` حاضر و در مقایسهٔ byte یکسان بودند؛ cache افزونه ۷۲ تعریف agent داشت. | این‌ها prompt/config هستند، نه فرآیند یا اجرای مدل. |
| نوع فراخوانی ECC | فایل checkout پین‌شده `.finn/ecc/rules/common/agents.md` صریحاً `Agent(subagent_type: "ecc:planner", prompt: "...")` را برای plugin و نام بدون پیشوند را برای نصب دستی توضیح می‌دهد. | syntax نمونهٔ ابزار میزبان است، **نه فرمان shell** و نه اثبات اینکه Arena آن را عرضه می‌کند. تشخیص نام نهایی در میزبان واقعی باید بررسی شود. |
| CLI واقعی | `npx --offline --package=@anthropic-ai/claude-code@2.1.328 -c 'claude --help'` موفق؛ گزینه‌های `--agents`, `--agent`, `--plugin-dir`, `--output-format stream-json` را نشان داد. `claude agents --help` نیز مدیریت background session را نشان داد. | میزبان Claude Code مسیر فنی متفاوتی از ابزارهای خود Arena دارد. `--agent` به‌تنهایی اثبات فراخوانی subagent توسط orchestrator نیست؛ `claude agents` نمایش session نیز معادل فهرست subagentهای ECC نیست. |
| وضعیت افزونه | `claude plugin list --json` به‌صورت فیلتر metadata: `ecc@ecc`, v2.2.3, `scope: local`, `enabled: true`, `projectEnabled: false`. `node_modules` در cache افزونه دیده نشد؛ گزارش نصب قبلی `dependencies-refused` و `restartRequired` داشته است. | معنای دقیق دو flag متناقض‌نما و اثر dependency بر قابلیت agent در میزبان باید با اجرای واقعی ارزیابی شود؛ نمی‌توان گفت همهٔ امکانات فعال یا همه ناکارآمد هستند. [گزارش setup](../../finn/reports/ecc-native-setup.md). |
| احراز هویت CLI | `claude auth status --json` با خروجی صرفاً metadata: exit 1، `loggedIn: false`, `authMethod: none`, `apiProvider: firstParty`. | برای همین CLI/context، ورود native گزارش نشده است. این نتیجه دربارهٔ حساب کاربر، نشست‌های دیگر، تمام providerها یا تمام نسخه‌های میزبان تعمیم ندارد و ارزش credential را افشا نمی‌کند. |
| session موجود | `claude agents --json --all --cwd /home/user/MP` exit 0 و آرایهٔ صفر session برگرداند. | فقط نمای sessionهای این دستور در این cwd/محیط؛ نبود زیراجنت در نشست‌های قدیمی را ثابت نمی‌کند. محتوای history یا session خصوصی چاپ نشد. |
| Arena فعلی | ابزارهای در اختیار عامل شامل bash و سایر ابزارهای فعلی هستند؛ ابزار مستقلی با رابط spawn/delegate agent دیده نمی‌شود. | از داخل مخزن با نصب فایل/CLI نمی‌توان به‌تنهایی ابزار جدیدی به رابط همین نشست اضافه کرد. میزبان دیگر یا قابلیت جدید پلتفرم ممکن است مسیر متفاوتی ارائه دهد. |

`REA` برای شناخت و ثبت ساختار/contract مفید است، اما ابزار فعال‌سازی مدل، پرداخت، احراز هویت یا اجرای زیراجنت نیست. `ecc consult` هم انتخاب heuristic است و subagent اجرا نمی‌کند. ادعای کاربر دربارهٔ جلسات دیگر رد نمی‌شود؛ بدون transcript/شناسهٔ فراخوانی آن نشست، مکانیسم دقیق آن نامعلوم است.

## ۳. مسیرهای ممکن، به ترتیب کم‌خطر

### مسیر A — خود Arena ابزار واقعی delegation ارائه کند

1. در نشست/میزبان مناسب، فهرست ابزارهای واقعی همان نشست را بررسی کن؛ اگر ابزار فراخوانی agent دارد، سازگاری آن با تعریف‌های ECC و نام نقش‌ها را با راهنمای آن میزبان تأیید کن. `Agent(...)` مستند ECC را فقط اگر میزبان واقعاً چنین APIای دارد استفاده کن؛ syntax و نام دقیق ممکن است فرق کنند.
2. با یک ورودی **ساختگی و فاقد کد پروژه/اطلاعات عضو**، یک وظیفهٔ کوچک `planner` و سپس یک review محدود انجام شود. فراخوانی، شناسهٔ parent/child یا tool-call و نتیجهٔ واقعی ثبت و جمع‌آوری شود. اگر tool واقعاً وجود ندارد، هیچ roleplay جایگزین آن نیست.
3. پس از اجازهٔ صریح برای ارسال محدودهٔ لازم کد به ارائه‌دهندهٔ مدل و تعیین هزینه/محرمانگی، همان روش را برای میکرولوپ‌های مجاز [برنامهٔ QF](PLAN-FINN-ECC-MICROLOOPS-QA.md) به کار ببر. هیچ secret، دیتای عضو یا کل مخزن به‌صورت پیش‌فرض ارسال نشود.

**وضعیت:** API delegation در این نشست قابل مشاهده نیست؛ تغییر این وضعیت از طریق نصب فایل در workspace اثبات نشده است.

### مسیر B — میزبان Claude Code جداگانه با ECC

1. `claude --help` و `claude auth status` فقط به‌صورت metadata؛ احراز هویت/مجوزهای سرویس باید توسط کاربر در محیط امن و مطابق روش ارائه‌دهنده مدیریت شود، نه ارسال رمز یا token در چت. وضعیت احراز هویت فعلی همین sandbox `loggedIn: false` است.
2. در محیط مجاز، افزونهٔ محلی `ecc@ecc` و scope/restart و نیاز dependency آن بررسی شوند، یا agentهای محلی `.claude/agents/` به‌طور مستند توسط همان host شناسایی شوند. plugin-scoped `ecc:planner` را با نام دستی `planner` اشتباه نگیر؛ در شواهد تشخیص میزبان را ثبت کن. `--plugin-dir` یک راه **نامزد** برای بارگذاری session-local است، نه تضمین شناسایی سالم.
3. ابتدا smoke test کاملاً ساختگی/بدون کد MP، با محدودهٔ دسترسی کم، hooks خاموش و بدون ابزار تغییر فایل، در سقف هزینهٔ تأییدشده. یک orchestrator باید واقعاً ابزار Agent را برای `ecc:planner` یا نام شناسایی‌شده صدا بزند، نتیجه را جمع کند و metadata زنجیرهٔ فراخوانی را ثبت کند؛ صرف `--agent planner` یا پاسخ مدل با عنوان planner این گیت نیست. از حالت bypass-permissions یا allowlist سراسری استفاده نشود.
4. فقط بعد از اثبات و تأیید ارسال کد، وظیفهٔ محصول محدود به فایل‌ها/خروجی ضروری، ابزارهای read-only یا کمترین مجوز، دادهٔ ساختگی، بودجه و سیاست حذف transcript تعریف شود. مدل/ارائه‌دهنده ممکن است خارج از کشور باشد؛ حریم و انتقال داده با مالک روشن شود. بازبین زیراجنتِ جدا، بازبین انسانی مستقل یا تضمین امنیت نیست.

**وضعیت:** CLI و تعریف‌ها قابل مشاهده‌اند، ولی login، بارگذاری مؤثر، اجرای مدل، هزینه/انتقال داده و tool-call child اثبات نشده‌اند؛ هیچ inference یا ارسال کد در این بررسی انجام نشد.

### مسیر C — host دیگر با اجرای agent

طبق مستندات ECC، پشتیبانی targetهای دیگر ممکن است؛ ابتدا نسخه، قابلیت واقعی delegation، تبدیل فرمت agent و سیاست داده بررسی شوند. نصب مجموعهٔ فایل‌ها یا نام‌گذاری مدل بدون API delegation گواه اجرا نیست. در نبود این ابزار، عامل اصلی با checklist ECC کار می‌کند و «مرور دستی» ثبت می‌کند، نه «بازبینی مستقل».

## ۴. تعریف دقیق آزمون پذیرش پیش از استفاده در پروژه

- ثبت نسخهٔ host، نسخه/SHA ECC، نحوهٔ بارگذاری و نام role شناسایی‌شده؛ مشخص شود دستور `--agent` برای main session است یا tool-call برای child.
- ورودی مصنوعی محدود و بدون دسترسی به repo، محیط با least privilege؛ بدون session logging حساس، secret، شبکهٔ اضافه یا عملیات نوشتن.
- ثبت شواهد واقعی: نوع ابزار فراخوانی، شناسهٔ parent و child یا trace معادل میزبان، نتیجه/زمان تکمیل و اینکه والد خروجی child را دریافت کرده است. وجود نام agent در متن، لیست فایل یا `consult` کافی نیست.
- شواهد را با redaction ذخیره کن، بدون promptهای شامل کد محرمانه یا محتویات credential. هر گیت اجرا نشده `UNKNOWN/BLOCKED` است. اجرای موازی بدون جمع‌آوری نتایج مجاز نیست.
- بعد از موفقیت، وظایف ECC در هر میکرولوپ از [طرح QA](PLAN-FINN-ECC-MICROLOOPS-QA.md) طبق دامنه و نتیجهٔ واقعی انجام شوند؛ تست مستقل برنامه، CI، دستگاه و بازبینی حقوقی/مالی همچنان جایگزین‌ناپذیرند.

## ۵. قدم بعدی

برای تشخیص نشست قبلی، نام نشست یا شاهد غیرمحرمانه از tool-call/agent-id یا تصویر آن می‌تواند نشان دهد آن نشست از کدام میزبان و مسیر delegation استفاده کرده است؛ **اطلاعات ورود لازم نیست**. اگر هدف امتحان یک میزبان بیرونی باشد، ابتدا دربارهٔ اجرای model call، provider و هزینه و فرستادن داده به بیرون باید اجازهٔ مشخص گرفته شود. تا آن زمان هیچ تغییر خودکاری در login، پلاگین، credential، hooks یا محصول انجام نشود. برای ادامهٔ ساخت، وضعیت و مجوزهای [طرح QF](PLAN-FINN-ECC-MICROLOOPS-QA.md) رعایت شوند.
