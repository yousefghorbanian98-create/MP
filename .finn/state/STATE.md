# FINN State — وضعیت جاری لوپ

## Snapshot جاری — M84 تا M87 و CI follow-up (2026-11-16)

- شاخهٔ فعال `arena/4f336f66-mp` روی origin در `b58d0536290b9ad80158c8c67159f6833eaab563` (`b58d053`) است. CI `44247416109` همین commit را آزمود. Worktree اکنون helper را به یک annotation تجمیعی برای همهٔ تست‌های fail تغییر می‌دهد تا محدودیت تعداد annotationهای GitHub چهار نام را حذف نکند؛ این patch هنوز push نشده. Untracked evidence/reports انتخابی stage نشده و دست‌نخورده مانده است.
- CI `44247416109`: backend، Studio، live-contract و e2e-api **PASS**؛ `flutter analyze` **PASS**, `flutter test` **FAIL** (13 failures), manifest **SKIP**؛ `secret-scan` **FAIL** روی matchهای تاریخی. Helper نام 9 test را annotation کرد، اما GitHub سقف annotation-step را اعمال و چهار نام دیگر را حذف کرد؛ raw log/artifact از signed URL با EOF دریافت نشد. فایل‌های نام‌دار: `bodycomp_real_data_test`, `session_refresh_test` (2), `volume_card_test` (3), `adaptive_nutrition_test`, `member_checkin_history_test` (2). گزارش: `finn/reports/ci-follow-up-441922-441942.md`.
- شواهد: CI `44247416109` backend، Studio، live-contract و e2e-api را پاس کرد؛ local Studio API coverage **4 passed**, full **219 passed / 9 skipped** و build قبلاً پاس شده‌اند. Backend full **853 passed / 2 skipped, 86.30% coverage** و M84/M86 targeted **20 passed** شواهد قبلی‌اند؛ Ruff full backend پاس. Dart Tree-sitter **64/0**, manifest **1/0**, workflow YAML parse و Kotlin syntax **2/0** پاس‌اند (Kotlin نه compile/type-check)؛ shell scripts **23** در بررسی قبلی پاس. Python diagnostic helper با synthetic JSON و `py_compile` بررسی می‌شود؛ Flutter/Dart executable محلی نیست، پس این گیت‌ها جایگزین full Flutter tests یا Android runtime/build نیستند.
- CI `44247416109` تأیید کرد analyzer پس از fixهای `0ace8fe` و connectivity test در `01a7177` پاس است. JSON diagnostic helper 13 failure شمرد ولی فقط 9 نام را به‌علت annotation cap نشان داد. Worktree patch این‌ها را به یک annotation با شمارش کامل و فهرست همهٔ test names/source lines تبدیل می‌کند؛ assertion values و stack traces چاپ نمی‌شوند. CI تازه لازم است.
- **M84 `UNKNOWN`**؛ analyzer پاس شده اما full Flutter test run `44247416109`، 13 failure دارد و نتیجهٔ مجزای M84 widget test قابل‌تأیید نیست. **M85 `UNKNOWN`** چون source/معیار بالینی و بازبین واجدصلاحیت مصوب نداریم. **M86 `PASS` فقط برای قرارداد/backend**، نه Client. **M87 `UNKNOWN`**؛ feature flag `MP_ANDROID_OFFLINE_FEEDBACK_ENABLED=false` می‌ماند تا Flutter/native persistence و سیاست رمزنگاری دستگاه بررسی شود. M88 از وابستگی M87 جلوتر نمی‌رود.
- Gitleaks history در `44247416109` همچنان fail است. گزارش فقط مسیر/rule/commit را نگه می‌دارد؛ مقادیر خارج از گزارش‌اند. مقادیر password تاریخی placeholder واضح نبودند و باید تا تأیید مالک **potentially real/exposed** فرض شوند؛ چرخش credential/signing key را مالک جداگانه از مسیر امن بررسی کند. نه allowlist گسترده، نه rewrite تاریخچه، نه دست‌زدن به کلید انجام نشد.
- `.devcontainer` و handoff فقط آماده‌اند؛ Codespace واقعی ساخته/هزینه نشده و deferral تا handoff پایانی حفظ است. `evidence/` و گزارش‌های آرشیوی انتخابی/دست‌نخورده می‌مانند. هیچ APK/final bundle، release، deploy، DB تولید، SMS یا پرداخت واقعی انجام نشده.

## Snapshot تاریخی — پس از M83 (2026-11-16)

- وضعیت: `IN_PROGRESS`; M63/M64/M65/M67/M70/M71 همان `PASS`های شاهددار؛ M66/D10 و M72–M83 برای Flutter runtime `UNKNOWN`; M68/M69/M89/M91/M92/M94/M96 `BLOCKED`; M85/M93/M95 `UNKNOWN`. M83 دفتر واقعی credit/debit، ماندهٔ هم‌snapshot، ترتیب و pagination را در backend و Client پیاده کرد؛ backend/Studio/static gates سبزند، اما Flutter `pub get`/analyze/widget/full tests/APK اجرا نشده‌اند، پس M83 از نظر end-to-end کلاینت `UNKNOWN` است. شمارش جاری: backend full **812 passed/2 skipped**, Studio **219 passed/9 skipped** + build، Dart static **61/0**, route inventory **119**; route guard و API coverage سبزند. طبق صف D-033، loop مستقل بعدی M84 آماده است؛ M99 و handoff Codespaces همچنان انتهای بازه‌اند. منبع: `docs/MuscleParadise/LOOP-PLAN-M63-M99.md`.
- اصل اجرای جاری D-033: همهٔ loopهای TODO که صف جاری `READY` کرده بدون نظارت/تأیید روتین ادامه می‌یابند؛ تصمیم محدود و برگشت‌پذیر ثبت می‌شود، blocker واقعی فقط loop وابسته را متوقف می‌کند و loopهای مستقل ادامه دارند. هیچ گیت یا PASS بی‌شاهدی مجاز نیست.
- شاخه: `arena/4f336f66-mp`; پایه ثبت‌شده `d64e3b0`. تغییری commit/push نشده است.
- M63: مرز n8n و اسناد هم‌راستا؛ شاهد مستندی و جست‌وجوی متنی، نه تست محصول. جزئیات در نقشهٔ loop.
- M64: workflowها بازبینی و YAMLها با parser بررسی شدند؛ CI/APK diagnostics به artifact منتقل و permissionها تفکیک شدند. `container packages:write`, APK manual delivery/Release write و Dokploy secret webhook هنوز اثر باقی‌مانده‌اند. هیچ workflow اجرا نشد؛ تنظیمات branch protection/secret در GitHub تأیید نشده‌اند. شاهد: `finn/reports/m64-workflow-audit.md`.
- M65: SEC-02 روی SQLite موقت با دادهٔ مصنوعی پیش از fix پنج شکست داد. پس از fix، مجموعهٔ 65 تست مرتبط، ruff و migration scratch upgrade/downgrade/upgrade سبز شدند. شاهد: `finn/reports/m65-qr-security.md`; no production DB/CI/device E2E.
- M66/D10: `UNKNOWN`; تست Dart حاضر است و نیازمند اجرای واقعی Flutter است. SDK و mirrorهای رسمی/CFUG/Runflare/Myket/TarazERP و Pub در این sandbox قابل‌دریافت نبودند (TLS/EOF، 0 archive bytes)؛ CI هم روی شاخهٔ جاری اجرا نشده. نبود executable محلی به‌تنهایی blocker پروژه نیست؛ handoff پایانی در `finn/reports/codespaces-user-handoff.md`.
- M67: `PASS`; گزارش `finn/reports/m67-studio-auth.md`. در همان loop، Studio **217 passed / 9 skipped** و build/typecheck موفق؛ backend auth/API/M65 subset **24 passed** و Ruff موفق بود. OTP، refresh single-flight/یک retry، 403/auth recursion guard، role gate، logout/access revocation نشست‌های جدید و raceهای refresh/logout با تست پوشش دارند.
- M67 caveat: tokenها هنوز `localStorage` هستند، نه HttpOnly؛ JWTهای legacy بدون `sid` تا انقضای کوتاه خود stateless می‌مانند؛ ورود SMS واقعی/CI/production آزموده نشده. `npm audit` full چهار آسیب‌پذیری dev toolchain (۳ moderate، ۱ high) دارد؛ `npm audit --omit=dev` صفر است. `npm run lint` به‌خاطر نبود ESLint/config اجرا نشد.
- M70: `PASS`; `RoleManager` فقط برای super_admin render/fetch می‌شود؛ admin همچنان Settings مجاز را می‌بیند اما نقش‌مدیریت super_admin-only را نه. Studio 217/9 و build سبز؛ backend matrix test `/admin/users`، admin=403 را حفظ کرد. شاهد: `finn/reports/m70-settings-role-gate.md`.
- M71: `PASS` محلی; گیت مسیرهای واقعی در `studio/tests/apiCoverage.test.ts` از AST تایپ‌اسکریپت و tokenizer دارت استفاده می‌کند؛ comment/string-only مصرف‌کننده نیست و پارامتر client مسیر ثابت backend را wildcard نمی‌کند. 114 route یا call دارند یا exception؛ 34 مورد بدون call مستقیم (31 TODO، 3 شاهد عملیاتی). targeted 4 passed، full Studio 217/9، build سبز. محدودیت: route inventory فقط path دارد؛ verb/runtime/CI/backend/Flutter/E2E اثبات نشده. گزارش: `finn/reports/m71-api-coverage.md`.
- شواهد تاریخی پیش از این بازه: M61 (backend 785 passed / 1 skipped؛ Studio 196 passed / 9 skipped؛ CI run `43733055890`). این‌ها اجرای تازهٔ M63–M70 نیستند.
- ابزارهای جاری: `.finn/ecc`، `~/toolchain/rea` و `.mcp.json` در sandbox حاضر نیستند؛ فایل‌های `.claude/agents/` نقش/چک‌لیست‌اند و subagent اجرا نشده است.
- n8n: instance/credential/integration پیدا نشده؛ مرز آن در ADR-005 ثبت است و هیچ notifier ساخته نشده است.
- کارگاه از baseline کثیف بود و همچنان باید همهٔ آثار حفظ شوند؛ پیش از هر تغییر وضعیت تازه بگیر و هیچ فایل قبلی را reset/overwrite نکن. هیچ‌کدام از untrackedهای جاری حذف نشوند.
- M82: گزارش `finn/reports/m82-phone-change.md`؛ dual OTP به ترتیب شمارهٔ قدیم/جدید، uniqueness + unique-race conflict handling، challenge دارای hash/TTL/attempt-limit و user scope، `auth_version` برای ابطال JWTهای قدیمی و revoke تمام refreshها. Fake-SMS backend full **810/2**، Studio **219/9** + build، Dart static **60/0**، Alembic drift check clean، routes **118**. Flutter runtime `UNKNOWN` به‌علت نبود Flutter/Dart/Java/Android SDK؛ هیچ SMS واقعی/CI/production DB/push/commit انجام نشد.
- M83: گزارش `finn/reports/m83-wallet-ledger.md`؛ endpoint از `wallet_transactions` واقعی، ماندهٔ SQL و صفحه در یک statement، ID DESC + cursor، ownership member/staff؛ Wallet UI مانده را از همان ledger response می‌گیرد و Payment history جدا می‌ماند. Backend full **812/2**, Studio **219/9** + build/API coverage, Dart static **61/0**, route guard pass, routes **119**. Flutter widget tests افزوده ولی runtime اجرا نشده؛ `flutter`/`dart`/`java`/Android SDK نیستند، پس M83 `UNKNOWN` و loop بعدی M84 است. بدون CI/production/commit/push.
- در M81 تا M83 هیچ Flutter suite/build/analyze، CI، GitHub workflow، push، release، deploy/rollback یا production DB migration اجرا نشد؛ Studio test/build محلی و backend tests متمایزند. هیچ‌یک از untrackedهای baseline حذف/overwrite نشود.

## Snapshot تاریخی پیش از ادامهٔ M45/M61 (حفظ‌شده)

- وضعیت وقت: READY (فاز ۰ بازسازی‌شده با ابزارهای رسمی — آمادهٔ M45)
- میکرو-چرخهٔ وقت: M43-c3 + M44 تمام‌شده | بعدی: M45 (استودیو روی API واقعی)
- شمارنده تلاش‌های رفع خطا در چرخهٔ وقت: 0
- آخرین گیت سبزِ ثبت‌شده در همان snapshot: REA-REVIEW-2026-11-15 (۲۷۹ تست، ۴/۴ eval درصد، ۳/۳ eval تجویز، ruff 0، tsc 0، vitest 18)
- شاخهٔ کاریِ جاری این نشست: arena/4f336f66-mp (HEAD: d64e3b0)

## وضعیت فعلی sandbox و ابزارها

- در sandbox بازسازی‌شدهٔ فعلی، `/home/user/toolchain`، `.finn/ecc` و `.mcp.json` **وجود ندارند**؛ نصب‌های بیرون workspace/gitignored از اجرای قبلی به این محیط نیامده‌اند.
- فایل‌های موقت بررسی‌شدهٔ همین کار در `/tmp` هم باقی نمانده‌اند. فایل‌های منبع/مستندات داخل workspace نگه داشته شده‌اند.
- نسخه‌ها و نتایج نصب قبلی در ادامه ثبت شده‌اند؛ ابزارهای اجرایی فعلاً فعال نیستند و با اسکریپت پین‌شده قابل بازسازی‌اند.

## ابزارها (نسخه‌ها و pinهای ثبت‌شده)

- **ECC:** `affaan-m/ECC` — کامیت `d2ef2680594f9a17526a6e1a2e18b3d242c5d17b` (۲۰۲۶-۱۱-۰۶، v2.2.3)
  - ۷۱ ایجنت / ۳۱۴ skill / ۹۸ فرمان / ۲۳ بستهٔ قوانین / hookها → promptهای نصب‌شده در `.claude/`
  - clone کامل در `.finn/ecc/` طی اجرای قبلی تأیید شد؛ این مسیر gitignored و در sandbox فعلی حاضر نیست.
  - ⚠️ نصب قدیمی از فورک `WorldFlowAI/everything-claude-code@432485ba` بود (۲۰۲۶-۰۱-۲۳) — منسوخ شد
- **REA:** `morluto/rea` v6.9.0 در اجرای قبلی تأیید شد؛ package فعلاً در `~/toolchain/rea` نصب نیست.
  - Node لازم: `^22.23.4 || ^24.22.1 || >=26.12.1`؛ Node سیستم `22.22.3` است → portable `24.22.3` در اجرای قبلی استفاده شد، اما فعلاً وجود ندارد.
  - skill: `.claude/skills/reverse-engineer-anything` در workspace حاضر است · MCP: `.mcp.json` در این sandbox غایب و توسط اسکریپت بازتولید می‌شود.
  - موتور native (Ghidra/Hopper/IDA/JADX): **نصب نیست — لازم هم نیست**
  - اثبات کارکرد: `identify-flutter-build` روی APK خودمان → `flutter_detected: true`, `dart_version 3.14.0`, coverage: partial
  - راهنما: `docs/MuscleParadise/REA-OPERATIONS.md`
- **اسکریپت بازتولید:** `docs/MuscleParadise/finn/install-toolchain.sh` (`all|ecc|rea`، idempotent)

### بازتأیید نصب ابزارها (2026-11-16)

- ECC در کامیت پین‌شده دوباره checkout شد؛ `.claude/{agents,commands,skills,rules,hooks}` با منبع ECC یکسان است، به‌جز skill جداگانهٔ REA (۹ فایل). هیچ فایل محلی overwrite نشد.
- REA CLI `6.9.0` با Node پرتابل `24.22.3` اجرا شد؛ smoke test واقعی `inspect-sqlite-database` روی DB موقت موفق بود.
- `.mcp.json` پروژه‌ای دارد؛ setup dry-run هیچ IDE/client نصب‌شده‌ای پیدا نکرد. باید client مصرف‌کننده reload/approve شود تا MCP در آن فعال شود.
- `rea doctor` عمداً `healthy: false` می‌دهد: Hopper/Ghidra/IDA/JADX/Kuna حاضر نیستند و REA skill به setup-managed client وصل نیست؛ Node/host سالم‌اند، و این نصب را برای قابلیت‌های موجود مثل SQLite بی‌استفاده نمی‌کند.
- `npm audit` برای REA سه یافتهٔ **moderate** از مسیر Frida→minimatch گزارش داد؛ finding با شدت high/critical گزارش نشد. `npm audit fix --force` اجرا نشد چون REA را به نسخهٔ ناسازگار 6.4.0 downgrade می‌کرد.
- `install-toolchain.sh` به‌روزرسانی شد تا ECC را از pin بخواند، فایل‌های `.claude/` را فقط افزایشی نصب کند، REA را روی 6.9.0 پین کند و MCP configهای دیگر را حفظ کند؛ `install-ecc.sh` اکنون به همین نصب‌کنندهٔ امن delegate می‌کند.

## وضعیت CI (ران 43723865660 — قرمز)

| Job | علت قرمز | رفع |
|---|---|---|
| backend | `ruff format --check`: ۵۲ فایل | `ruff format .` |
| client-flutter | `test/set_feedback_sheet_test.dart` ایمپورت `package:mp_app/...` (نام پکیج `mp_client`) | تغییر ایمپورت → ۵ خطا + ۱ تست فیل رفع می‌شود |
| studio | ✅ سبز | — |
| e2e-api | ⏭️ skip (وابستهٔ backend) | بعد از سبزی backend |

تست واقعی: backend `298 passed`، client `17 passed / 1 failed-to-load` → **کد سالم است، قرمزی از فرمت و نام پکیج است.**

## M45 — استودیو روی API واقعی (2026-11-15) ✅

| جزء | شاهد |
|---|---|
| `GET /admin/attendance` (سری روزانه، جلسه باز/بسته) | ۹ تست در `test_m45_admin_attendance.py` |
| `GET /admin/members-summary` (وضعیت اشتراک + days_left سقف‌دار) | همان فایل |
| `GET /admin/checkins` (جریان ورودها، شامل ردشده) | ۵ تست در `test_m45_checkin_feed.py` |
| `GET /programs` (فهرست با نام عضو + شمارش وضعیت) | ۵ تست در `test_m45_programs_list.py` |
| استودیو: `src/data/mock.ts` **حذف شد** | REA evidence `ev_a3e81c13…` — ۲۶ منبع سورس، بدون mock |
| استودیو: Dashboard/Members/Programs/CheckIn روی API | ۳۰ تست vitest + tsc صفر خطا |

**گیت‌ها:** backend ۳۱۷ تست سبز · ruff check/format ۰ · studio tsc ۰ · vitest ۳۰.
**نکتهٔ صادقانه:** `alembic check` drift نشان می‌دهد (۲ نبود-index + nullable ناسازگار) — این drift **قبل از M45** وجود داشت، من مدلی اضافه نکردم. برای M46 در صف است.

## وضعیت CI — ✅ سبز (2026-11-15, run 43733055890)
| Job | نتیجه |
|---|---|
| studio | ✅ |
| client-flutter | ✅ **اولین بار** |
| backend | ✅ |
| e2e-api | ✅ |

## استثناهای صادقانه (تا رفع نشوند «آمادهٔ کامل» اعلام نشود)
1. Flutter SDK محلی نیست → تست‌های Dart محلی اجرا نشدند (اولین اجرا در CI).
2. `alembic check` drift دارد (۱۴ عملیات) — پیش از M45 بود؛ migration در M46.
3. APK تازه با اصلاحات Android ساخته نشده.

## M46 — بازبینی و ترمیم کامل (2026-11-15)
HEAD `4ef7c08` · CI 43746770460 سبز ۴/۴ · **۱۵ باگ واقعی رفع شد**

### رفع‌شده
| # | باگ | کشف با |
|---|---|---|
| 1 | Settings کاملاً دکوری (flags در useState) | ممیزی UI |
| 2 | `GET /admin/flags` نداشت | TDD |
| 3 | `/members/me` نقش نمی‌داد | ممیزی TopBar |
| 4 | جست‌وجو در ۶ صفحه بی‌اثر | grep |
| 5 | عنوان finance/analytics گم | Sidebar vs TopBar |
| 6 | هویت hardcoded «مربی مهدی» | خواندن کد |
| 7 | `configure_logging` هرگز صدا زده نمی‌شد | vulture |
| 8 | استخر اتصال ۱۵ < ۴۰ ترد | locust |
| 9 | SQLite بدون WAL | locust |
| 10 | **FK خاموش** → ۳ خرابیِ خاموش | PRAGMA foreign_keys=ON |
| 11 | `exercise_id` بدون کاتالوگ | تست FK |
| 12 | `approved_by=0` (TODO رهاشده) | تست FK |
| 13 | vite بدون proxy → فرانت به بک نمی‌رسید | تست زنده |
| 14 | ۴ دکمهٔ محصول بدون onClick | ممیزی دکمه‌ها |
| 15 | `ProgramOut` بدون `approved_by` | تست زنده |

### گیت‌ها
backend ۳۵۱ · ruff پاک · bandit ۰H/۰M · tsc ۰ · vitest ۳۰ · semgrep ۰/۱۴۹ فایل

## به‌روزرسانی M61 (۲۰۲۶-۱۱-۱۶)

- میکرو-چرخهٔ جاری: **M61** (پاک‌سازی P0 از `TODO-2026-11-16.md`) — تکمیل‌شده
- گیت‌ها: backend **۷۸۵ pass / ۱ skip** · studio **۱۹۶ pass / ۹ skip** · tsc پاک ·
  ruff پاک · `dart_gate` ۴۱ فایل / ۰ یافته
- بسته‌شده در این چرخه: D1 (ثبت چهره ۴۰۳)، D2 (چک‌این ۴۲۲)، D3 (نبود logout)،
  D5 (بنر تخفیف دروغین + S2 انقضا)، D6 (گیت دروغ‌گو)، D7 (VolumePanel روی items[0])
- مرحلهٔ بعدی: D4 (پیکرسنجی جعلی)، D9/D10 (refresh نشست)، S3 (اعلان‌ها)

## به‌روزرسانی M97 (۲۰۲۶-۱۱-۱۸)

- میکرو-چرخهٔ جاری: **M97** (Alembic drift / تاریخچهٔ مهاجرت / مانور backup+restore) — `PASS` برای دامنهٔ backend+docs
- گیت‌های محلی: backend targeted **36 passed** · کل suite **861 passed / 1 failed (cwd-sensitive) / 1 skipped** · ruff check+format سبز · bandit `-ll` پاک · docs gate **7 فایل / 99 لینک / ۳ Mermaid**
- یافته و اصلاح: `scripts/backup.py` حالا `verify` و `restore --extras-to` دارد؛ مانور scratch بدون بازنویسی فایل‌های زنده
- محدودیت ثبت‌شده: SQLite-only؛ لایهٔ CHECK/view/trigger مقایسه نشد؛ DB واقعی/Postgres آزمون نشده؛ Flutter/Codespaces در این sandbox در دسترس نیست
- مرحلهٔ بعدی: **M98** (UX-G3 haptics + Q5 micro-interactions با test و reduced-motion)، سپس M99 گزارش/بستهٔ نهایی

## به‌روزرسانی M90/M98 (۲۰۲۶-۱۱-۱۸)

- **M90** رسید سفارش عضو در اپ: `orderReceiptProvider` + «سفارش‌های من»/شیت رسید (fail-closed، فقط GET) → `UNKNOWN` تا CI
- **M98** `MpHaptics` + `MpMotion` (کاهش حرکت) در بازخورد ست/کلاس/فروشگاه/شل → `UNKNOWN` تا CI؛ shared-element عمداً نه
- گیت‌های محلی پس از این دو loop: backend **867 passed / 1 skipped** (از `mp-app/backend`) · Studio **219 passed / 9 skipped** + build · ruff check/format سبز · bandit `-ll` پاک · Dart static gate **۷۲ فایل / ۰ یافته** · docs gate **7 فایل / 99 لینک / ۳ Mermaid**
- ابزار این nوبت: venv محلی `/home/user/.venv-mp` (backend deps + ruff/bandit + tree-sitter برای `dart_gate`) و `node_modules` استودیو از npm — بیرون از snapshot؛ برای بازتولید: `python3 -m venv .venv && pip install -e "mp-app/backend[dev]" tree-sitter tree-sitter-dart`
- مرحلهٔ بعدی: **M99** — گزارش شواهد/بلوکرهاب، تطبیق با CI پس از push طبق D-047، و نهایی‌سازی handoff Codespaces؛ بدون release/deploy/ساخت ماشین ابری
