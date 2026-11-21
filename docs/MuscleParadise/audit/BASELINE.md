# خط پایه اندازه‌گیری‌شده (BASELINE)

> WP 0.1 — **بخشی**. این سند با اندازه‌گیری روی commit `662ff88` (base ممیزی) ساخته شده،
> نه روی HEAD فعلی؛ کامیت‌های ممیزی خودِ اعداد را تغییر داده‌اند و مقایسهٔ «قبل» باید از base باشد.
> ستون «تأیید ابزار دوم» (الحاقیهٔ A1، بخش ۶) برای مقایسه با radon/lizard/semgrep است.

## الف) ruff ۰٫۱۷٫۶ روی `mp-app/backend` (commit 662ff88، `--no-cache`)

| اندازه‌گیری | نتیجه | exit | زمان (ms) |
|---|---|---|---|
| `ruff check .` با پیکربندی فعلی (۸ خانواده: E,F,W,I,N,UP,B,SIM) | All checks passed! | 0 | 52–58 |
| `ruff check --select ALL .` | ۱۱٬۷۷۸ یافته، ۱۰۴ قاعدهٔ متمایز، ۱٬۰۱۰ قابل‌رفع خودکار (۹۹۶ unsafe) | 1 | 296 |
| `ruff format --check .` | ۳۷۸ فایل پیش‌تر قالب‌بندی‌شده | 0 | 57 |

## ب) شمارش قاعده‌های مرتبط با یافته‌ها (همان commit)

| قاعده | تعداد | یافته / تابع / محل | وضعیت در ممیزی |
|---|---|---|---|
| `C901` (سقف ۱۰) | ۱۵ | `app/config.py:128` = **۲۸**؛ `engine/axis_prescription.py:43` = ۲۱؛ `modules/payments/manual_transfer_policy.py:45` = ۲۰؛ `engine/churn_risk.py:22` = ۱۸؛ `app/deps.py:42` = ۱۱ | F‑15 |
| `TRY400` | ۶ | `app/sms.py:66,69,72,99,102,105` | **F‑29** |
| `DTZ011` | ۳ | `modules/axis_assessment/service.py:31`، `modules/nutrition/service.py:124,182` | **F‑28** |
| `DTZ001` | ۱ | `tests/regression/test_manual_transfer_policy.py:165` | F‑28 (تست) |
| `S310` | ۶ | `app/sms.py:52,61,94` + `eval/llm_column.py:59,100,107` | **F‑29** (سه مورد اول) |
| `S608` | ۰ | — (`ruff check --select S608` بدون یافته؛ semgrep تنها گیت F‑22 است) | F‑22 |
| `S105` | ۳ | `app/config.py:16:22`، `modules/auth/schemas.py:46:23`، `tests/integration/test_m67_studio_auth.py:37:42` | ریشهٔ F‑02 (اولی) |
| `S106` | ۱ | `tests/regression/test_production_ops.py:44:13` (`sms_password`) | ثبت‌شده در A1.1 |
| `RUF100` (بلااثر) | **۳۹ ادعا — تأیید‌نشده** | اندازه‌گیری‌شده: `--select RUF100` ⇒ ۷۲؛ `--extend-select RUF100` روی پیکربندی فعلی ⇒ ۵۹. عدد ۳۹ فقط با پیکربندی پیشنهادی ruff-recommended (که هنوز در دسترس نیست) قابل بازتولید است. بیشترین مکان‌ها: `scripts/dast.py` ۵، `cache/store.py` ۵ | WP 0.9 |
| `ERA001` | ۱۱ | همه کامنت فارسی مستندساز (راستی‌آزمایی‌شده) | پیکربندی: ignore |
| `RUF001` | ۲۳۰ | متن فارسی | پیکربندی: ignore |
| `S101` | ۲٬۷۳۶ | `assert` در تست‌ها | per-file-ignore |
| `PLC0415` | ۹۸۸ | import تنبل | ignore |
| `TRY003` | ۳۶۰ | پیام فارسی inline | ignore |
| `EM101` | ۳۰۹ | پیام فارسی inline | ignore |
| `SLF001` | ۲۵ | دسترسی خصوصی | بررسی |
| `PLW0603` | ۷ | `global` در logging/observability/profiling | F‑03 |

## ج) اختلاف‌های اندازه‌گیری با الحاقیهٔ A1 (باید در برنامه اصلاح شوند)

| مورد | الحاقیه | اندازه‌گیری | تصمیم |
|---|---|---|---|
| `RUF100` | ۳۹ | **۷۲** | عدد اندازه‌گیری‌شده ملاک است؛ گیت WP 0.9 = ۰ |
| قاعده‌های متمایز `--select ALL` | ۱۰۸ (تعداد خط خروجی) | **۱۰۴** (تأیید A1.1؛ ۴ خط غیرقاعده) | ملاک: اندازه‌گیری |
| `S105` | ۴ مورد | **۳ + S106 ×۱** (`test_production_ops.py:44:13`) | ملاک: اندازه‌گیری (A1.1) |
| `logging.error` در `sms.py` | «`logging.error`» | در کد `log.error` است؛ TRY400 شش مورد را تأیید می‌کند | تأیید شد |
| `ruff-recommended.toml` | — | **رفع‌شده:** کیتِ `MP-BUILDER-KIT-2026-11-21.zip` (sha256 zip `9a192500…`) را داد؛ نسخهٔ عیناً کپی‌شده در `docs/MuscleParadise/audit/ruff-recommended.toml` (sha256 `6bafdba1…`) | بازشده |
| `BASELINE.md` با ۴۹ ردیف (WP 0.1) | — | پیش از این موجود نبود؛ این سند نسخهٔ بخشی است | ۴۹ ردیف هنوز ناقص |

## د) اصلاحیهٔ A1.1 (ثبت‌شده در `EXECUTION-LOG.md`)

- ۱۰۴ قاعدهٔ متمایز تأیید شد؛ ۱۰۸ تعداد خطوط خروجی بود.
- S105 = ۳، S106 = ۱ (تأیید شد).
- `log.error` ⇒ `log.exception` فقط در ۶ محل داخل `except` (`app/sms.py:66,69,72,99,102,105`)؛ `:58` و `:91` بیرون از `except`‌اند.
- RUF100: ادعای ۳۹ هنوز تأیید نشده (بند ب).
- `ruff-recommended.toml`: در این نوبت متن آن در پیام نیست؛ WP 0.9 مرحلهٔ ۱ متوقف است.
- اعداد میلی‌ثانیه ماشین‌وابسته‌اند؛ فقط نسبت‌ها ملاک‌اند.

## ه) A1.3 — پیکربندی نصب‌شده و اعداد تأییدشده (WP 0.9)

| اندازه‌گیری | روی 662ff88 | روی HEAD (07f096d) | یادداشت |
|---|---|---|---|
| کل یافته (پیکربندی A1.3 §۵ + ERA001 در ignore) | **۴۱۹** | ۳۸۴ | گام ۱: ۴۳۰؛ HEAD پس از رفع‌های ایمن |
| قواعدِ متمایز | **۵۱** | ۴۷ | گام ۱: ۵۲ |
| RUF100 با پیکربندی نصب‌شده | **۳۹** (پس از ERA: ۳۹) | ۴ | ۴ = `noqa: S608` در c3f01ab129e2 (تا WP 4.5 عمداً باقی) |
| RUF100 با `--select RUF100` تنها | ۷۲ | — | **نادرست** برای گیت: `--select` بقیهٔ قواعد را خاموش می‌کند |
| RUF100 با `--extend-select RUF100` روی پیکربندی قدیمی | ۵۹ | — | ادعای ۵۹ تأیید شد؛ عدد مرجع نیست |
| TRY400 / DTZ011 / DTZ001 | ۶ / ۳ / ۱ | ۶ / ۳ / ۱ | باز تا WP 2.6 / 3.6 |
| C901 | ۱۵ | ۱۵ | F‑15 (گیت نیست) |
| S105 / S106 | ۳ / ۱ | ۴ / ۱ | HEAD یک S105 از کد WP 1.x دارد (`tests/integration/_metrics.py:3`) |
| format --check | ۳۷۸ فایل پاک | ۳۸۵ فایل پاک | HEAD فایل بیشتر دارد؛ خطای قالب صفر |
| `ruff check` کاملِ پیکربندی (پیش از اصلاح) | بلاتغییر | ۴۴۰ | افزایش ۱۰ از کد WP 1.1–1.4 |

**تفسیر:** گیت‌های مطلق (۴۳۰/۵۲/۴۱۹/۵۱/۳۹) روی `662ff88` تعریف شده‌اند و PASS هستند. روی HEAD، ۱۰ یافتهٔ اضافه از کد این شاخه است (S603 +۴، S607 +۳، S105 +۱، RUF100 +۱، FURB167 +۱، FURB192 +۱، TC001 −۱)؛ ثبت شده و گیت مطلقِ روی HEAD نیست (AD‑3).

## و) بازتولید با کیت `MP-BUILDER-KIT-2026-11-21` (WP 0.1، بخشی)
- **منبع:** `handoff/MP-BUILDER-KIT-2026-11-21.zip` در `Chat2DB@arena/2cde32d6-chat2db` (sha256 `9a1925005ca5c28c128f242a913da2a179a32eafaad8967bc908f34506492834`)؛ `MANIFEST.sha256` ✔.
- **فرمان:** `git worktree` روی `662ff88` ⇒ `RUFF=ruff-0.17.6 CFG=ruff-recommended.toml bash verify-addendum-gates.sh before` ⇒ **PASS** (exit 0).
- **شاهد:** کل ۴۳۰ · قواعد متمایز ۵۲ · RUF100 **۳۹** · TRY400 ۶ · DTZ011 ۳ · C901 ۱۵ · format ۳۷۸ فایل already formatted · ۲۰ noqa ممنوع‌الحذف ۲۰/۲۰ · noqa S608 ۴/۴.
- **نتیجه:** ادعای RUF100 = ۳۹ (بخش ب) با پیکربندی توصیه‌شده **تأیید** شد؛ با پیکربندی فعلی پروژه ۵۹–۷۲ است. هر دو عدد در جدول بالا ثبت‌اند.
- **باقی‌مانده WP 0.1:** ۴۹ ردیف عددیِ §۱۰ پروندهٔ شواهد هنوز اجرا نشده‌اند (پراب‌های زنده و جهش mutmut و بار). این بخش در این نوبت انجام نشد.

## ز) ۴۹ ردیف WP 0.1 — T‑01…T‑49 (پروندهٔ شواهد §۱۰)

> **قاعده:** هر ردیف یکی از سه وضعیت را دارد: `MEASURED-BY-YOU` (در این مخزن و در این نوبت اجرا شد) · `INHERITED-WITNESS` (اجرای دوباره نیازمند زیرساختی است که نداریم؛ شاهد خام + sha256) · `DEFERRED(D‑n)` (نه قابل اجرا و نه شاهد دارد؛ رکورد §۵ پیام بازتولید). `PARTIAL` وجود ندارد.
> **سرور:** HEAD = `5188a0d`، base = `662ff88`. S3 = فرمان Dockerfile (uvicorn، ۲ ورکر، `--proxy-headers --forwarded-allow-ips='*'`) با `MP_ALLOW_DEV_OTP_ECHO=true` (انحراف از Dockerfile؛ بخش «انحراف‌ها» را ببینید). DB = `/home/user/audit-run/data/mp.db` (SQLite، head `a7c3d9e1f2b4`).
> **شاهد:** `docs/MuscleParadise/audit/evidence/after/` (HEAD) و `evidence/before/` (base) و `evidence/after/t-rows/` (پراب‌های زنده و ابزارهای ایستای تکمیلی). اسکریپت‌های اجرا: `evidence/after/t-rows/scripts/`.
> **ارقام میلی‌ثانیه** ماشین‌وابسته‌اند؛ فقط نسبت‌ها و شمارش‌ها ملاک‌اند.

| ID | موضوع | فرمان / روش | نتیجهٔ اندازه‌گیری‌شده | دسته | شاهد | یادداشت (مقایسه با شاهد ممیزی ۲۰۲۶‑۱۱‑۲۰) |
|---|---|---|---|---|---|---|
| T‑01 | سوئیت بک‌اند + پوشش | `pytest -q --cov=. --cov-report=xml` | **1191 passed، 2 skipped، exit 0**، پوشش **84٪** (10865 stmt، 1727 miss)، 314.8 s | MEASURED-BY-YOU | `after/backend-coverage.xml`، `/home/user/audit-run/pytest-after-cov.txt` (`PYTEST_RC=0`) | شاهد: ۱۰۹۵ پاس / ۸۳٫۷۳٪. اختلاف از کامیت‌های WP بعد از base است |
| T‑02 | مهاجرت روی DB خالی | `alembic upgrade head` (SQLite) | exit 0؛ head = **`a7c3d9e1f2b4`**؛ **65** جدول (با `alembic_version`) | MEASURED-BY-YOU | `after/t-rows/T02-alembic-heads.txt` | شاهد: head و ۶۵ جدول ✓ |
| T‑03 | ORM ⟷ DB | مقایسهٔ `Base.metadata` با `sqlite_master` (`import app.main`) | ORM **64** ⟷ DB **64**؛ اختلاف: **۰** | MEASURED-BY-YOU | `after/t-rows/T03-orm-vs-db.txt` | شاهد: ۶۴ ⟷ ۶۴ ✓ |
| T‑04 | type-check استودیو | `npx tsc --noEmit` | exit **0**، ۰ خطا | MEASURED-BY-YOU | `after/t-rows/T04-tsc.log`، `T04.rc` | شاهد: ۰ خطا ✓ |
| T‑05 | تست استودیو | `npx vitest run` | **45 فایل پاس + 1 skip**؛ **298 پاس / 9 skip**، exit 0 | MEASURED-BY-YOU | `after/t-rows/T05-vitest.log` | شاهد: ۲۸۲ پاس / ۹ skip (۴۵ فایل). تست‌های اضافه‌شده در WP‌ها |
| T‑06 | lint + format بک‌اند | `ruff check` (پیکربندی بلوکینگ)، `ruff format --check`، ruff 0.17.6 | بلوکینگ: exit **0**؛ format: exit **0** (HEAD)؛ ruff پیشنهادی (`--no-cache`): base **430** → HEAD **380** | MEASURED-BY-YOU | `after/summary.json`، `before/summary.json` | شاهد: ۴۳۰ و ۳۷۸ فایل ✓ (base). پیکربندی درخت HEAD روی خانوادهٔ غیربلوکینگ ۳۳۸ دارد (بخش ه) |
| T‑07 | پیچیدگی چرخه‌ای | `radon cc -s -n C` | C-or-worse: base **47** → HEAD **47** | MEASURED-BY-YOU | `before/radon-cc.txt`، `after/radon-cc.txt` | شاهد: ۴۱ بلوک ≥C، ۲ تابع F. اختلاف روش شمارش (C‑or‑worse در برابر ≥C) |
| T‑08 | قابلیت نگهداشت | `radon mi` | **224** فایل؛ **۰** فایل با درجهٔ C یا بدتر | MEASURED-BY-YOU | `after/radon-mi.txt` | شاهد: ۱۹۵ فایل، بدون C ✓ (تعداد فایل‌ها تفاوت دارد) |
| T‑09 | طول و پیچیدگی توابع | `lizard --CCN 10 --length 60 -w` | هشدار: base **55** → HEAD **55** | MEASURED-BY-YOU | `after/lizard-warnings.txt` | شاهد: ۵۵ هشدار ✓ |
| T‑10 | کد مرده | `vulture --min-confidence 80` | **1** یافته (base و HEAD) | MEASURED-BY-YOU | `after/vulture.txt` | شاهد: ۱ ✓ |
| T‑11 | امنیت ایستای بک‌اند | `bandit -r` | base: H/M/L = 0/0/**10**؛ HEAD: 0/0/**4** | MEASURED-BY-YOU | `before/bandit.json`، `after/bandit.json` | شاهد: ۱۰ LOW، HIGH = ۰ ✓ (base) |
| T‑12 | آسیب‌پذیری وابستگی‌ها | `pip-audit` روی freeze | **90** بسته، **۰** آسیب‌پذیری شناخته‌شده | MEASURED-BY-YOU | `after/pip-audit.json`، `after/requirements-freeze.txt` | شاهد: ۲۹ نیازمندی `mp-deps.txt`؛ این بار کل freeze اندازه‌گیری شد |
| T‑13 | رمز نشت‌شده | `detect-secrets scan` (بدون `evidence/`) | base **169** ⇒ HEAD **171** علامت (فایل‌های علامت‌خورده شمارش شد) | MEASURED-BY-YOU | `before/detect-secrets.json`، `after/detect-secrets.json` | شاهد: ۶۴ فایل، ۷ اصابت «Secret Keyword»، ۰ رمز واقعی. روش شمارش متفاوت است؛ «۰ رمز واقعی» با بازبینی دستی (ادعای ممیزی) تأیید نشد و این بار بازبینی نشد |
| T‑14 | قواعد اختصاصی بک‌اند (semgrep) | `semgrep --config semgrep-mp.yml` روی `mp-app/backend` | base **19** ⇒ HEAD **2** (`mp-money-division` ×۲: `modules/admin/analytics.py:157,325`)؛ خطا: ۰ | MEASURED-BY-YOU | `after/t-rows/T14-semgrep-backend-BASE-662ff88.json`، `T14-semgrep-backend-full.json` | شاهد: ۱۹ ✓ (base). ۱۷ یافته در WP 1–4 بسته شد (F‑21/F‑22 و …) |
| T‑15 | قواعد اختصاصی استودیو | همان، روی `mp-app/studio/src` | base **8** ⇒ HEAD **2** (`Analytics.tsx:106` float-money؛ `Nutrition.tsx:50` sentinel) | MEASURED-BY-YOU | `after/t-rows/T15-semgrep-studio-BASE-662ff88.json`، `T15-semgrep-studio.json` | شاهد: ۸ ✓ (base). بقیهٔ float-money در WP 2.x بسته شد |
| T‑16 | قواعد اختصاصی Dart | همان، روی `mp-app/client/lib` | base **1** = HEAD **1** (`core/api_client.dart:191`) | MEASURED-BY-YOU | `after/t-rows/T16-semgrep-client-BASE-662ff88.json` | شاهد: ۱ ✓. بدون تغییر در این شاخه |
| T‑17 | lint واقعی استودیو (F‑10) | ESLint 9 flat config (`eslint.config.mjs`، `bf1daa1`)، `eslint src --format json` | HEAD: **0 خطا / 0 هشدار** در ۵۴ فایل (exit 0) | MEASURED-BY-YOU (HEAD) + INHERITED-WITNESS (base) | `after/t-rows/T17-eslint.json`؛ base: `raw/eslint-studio.json` (sha256 در کیت) | base پیکربندی ESLint نداشت؛ شاهد ممیزی: ۳۱ خطا / ۳ هشدار. ESLint به‌عنوان بخشی از WP 0.5 در این شاخه اضافه شد |
| T‑18 | وابستگی دوری | `madge --circular` | **No circular dependency found**، exit 0 | MEASURED-BY-YOU | `after/t-rows/T18-madge.log` | شاهد: ✓ |
| T‑19 | تکرار کد | `jscpd --min-tokens 70` (فقط `src`) | **2** clone در `src` | MEASURED-BY-YOU | `after/t-rows/T19-jscpd/`، `T19-jscpd.log` | شاهد: ۹ clone در دامنهٔ گسترده‌تر (۲۱۱ منبع). دامنه متفاوت است؛ عددی برای base اجرا نشد |
| T‑20 | مرده‌کدِ TS (knip) | `npx knip` (نسخهٔ جاری) و `npx knip@5` | نسخهٔ جاری: **کرش** `ArrayBuffer allocation failed` در oxc-parser (بازتولید شد). knip@5 اجرا شد: **۲** فایل بی‌استفاده (`electron/preload.cjs`، `public/sw.js`—نقاط ورود، مثبت کاذب)، **۳** unlisted، **۳۹** type export، **۱** binary، **۶** export | MEASURED-BY-YOU (knip@5) | `after/t-rows/T20-knip-v5.json`، `T20-knip.err` | شاهد: کرش (همان)؛ knip@5 جایگزین شد و نسخه ثبت است |
| T‑21 | امتیاز جهش (OTP/پرداخت) | حلقهٔ دستی: اعمال هر جهش روی کپی + `pytest` (`mut_loop.py`) | **۲۶ کشته / ۱۹ زنده = ۵۷٫۸٪** (۴۵ جهش)؛ **۴۵/۴۵** توافق با شاهد | MEASURED-BY-YOU | `after/t-rows/T21-mutmut-manual.json`، `scripts/mut_loop.py` | شاهد: ۲۶/۴۵ = ۵۷٫۸٪ ✓. mutmut 2.x/3.x به‌تنهایی استفاده نشد (بازبینی بند ۱۰) |
| T‑22 | سیم‌کشی UI استودیو | `scan_ui_wiring.py` | **۸۴** دکمه؛ **۷۴** با `onClick`؛ **۱۰** بدون؛ **۰** تهی؛ **۴۱** onClick بدون رسیدن به API؛ ۳ صفحه بدون import از `api.ts` | MEASURED-BY-YOU | `after/t-rows/scan_ui_wiring.log` (JSON خارج از مخزن: `/home/user/Chat2DB/audit/evidence`) | شاهد: ۸۴ / ۷۴ / ۱۰ / ۰ ✓ دقیق |
| T‑23 | گارد شناسهٔ مسیر (`PathId`) | AST روی همهٔ `*router*.py` (`pathid_scan.py`) | base: بدون گارد **0**، `int` خام **60**؛ HEAD: **0** / **60** | MEASURED-BY-YOU | `after/t-rows/T23-pathid-scan*.json` | شاهد: ۵۵ (روش متفاوت). روی هر دو commit ۶۰ است؛ این شاخه آن را تغییر نداده |
| T‑24 | — | در کیت تعریف نشده | — | DEFERRED(D‑1) | — | ردیف‌های ۲۴ تا ۲۹ در هیچ‌کدام از سندهای کیت نیستند |
| T‑25 | — | در کیت تعریف نشده | — | DEFERRED(D‑1) | — | ← D‑1 |
| T‑26 | — | در کیت تعریف نشده | — | DEFERRED(D‑1) | — | ← D‑1 |
| T‑27 | — | در کیت تعریف نشده | — | DEFERRED(D‑1) | — | ← D‑1 |
| T‑28 | — | در کیت تعریف نشده | — | DEFERRED(D‑1) | — | ← D‑1 |
| T‑29 | — | در کیت تعریف نشده | — | DEFERRED(D‑1) | — | ← D‑1 |
| T‑30 | دود پس از boot (S3) | `curl` روی S3 | `/health` **200**؛ `/api/v1/health/ready` **200** (`ready: true`)؛ `/api/v1/metrics` **403 `metrics_disabled`** (base: 200 بی‌احراز)؛ OpenAPI **141** مسیر ✓؛ هدرهای امنیتی ✓؛ `dev_code` فقط با `MP_ALLOW_DEV_OTP_ECHO=true` | MEASURED-BY-YOU | `after/t-rows/T30-smoke.txt`، `after/metrics-noauth.txt` (base) | شاهد: `/metrics` ۲۰۰ بی‌احراز روی base. روی HEAD با پیکربندی Dockerfile پاسخ `metrics_disabled` است؛ حفاظت در پیکربندی تولید جدا بررسی نشد. مسیر اولیهٔ smoke بدون `/api/v1` بود (۴۰۴ خطای پراب بود و اصلاح شد) |
| T‑31 | seed زنده (۱۶ عملیات) | `probe_contract.py seed` | **۱۴ ✓ / ۲ ✗**: `shop.cart_add` = 422 (validation)، `shop.checkout` = 409 `shop_online_closed` | MEASURED-BY-YOU | `after/t-rows/contract_seed.log` | شاهد: ۱۴/۲ ✓ (علت ۲ خطا متفاوت: ۴۰۴ ⇒ ۴۲۲/۴۰۹) |
| T‑32 | ماتریس مجوز | `probe_contract.py matrix` | **۱۹۴۵** سلول؛ **۰** × 5xx؛ ۹۲ × 2xx؛ ۱۸۵۳ × 4xx | MEASURED-BY-YOU | `after/contract-matrix-raw.json`، `after/t-rows/contract_matrix.log` | شاهد: ۱۱۴۱ سلول (تعداد عملیات × نقش متفاوت). ۰ × 5xx ✓ |
| T‑33 | ورودی خصمانه (نسخهٔ ۱) | `probe_contract.py invalid` | ۰ × 5xx؛ ۰ نشت stack؛ **۱** پاسخ 2xx غیرمنتظره | MEASURED-BY-YOU | `after/contract-invalid-findings.json` | شاهد: نسخهٔ ۱ «نادرست‌نتیجه» بود (۶۶۴ × 401 به‌خاطر logout-all)؛ این اجرا همان مشکل را نداشت |
| T‑34 | ورودی خصمانه (نسخهٔ ۲، احراز تأییدشده) | `probe_invalid_authed.py` | **۸۷۲** سلول؛ **۰** × 5xx؛ **۰** نشت؛ **۴۸** × 2xx روی شناسهٔ غیرمجاز؛ **۷۰** رد گارد شناسه | MEASURED-BY-YOU | `after/contract-invalid-authed.json`، `after/t-rows/invalid_authed.log` | شاهد: ۸۷۲ / ۰ / ۴۸ / ۷۰ ✓ دقیق |
| T‑35 | باتری امنیت زنده (T1–T10) | `probe_live_security.py` | **۱۱ PASS**، **۱ FAIL** (T7: پراب انتظار دارد origin ها بازتاب نشوند؛ `https://evil.example.com` ⇒ 400 بدون بازتاب، ولی `http://127.0.0.1:5173` ⇒ 200 با بازتاب. این origin در allowlist پیش‌فرض است (`config.py:89`) ⇒ نیاز به triage)، **۱ NOTE** (T10) | MEASURED-BY-YOU | `after/live-security-verdicts.json`، `live-security-raw.json` | شاهد (base، باتری متفاوت): S1 بدون `sid`، `/metrics`، `amount_rial=10^18`، ۰/۱۶ نشت؛ مقایسهٔ مستقیم ممکن نیست چون ساختار آزمون‌ها فرق دارد |
| T‑36 | محدودیت نرخ OTP | `probe_otp_limits.py A B C D E` | A: `[401,401,401,429]`، کد واقعی پس از ۴ حدس ⇒ **429**، بازپخش ⇒ 429؛ B: قفل بعد از سقف ✓؛ **C: FAIL — ۳۰/۳۰ پذیرفته با XFF تصادفی**؛ D: baseline **۳/۱۴**؛ E: متریک بدون برچسب IP (۰ خط) | MEASURED-BY-YOU | `after/otp-ratelimit-verdicts.json`، `after/t-rows/otp_limits_all.log` | شاهد: C = ۳۰/۳۰ ✓؛ D = ۳/۱۴ ✓؛ E ✓ |
| T‑37 | حدس انفجاری OTP | اسکریپت جدید `T37_bruteforce.py` (در کیت نبود) | ۶۰ حدس در ۰٫۱۳۵ s (≈۴۴۳/s)؛ **۳ × 401 + ۵۷ × 429**؛ کد واقعی پس از دسته ⇒ 429؛ بازپخش ⇒ 429 | MEASURED-BY-YOU | `after/t-rows/T37-otp-bruteforce.json`، `scripts/T37_bruteforce.py` | شاهد: ۵۵×400 `otp_locked` + ۵×401، ۲۲۸/s. کد پاسخ و نرخ متفاوت؛ **هر دو نسخه** حدس نامحدود را مسدود کردند |
| T‑38 | XFF روی CMD واقعی Dockerfile | `curl` روی S3؛ ۱۴ baseline بدون هدر، ۳۰ با XFF تصادفی (پنجرهٔ جداگانه) | baseline: **۵/۱۴** پذیرفته؛ XFF: **۳۰/۳۰** پذیرفته (ضریب تکثیر با ۲ ورکر) | MEASURED-BY-YOU | `after/t-rows/T38-xff-dockerfile.txt`، `after/xff-dockerfile-cmd.json` (base) | شاهد: ۳۰/۳۰ در برابر ۳/۱۴ ✓ (baseline در این پنجره ۵ بود) |
| T‑39 | ۲۰۰ کلاینت همزمان با توپولوژی Docker/Postgres/Valkey | `docker info`، `psql`، `valkey-cli` | `docker: command not found`؛ سوکت وجود ندارد؛ `psql` و `valkey-cli` نصب نیستند | DEFERRED(D‑2) | `after/t-rows/T39-env-docker.txt` | شاهد جایگزین: T‑40 و T‑46 (پلهٔ ۸۰ ورکر) |
| T‑40 | بار پله‌ای روی سرور کنترل (`serve_plain`، بدون ابزار) | `probe_load.py plain-dev 10 40 60 80` (۴۰ s هر پله) | ۱۰ ⇒ **293.4 rps**، خطا ۰؛ ۴۰ ⇒ **102.6 rps** با **۴۰ timeout**؛ ۶۰ ⇒ **290.4 rps**، خطا ۰؛ ۸۰ ⇒ **271.3 rps**، ۰ timeout، p99 547 ms | MEASURED-BY-YOU | `after/load-plain-dev.json`، `after/t-rows/T40-load-plain-dev.log` | شاهد: ۱۰→۱۹۶ rps، ۸۰→۹۴٫۷ با ۸۰ timeout. **اشباع در ۸۰ روی کنترل بازتولید نشد**؛ همان پله روی سرور ابزاردار (T‑46) اشباع را نشان داد |
| T‑41 | هزینهٔ لاگ (`bench_logging`) | `bench_logging.py` | در عمق ۱۰: **rich** میانهٔ **65.66 ms** و **35,961 B/خطا**؛ **JSON**: **0.02 ms** و **202 B** | MEASURED-BY-YOU | `after/t-rows/logging-cost.json`، `bench_logging.log` | شاهد: «تا ~۹٬۶۰۰×» و «~۶۳۰×»؛ این بار نسبت‌ها ملاک‌اند (ماشین‌وابسته) |
| T‑42 | بازتولید `SystemError` در RBAC | `repro_rbac_systemerror.py` (۸۰ نخ، عمق ۴۰، ۴۰۰ فراخوانی)، ۳۲٬۰۰۰ فراخوانی | **۱ SystemError** در ۳۲٬۰۰۰؛ `AST constructor recursion depth mismatch`. همچنین همین خطا در لاگ سرور کنترل (T‑40) و سرور ابزاردار (T‑46) دیده شد | MEASURED-BY-YOU | `after/t-rows/rbac-systemerror-repro.json`، `repro_rbac.log` | شاهد: ۳–۷ خطا در ۸۰ نخ؛ **پدیده تکرار شد** (تعداد متفاوت) |
| T‑43 | تأخیر `enforce()` | همان اسکریپت (معادل زیر تماس ۸۰ نخ) | p50 **0.69 ms**، p95 **96.2 ms**، max **1204 ms** | MEASURED-BY-YOU (معادل) | `after/t-rows/rbac-systemerror-repro.json` | شاهد: میکرو‌بنچ ۳ مسیر × ۳۰۰ (µs) در کیت نیست؛ فقط معادل تحت تماس اندازه‌گیری شد |
| T‑44 | اثبات رفع (جدول پیش‌کامپایل، ۲۴ تصمیم) | PoC داخلی ممیزی | — | DEFERRED(D‑3) | — | ← D‑3 |
| T‑45 | diff قرارداد ⟷ OpenAPI زنده | اسکریپت اختصاصی ممیزی | — | DEFERRED(D‑4) | `after/openapi-live.json` (۱۴۱ مسیر، اندازه‌گیری شد) | ← D‑4 |
| T‑46 | مشاهده‌پذیری استخر (سرور ابزاردار) | `serve_backend.py` + `probe_load.py backend-instr 40 80` | **۵۰** رویداد `held_over_1s`؛ بیشینهٔ `checked_out` = **57** (ظرفیت ۶۰ نرسید)؛ میانهٔ `held_ms` = **46.8 s**؛ بار ۸۰ ورکر: **108.8 rps**، **۸۰ timeout**، p99 **17.3 s** | MEASURED-BY-YOU | `after/t-rows/pool-events.jsonl`، `load-backend-instr.json`، `T46-load-instr.log` | شاهد: ۱۴۵ رویداد، ۹۰ در ظرفیت ۶۰، میانه ۱٫۳ s. **اشباع در ۸۰ بازتولید شد**؛ نمونه‌برداری و زمان‌ها متفاوت‌اند |
| T‑47 | یکپارچگی DB و بازتاب خروجی | `sqlite3` (`integrity_check`، شمارش)، `grep max_length` | `integrity_check` = **ok**؛ ۶۵ جدول (با `alembic_version`)؛ `users` = **259**؛ `note` سقف **1000** (`modules/expenses/schemas.py:29`) | MEASURED-BY-YOU | `after/t-rows/*` | شاهد: `users` = ۲۶۱ (داده‌های seed متفاوت است)؛ بقیه ✓ |
| T‑48 | رفتار وابسته به پیکربندی shop | `curl` روی S3 (پیش‌فرض) و S1 (`MP_SHOP_ONLINE_PURCHASE_ENABLED=true`) | S3 ⇒ کاربر بدون پروفایل: **409 `shop_online_closed`**؛ S1 ⇒ همان کاربر: **404 `not_found`** («پروندهٔ عضو یافت نشد»)؛ S1 ⇒ کاربر ۱ با سبد خالی: 400 `empty_cart` | MEASURED-BY-YOU | `after/t-rows/T48-shop-S3.txt`، `T48-shop-S1.txt` | شاهد: S3 = 409، S1 = 404 ✓ |
| T‑49 | زنده‌بودن توکن (canary) | پیش و پس از `probe_invalid_authed.py` | canary نقش‌های admin و member هر دو **200** قبل و بعد؛ `tokens_live_throughout = true`؛ **۰** ورود مجدد | MEASURED-BY-YOU | `after/contract-invalid-authed.json` | شاهد: ۲۰۰ و ۰ ورود مجدد ✓ |

### ز.۱ · انحراف‌ها از اجرای ممیزی (ثبت برای شفافیت)

1. **`MP_ALLOW_DEV_OTP_ECHO=true` روی S3.** Dockerfile و compose این پرچم را روشن نمی‌کنند (`deploy_gate.py` آن را در compose رد می‌کند). پراب‌های OTP بدون `dev_code` نمی‌توانند ورود کنند، پس فقط برای اجرای پراب‌ها روی DB محلی روشن شد. نتایج T‑30 و T‑36 تا T‑38 با این پرچم است؛ رفتار پیش‌فرض (بدون echo) جداگانه بررسی شد: پاسخ OTP بدون `dev_code` است.
2. **`probe_otp_limits.py bruteforce` در کیت نیست.** اجرای آن ۰ ثانیه، exit 0 و بدون خروجی بود؛ این یک «پاس» کاذب بود و رد شد. T‑37 با اسکریپت جدید `T37_bruteforce.py` اندازه‌گیری شد.
3. **knip نسخهٔ جاری کرش می‌کند.** T‑20 با knip@5 اجرا شد و نسخه ثبت است.
4. **روش شمارش** T‑13 (detect-secrets)، T‑19 (jscpd)، T‑23 (pathid) و T‑07 (radon) با شاهد ممیزی یکی نیست؛ ارقام هر دو ثبت شدند و ملاک، عدد اندازه‌گیری‌شدهٔ همین commit است.
5. **پراب‌های کیت روی `/tmp/run` اجرا شدند:** مسیرهای ثابت پراب‌ها (`/tmp/run/MP`، `/tmp/run/venv`) با symlink به مخزن و venv ارضا شدند؛ هیچ فایلی در مخزن اصلی تغییر نکرد.
6. **`scan_ui_wiring.py` خروجی JSON را در `/home/user/Chat2DB/audit/evidence` می‌نویسد** (مسیر ثابت کیت، خارج از مخزن). متن کامل stdout در `after/t-rows/scan_ui_wiring.log` ثبت است.
7. **`mp-app/studio/dist`** پیش از هر commit حذف می‌شود (در این شاخه وجود ندارد).

### ز.۲ · رکوردهای `DEFERRED(D‑n)` (قالب §۵ پیام بازتولید)

```text
D-1: ردیف‌های T‑24 تا T‑29 در کیت تعریف نشده‌اند
یافته/بند مرتبط: بند ۷ تعریف انجام‌شد (شمارش ۴۹ ردیف)؛ هیچ F-id مستقیم
چرا در این محیط ممکن نیست: این ردیف‌ها در MP-EVIDENCE-DOSSIER-2026-11-20.md و هیچ فایل دیگر کیت (`grep -rn "T.2[4-9]"`) وجود ندارند؛ فقط T‑01…T‑23 و T‑30…T‑49 تعریف شده‌اند
تلاش انجام‌شده: `grep -rn "T-2[4-9]\|T‑2[4-9]" /home/user/audit-run/kit/unpacked/` ⇒ خروجی خالی (exit 1)
شاهد جایگزین: ۴۳ ردیف تعریف‌شده در بالا اندازه‌گیری شد؛ شمارش ۴۹ در پیام بازتولید با این شکاف سازگار نیست
ریسک باقیمانده: اگر ردیف‌های ۲۴ تا ۲۹ در نسخه‌ای دیگر از ممیزی وجود داشته باشند، ممکن است یک یافته پوشش نیافته باشد
مسیر ارتقا: دریافت تعریف این شش ردیف از نویسندهٔ ممیزی؛ سپس اجرا و جایگزینی با MEASURED-BY-YOU
```

```text
D-2: T‑39 — بار ۲۰۰ کلاینت روی توپولوژی Docker/Postgres/Valkey
یافته/بند مرتبط: بند ۷ تعریف انجام‌شد (۲۰۰ کلاینت همزمان)؛ T‑39
چرا در این محیط ممکن نیست: نه Docker daemon، نه Postgres، نه Valkey در محیط است
تلاش انجام‌شده: `docker info` ⇒ `docker: command not found` (exit 127)؛ سوکت وجود ندارد؛ `psql`، `valkey-cli` نصب نیستند (`after/t-rows/T39-env-docker.txt`)
شاهد جایگزین: `after/load-plain-dev.json` (پلهٔ ۸۰ ورکر روی کنترل) و `load-backend-instr.json` + `pool-events.jsonl` (پلهٔ ۸۰ روی سرور ابزاردار): اشباع استخر و ۸۰ timeout را ثبت کرد
ریسک باقیمانده: رفتار ۲۰۰ اتصال همزمان روی Postgres و Valkey واقعی و عدد ظرفیت در توپولوژی تولید؛ این نقص بازتولید شد ولی عدد توپولوژی تولید نه
مسیر ارتقا: نصب Docker و اجرای `docker compose` پروژه، سپس اجرای `audit/probe_concurrency.py` روی S3
```

```text
D-3: T‑44 — PoC اثبات رفع (جدول پیش‌کامپایل، ۲۴ تصمیم)
یافته/بند مرتبط: بند ۷ تعریف انجام‌شد (جدول پیش‌کامپایل RBAC)؛ شناسهٔ F در کیت مشخص نشده — T‑43/T‑44
چرا در این محیط ممکن نیست: اسکریپت PoC در کیت نیست و خروجی خامی هم در `raw/` ندارد؛ عددها فقط در متن داشبورد ممیزی آمده‌اند
تلاش انجام‌شده: جست‌وجو در کیت برای `precompil`/`PoC`/`24` ⇒ شاهد خام پیدا نشد
شاهد جایگزین: T‑42/T‑43 (معادل تحت تماس) اندازه‌گیری شد؛ اثبات «۲۴/۲۴ تصمیم یکسان» بازتولید نشد
ریسک باقیمانده: یکسانی تصمیم‌های جدول پیش‌کامپایل با enforce زنده تأیید نشده است
مسیر ارتقا: دریافت اسکریپت PoC؛ اجرای آن روی HEAD و ثبت شمارش «همان تصمیم»
```

```text
D-4: T‑45 — diff قرارداد (`probe_contract`) ⟷ OpenAPI زنده
یافته/بند مرتبط: F‑13 (گارد تکراری)، F‑25 (گارد شناسه)، بند ۷
چرا در این محیط ممکن نیست: اسکریپت اختصاصی diff در کیت نیست؛ `contract-diff.json` در `raw/` وجود ندارد
تلاش انجام‌شده: `ls raw/ | grep contract-diff` ⇒ خالی؛ `probe_contract.py` حالت diff ندارد (`all|seed|matrix|invalid`)
شاهد جایگزین: `after/openapi-live.json` (۱۴۱ مسیر، همان شمار T‑30) و `contract-matrix-raw.json` (۱۹۴۵ سلول با `guards`)
ریسک باقیمانده: صفر drift در هر دو جهت و هیستوگرام گاردها تأیید نشده‌اند
مسیر ارتقا: دریافت اسکریپت diff و اجرای آن روی `openapi-live.json` و ماتریس
```

### ز.۳ · جمع‌بندی

- **۴۹ ردیف:** `MEASURED-BY-YOU` = **۴۰** (T‑01…T‑23 = ۲۳، T‑30…T‑38 = ۹، T‑40…T‑43 = ۴، T‑46…T‑49 = ۴)؛ `DEFERRED(D‑n)` = **۹** (T‑24…T‑29 با D‑1 = ۶، T‑39 با D‑2، T‑44 با D‑3، T‑45 با D‑4). ۴۰ + ۹ = ۴۹ ✓.
  - T‑17 در ستون «base» به `INHERITED-WITNESS` (`raw/eslint-studio.json`) استناد می‌کند؛ ستون HEAD آن `MEASURED-BY-YOU` است.
  - هیچ ردیف `PARTIAL` یا خالی نیست.
- **موارد باز برای triage (نه ادعای یافتهٔ تازه):**
  - T7 (CORS): بازتاب `http://127.0.0.1:5173` که در allowlist پیش‌فرض است؛ باید بررسی شود آیا این allowlist در تولید هم فعال است (T‑35).
  - اشباع استخر در ۸۰ ورکر روی سرور ابزاردار و `SystemError` از casbin در RBAC هنوز دیده می‌شوند (T‑42/T‑46). روی سرور کنترل T‑40 اشباع نشد.
  - T‑37 با پراب بازنویسی‌شده اجرا شد؛ کد پاسخ و نرخ با شاهد ممیزی یکی نیست.
