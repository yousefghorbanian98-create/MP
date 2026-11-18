# M99 — گزارش پایانی بازهٔ M63–M99 (شواهد، status، بلوکرهاب، بازتولید)

- تاریخ: ۲۰۲۶-۱۱-۱۸ (UTC)
- شاخه: `arena/4f336f66-mp` (status `active`)، پایه `d64e3b008d1c6c20c65c5ebfa4816277d4d23ce0`
- HEAD پیش از این بسته: `7a998595da69bc662636f85aeba395f0228a5157` — run `44264066269`: `studio` · `client-flutter` · `backend` · `live-contract` · `e2e-api` **success**، `secret-scan` **failure**
- این loop **اجازهٔ انتشار نیست**: بدون release، بدون deploy، بدون تغییر DB تولید، بدون پرداخت/SMS واقعی. هیچ ادعای «کامل/بی‌نقص» نمی‌شود.

## ۱) وضعیت هر loop (با نوع شاهد)

| Loop | وضعیت | نوع شاهد / دلیل |
|---|---|---|
| M63 n8n boundary | `PASS` | سیاست واحد در ADR-005 و اسناد همسو؛ هیچ instance/integration ساخته نشد |
| M64 workflow audit | `PASS` | `finn/reports/m64-workflow-audit.md`؛ چهار YAML parse؛ نبود write path در `ci.yml` |
| M65 QR/عضویت security | `PASS` | بازتولید pre-fix با تست قرمز، سپس fix + 65 تست مرتبط + migration scratch |
| M66 D10 refresh | `UNKNOWN` | `session_refresh_test.dart` فقط در CI اجرا می‌شود؛ history: run `44247416109` 13 Flutter failure داشت (نام‌ها زیر سقف annotation) |
| M67 Studio auth/session | `PASS` | `finn/reports/m67-studio-auth.md`؛ Studio 217/9 + build، backend 24 passed |
| M68 signing key (SEC-01) | `BLOCKED` | تصمیم مالک دربارهٔ Play App Signing/چرخش کلید لازم است |
| M69 face vs QR | `BLOCKED` | تصمیم scope محصول + رضایت/مدل/مجوز |
| M70 Settings role gate | `PASS` | `finn/reports/m70-settings-role-gate.md` |
| M71 API coverage gate | `PASS` | `finn/reports/m71-api-coverage.md`؛ AST/tokenizer؛ 4 targeted + Studio full |
| M72 membership display | `UNKNOWN` | کد+تست نوشته‌شده، static gate سبز؛ runtime Flutter فقط در CI |
| M73 food logging | `UNKNOWN` | 25 backend passed + کاتالوگ MIT parse شد؛ Flutter runtime شاهد ندارد |
| M74 class cancel | `UNKNOWN` | pre-fix 200 → ownership fix؛ 46 backend passed؛ Flutter widget در CI |
| M75 notifications | `UNKNOWN` | 65 backend passed؛ Flutter runtime در CI |
| M76 readiness | `UNKNOWN` | 22 unit/integration passed؛ Flutter در CI |
| M77 weekly volume | `UNKNOWN` | 13 backend passed؛ Flutter در CI |
| M78 adaptive nutrition client | `UNKNOWN` | 74 backend passed؛ Flutter در CI |
| M79 JP7 crosswalk | `UNKNOWN` | regression assertions؛ Flutter در CI |
| M80 check-in history | `UNKNOWN` | 52 backend passed؛ Flutter در CI |
| M81 member chat | `UNKNOWN` | 13 chat + coverage gate؛ Flutter در CI |
| M82 phone change | `UNKNOWN` | backend full 810/2 + migration scratch؛ Flutter در CI |
| M83 wallet ledger | `UNKNOWN` | backend full 812/2 + route guard؛ Flutter در CI |
| M84 booking name | `UNKNOWN` | backend 20 targeted + full 853/2؛ نتیجهٔ مجزای widget test نامعلوم |
| M85 screening scope | `UNKNOWN` | نیازمند معیار بالینی مصوب و reviewer — تصمیم بیرونی |
| M86 offline contract | `PASS` (فقط قرارداد/backend) | `test_m57_sync.py` 12 passed |
| M87 Android outbox | `UNKNOWN` | Kotlin compile/Gradle/device/encryption policy انجام نشده؛ flag خاموش |
| M88–M89 | `BLOCKED` | وابستگیِ اثبات‌نشده به M87 / پیش‌نیاز بیرونی |
| **M90 member receipt** | `UNKNOWN` (منتظر CI) | `finn/reports/m90-member-receipt.md` — کد+۷ تست، static gate ۶۸/۰، Studio 219/9؛ `flutter analyze`/`test` محلی ممکن نبود |
| M91–M92 | `BLOCKED` | پیش‌نیاز credential/تصمیم بیرونی |
| M93 | `UNKNOWN` | بدون گیتِ اجراییِ قابل‌دسترس در این sandbox |
| M94 | `BLOCKED` | پیش‌نیاز بیرونی |
| M95 | `UNKNOWN` | — |
| M96 | `BLOCKED` | — |
| **M97 migration/backup** | `PASS` (backend+docs) | `finn/reports/m97-migration-drift.md` — ۵۲ جدول parity، یک head، baseline با stamp، مانور verify/restore؛ ۵ تست جدید |
| **M98 haptics + reduced motion** | `UNKNOWN` (منتظر CI) | `finn/reports/m98-haptics-motion.md` — messenger test + `MpMotion`؛ static gate ۷۲/۰ |
| M99 | این گزارش | — |

بازهٔ مستقل برند (M100–M106) در `LOOP-PLAN-M100-M106.md` و `finn/reports/m106-brand-identity-review.md`؛ آن track ترتیب این صف را جابه‌جا نکرد.

## ۲) گیت‌های اجراشده در این محیط (پس از M90/M97/M98)

| گیت | نتیجه |
|---|---|
| `pytest -q tests` از `mp-app/backend` | **867 passed / 1 skipped** (۲۲۳s) |
| همان suite از ریشهٔ مخزن | 861 passed / 1 failed — تنها شکست `test_monitoring::test_alert_rules_cover_slo_and_down` است که `../infra/monitoring/alerts.yml` را نسبت به cwd باز می‌کند؛ از `mp-app/backend` سبز (10 passed). **ثبت می‌شود، اصلاح نشد** (خارج از دامنهٔ این loops و گیت CI را نمی‌شکند) |
| `ruff check .` · `ruff format --check .` | All checks passed · 311 files already formatted |
| `bandit -r . -ll` (بدون tests) | rc=0، بدون یافتهٔ medium/high |
| `npm test` (Studio) | **219 passed / 9 skipped** (33 فایل) |
| `npx vitest run tests/apiCoverage.test.ts` | **4 passed** |
| `npm run build` (Studio) | موفق (`tsc -b` + Vite) |
| `tools/dart_gate.py --include-tests` | **۷۲ فایل Dart / ۰ یافته** |
| `tools/manifest_gate.py` | ۱ مانیفست / ۰ یافته |
| `scripts/docs_gate.py` | ۷ فایل Markdown · ۹۹ لینک محلی · ۳ Mermaid · SVG XML سبز |
| `git diff --check` | پاک |
| `flutter pub get/analyze/test`, Gradle, emulator | **اجرا‌نشده** — Flutter/Dart/Java/Android SDK در این sandbox نصب نیست و دانلود از `storage.googleapis.com`/`dl.google.com` مجاز نیست؛Codespaces هم ساخته نشد (هزینه/دسترس) |
| `pip-audit` | **اجرا‌نشده** — venv موقت من pinned نبود؛ اجرای آن دربارهٔ این sandbox نتیجه می‌داد نه `pyproject.toml` پروژه. در CI اجرا می‌شود |
| REA / ECC subagents | **اجرا‌نشده** — نه `claude` CLI، نه REA، نه کلید API (بررسی شد: unset). چک‌لیست‌های `.claude/agents/*` دستی اعمال شدند و به‌عنوان اجرای ایجنت ثبت نمی‌شوند |

## ۳) بلوکرهای بیرونی (هیچ‌کدام با حدس باز نشدند)

1. **SEC-01 signing key (M68)** — تصمیم مالک + چرخش کلید.
2. **Face vs QR scope (M69)** — تصمیم محصول/مدل، رضایت، مسیر لغو.
3. **Screening (M85)** — معیار بالینی، منبع و reviewer مصوب.
4. **M87→M88/M89** — Kotlin/Gradle compile، Android persistence، دستگاه واقعی.
5. **Flutter runtime (M66, M72–M85, M90, M98)** — analyzer/widget test فقط در CI یا Codespaces.
6. **M104/M105 برند** — اندازه‌گیری startup و adaptive mask روی دستگاه؛ `app_icon.png` دست‌نخورده است.
7. **هزینه/ابزار** — Repowise LLM و هر model پولی: خاموش (بدون approve). Codespaces: config آماده، ماشین ساخته نشد.

## ۴) بازتولید در یک محیط دارای ابزار

```bash
# Backend (گیت‌های CI-مانند)
python3 -m venv .venv && .venv/bin/pip install -e "mp-app/backend[dev]"
cd mp-app/backend
../.venv/bin/python -m pytest -q tests          # انتظار: 867 passed / 1 skipped
../.venv/bin/ruff check . && ../.venv/bin/ruff format --check .
../.venv/bin/bandit -r . -ll -q

# گیت‌های خاص این بسته
../.venv/bin/python -m pytest -q tests/integration/test_m97_migrations_and_backup.py \
    tests/integration/test_m47_migration_drift.py tests/integration/test_backup_drill.py

# Studio
cd mp-app/studio && npm ci && npm test && npm run build

# Flutter (نیازمند SDK — Codespaces/CI)
cd mp-app/client && flutter pub get \
  && flutter analyze --no-fatal-infos \
  && flutter test test/shop_orders_receipt_test.dart test/motion_haptics_test.dart \
       test/set_feedback_sheet_test.dart test/classes_cancel_test.dart && flutter test

# بدون SDK: گیت ایستا
python3 mp-app/client/tools/dart_gate.py --include-tests   # نیاز: pip install tree-sitter tree-sitter-dart
python3 scripts/docs_gate.py
```

## ۵) package این بسته (چه چیزی commit/push شد)

طبق D-047 فقط این گروه به `arena/4f336f66-mp` می‌رود: اسناد agent/docs (AGENTS.md، docs/README، handoff، ADR/architecture index، atlas SVG، `scripts/docs_gate.py` + job `docs` در `ci.yml`)، اصلاحات M97 (`backup.py`، دو تست backend، OPS-RUNBOOK، runbooks/provisioning)، M90 و M98 در `mp-app/client/lib|test`، و گزارش‌های `finn/reports/m90-*.md`/`m97-*.md`/`m98-*.md`/`m99-*.md`/`m106-*.md`.

عمداً بیرون Git می‌مانند: `evidence/` و باقی گزارش‌های untracked محلی، `venv/`، `.repowise/`، هر فایل signing/APK، و `pubspec.lock` تولیدی.

## ۶) بازگشت

- M97: حذف `test_m97_migrations_and_backup.py` و برگرداندن `backup.py`/دو سند؛ `verify`/`--extras-to` می‌روند.
- M90/M98: حذف پنج فایل جدید (`persian_format.dart`, `order_receipt_sheet.dart`, `my_orders_sheet.dart`, `haptics.dart`, `motion.dart` + تست‌ها) و برگرداندن `shop_page.dart`, `set_feedback_sheet.dart`, `classes_page.dart`, `app_shell.dart`.
- هیچ migration/schema/dependency در این بسته نیست؛ بازگشت، داده یا استقرار را درگیر نمی‌کند.
