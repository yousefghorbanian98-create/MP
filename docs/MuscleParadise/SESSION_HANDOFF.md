# Handoff نشست — Muscle Paradise

> این فایل **خلاصهٔ جاری برای ادامهٔ کار** است، نه آرشیو گفتگو و نه منبع نهایی وضعیت محصول. پیش از فشرده‌سازی context یا پایان هر کار معنادار، همین snapshot را جایگزین/به‌روز کن؛ تاریخچه را با انباشت transcript طولانی نکن.

## Snapshot فعلی

- **هدف پایدار کاربر:** توسعهٔ محصول با کمک AI، بدون بازخوانی بی‌هدف کل مخزن؛ معماری، تصمیم‌ها و قدم بعدی باید در فایل‌های Git-tracked قابل انتقال باشند.
- **کار این handoff:** راه‌اندازی ورودی ایجنت‌ها و نقشهٔ مستندات؛ مستندات C4، نقشهٔ ماژول‌ها و پنج ADR موجود را کشف و به آن‌ها پیوند بده، نه اینکه دوباره از حافظه بازنویسی شوند.
- **وضعیت این کار:** ساختار مرجع در `AGENTS.md` و `docs/README.md` اضافه شده؛ فهرست‌های معماری/ADR و همین handoff تکمیل شده‌اند. `AGENTS.md` اکنون صریحاً D-033 و مرز اجرای واقعی ECC/REA را می‌گوید. این کار تغییری در منطق runtime محصول ایجاد نمی‌کند.
- **صف محصول:** در snapshot فعلی TODO جاری خودش `docs/MuscleParadise/TODO-2026-11-16.md` را مرجع معرفی می‌کند و نقشه‌های جاری را در همان سند مشخص کرده است. پیش از ادامه، سربرگ آن و وجود TODO جدیدتر را بررسی کن؛ فقط loopی را ادامه بده که واقعاً در مرجع جاری فعال/مجاز است.
- **Repowise بعدی:** `DX-REP-01` در بخش P3 همان TODO ثبت شد؛ زمان مناسبش پیش از epic بزرگ چندنشستی یا انتقال به clone تازه است. فعلاً MCP برای Arena وصل نیست و در وضعیت بدون LLM/full-text بماند.
- **اسناد تاریخی:** `MASTER_MAP.md`, `FINN_LOOP.md`, `READY-TO-RESUME-2026-11-15.md` و گزارش‌های تاریخ‌دار به‌تنهایی صف جاری نیستند. محدودیت‌ها و وضعیت امنیت/انتشار را از TODO و سند امنیتی جاری بخوان؛ این فایل آن‌ها را کپی نمی‌کند.

## Repowise و قابلیت انتقال

- Repowise `0.61.0` در این workspace فقط در `venv/repowise` نصب شده و index محلی زیر `.repowise/` است؛ هر دو مسیر Git-ignored هستند. قاعدهٔ ignore برای `.repowise/` در `.gitignore` تغییر محلیِ موجود از مرحلهٔ setup است؛ آن را حذف نکن.
- index با حالت code-derived و بدون LLM ساخته شده بود: ۱٬۵۸۳ فایل پردازش، ۵۳۶ صفحه، full-text فعال و semantic خاموش؛ هزینهٔ مدل صفر بود.
- اتصال MCP برای Arena Agent Mode انجام نشده است؛ در clone/نشست دیگری وجود این index یا virtualenv را فرض نکن.
- حافظهٔ پایدار و قابل انتقال: این فایل برای اشارهٔ کوتاه، [AGENTS.md](../../AGENTS.md) برای پروتکل ایجنت، و مستندات محصول/معماری لینک‌شده از [docs hub](../README.md) هستند. Repowise فقط شتاب‌دهندهٔ اختیاری است.

## نتیجه و شواهد آخرین کار

- **کارهای نشست:** ورودی مشترک ایجنت‌ها و نقشهٔ معماری/تصمیم‌ها/حافظهٔ نشست ساخته شد؛ سپس `DX-REP-01` به P3 TODO افزوده شد تا تکمیل Repowise در زمان مناسب برنامه‌ریزی شود. C4 و ADRهای موجود دوباره‌نویسی نشدند.
- **مسیرهای تغییرکرده:** `AGENTS.md`, `README.md`, `docs/README.md`, `docs/MuscleParadise/SESSION_HANDOFF.md`, `docs/MuscleParadise/TODO-2026-11-16.md`, `docs/MuscleParadise/architecture/README.md`, `docs/MuscleParadise/adr/README.md`, `docs/MuscleParadise/adr/TEMPLATE.md`, `docs/MuscleParadise/assets/knowledge-atlas.svg`, `scripts/docs_gate.py`, `.github/workflows/ci.yml`.
- **پروتکل واقعی این مسیر:** نصب Repowise، hub/hand-off و DX-REP-01 را عامل اصلی Arena انجام داد؛ هیچ چرخهٔ کامل F.I.N.N، subagent از ECC یا اجرای REA در این کار انجام نشد. بررسی محیط نشان داد `claude`، `claude-code` و `rea` روی PATH نیستند و `.finn/ecc` و `~/toolchain/rea` هم حاضر نیستند. گیت محلی مستندات و بررسی دستی پیوندها اجرا شدند؛ این‌ها جای ECC/REA یا بازبینی مستقل را نمی‌گیرند.
- **اعتبارسنجی مستندات:** `python3 scripts/docs_gate.py` موفق شد: ۷ فایل Markdown، ۹۹ پیوند محلی، ۳ بلوک Mermaid، سرفصل‌های handoff، لینک‌های README و XML/SVG. پس از افزودن DX-REP-01، پیوندهای آن به hub/معماری/هندآف محلی بررسی شدند؛ `git diff --check` نیز موفق بود. job مستندات به CI اضافه شده ولی GitHub Actions در این نشست اجرا نشده؛ runtime/backend/frontend تست نشدند.
- **اثر محصول:** کد یا رفتار runtime تغییر نکرد؛ Repowise مجدداً اجرا نشد و هیچ مدل/embedding استفاده نشد.
- **حفظ workspace:** بستهٔ M63–M99 + M107/M108 روی `origin/arena/4f336f66-mp` است (تا `2ac6ecc`)؛ `evidence/` و گزارش‌های تاریخی `finn/reports/M0*` عمداً untracked ماندند و `.repowise/`/venv در ignore. پیش از ادامه، `git status` و head را با `gh run list --branch arena/4f336f66-mp --limit 1` تطبیق بده — اگر sandbox تازه‌ای checkout را به پایه برگردانده باشد، `git fetch` + `git reset --mixed <head>` کار می‌کند (بدون `--hard`؛ این دقیقاً همان چیزی است که یک بازسازی mid-session را بی‌ضرر کرد).

## اقدام بعدی

1. در نشست بعدی، ابتدا وضعیت Git و این handoff را بخوان؛ سپس `AGENTS.md` و [docs hub](../README.md).
2. **گیت‌های Client/Android را دستی اجرا نکن — `client-pinned` آن‌ها را می‌گیرد (M108).** جاب `client-pinned` در `ci.yml` روی Flutter پین‌شدهٔ devcontainer (پین از `.devcontainer/Dockerfile` پارس می‌شود؛ drift = fail) اجرا می‌کند: `dart format` **گیتِ کشنده** (از M109) · analyze · `test --coverage` · `flutter build apk --debug`. شاهد فعلی روی `cf0ef2c` (run `44348498677`؛ پیش‌تر `7a3486a`/`44325309997`): **156 passed / 0 failed / 0 skipped**، coverage **77.2%**، apk ساخته شد ⇒ کامپایل Kotlin/Gradle (M87) تأیید؛  اعداد از `gh api "repos/<repo>/check-runs/<job-id>/annotations"` خوانده می‌شوند (مسئلهٔ M95: `--log` برای jobهای Flutter چیزی برنمی‌گرداند). **`apk.yml` را dispatch نکن** تا SEC-01 باز است (keystore مخزن را استفاده می‌کند).
3. **کار دستیِ باقی‌مانده برای کاربر فقط گوشی است (§۶ runbook).** M109 (فرمت ۶۵ فایل) با workflow `client-format-fix` و PR #1 بسته شد؛ Codespace ریل لازم نیست. اگر روزی لازم شد، `.github/workflows/client-format-fix.yml` الگوی «CI انجام می‌دهد، PR بازبینی می‌شود» است: `git add -u -- '*.dart'` (نه `-A`)، اثبات روی blobهای staged، PR در CI با `gh api -X POST /repos/{}/pulls` باز می‌شود، نه `gh pr create` — و توجه کن که «Allow GitHub Actions to create and approve pull requests» در این مخزن **خاموش** است، پس job token نمی‌تواند PR بسازد (403)؛ workflow شاخه را می‌فرستد و `::warning` می‌دهد و PR را ایجنت/انسان باز می‌کند. هرگز `metadata:` را به `permissions:` اضافه نکن: کلیدِ نامجاز است و کل فایل را بی‌اعتبار می‌کند.
4. **اگر لاگ Codespace/دستگاه از کاربر آمد:** همان را در [runbook M107](runbooks/codespaces-execution.md) با مرحله‌اش تطبیق بده و فقط بر اساس خروجی، status همان loop را عوض کن (M87 کامپایل، M104 startup، M105/M106 ماسک، بُعد دستگاه M89/M90/M98). بدون لاگ، `UNKNOWN` می‌ماند.
4. اگر کاربر قابلیت محصولی مشخصی خواست، مرجع صف جاری را بررسی کن و فقط مستندات معماری/تصمیم و تست‌های همان مسیر را بخوان.
5. اگر scope بعدی هنوز مشخص نیست، از این فایل کار جدید حدس نزن؛ از درخواست فعلی کاربر پیروی کن. تصمیم‌های بازِ مالک که با حدس باز نمی‌شوند: SEC-01 (چرخش کلید/`secret-scan`)، face-vs-QR (M69)، معیار بالینی (M85)، merchant درگاه زنده (Q6/M91-live)، و سیاست storage/consent برای M93–M96.

## قالب به‌روزرسانی برای نشست‌های بعد

جمله‌های نمونه را با شواهد واقعی جایگزین کن و بخش‌های نامربوط را حذف کن:

- **هدف/معیار پذیرش:** چه چیزی باید تمام شود؟
- **وضعیت:** انجام‌شده / نیمه‌تمام / مسدود، با دلیل.
- **فایل‌ها و تصمیم‌ها:** مسیرهای دقیق، و پیوند به ADR در صورت نیاز.
- **شاهد:** فرمان تست/CI و نتیجهٔ دقیق؛ موارد اجرا‌نشده را جدا بنویس.
- **محدودیت/مانع:** فقط مانع واقعی، بدون secret یا دادهٔ شخصی.
- **قدم بعدی دقیق:** اولین فایل/بخش/فرمان امنی که نشست بعد باید سراغش برود.
