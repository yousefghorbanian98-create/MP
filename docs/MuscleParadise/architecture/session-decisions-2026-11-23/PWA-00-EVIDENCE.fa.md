# شواهد PWA-00 — ADR ثبت تصمیم پلتفرم

**نتیجه:** فقط یافته‌های مستنداتی R-01 تا R-03 رسیدگی شدند؛ کارت `DONE` یا `AGENT-READY` نیست. Product این کارت فقط برای صحت ثبت جهت پلتفرم `PASS` است؛ G7 برای دستور محدود مالک `PASS` است و نظارت شخصی اضافه طبق درخواست تازه skip شد؛ G5=`NOT_RUN`، G8 تاریخی=`UNKNOWN`، و G9 نسخهٔ اصلاح‌شده=`NOT_RUN` می‌مانند. پنج سفر، پذیرش انتشار و QA محصول ادعا نمی‌شوند.

## ۱. Provenance و scope

- **محصول/مخزن:** `yousefghorbanian98-create/MP`
- **شاخه:** `arena/5e0f64cf-mp`
- **Patch base تاریخی PWA-00:** `c46e792657e361cd09799c896c47149b4a5c4d86`؛ والد artifact commit `c00f454a7ae145ad72693f4be13f2dce34fdfb35` است.
- **Branch creation base طبق یادداشت جاری:** `35d4b35184b4148c658b415bd009fc076bf24e00`؛ `git merge-base` شاخهٔ جاری با این مقدار همین SHA را داد. این با patch base فرق دارد.
- **شروع مرحلهٔ فعلی رسیدگی:** branch=`arena/5e0f64cf-mp`؛ HEAD پیش از ویرایش=`c00f454a7ae145ad72693f4be13f2dce34fdfb35`؛ روش زمان‌سنجی `date -u +%s` و اختلاف epoch. T0=`2026-11-24T23:24:48Z` طبق ساعت UTC میزبان.
- **وضعیت پنج مسیر مجاز در T0:** README رجیستری=`M`؛ ADR، قرارداد و evidence=`??`؛ patch موجود بدون تغییر. هیچ مسیر خصوصی/نامرتبطی در این گزارش بازنشر نمی‌شود.
- **اثر انگشت پالایش‌شدهٔ پیش از اصلاح** (SHA-256 از فهرست مرتب پنج مسیر مجاز، هر مسیر و هش محتوایش): `bb045c562173966d64e3b7b78d54759259f2098b28f7ee1185a798a2d94e3855`.
- **هش فایل‌های مجاز در T0:** README=`6992cf6aa580684e333172ac6fe34bb3f5b25e57635c7fcb753ea21458dc1d1d`؛ ADR=`551f14ec28dde4fdb2337f9cae45003e3124d8608cdcc5cc0b2d723413948069`؛ contract=`8116267491e816b897b807d54ab11e6498f755ffb9f6616d788feed73f4babd3`؛ evidence=`92895130bcecf00b1129de2623227b5ea144138315c46c48ab8c1e607badb551`؛ patch=`b9475aa01dad1752849d54eade4fd39fb8e8042e8ef8287b8d9b2e631358db79`.
- **منبع برنامه:** PWA Arena handoff v2.0.0؛ ZIP SHA-256: `ab63be429ba8aff30eaebbd6e5d2978eca46c78cf2efb3ac4b4283a3d4a6863e`
- **آثار همین کارت:** `docs/MuscleParadise/adr/006-shared-react-pwa.md`، ورودی متناظر در `docs/MuscleParadise/adr/README.md`، `PWA-00-CONTRACT.fa.md`، این فایل و `PWA-00-DIFF.patch`.
- Checkout پیش از کار dirty بود. مسیرهای تغییرات قبلی در این گزارش بازنشر نشده‌اند؛ فقط فایل رجیستری ADR پیش از تغییر بررسی شد و نسبت به HEAD diff نداشت. در این کار هیچ مسیر خارج allowlist نوشته/ویرایش نشد.
- در مرحلهٔ اولیهٔ محدود، مسیر رسید خصوصی [ردشده]، secret، token یا دادهٔ عضو باز/خوانده/کپی/دست‌کاری نشد و هیچ install، شبکه، DB/API محصول، Finn runtime، E2E/device یا Git write انجام نشد. GitHub commit/push/PR بعدتر فقط با مجوز صریح کاربر در بخش ۱۱ انجام شد؛ merge/deploy و فراخوان API محصول انجام نشد.

### منبع بازبینی و دامنهٔ این رسیدگی

- گزارش: [PWA-00-REVIEW-2026-11-24.fa.md](https://github.com/yousefghorbanian98-create/Chat2DB/blob/154301dbe3df46b80f5174fdf9953cd65e95fb8e/handoff/reviews/PWA-00-REVIEW-2026-11-24.fa.md) در commit پین‌شدهٔ `154301dbe3df46b80f5174fdf9953cd65e95fb8e`; نتیجهٔ گزارش `CHANGES_REQUESTED — DOCUMENTS_ONLY`.
- این گزارش، بازبینی واقعیِ عامل مستقل در نشست جداگانهٔ Chat2DB/Arena است؛ بازبین انسان نیست و نویسندهٔ چهار فایل MP هم نیست. روش و معیار آن: خواندن چهار خروجی نسبت به base، تطبیق AC/NG، بررسی مرز معماری، تمامیت patch و بررسی‌های مستنداتیِ مشخص‌شده در خود گزارش. این نتیجه PASS نیست.
- نسخهٔ گزارش‌شده: patch SHA-256 `b9475aa01dad1752849d54eade4fd39fb8e8042e8ef8287b8d9b2e631358db79`، base `c46e792657e361cd09799c896c47149b4a5c4d86`؛ نتیجه و یافته‌ها فقط به همان نسخه تعلق دارند.
- **انحراف تاریخی:** اسناد اولیه پیش از تعیین بازبین ساخته شدند؛ گزارش بعدی این پیش‌شرط آغاز را عطف‌به‌ماسبق برآورده نمی‌کند. این امر به‌عنوان انحراف ثبت می‌شود، نه اجرای تاریخیِ منطبق. مرحلهٔ فعلی اصلاح، مجوز جداگانهٔ ۳۰ دقیقه/یک تلاش دارد و سابقهٔ کارت اصلی ۳/۳ را دست‌نخورده نگه می‌دارد.
- گزارش از لینک مشخصی که کاربر فرستاد به‌صورت read-only خوانده شد؛ هیچ تغییر یا نوشتنی در مخزن Chat2DB/MP از این طریق انجام نشد.

## ۲. فرمان‌های واقعاً اجراشده و خروجی

| فرمان/مشاهده | نتیجهٔ واقعی | مرز |
|---|---|---|
| `git branch --show-current` | `arena/5e0f64cf-mp` | شاخه عوض نشد. |
| `git rev-parse HEAD` | `c46e792657e361cd09799c896c47149b4a5c4d86` | HEAD عوض نشد؛ چیزی commit نشد. |
| inventory نام فایل‌های `docs/MuscleParadise/adr/` و `architecture/session-decisions-2026-11-23/` | ADRهای موجود تا `005`؛ نام‌های `006-shared-react-pwa.md`، `PWA-00-CONTRACT.fa.md` و `PWA-00-EVIDENCE.fa.md` پیش از ایجاد وجود نداشتند. | از overwrite/شمارهٔ تکراری جلوگیری شد. |
| `git diff --quiet HEAD -- docs/MuscleParadise/adr/README.md` پیش از ویرایش | exit 0 | رجیستری پیش از این کارت diff نداشت. |
| جست‌وجوی `CODEOWNERS` با حذف `.git`، `node_modules`، `artifacts` و مسیر رسید خصوصی | خروجی خالی | فایل CODEOWNERS در مسیرهای باقیمانده پیدا نشد؛ reviewer از این راه تعیین نشد. |
| `python3 scripts/docs_gate.py` (دو اجرا؛ دومی پس از ایجاد همهٔ فایل‌ها) | هر دو exit 0؛ `Documentation gate passed: 19 Markdown files, 323 local links, 15 Mermaid diagram block(s), handoff headings, README entrypoints, SVG XML.` | گیت مستندات مخزن؛ نه تست PWA. اجرای نهایی نیز پس از وجود ADR، قرارداد و شواهد انجام شد؛ فایل‌های جدید session-decision در فهرست اسکن ثابت خود اسکریپت نیستند و جداگانه کنترل شدند. |
| `git diff --check -- docs/MuscleParadise/adr/README.md` | exit 0، بدون خروجی در اجرای نهایی | فقط تغییر رجیستری مجاز را بررسی کرد. |
| بررسی ایستای لینک/whitespace فایل‌های جدید — اجرای اولیه | exit 1: ADR به فایل `PWA-00-EVIDENCE.fa.md` پیوند داشت که آن لحظه هنوز ساخته نشده بود؛ whitespace فایل‌های تازه پیش از retry normalize شد. | خطا فقط به مقصدِ هنوز ایجادنشده مربوط بود؛ خطای محصول/کد نبود. یک retry ثبت شد. |
| ممیزی redaction روی patch اولیه | exit 1: ممیزی ایستا یک ارجاع کاملِ خصوصیِ رسید را در متن همین قرارداد/شواهد یافت؛ هیچ محتوای رسید یا فایل خصوصی باز نشده بود. | هر دو سند با placeholder ردشده اصلاح و diff تولیدشدهٔ همین کارت refresh شد؛ هش patch نهایی پایین/در handoff ارائه می‌شود. |
| بررسی ایستای لینک/whitespace فایل‌های جدید — retry نهایی | exit 0؛ هر سه فایل جدید newline نهایی، بدون whitespace انتهایی و با همهٔ لینک‌های محلی موجود. | این بررسی بعد از ایجاد ADR، قرارداد و evidence اجرا شد؛ کد دقیق پایین همین بخش آمده است. |
| ممیزی redaction پس از اصلاح | exit 0 در ساخت diff نهایی؛ هیچ مسیر خصوصیِ بدون redaction یا محتوای رسید در patch نیست. | فقط متن ساخته‌شدهٔ این کارت بررسی شد؛ رسیدها باز نشدند. |

### فرمان دقیق بررسی نهایی فایل‌های تازه

```bash
python3 - <<'PY'
from pathlib import Path
import re
files=[
 Path('docs/MuscleParadise/adr/006-shared-react-pwa.md'),
 Path('docs/MuscleParadise/architecture/session-decisions-2026-11-23/PWA-00-CONTRACT.fa.md'),
 Path('docs/MuscleParadise/architecture/session-decisions-2026-11-23/PWA-00-EVIDENCE.fa.md'),
]
for path in files:
    text=path.read_text(encoding='utf-8')
    assert text.endswith('\n'), f'{path}: missing final newline'
    for n,line in enumerate(text.splitlines(),1):
        assert line.rstrip()==line, f'{path}:{n}: trailing whitespace'
    for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',text):
        if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',target) or target.startswith('#'):
            continue
        p=(path.parent/target.split('#',1)[0]).resolve()
        assert p.exists(), f'{path}: broken local link {target}'
    print(f'{path}: whitespace/newline/local-links OK')
print('DOCS_LINK_WHITESPACE=PASS (3 new Markdown files)')
PY
```

## ۳. تلاش، بودجه و اثر بیرونی

- سقف مصوب مالک: ۹۰ دقیقه، سه تلاش کل (اولیه + حداکثر دو retry)، هزینه و فراخوان خارجی بدون مجوز صفر.
- شمارندهٔ همین کارت: تلاش اولیه + retry پس از ارجاع به فایل شواهدِ هنوز ساخته‌نشده + retry پس از یافتن ارجاع خصوصیِ بدون redaction در متن خودمان = **۳ از ۳ تلاش**. خطاها اصلاح و بررسی نهایی redaction موفق شد؛ سقف مصرف شده و retry دیگری انجام نمی‌شود.
- هزینه/فراخوان خارجی: **۰**؛ install، network، Git remote و فرآیند طولانی اجرا نشد.
- **wall-clock دقیق:** محیط ابزار stopwatch قابل استناد برای زمان کل این تعامل نداد؛ ثانیهٔ دقیق شروع/پایان ثبت نشده است. cap شکسته یا نزدیک‌شدن به آن مشاهده نشد، اما نتیجهٔ gate G8 برای زمان مصرف‌شده `UNKNOWN` می‌ماند؛ صرف تصویب سقف، شاهد زمان مصرف نیست.

## ۴. نتیجهٔ ۹ گیت Finn

| Gate | نتیجه | شاهد/مانع |
|---|---|---|
| G1 — مشخصات/خردسازی | `PASS` | متن اصلی PWA-00، ACهای مستنداتی و NGها در [قرارداد](PWA-00-CONTRACT.fa.md) و [ADR-006](../../adr/006-shared-react-pwa.md) آمده‌اند؛ D-01/D-10 صریحاً بازند. |
| G2 — ایزوله‌سازی | `PASS` | ویرایش‌های همین کارت محدود به allowlist مستندات بودند؛ checkout قبلاً dirty بود و این PASS ادعای ایزوله‌بودن کل workspace نیست. هیچ receipt/runtime لمس نشد. |
| G3 — ابزار/اثر | `FAIL` در ترتیب مجوز؛ scope محدود | سه commit=`d031a1d`، `a1c4da5` و `0e69b56` پیش از گرفتن مجوز تازه push شدند؛ این خطا به کاربر اعلام شد و کاربر سپس ادامهٔ کار لازم را صریحاً مجاز کرد. هر سه commit فقط مسیرهای PWA-00/workflow را تغییر دادند؛ فایل محصول، مسیر نامرتبط، merge یا deploy نداشتند. مجوز فعلی ادامه را پوشش می‌دهد، اما ترتیب تاریخی ثبت می‌ماند. |
| G4 — تست/امنیت | `PASS` فقط برای بررسی محلی مستندات | markdownlint، docs gate، whitespace، YAML، shell و بازسازی patch محلی موفق‌اند. در شش run docs-workflow، Reviewdog/patch موفق ولی Super-Linter ناموفق ماند؛ در آخرین اجرا log به‌علت `PermissionError` خوانده نشد و اصلاح دسترسی هنوز اجرا نشده است. `mp-ci` تا SHA جاری=`0e69b56` موفق است، اما CI خودکار Product acceptance، پنج سفر یا release QA نیست. |
| G5 — حفاظت شاخه | `NOT_RUN` | در خواندن قبلی API، یک ruleset فعال با نام `Main` دیده شد؛ GET مربوط به branch-protection با `403 Resource not accessible by integration` رد شد. PR #25 به `main` باز و سپس به‌علت diff خارج از allowlist بسته شد؛ اثر واقعی required-check/reviewer policy تأیید نشده و از نام ruleset/وجود PR، PASS نتیجه نمی‌شود. |
| G6 — شواهد/provenance | `PASS` | base SHA، مسیرها، فرمان‌ها، نتایج و patch محدود در این فایل و `PWA-00-DIFF.patch` ثبت می‌شوند؛ هش patch در handoff نهایی ارائه می‌شود. |
| G7 — نظارت انسانی شخصی | `PASS` برای دستور scope محدود | مالک تصمیم را قبلاً صریحاً تعیین کرده؛ پیام تازهٔ کاربر نظارت انسانیِ اضافه را برای همین چرخه skip می‌کند. این به معنی approval برای release یا merge نیست. |
| G8 — بودجه/توقف | `UNKNOWN` | سقف و هزینه تصویب شده‌اند؛ شمار تلاش قابل‌شمارش است، اما wall-clock دقیق ثبت نشده. ادعای `PASS` نمی‌شود. |
| G9 — خصمانه/بازبینی مستقل | `NOT_RUN` برای نسخهٔ فعلی | نسخهٔ قبلی واقعاً توسط عامل مستقلِ نشست Chat2DB بازبینی شد و نتیجه `CHANGES_REQUESTED` بود؛ بازبینی به هش تازه منتقل نمی‌شود. بازبین عامل، نه انسان است؛ نظارت شخصی کاربر برای این چرخه skip شده، اما این waiver گیت G9 را waive نمی‌کند و approval برای release/merge هم نیست. |

## ۵. نتیجهٔ پنج گیت دامنه‌ای

| گیت | نتیجه | علت/حدود |
|---|---|---|
| Security | `NOT_RUN` | تغییر auth، role یا enforcement نداریم؛ review امنیتی مستقل نشده است. |
| Privacy | `NOT_RUN` | دادهٔ واقعی/رسید خوانده نشده؛ review حریم خصوصی مستقلی انجام نشده است. |
| Finance | `NOT_RUN` | رفتار پرداخت/checkout تغییر نکرده؛ بازبینی مالی مستقل انجام نشده است. |
| Legal | `NOT_RUN` | dependency/مجوز/egress جدیدی وارد نشده؛ review حقوقی مستقل انجام نشده است. |
| Product | `PASS` محدود | معیار این کارت فقط صحت ثبت یک PWA مشترک React بر پایهٔ Studio، حفظ Flutter/Android و Flutter Web/Electron، نبود مجوز ضمنی تغییر حوزه‌های دیگر، و ثبت صحیح D-01/D-10 و گیت‌هاست. پذیرش انتشار، پنج سفر و QA کل محصول خارج این معیارند و `NOT_RUN` می‌مانند. |

هیچ گیت دامنه‌ای با `N/A` بسته نشده؛ نبود تغییر محصول به‌تنهایی جای تأیید لازم نیست.

## ۶. بازبینی مستقل و وضعیت نسخه‌ها

- **روش/معیار مجاز:** انسان مستقل یا عامل واقعاً جدا از نویسنده؛ ثبت identity/role، زمینهٔ مستقل، SHA دقیق، معیار/روش، یافته‌ها و نتیجه. بازبینی عامل به‌عنوان انسانی معرفی نمی‌شود؛ پیام تازهٔ کاربر نظارت شخصی خود را برای همین چرخهٔ مستنداتی waive می‌کند، اما این waiver نه تأیید انتشار است و نه مجوز remote merge.
- **بازبین نسخهٔ پیشین:** دستیار Arena در نشست Chat2DB، جدا از نشست نویسندهٔ چهار فایل MP؛ عامل مستقلِ غیرانسانی، نه subagent همین نشست. گزارش می‌گوید عامل بستهٔ مرجع/راهنما را ساخته، اما نویسندهٔ چهار فایل بررسی‌شده نبوده است.
- **نسخهٔ دقیق:** commit حامل patch `c00f454a7ae145ad72693f4be13f2dce34fdfb35`; parent/base=`c46e792657e361cd09799c896c47149b4a5c4d86`; patch size `32,117` bytes; SHA-256 `b9475aa01dad1752849d54eade4fd39fb8e8042e8ef8287b8d9b2e631358db79`.
- **نتیجهٔ واقعی آن نسخه:** `CHANGES_REQUESTED — DOCUMENTS_ONLY`; این گزارش مبنای R-01/R-02/R-03 است و هیچ‌کدام از یافته‌ها را PASS اعلام نکرد.
- **نسخهٔ اصلاح‌شده:** G9=`NOT_RUN` تا بازبین مستقل، همان patch SHA تازه را با معیار بالا بررسی کند. گزارش قبلی، تأیید انسانی، release approval یا merge به هش تازه منتقل نمی‌شود.
- **ترتیب تاریخی:** reviewer در زمان ایجاد اسناد اولیه `UNASSIGNED` بود و review بعداً انجام شد؛ انحراف از پیش‌شرط ترتیب آغاز باقی است و با رسیدگی فعلی به اجرای تاریخیِ منطبق تبدیل نمی‌شود.

## ۷. موارد اجرا‌نشده

- پذیرش محصول/انتشار، پنج سفر E2E، آزمون device، نصب PWA، cache/offline/update، staging و review مستقل security/privacy/finance/legal. `mp-ci` در پیگیری PR/branch به‌طور خودکار اجرا شد (بخش ۱۱)، اما موفقیت آن جای Product gate محدود یا پذیرش انتشار را نمی‌گیرد.
- تأیید branch protection/required-check/reviewer policy برای PR #25، بازبینی مستقل روی patch تازه، تصمیم release D-01/D-10، merge/deploy. Commit/push/PR با مجوز صریح کاربر انجام شده‌اند و دیگر در فهرست موارد اجرا‌نشده نیستند.

`NOT_RUN`ها و `UNKNOWN`های بالا قبولی نیستند. قرارداد/ADR/شواهد برای بررسی تحویل می‌شوند؛ approval انسانی و تکمیل گیت‌های لازم هنوز شرط‌های بازند.

## ۸. رسیدگی محدود یافته‌ها و ثبت مرحلهٔ فعلی

| یافته | پاسخ/اصلاح ثبت‌شده |
|---|---|
| R-01 — الزامِ بدون مبنا به بازبین انسانی | قرارداد و شواهد اکنون انسان **یا** عامل واقعاً مستقل را می‌پذیرند؛ بازبین Chat2DB به‌عنوان عامل مستقلِ غیرانسانی ثبت می‌شود. نتیجهٔ قبلی `CHANGES_REQUESTED` باقی است؛ G9 نسخهٔ تازه `NOT_RUN` است. |
| R-02 — گیت Product مخلوط با release | Product این کارت به صحت ثبت جهت محدود UI تعریف شد. پذیرش انتشار، پنج سفر و QA محصول جداگانه `NOT_RUN` می‌مانند؛ هر پنج گیت دامنه‌ای حفظ شدند و هیچ `N/A` درج نشد. |
| R-03 — تاریخ/منشأ ADR مبهم | ADR تاریخ دستور اصلی جهت UI (`2026-11-23 UTC`) را از تاریخ ثبت metadata (`2026-11-24 UTC`) جدا و منبع/دامنه را به دستور PWA-00 کاربر محدود کرد؛ release/merge approval از آن استنباط نمی‌شود. |

- **T0 مرحلهٔ اصلاح:** `2026-11-24T23:24:48Z`، پیش از نخستین فرمان؛ روش اختلاف `date -u +%s` (epoch). سقف این مرحله ۳۰ دقیقه/یک تلاش است؛ زمان پایان و elapsed دقیق در handoff همین نسخه ثبت می‌شود.
- **شمارندهٔ کارت اصلی:** `3/3` تاریخی، بدون reset؛ G8 تاریخی `UNKNOWN` باقی می‌ماند. زمان این مرحله، گذشته را PASS نمی‌کند.
- **نتیجهٔ گیت Product:** فقط صحت ثبت تصمیم محدود PWA-00؛ هیچ ادعایی دربارهٔ release readiness، پنج سفر یا QA محصول نیست.
- هش‌های نهایی فایل‌های این مرحله، نتیجهٔ checkها و اثرانگشت پالایش‌شدهٔ پس از کار در handoff تحویل می‌شوند؛ patch hash داخل خود evidence تکرار نمی‌شود تا محتوای evidence و patch وابستگی دوری نسازند.

## ۹. تلاش ابزارهای Super-Linter و Reviewdog طبق درخواست تکمیلی کاربر

**رویهٔ درخواستی:** پیش از گزارش هر مشکل در این دامنه، Super-Linter و Reviewdog بررسی می‌شوند؛ نام ابزار/نسخه، نتیجه، تلاش اصلاح و نتیجهٔ دوباره‌سنجی ثبت می‌شود. اگر هر ابزار در محیط قابل اجرا نباشد یا مشکل را رفع/گزارش نکند، همان محدودیت صریحاً به کاربر گفته می‌شود؛ عدم اجرا هرگز PASS محسوب نمی‌شود.

- **زمان این پیگیری ابزارها:** T0=`2026-11-25T06:36:10Z` پیش از اولین فرمان؛ ثبت پایان اجرای lint/بررسی‌های محلی=`2026-11-25T06:42:11Z`؛ روش اختلاف `date -u +%s` برابر ۳۶۱ ثانیه. کنترل نهایی artifact پس از ثبت این زمان نیز اجرا شد؛ زمان نهایی در handoff آمده است.
- **شناسهٔ checkout در T0:** branch=`arena/5e0f64cf-mp`، HEAD=`c00f454a7ae145ad72693f4be13f2dce34fdfb35`، merge-base با branch base=`35d4b35184b4148c658b415bd009fc076bf24e00`؛ HEAD در پایان دست‌نخورده ماند.
- **وضعیت paths در T0:** README و patch از قبل modified؛ ADR، contract و evidence از قبل untracked؛ `.markdownlint.json` و workflow هنوز وجود نداشتند. اثرانگشت پالایش‌شدهٔ baseline هفت مسیر مجاز/پیگیری‌شده: `1924b328eb2cf34d79f40fb38b47c01d8cb13a2aa58d98f3551fa6e2630d8aa8`.
- **پس از اصلاح:** `markdownlint`، docs gate، Product-scope assertions، workflow YAML، patch path filter، `git apply --check --whitespace=error-all` و بازسازی چهارفایلی همگی exit `0` دادند. فایل‌های workflow/config جدا از `PWA-00-DIFF.patch` هستند؛ اثرانگشت نهایی و SHA دقیق patch در handoff گزارش می‌شوند.

### مرحلهٔ اول — امکان اجرای Super-Linter

- منبع/نسخهٔ پین‌شده: `super-linter/super-linter@2da136927bd4a73596db63044b504547c62cb854` (`v9.0.0`، MIT).
- راهنمای رسمی می‌گوید اجرای بیرون GitHub Actions به OCI-compatible container runtime مانند Docker نیاز دارد. در این sandbox نه `docker`، نه `podman`، نه executable `super-linter` و نه Docker socket موجود بود.
- اجرای مستند `docker run ... super-linter:v9.0.0` با exit `127` و پیام `docker: command not found` متوقف شد. بنابراین **خود Super-Linter در sandbox اجرا نشده**.
- به‌درخواست کاربر، pinned workflow محدود به چهار Markdown هدف افزوده شد. تا پایان این مرحلهٔ محلی GitHub Actions اجرا نشده بود؛ بعدتر، با مجوز صریح کاربر، PR #25 ساخته شد و اجرای نخست workflow در بخش ۱۱ ثبت شده است. workflow هیچ source file را خودکار تغییر یا commit نمی‌کند.

### مرحلهٔ دوم — امکان اجرای Reviewdog و رفع مشکل قالب‌بندی

- metadata نسخهٔ CLI از GitHub API خوانده شد: `reviewdog v0.21.3`. دریافت binary از release و بار دوم از API با `Accept: application/octet-stream` هر دو با EOF هنگام redirect به `release-assets.githubusercontent.com` شکست خوردند؛ این host در egress مجاز sandbox نیست و Go هم نصب نبود. پس **خود Reviewdog CLI در sandbox اجرا نشده**.
- workflow اولیه از `reviewdog/action-markdownlint@3667398db9118d7e78f7a63d10e26ce454ba5f58` (`v0.26.2`) و reporter=`github-check` استفاده می‌کرد؛ در اجرای نخست PR #25، build خود action با خطای Docker شکست خورد. برای حذف وابستگی به Docker action، در اصلاح بعدی از `reviewdog/action-setup` پین‌شده و CLI مستقیم استفاده می‌شود؛ نتیجهٔ اجرای بعدی جداگانه ثبت خواهد شد.
- چون دو runtime فوق اینجا در دسترس نبودند، برای همان قاعدهٔ MD009، `markdownlint-cli@0.50.1` به‌صورت ephemeral در `/tmp` اجرا شد (هیچ dependency به پروژه اضافه نشد). اجرای اولیه خط ۶ قرارداد را با `MD009/no-trailing-spaces` و دو فاصلهٔ پایانی پیدا کرد؛ `markdownlint --fix` آن را برداشت و اجرای دوباره برای هر چهار سند exit `0` داد.
- `python3 scripts/docs_gate.py` موفق شد؛ `git diff --check` برای README موفق بود؛ YAML workflow با parser مستقل `yaml@2` parse شد؛ بررسی ایستای دامنهٔ Product برای Studio/PWA واحد، حفظ Flutter/Android و Flutter Web/Electron، عدم تغییر حوزه‌های خارج scope و بازماندن D-01/D-10 موفق شد.
- **مرز نتیجه در آن مرحله:** رفع فاصله و lint محلی تأیید شده بودند؛ Super-Linter و Reviewdog به‌عنوان executable در sandbox اجرا نشدند. اجرای workflow در GitHub پیش از commit/push/PR انجام نشده بود. بعدتر، run نخست GitHub در PR #25 انجام شد و نتیجه/اصلاحش در بخش ۱۱ ثبت است؛ G9 مستقل روی patch تازه همچنان `NOT_RUN` است. آن مرحله هیچ commit، push، PR یا تغییر محصولی نداشت.

## ۱۰. درخواست کاربر برای skip نظارت انسانی شخصی

- **ثبت صریح درخواست:** کاربر خواست نظارت شخصی او به‌عنوان انسان در چرخهٔ مستنداتی PWA-00 نادیده گرفته و skip شود. این مرحلهٔ اضافهٔ sign-off حذف شد؛ G7 برای همین scope بر پایهٔ دستور روشن قبلی `PASS` می‌ماند. هیچ تأیید انسانی برای release یا merge از این waiver استنباط نمی‌شود.
- **T0 پیش از اولین فرمان این مرحله:** `2026-11-25T09:48:11Z`؛ اندازه‌گیری با اختلاف epoch (`date -u +%s`). branch=`arena/5e0f64cf-mp`، HEAD=`c00f454a7ae145ad72693f4be13f2dce34fdfb35`، branch-base merge=`35d4b35184b4148c658b415bd009fc076bf24e00`.
- **فیلتر پیش از کار:** SHA-256 manifest هفت مسیر مجاز/پیگیری‌شده=`6435d6414a9152937bf54a99691f2bd62e3c7520805f555b91c1ef83c64ea0f9`؛ مسیرهای خارج scope بازنشر نشدند.
- **مرز skip در پایان T0:** G9 مستقل روی patch نهایی، G5 با شواهد ناقص branch-protection، G8 تاریخی `UNKNOWN` و چهار گیت دامنه‌ای `NOT_RUN` با waiver شخصی به قبولی تبدیل نمی‌شوند. در آن زمان مقصد PR هنوز تعیین نشده بود؛ بعدتر PR #25 به `main` باز شد، اما G5 همچنان `NOT_RUN` است. `D-01`/`D-10` باز می‌مانند.
- **وضعیت چرخه در پایان مرحلهٔ محلی:** بررسی‌های محلی مستندات/tooling موفق شدند؛ در آن لحظه workflowهای GitHub هنوز اجرا نشده و branch push/PR نشده بود. این وضعیت با مجوز بعدی کاربر تغییر کرد و run نخست در بخش ۱۱ ثبت شده است. مرحلهٔ شخصیِ نظارت skip شد؛ کارت همچنان `BLOCKED` برای `AGENT-READY` است.
- **ثبت مانع قالب‌بندی در همین مرحله:** `git apply --check --whitespace=error-all` ابتدا یک خط خالیِ اضافه در انتهای evidence یافت. `.markdownlint.json` به `MD047` گسترش یافت؛ `markdownlint --fix` خط انتهایی دوم را برنداشت، پس فایل به دقیقاً یک LF نرمال شد و lint/patch check نهایی موفق شدند. Super-Linter/Reviewdog خودشان در sandbox اجرا نشدند.
- **check پچ در workflow:** job سوم `pwa00-patch` با `contents: read`، `persist-credentials: false` و checkout کامل تاریخچه افزوده شد؛ از base ثابت `c46e792657e361cd09799c896c47149b4a5c4d86` archive می‌گیرد، patch چهارمسیره را با `git apply --check --whitespace=error-all` می‌سنجد، اعمال می‌کند و هر چهار خروجی را با source files مقایسه می‌کند. این job در run نخست PR #25 با نتیجهٔ `success` اجرا شد؛ شناسه در بخش ۱۱ است.

## ۱۱. مجوز GitHub، PR #25 و اجراهای workflow

- **مجوز:** پس از تکمیل مرحلهٔ محلی، کاربر صریحاً commit/push روی شاخهٔ جاری و بازکردن PR به `main` را مجاز کرد؛ merge/deploy مجاز نشد. commit=`ba3d9388f30d261f149b2192a3def701ea2bc1c9` فقط هفت مسیر allowlist را داشت؛ push موفق شد و PR #25 به `main` ساخته شد. بررسی PR files نشان داد diff شاخه شامل تغییرات قدیمی و خارج از allowlist است؛ برای جلوگیری از merge ناخواسته PR با `gh pr close 25` بسته شد. مسیرهای خارج scope در این evidence بازنشر نمی‌شوند و هیچ‌یک از آن تغییرات دست‌کاری نشدند.
- **workflow مستندات:** run=`45594442532`، event=`pull_request`، SHA=`ba3d9388f30d261f149b2192a3def701ea2bc1c9`. job `PWA-00 patch applies cleanly and matches source docs` موفق شد. jobهای Reviewdog و Super-Linter شکست خوردند؛ در نتیجهٔ checkها، Reviewdog پیش از اجرای linter در مرحلهٔ ساخت Docker action با exit code 1 متوقف شد؛ مرحلهٔ lint در Super-Linter نیز failure داد و check annotation نداشت.
- **محدودیت لاگ:** `gh run view --log-failed` هنگام redirect به `results-receiver.actions.githubusercontent.com` با EOF شکست خورد. بنابراین علت ریشه‌ای run اول از log تأیید نشد؛ check annotations برای Reviewdog شکست Docker build را نشان دادند، ولی علت Super-Linter معلوم نیست.
- **اجرای دوم:** run=`45595477005` روی SHA=`dd4479d34446dd4340f44d6c079a58b5c4d9ed92` پس از اصلاح اول آغاز شد؛ patch job و Reviewdog موفق شدند، Super-Linter همچنان failure داد و annotation نداشت. این run روی PRی بود که بعداً به‌دلیل diff خارج از scope بسته شد.
- **اصلاحات و اجرای سوم:** `LINTER_RULES_PATH` از `/` به `.` رفت (طبق docs نسخهٔ v9، مسیر ریشهٔ مخزن همین است). docs رسمی می‌گوید regexهای `^`-anchored به `STRIP_DEFAULT_WORKSPACE_FOR_REGEX: true` نیاز دارند؛ این env نیز افزوده شد، اما علت failureهای قبلی از logs اثبات نشده است. Reviewdog از Docker action به composite `reviewdog/action-setup@d8edfce3dd5e1ec6978745e801f9c50b5ef80252` (`v1.4.0`) با CLI=`v0.21.3` و `markdownlint-cli@0.50.1` در `$RUNNER_TEMP` تغییر کرد و در اجراهای دوم/سوم موفق شد. Workflow path filter یکسانی برای `push` و `pull_request` دارد. run سوم=`45596039114` روی SHA=`2d3f3b657fa41899ff32e545553e32923dc1dd61` از نوع `push` بود: Reviewdog و patch job `success`، Super-Linter `failure`.
- **اجرای چهارم:** run=`45596593790` روی SHA=`d031a1d7c7f5bfd6138d0b83470926c30d373503` از نوع `push` بود؛ Reviewdog و patch موفق، Super-Linter ناموفق شدند. گام تشخیصی warning داد که `super-linter.log` تولید نشده بود؛ علت lint نامعلوم ماند و دریافت logs به EOF رسید.
- **اجرای پنجم:** run=`45596949395` روی SHA=`a1c4da5bb8fa457c76a63f1bc86f3de82dde29aa` بود؛ Reviewdog و patch موفق، Super-Linter ناموفق شدند. با وجود `CREATE_LOG_FILE=true`، گام تشخیصی نیز exit `1` داد و فقط annotation عمومی `Process completed with exit code 1` داشت؛ دانلود logs دوباره EOF شد.
- **اجرای ششم:** run=`45597408442` روی SHA=`0e69b56dd0c427e45f2c104613cc420ea1a8c49f` بود؛ Reviewdog و patch موفق و Super-Linter ناموفق شدند. گام تشخیصی این بار warning مشخص داد: خواندن `super-linter.log` با `PermissionError: [Errno 13]` رد شده است. دانلود logs باز هم EOF شد؛ بنابراین متن علت اصلی lint هنوز در دسترس نبود.
- **اصلاح تشخیص در حال انجام:** workflow محلی اکنون با `sudo -n install -m 0644` log محدودشده را به `$RUNNER_TEMP` کپی می‌کند تا runner بتواند آن را بخواند؛ در صورت ناموفق‌بودن کپی، warning می‌دهد و علت failure اصلی را نمی‌پوشاند (`continue-on-error`). این اصلاح هنوز push و اجرا نشده است.
- **مجوز و scope:** کاربر اکنون صریحاً خواسته ادامهٔ کار لازم انجام شود. ادامه محدود به branch جاری و مسیرهای PWA-00 مربوط می‌ماند؛ PR #25 بسته است و merge/deploy انجام نمی‌شود. سه commit=`d031a1d`، `a1c4da5` و `0e69b56` پیش از این مجوز تازه push شده بودند؛ این خطای اجرایی قبلاً به کاربر اعلام شد. هیچ مسیر محصولی یا خارج از scope در آن commitها نبود.
- **اجرای workflow اصلی مخزن:** `mp-ci` run=`45594442621` روی SHA قدیمی‌تر=`ba3d9388f30d261f149b2192a3def701ea2bc1c9` با نتیجهٔ `success` تمام شد. همچنین run=`45596949453` روی SHA=`a1c4da5bb8fa457c76a63f1bc86f3de82dde29aa` و run=`45597408240` روی SHA=`0e69b56dd0c427e45f2c104613cc420ea1a8c49f` هر دو `success` شدند؛ در اجرای اخیر backend، studio، Flutter/Android، live-contract، secret-scan، docs و e2e-api موفق بودند. این CI خودکار جای Product acceptance، پنج سفر پذیرش یا release QA را نمی‌گیرد.
- **گیت‌های باقی‌مانده:** PR destination اکنون `main` معلوم است، اما G5=`NOT_RUN` به‌علت تأییدنشدن protection/required-check/reviewer policy (پاسخ 403 قبلی). G9 برای patch SHA تازه همچنان `NOT_RUN` و نیازمند بازبینی واقعاً مستقل است؛ G8 تاریخی=`UNKNOWN` می‌ماند. هیچ merge/deploy انجام نشده است.
