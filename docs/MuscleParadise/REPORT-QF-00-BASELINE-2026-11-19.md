# QF-00 — baseline و inventory آغازین پروژه

**تاریخ اجرا:** ۲۰۲۶-۱۱-۱۹ · **شاخه:** `arena/a72fbc61-mp` · **baseline:** `28eea71776793098c05c6d3100ab69bc543c98ba`
**وضعیت:** `IN PROGRESS / GATE BLOCKED` — این گزارش آغاز QF-00 و ثبت شواهد است؛ نه تکمیل inventory همهٔ interactionها، نه تأیید QA مستقل، و نه PASS کل برش.
**مرجع برنامه:** [QF-00 تا QF-32](PLAN-FINN-ECC-MICROLOOPS-QA.md) · [تصمیم‌های محصول](TODO-CLOUD-FINANCE-ACCESS.md) · [صف اجرایی پیشین](TODO-2026-11-16.md).

## ۱. منبع و وضعیت مخزن

- در آغاز `git status --short --branch` فقط شاخهٔ `arena/a72fbc61-mp` را نشان داد؛ فایل tracked تغییرکرده یا untracked وجود نداشت. `HEAD`, `origin/main` و آخرین commit main همگی `28eea71776793098c05c6d3100ab69bc543c98ba` بودند. شاخهٔ مجاز روی origin هنوز وجود نداشت؛ فاصلهٔ baseline با main صفر بود. `git ls-remote --heads origin arena/a72fbc61-mp` خروجی نداشت.
- PRهای ۳، ۴ و ۵ با GitHub API/`gh pr view` به‌ترتیب `MERGED` گزارش شدند: PR ۳ در `a238fd1…`، PR ۴ در `a284041…` و PR ۵ در baseline حاضر `28eea717…`. در checkout فعلی، `PaymentPanel.tsx` همراه آزمون‌های lookup fail-closed/پاک‌کردن انتخاب کهنه موجود است؛ workflow QR پیش از stage/commit آزمون می‌کند و hash فایل‌های آزموده‌شده و blobهای staged را تطبیق می‌دهد؛ `README.md` به `assets/system-architecture.svg` پیوند دارد و asset و `system-atlas.md` tracked هستند.
- CI برای همین baseline: [run 44541693998](https://github.com/yousefghorbanian98-create/MP/actions/runs/44541693998) با نتیجهٔ کلی `success`؛ هر ۸ job دیده‌شده موفق‌اند: secret-scan، docs، backend، Studio، client/flutter، client-pinned، live-contract و e2e-api. گیت client-pinned شامل SDK پین‌شده، analyze، test، Android debug compile و فرمت است. این شاهد فقط برای SHA فوق است.
- مجوز پروژه اختصاصی است. هیچ فایل کلید، دادهٔ عضو، دیتابیس محلی یا artifact خام حجیم در این گزارش قرار ندارد.

## ۲. پیش‌نیازها و امکان استفاده از ابزار

| ابزار | نسخه/شاهد | نتیجه و حد |
|---|---|---|
| Python و Backend | Python `3.11.2`؛ محیط بازتولیدپذیر محلی در `.venv/`؛ `pip install -e 'mp-app/backend[dev]'` موفق | آماده برای تست Backend؛ pyproject بازهٔ حداقلی دارد، lock کامل Python ندارد. وابستگی‌ها در venv نادیده‌گرفته‌شده ماندند. |
| Node و Studio | Node `22.22.3`، npm `10.9.8`؛ `npm ci` موفق طبق `package-lock.json` | آماده. `npm audit` پس از نصب ۴ advisory (۳ moderate، ۱ high؛ Vite مستقیم و Vitest مستقیم/ترانزیتی) نشان داد؛ `npm audit fix` اجرا نشد چون پیشنهاد ارتقا major است. |
| Flutter/Android | `.devcontainer/Dockerfile`: Flutter `3.50.0`, revision `ab2912035e160d9cad6306df307576da6128ebdb`, SHA-256 آرشیو `6ea2d806fd57269ae783e6788e2a81fc26eaad782f1e0d0ff38623bb765ff9f5`; Java 17 در devcontainer؛ Gradle wrapper `9.5.0` | `flutter`, `dart`, `java`, `adb`, `sdkmanager` و Docker در PATH نیستند. ابزار از منبع رسمی خارج از میزبان‌های مجاز egress قابل دریافت نبود؛ نصب حدسی/نامعتبر انجام نشد. CI baseline تست Flutter و Android debug را می‌پوشاند؛ دستگاه فیزیکی `UNKNOWN`. |
| REA | `rea-agents@6.9.0` و Node portable `24.22.3` طبق `install-toolchain.sh`; اجرای CLI `rea --version`=`6.9.0` | واقعاً اجرا شد؛ تحلیل‌ها در §۴. `rea doctor`=`healthy:false`, `environment_healthy:false`: engineهای Hopper/Ghidra/IDA/JADX/Kuna حاضر نیستند و check هویت skill config drift گزارش کرد. هیچ provider یا client مدل پیکربندی نشده بود. خود Node سیستم `22.22.3` حداقل REA (`22.23.4`) را نمی‌رساند؛ CLI با Node portable سازگار اجرا شد. نصب npm با Node سیستم یک هشدار EBADENGINE داد. |
| ECC | pin فایل `.finn/ecc-commit.txt` = `d2ef2680594f9a17526a6e1a2e18b3d242c5d17b`; checkout همین SHA و clean؛ `install-toolchain.sh all` موفق | checkout pinned آماده است؛ اسکریپت هیچ فایل موجود `.claude` را overwrite نکرد (۱ اختلاف skill حفظ شد، صفر فایل افزوده شد). ابزار delegation واقعی در این Agent Mode در دسترس نیست؛ هیچ agent/subagent، reviewer مستقل یا QA مستقل اجرا نشد. خواندن role prompt/consult را اجرای agent حساب نمی‌کنیم. |
| RepoWise | طبق راهنمای شروع `0.61.0` اختیاری | نصب/اجرا نشد: برای پیمایش این inventory ضرورت نداشت؛ نقشه‌های Git-tracked و اجرای واقعی REA کافی بودند. MCP مستقل RepoWise در میزبان قابل استفاده نبود. |
| FINN | چرخهٔ موجود در طرح پروژه | به‌عنوان روش اجرا می‌شود: Forge (baseline/دامنه)، Inspect (کد/قرارداد/REA)، Normalize (ثبت شاهد و رفع اختلاف)، Next (checkpoint/گیت بعدی). FINN بستهٔ نصب جداگانه نیست. |

`install-toolchain.sh all` مسیرها را پیش از اجرا بررسی کرد؛ `.finn/ecc` و `/home/user/toolchain` از قبل وجود نداشتند، `.claude` از قبل شامل فایل‌های محلی بود و دست‌نخورده ماند. اسکریپت Node portable، REA pinned و `.mcp.json` محلیِ ignored را افزود. `.venv/`, `node_modules/`, `.finn/ecc/` و `.mcp.json` وارد Git نمی‌شوند. REA صرفاً در فرایند محلی فراخوانی شد؛ دسترسی MCP برای Agent Mode یا ارسال کد به مدل بیرونی رخ نداد.

## ۳. نقشهٔ اجرایی اولیه از کد همین SHA

| بخش | موجودی مشاهده‌شده | مرز شواهد |
|---|---|---|
| API | FastAPI در `mp-app/backend/app/main.py`, API نسخه‌دار در `api/v1/api.py`; OpenAPI ساخته‌شده از app محلی **۱۲۱ path و ۱۳۷ method-operation**؛ ۱۹ پوشهٔ ماژول backend؛ ۵۲ جدول SQLAlchemy؛ ۲۷ revision Alembic با head=`b19c28d37e46` | در شروع نشست `api/routes.json` فقط path داشت؛ برش کد QF-00 در ادامه آن را با method/path/operationId/tags توسعه داد و تست freshness افزود. artifact همچنان اعلان OpenAPI است، نه permission مؤثر، رفتار runtime، schema validation یا اتصال UI. |
| اعضا / Flutter | Flutter + Riverpod؛ ۱۴ مسیر GoRouter از `/otp`, `/intake`, `/home` تا `today`, `progress`, `profile`; ۴۴ فایل Dart در `lib/`; ۲۸ فایل تست | CI baseline سبز است؛ local Flutter/device در دسترس نیست. inventory interaction هنوز نیازمند تطبیق هر اقدام با API و آزمون واقعی است. |
| کادر / Studio | React + TypeScript + Vite؛ ۱۲ فایل صفحه (۱۱ صفحهٔ protected در `App.tsx` + Login)؛ ۴۵ فایل TS/TSX در `src/`; ۳۴ فایل تست | آزمون/build محلی موفق است؛ roleNav صرفاً UI است و backend authorization شاهد جدا می‌خواهد. شمارش lexical دکمه‌ها به‌تنهایی فهرست اقدام‌ها نیست. |
| دامنه و persistence | ماژول‌های auth, admin, membership, payments, shop, programs, classes, nutrition, assessment, face_id, notification/chat, reporting, population, ai, updates و زیرساخت. تنظیم پیش‌فرض DB در `app/config.py` و Compose برابر SQLite است. | PostgreSQL، backup/restore عملیاتی و مسیر انتشار ابری از این inventory اثبات نمی‌شوند. |
| نقش و مجوز | `security/rbac.py` سیاست Casbin ایستا دارد: `member`, `coach`, `reception`, `manager`, `admin`, `super_admin`; inheritance ثابت و denyهای مالی/گزارش در کد حاضرند. `modules/admin/router.py` برای endpoint نقش، شرط `super_admin` دارد. | دسترسی‌های شخصی/زمان‌دار admin و financial grants به‌عنوان خواستهٔ جدید، در این inventory schema/API مستقلِ اثبات‌شده ندارند؛ مجوز server-side هر route باید در QFهای بعدی بررسی شود. |
| workflowها | ۶ فایل زیر `.github/workflows/`; `ci.yml` شامل backend، Studio، client، pinned Android/debug، docs، live contract و e2e؛ workflowهای release/deploy جدا و مشروط‌اند | وجود workflow به معنی dispatch/deploy/release نیست؛ هیچ deploy، release یا پرداخت واقعی اجرا نشد. |

### عملیات API به تفکیک prefix (اعلامیهٔ قرارداد، نه اثبات مجوز/کارکرد)

| Prefix | عملیات | Prefix | عملیات |
|---|---:|---|---:|
| `admin` | 13 | `ai` | 3 |
| `assessments` | 7 | `auth` | 8 |
| `axis-assessments` | 4 | `chat` | 5 |
| `classes` | 4 | `face` | 10 |
| `health` | 1 | `library` | 2 |
| `members` | 13 | `metrics` | 1 |
| `notifications` | 4 | `nutrition` | 8 |
| `payments` | 17 | `population` | 3 |
| `programs` | 10 | `reports` | 1 |
| `shop` | 21 | `updates` | 1 |
| root | 1 | **جمع** | **۱۳۷** |

این شمارش از `app.openapi()` محلی حاصل شد، نه از گراف معماری. REA قرارداد را با `inspect-api-contract` روی همان OpenAPI محلی اجرا کرد: ۱۲۱ path entry، ۱۳۷ inline operation، صفر `unknown`/diagnostic در محدودهٔ parser. این ابزار `$ref` را resolve نمی‌کند، schema/security را اعتبارسنجی کامل نمی‌کند و عملیات اعلام‌شده را به‌معنی اجرای runtime/authorization نمی‌گیرد.

### نگاشت آغازین حوزه → صفحه/مسیر/تست (کامل نیست)

| حوزه | UI/مسیر کد نامزد | API موجود در قرارداد | شاهد تست موجود در checkout |
|---|---|---|---|
| هویت/عضویت | Flutter `features/auth`, `profile`, `home`; Studio `Login`, `Members` | `/auth/*`, `/members*` | `client/test/session_refresh_test.dart`, `membership_test.dart`; backend `test_m67_studio_auth.py`, `test_ownership.py` |
| تمرین/کلاس | Flutter `today`, `classes`; Studio `Programs` | `/programs*`, `/classes*` | `today_page_test.dart`, `classes_cancel_test.dart`, `programsPage.test.tsx`; backend `test_m74_class_cancel.py` |
| تغذیه | Flutter `nutrition`; Studio `Nutrition` | `/nutrition*`, `/ai/nutrition/*` | `nutrition_food_log_test.dart`, `nutritionPage.test.tsx`; backend `test_m49_food_logging.py`, `test_m78_adaptive_nutrition_client.py` |
| ارزیابی/پیشرفت | Flutter `assessment14`, `bodycomp`, `progress`; Studio `Assessment` | `/assessments*`, `/axis-assessments*` | `assessment14_page_test.dart`, `bodycomp_real_data_test.dart`, `jp7Trend.test.ts`; backend `test_api_contract.py`, `test_m50_jp7_trend.py` |
| حضور/QR | Flutter `checkin`; Studio `CheckIn` | `/face/*`, `/members/me/checkins` | `qr_biometric_gate_test.dart`, `member_checkin_history_test.dart`; backend `test_m65_qr_security.py`, `test_m80_member_checkin_history.py` |
| چت/اعلان | Flutter `chat`, `notifications`; Studio `Chat` | `/chat/*`, `/notifications*` | `member_chat_page_test.dart`, `notifications_page_test.dart`, `chatPage.test.tsx`; backend `test_m51_chat.py`, `test_m75_notifications.py` |
| فروشگاه/کیف‌پول | Flutter `shop`, `wallet`; Studio `Shop` | `/shop*`, `/payments/wallet*` | `shop_page_test.dart`, `shop_orders_receipt_test.dart`, `wallet_history_test.dart`, `shopPage.test.tsx`; backend `test_m59_shop.py`, `test_m83_wallet_ledger.py` |
| مالی/پرداخت | Flutter `wallet`; Studio `Finance`, `PaymentPanel` | `/payments*` | `paymentPanel.test.tsx`, `financePage.test.tsx`; backend `test_payments_deep.py`, `test_sandbox_bank.py`, `test_manual_transfer_policy.py` |

این نگاشت فقط نقطهٔ شروع source/test trace است؛ وجود دو نام کنار هم، اتصال واحد UI→API→DB، تطابق role، coverage تمام خطاها یا E2E را ثابت نمی‌کند. `studio/tests/apiCoverage.test.ts` گیت AST/token فعلی و فهرست استثناها را نگه می‌دارد: در فایل ۴۰ entry صریح هست (برخی دارای `evidence` واقعی و برخی external/TODO)، نه ۴۰ قابلیت تأییدشده. چهار تست همین گیت در full Studio suite سبزند. تعداد متنی `<button`/`<Button` و callbackهای Flutter نیز صرفاً سرنخ‌اند، نه فهرست action نهایی.

### اختلاف مسیر هدف و مسیر جاری پرداخت

- **هدف انتشار اول:** `card_to_card`، فیش خصوصی، تطبیق مستقل انسانی با منبع بانکی، و تأیید idempotent/تراکنشی همراه ثبت مالی و فعال‌سازی اشتراک. فیش به‌تنهایی اثبات واریز نیست؛ عکس پیشرفت بدن خارج scope است.
- **شاهد کد موجود:** `modules/payments/router.py`, `service.py`, `gateway.py` و APIهای `/api/v1/payments*` شامل create/start/callback/verify/refund و پرداخت کیف‌پول/فروشگاه هستند. `manual_transfer_policy.py` خودش صریحاً یک transition-policy خالص و «متصل‌نشده به API، storage یا ledger» است؛ این به‌تنهایی workflow کارت‌به‌کارت نیست.
- بنابراین فهرست endpointهای موجود، وجود قاعدهٔ policy، تست‌های sandbox یا `manual=True` در مسیر gateway هیچ‌کدام تکمیل مسیر هدف انسانی/فیش خصوصی/فعال‌سازی اشتراک را ثابت نمی‌کند. `card` تاریخی/درگاه را با هدف `card_to_card` یکی نمی‌گیریم. QF-05..09 نیازمند trace مستقل UI→API→DB، مجوز، رقابت، retry و rollback هستند.

## ۴. اجرای واقعی REA و حد آن

1. `rea --version` با PATH شامل Node portable → `6.9.0`.
2. تولید OpenAPI در حافظهٔ process محلی با `from app.main import app; app.openapi()` (بدون DB/سرویس بیرونی) و ذخیرهٔ موقت؛ سپس `rea inspect-api-contract <temp-openapi> --detail summary --evidence_output <temp> --format json` موفق شد. OpenAPI SHA-256=`ff4f7f963cbf10a2e30a7f070dc4429efc0dfa69264e6ba202da985bf3ad417e`; Evidence=`ev_55d66190a59f5005fd292f9e2766982fa29275b356bc9523b18b78ceca852f33`. فایل موقت پس از استخراج شمارش حذف شد.
3. `rea analyze-javascript-application mp-app/studio --artifact-format directory --source-paths-json <9-path fixture> --detail summary --evidence_output <temp> --format json` موفق شد. ۹ فایل منتخب (`App.tsx`, API clientها, auth, PaymentPanel, RoleManager, Finance, CheckIn, Shop) به‌شکل static/inert تحلیل شدند؛ Evidence=`ev_84b8cef342767caa91fd4e4a9c33e9c1d92ce5afcb5e44e4c7a10908b297f754`. گراف partial است: ۸٬۶۵۵ فایل فهرست‌شده بیرون از تحلیل منبع انتخابی ماندند، unknownهای گراف/semantic باقی‌اند و syntax/استنتاج static به‌معنی اجرا یا behavior نیست. Evidence کامل ۱۵۲٬۷۰۲٬۹۲۴ بایتی پس از استخراج خلاصه از `/tmp` حذف شد تا artifact بزرگ نگه‌داری نشود؛ دادهٔ خام به Git نرفت.
4. `rea doctor` با Node سازگار اجرا شد ولی `healthy=false`, `environment_healthy=false`; host Debian 12 و Node سالم، native analysis engines در دسترس نیستند، provider/client مدل تعریف نشده و identity skill `config_drift` دارد. هیچ کد/داده‌ای به مدل یا سرویس ابری ارسال نشد.
5. دو فراخوانی اول با `--view api-contract` و `--view javascript-routes` نامعتبر بود (پارامتر view JSON می‌خواست) و پیش از retry راهنما بررسی شد؛ اجرای اصلاح‌شدهٔ بدون `--view` موفق شد. این خطاها حذف یا PASS محسوب نشده‌اند.

REA در این برش برای پیمایش/قرارداد واقعاً استفاده شد. یک probe جداگانه که `app.routes` را فقط به‌صورت flat از `APIRoute` می‌خواند، به‌دلیل تجمیع lazy روترها در FastAPI نصب‌شده فقط `/health` را دید؛ این نتیجه نامعتبر تلقی و کنار گذاشته شد و شمارش معتبر از `app.openapi()` گرفته شد. نقش ECC یا subagent مستقل اجرا نشد؛ بنابراین S/T مستقل هنوز `BLOCKED`. RepoWise نداشتن یک گراف تازه را مانع ادامهٔ inventory دستی/کد نمی‌دانیم.

## ۵. baseline آزمون روی کد موجود

| فرمان/شاهد | نتیجه | محدودیت |
|---|---|---|
| `(cd mp-app/backend && ../../.venv/bin/python -m pytest --cov=. --cov-report=term-missing --cov-fail-under=70)` | **۹۴۸ passed / ۲ skipped**, coverage **۸۲٫۹۵٪**, exit 0، حدود ۶:۳۲ | `pytest-asyncio` یک deprecation warning و مجموعه warningهای موجود دارد. آزمون محلی با resolver فعلی، نه lock قفل‌شدهٔ Python. |
| `ruff check .` + `ruff format --check .` | هر دو موفق؛ ۳۲۰ فایل format شده | فقط Backend. |
| `bandit -q -r app modules security` | exit 1؛ چهار low-severity heuristic (نمونهٔ توسعه، token type `bearer` و default خالی)؛ صفر medium/high در گزارش | یافته‌ها به‌عنوان false positive خودکار حذف نشدند؛ run CI همان SHA برای job امنیتی سبز است. |
| `(cd mp-app/studio && npm test)` | **۲۲۵ passed / ۹ skipped**، ۳۳ فایل موفق و ۱ skipped؛ exit 0 | ۹ skip در live-contract محلی؛ e2e جدا در CI انجام شد. React `act` و Vite dynamic/static import warningها مشاهده شدند. |
| `npm run build` | TypeScript + Vite موفق؛ ۱۰۲۸ module transformed | خروجی build محلی داخل مسیر ignored `dist` ماند. |
| `npm audit` | ۴ مورد: ۳ moderate، ۱ high؛ repair پیشنهادشده major است | فقط audit؛ هیچ fix/ارتقای dependency انجام نشد. CI فعلی با policy «بدون critical» سبز است؛ مورد high باید پیش از release مجدداً بررسی شود. |
| `python3 scripts/docs_gate.py` | پس از تغییر handoff/plan موفق: ۱۳ Markdown، ۲۴۷ پیوند محلی، ۹ Mermaid | Gate مجموعهٔ CORE و صفحات module را می‌خواند؛ QF-00 report خودش در CORE ثابت نیست، بنابراین مقصدهای relative گزارش جداگانه راستی‌آزمایی شدند. |
| client/Android | `gh run view 44541693998` → jobهای client-flutter و client-pinned موفق؛ Android debug compile نیز موفق | Flutter/Dart/Java/SDK محلی و گوشی فیزیکی غایب؛ release-signing عمداً اجرا نشد. |
| `git diff --check` | موفق در baseline پاک | پس از تولید گزارش دوباره اجرا شود. |

### اولین پیاده‌سازی در QF-00 — manifest سطح operation

**نیاز بازتولیدشده:** artifact قدیمی `api/routes.json` فقط ۱۲۱ path را ثبت می‌کرد و method/operationId نداشت؛ از روی آن نمی‌شد inventory مسیرها را تا سطح ۱۳۷ operation ردیابی کرد.

- **Forge / تست قرمز:** `pytest tests/integration/test_routes_artifact.py -q` ابتدا `1 failed` شد: `operations` در artifact نبود. هیچ فایل runtime/product پیش از این شاهد تغییر داده نشد.
- **پیاده‌سازی:** `scripts/export_routes.py` اکنون از OpenAPI محلی، دو فهرست مرتب `paths` و `operations` می‌سازد؛ هر operation شامل `method`, `path`, `operationId`, `tags` است. `api/routes.json` با generator رسمی بازتولید شد: **۱۲۱ مسیر / ۱۳۷ operation**. تست تازگی artifact اکنون مساوی‌بودن عملیات، ترتیب و یکتایی `(method,path)` را با OpenAPI محلی می‌سنجد. فهرست قدیمی `paths` حفظ شده؛ مصرف‌کنندهٔ Studio سازگار ماند. runtime endpoint/permission تغییر نکرد.
- **QA همین تغییر:** تست هدفمند artifact **1 passed**؛ full backend `pytest --cov=. --cov-fail-under=70` **948 passed / 2 skipped**, coverage **82.92%**؛ `ruff check .` و `ruff format --check .` موفق؛ `scripts/route_guard_gate.py` → `137 routes | 128 guarded | 9 documented public`, pass؛ `npm test -- tests/apiCoverage.test.ts` → **4 passed**.
- یک اجرای اولیهٔ `ruff format --check .` پس از تغییر، تنها به‌علت wrapping خط چاپ در script شکست؛ فایل با `ruff format scripts/export_routes.py` اصلاح و Ruff/format/route-guard دوباره موفق شدند.
- **محدودیت:** این artifact هنوز OpenAPI declaration است؛ Casbin/endpoint guards، مالکیت هر entity، route-to-actionهای UI و response/errorها جداگانه نیاز به trace دارند. گیت role/QA مستقل و گیت QF-00 کامل نشده است.
- **CI همان SHA `6f236a8`:** run `44551275122` همهٔ jobها جز `secret-scan` را موفق کرد (Backend، Studio/build/audit، Flutter و Android debug، docs، live-contract، e2e-api). GitHub annotation فقط یک `generic-api-key` در این خط گزارش را نشان داد؛ مقدارها عمداً از گزارش CI خوانده/چاپ نشدند. این خط صرفاً SHA-256 و شناسهٔ opaque تولیدشدهٔ REA است، نه credential. برای حفظ اسکن کامل تاریخچه بدون rewrite، فقط fingerprint دقیق commit/path/rule/line به `.gitleaksignore` افزوده شد؛ هیچ rule/path/global allowlist اضافه نشد. خود اسکن با Gitleaks روی میزبان محلی قابل اجرا نبود؛ metadata redacted annotation تنها شاهد مصرف‌شده است.
- **CI تأیید exception دقیق:** commit `259a621` (policy + handoff) در run `44553561916` با **هر ۸ job موفق** تأیید شد: full-history secret-scan و تست regression استثناهای exact/synthetic، backend (lint/tests/security/Semgrep)، Studio tests/build/audit، Flutter، pinned SDK/Android debug، docs، live-contract و e2e-api. این نتیجه فقط scan/کدهای همان SHA را می‌پوشاند؛ QF-00 هنوز به‌علت inventory interaction و QA مستقل کامل نیست.

## ۶. ماتریس آغازین QF-00 و گیت‌های حل‌نشده

این بخش snapshot فهرست‌برداری است، نه صورت‌جلسهٔ کامل تمام UI actionها. شمارش‌های lexical برای پیدا کردن سطح بررسی به‌کار رفته‌اند و completeness نیستند.

| معیار Q0–Q10 | وضعیت آغازین | شاهد/ادامه |
|---|---|---|
| Q0 baseline/provenance | `PASS (baseline)` | SHA/branch/dirty، dependency و مجوز اختصاصی ثبت شد؛ پس از مستندات، baseline diff جدید باید بازبینی شود. |
| Q1 forge/reproduction | `PARTIAL` | تست تازگی operation manifest ابتدا fail شد و پس از پیاده‌سازی pass؛ baseline suite و API contract هم اجرا شدند. regression inventory UI/action کامل هنوز وجود ندارد. |
| Q2 تمام action/outputها و نقش‌ها | `UNKNOWN / IN PROGRESS` | ۱۲ صفحهٔ Studio، ۱۴ route عضو، ۱۳۷ operation، ۷۲ tag متنی `<button`/`<Button` در Studio و ۸۲ callback متنی Flutter نامزد بررسی‌اند. artifact اکنون ۱۳۷ method/path را نگه می‌دارد؛ اما شمارش‌ها تمام gesture/menu/keyboard/export/side effect را نمی‌پوشانند و هر اقدام باید به نقش/مالکیت و UI/API/DB/test نگاشت شود. |
| Q3 مسیر UI→API→DB | `PARTIAL` | CI baseline `live-contract` و `e2e-api` سبز؛ `apiCoverage` پس از تغییر 4 passed؛ همهٔ domainها/نقش‌ها/خطا/retry/قطع شبکه با هم پوشش داده نشده‌اند. |
| Q4 قرارداد/سازگاری | `PARTIAL` | OpenAPI و manifest مسیر+operation و freshness آن‌ها تست می‌شوند؛ schema/auth، مصرف‌کنندگان هر operation و authorization مؤثر تطبیق کامل نشده‌اند. |
| Q5 امنیت/حریم | `BLOCKED (independent review)` | CI secret-scan روی baseline سبز؛ هیچ subagent/reviewer مستقل در این میزبان نداریم و اسکن history همان SHA به تغییرات آینده تعمیم ندارد. |
| Q6 بار/کرش | `N/A برای inventory صرف؛ آتی UNKNOWN` | در این snapshot هیچ بار یا failure injection اجرا نشد؛ baseline پیکربندی/ظرفیت تولید را نمی‌سنجد. |
| Q7 حذف/refactor | `PASS (no product files changed)` | در inventory هیچ کد یا فایل قبلی حذف/بازنویسی نشد. |
| Q8 اجرا/build | `PARTIAL` | Backend/Studio محلی و client CI اجرا شدند؛ Android دستگاه/release و همهٔ محیط‌های داده هدف آزموده نشدند. |
| Q9 عملیات/a11y/RTL | `UNKNOWN` | baseline واحدگذاری، تعامل صفحه کوچک، screen reader، storage retention و restore را جامع ارزیابی نکرد. |
| Q10 گزارش/Next/checkpoint | `BLOCKED` تا review + commit/push + CI همین SHA | این سند و handoff آپدیت می‌شوند؛ diff اسناد باید دستی review/scan شود، سپس commit فقط روی شاخهٔ نشست push و run همان SHA بررسی شود. تا آن زمان QF-01 آغاز نمی‌شود. |

## ۷. موانع، ادامه و rollback

- مانع اصلی ادامهٔ توالی: نبود میزبان واقعی ECC-subagent/QA مستقل؛ `rea doctor` unhealthy برای provider/native analysis؛ Flutter/Android/device محلی غایب. روی loopهای نیازمند آن‌ها `BLOCKED/UNKNOWN` می‌مانند، نه PASS.
- برای QF-00 می‌توان کار مستقل inventory و mapping code/tests را با ابزارهای محلی ادامه داد؛ گزارش این نوبت **snapshot اولیه** است، نه closeout نهایی. inventory دقیق هر action/role/API/DB/output، تست منفی مستقیم authorization، و gapهای API-to-client ادامهٔ لازم‌اند.
- هیچ dependency محصولی، schema، behavior، DB محلی، branch دیگر، main، release، deployment، payment یا production تغییر نکرده است. ابزارهای محلی جدید در مسیرهای ignored باقی می‌مانند.
- نزدیک‌ترین اقدام بعدی: تکمیل ماتریس actionها با routeهای Studio/Flutter و مراجع API/test، بررسی مستقیم policy/ownership برای دامنه‌های اصلی و update کردن همین گزارش با status؛ سپس reviewer مستقل در صورت فعال‌شدن capability میزبان. پس از checkpoint تأییدشده، QF-01 فقط وقتی QF-00 و گیت‌هایش بسته‌اند.
