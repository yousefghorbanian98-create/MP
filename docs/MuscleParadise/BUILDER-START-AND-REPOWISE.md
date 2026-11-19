# شروع سازندهٔ بعدی: پیش‌نیاز، نصب و نقشهٔ انتقال

> وضعیت ۲۰۲۶-۱۱-۱۸: این مخزن عمومی است ولی مجوز آن اختصاصی است. محصول آمادهٔ release نیست؛ QF-00..32 و OV-01..11 اجرا نشده‌اند، QA مستقل ECC اثبات نشده و نصب/اتصال ابزار به‌تنهایی مجوز توسعه یا استقرار نیست.

## ۱. پیش‌نیازها، به ترتیب

1. Git و دسترسی به مخزن و شاخهٔ مجاز همان نشست؛ فایل‌های dirty و untracked را حفظ کنید. [LICENSE](../../LICENSE)، [AGENTS.md](../../AGENTS.md)، [handoff جاری](SESSION_HANDOFF.md)، [TODO ابری/مالی](TODO-CLOUD-FINANCE-ACCESS.md)، [طرح QF](PLAN-FINN-ECC-MICROLOOPS-QA.md) و [ماتریس نقش‌ها](PROPOSAL-SUBAGENTS-AND-CHECKPOINTS.md) را بخوانید. ابتدا `git status --short --branch` و `git rev-parse HEAD` را ببینید و وضعیت remote/CI همان SHA را بررسی کنید. هیچ branch/reset/force-push را از متون تاریخی اجرا نکنید.
2. برای Backend، Python 3.11 یا بالاتر، pip و venv؛ CI از Python 3.11 استفاده می‌کند. برای Studio، Node.js 22 و npm؛ `package-lock.json` موجود است. برای کلاینت، Flutter 3.50.0 و Dart همراه آن، Android SDK و Java 17؛ CI یک job با stable شناور و یک job با SDK پین‌شده دارد. `.devcontainer/Dockerfile` revision و checksum پین‌شده را مشخص می‌کند. Docker فقط برای استفاده از devcontainer لازم است، نه همهٔ آزمون‌ها. تنظیمات واقعی database، مهاجرت و سرویس‌ها را از README و runbookهای مربوط بگیرید و از secret یا دادهٔ واقعی در نمونه‌ها استفاده نکنید.
3. برای پژوهش اختیاری REA نسخهٔ `6.9.0` به Node `^22.23.4 || ^24.22.1 || >=26.12.1` نیاز دارد؛ این نسخه با Node 22 موجود در این sandbox سازگار نبود. ECC روی `.finn/ecc-commit.txt` پین شده است. FINN یک روش کار است، نه بستهٔ اجرایی مجزا. میزبان دارای امکان delegation واقعی، مدل مجاز و QA مستقل لازم است؛ در آزمایش این sandbox، Claude Code بدون ورود معتبر حتی یک child اجرا نکرد. اعتبارنامه‌ها را تنها خارج از چت و از روش امن میزبان تنظیم کنید؛ ارسال کد به مدل بیرونی مجوز جداگانه می‌خواهد.
4. RepoWise `0.61.0` اختیاری است؛ Python، pip، venv، Git و فضای کافی برای وابستگی‌های آن لازم‌اند. index در `.repowise/` و محیط ابزار، محلی/ignored هستند و در clone تازه وجودشان تضمین نمی‌شود. MCP Arena در این آزمایش متصل/اثبات نشد.

## ۲. نصب و تست پایه

در clone معتبر و پس از بازبینی مسیر و محیط (فرمان‌ها برای Linux/macOS هستند؛ Windows به مسیر venv و SDK مناسب خود نیاز دارد):

```bash
# از ریشهٔ مخزن؛ این وابستگی‌ها محیط تازه را تغییر می‌دهند.
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e 'mp-app/backend[dev]'
python scripts/docs_gate.py
(cd mp-app/backend && python -m pytest)

# جداگانه برای Studio؛ نصب از lockfile و آزمون کل پنل
(cd mp-app/studio && npm ci && npm test -- --run)

# پس از نصب SDK رسمی و بررسی نسخهٔ پین‌شده
(cd mp-app/client && flutter --version && flutter pub get && flutter analyze --no-fatal-infos && flutter test)
```

این مجموعهٔ نصب کامل در این sandbox دوباره اجرا نشده است: Flutter/Dart/Docker اینجا در PATH نبودند. در زمان انتقال فقط تست ایزولهٔ policy با Python 3.11 و pytest 8.4.2 اجرا شد: ۵۴ passed، یک هشدار پیکربندی ناشی از نصب‌نشدن pytest-asyncio. CI تاریخی [run 44507836824](https://github.com/yousefghorbanian98-create/MP/actions/runs/44507836824) روی `dc572a7c2fbb7ab094297cfec4bd56accca6dc1b` هشت job سبز داشت، نه تأیید release یا هر commit بعدی. نسخه‌های dependency پایتون حداقلی‌اند، نه lock کامل؛ در محیط جدید ابتدا resolver و مجوزها را بازبینی کنید.

### نصب اختیاری REA/ECC

`docs/MuscleParadise/finn/install-toolchain.sh` را **پیش از اجرا بخوانید**: checkout ECC، فایل‌های `.claude`، نصب خارج مخزن و تنظیم MCP را ممکن است تغییر دهد. نمونهٔ نصب `bash docs/MuscleParadise/finn/install-toolchain.sh all` است؛ در آزمایش پیشین به اختلاف `LICENSE-REA` خورد و کامل نشد. مقایسهٔ اصلاح‌شده با `bash docs/MuscleParadise/finn/test-check-rea-skill.sh` روی fixture بررسی می‌شود، اما موفقیت نصب مجدد کامل یا اتصال MCP در این انتقال اثبات نشده است. وضعیت واقعی `rea doctor` و میزبان را پس از نصب بررسی کنید؛ failure را موفق اعلام نکنید. جزئیات [گزارش آماده‌سازی](REPORT-PRELOOP-READINESS-2026-11-18.md) و [smoke واقعی ECC](REPORT-ECC-QA-TRIAL-2026-11-18.md).

## ۳. خروجی RepoWise و محدوده

[گراف Structurizr تولیدشده](architecture/repowise-transfer-2026-11-18.dsl) و [فهرست ورودی‌های mirror](architecture/repowise-transfer-scope-2026-11-18.txt) فقط نقشهٔ کمکی و قابل‌انتقال‌اند. RepoWise 0.61.0 واقعاً بر یک mirror انتخابی با Git مصنوعی، HOME ایزوله، بدون provider/model، بدون hook/editor و با `--mode fast --no-prose` اجرا و گراف صادر شد. mirror پیش از نگارش این راهنما و به‌روزرسانی نهایی handoff ساخته شد؛ همین راهنما، manifest، گراف و اصلاحات بعدی در index آن نیستند. ۵۶۴ فایل ورودی در manifest آمده است؛ status ابزار ۵۵۲ working-tree files، صفر صفحه، full-text و semantic ناموجود، و مدل/provider تهی گزارش کرد. ابزار هنگام export عدد ۲ container، ۲۱ component و ۹۸ relation گزارش کرد، ولی شمارش مستقل DSL فقط ۴۴ خط رابطه با `->` می‌یابد؛ علت تفاوت تأیید نشده است. این اعداد تابع تحلیل ابزارند؛ Dart و بعضی وابستگی‌ها ممکن است شناسایی نشوند. تاریخچهٔ mirror فقط یک commit مصنوعی است. محتوای `.claude/settings.local.json`، گزارش خام M113، داده‌های واقعی، فایل‌های ignored و بخش‌های خارج manifest پوشش ندارند. این گراف جای source، امنیت، قرارداد API، معماری واقعی یا آزمون نیست و نبود رابطه اثبات نبود وابستگی نیست.

### بازسازی امن اختیاری

ابتدا مسیرها و محرمانگی را دستی مرور کنید. به جای اجرای ابزار روی working tree اصلی، یک کپی فیلترشدهٔ بدون secret و بدون تاریخچهٔ واقعی بسازید؛ با manifest بالا scope را بسنجید، کپی را جداگانه اسکن کنید، و فقط داخل آن Git مصنوعی راه‌اندازی کنید. نمونهٔ زیر **پس از ساخت و بازبینی دستی** آن کپی است؛ هیچ فایل یا hook اصلی را تغییر ندهید:

```bash
# نمونه، پس از تعیین مسیرهای واقعی خودتان؛ با HOME خالی و بدون credential
python3 -m venv /path/to/isolated-repowise-venv
/path/to/isolated-repowise-venv/bin/pip install 'repowise==0.61.0'
# ابتدا کپی پالایش‌شده را در /path/to/safe-mirror بسازید و secret-scan کنید.
# سپس داخل همان کپی یک Git مخزن مصنوعی با یک snapshot بسازید.
# HOME را به یک پوشهٔ خالیِ اختصاصی و PATH را به ابزارهای لازم محدود کنید.
export REPOWISE_OFFLINE=1 REPOWISE_SKIP_EDITOR_SETUP=1 DO_NOT_TRACK=1
repowise init /path/to/safe-mirror --yes --mode fast --no-prose --no-hook --no-distill-hook --no-editor-setup --no-agents --no-codex --no-claude-md --no-seed
repowise status /path/to/safe-mirror --no-workspace
(cd /path/to/safe-mirror && repowise export . --format structurizr --standalone --components --no-externals -o /path/to/reviewed-output.dsl)
```

دستورها الگو هستند نه نصب آزموده‌شده در سیستم دیگر. `--yes` بدون پرچم‌های محدودکننده می‌تواند hook/editor را تغییر دهد؛ `update --full` می‌تواند scope و تولید را تغییر دهد. هر خروجی، cache، مسیر مطلق، محتوا و metadata را قبل از انتشار بازبینی و secret-scan کنید. خروجی‌های خام index و شواهد را در Git نگذارید. گراف دستی [C4](architecture/c4.md)، [نقشهٔ ماژول‌ها](architecture/module-map.md)، [هدف ابری/مالی](architecture/cloud-finance-access.md) و [جریان‌های OV](architecture/oss-value-flows.md) وضعیت‌ها را جداگانه مشخص می‌کنند.

## ۴. آنچه عمداً منتقل نشده است

تنظیم محلی `.claude/settings.local.json`، داده‌های خام `finn/reports/rea/m113/`، cache/venv و هر secret عمداً منتشر نشده‌اند. نسخهٔ منتشرشدهٔ `finn/reports/rea/m113-review.md` خلاصهٔ پالایش‌شده است؛ اصل گزارش در workspace پیشین دست‌نخورده ماند. raw M113 حتی با بررسی منشأ هش‌ها برای انتشار عمومی تأیید نشده است. اگر شواهد خام لازم‌اند از مالک مسیر خصوصی و امن انتقال بخواهید؛ حذف آن‌ها از Git به معنای نابودی یا تأیید امنیت محتوایشان نیست. در هر نشست دوباره وجود و SHA فایل‌ها و CI را بررسی کنید؛ هیچ انتقالی ادعای بازیابی همهٔ داده‌های خصوصی را ندارد.
