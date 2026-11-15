# Changelog

همهٔ تغییرات مهم این پروژه در این فایل ثبت می‌شود. قالب: [Keep a Changelog](https://keepachangelog.com/) + نسخه‌بندی معنایی.

## [Unreleased]

### Added — M33-c2 (2026-11-14) — schema بردار ۱۴محوره
- فیلدهای `axis_coverage` (بردار وزنی ۱..۱۴ با بازهٔ ۰..۱) + `intensity_band` + `progression_key` روی `catalog_exercises` + مهاجرت `d4e5f6a1b2c3`
- نگهبان `validate_coverage` + ۳ تست مدل (۲۰۵ کل)

### Added — M33-c1 (2026-11-14) — سامانهٔ ۱۴ توانایی، میکرو-لوپ نخست
- ورود کاتالوگ `free-exercise-db` (۸۷۶ حرکت، Unlicense) — جدول‌های `catalog_sources` + `catalog_exercises`، اسکریپت idempotent `scripts/import_exercise_catalog.py` + راستی‌آزمایی sha256
- ثبت مجوز در `NOTICE-THIRD-PARTY.md` + سند منبع (`data/external/free_exercise_db/SOURCE.md`) + rule-evidence (`finn/reports/evidence/M33c1-free-exercise-db.rule-evidence.json`)
- ۵ تست جدید (۲۰۲ کل) — ruff/bandit/pip-audit پاک

### Added — M21 (2026-11-14) — پایان دور دوم
- یکپارچه‌سازی: ۱۵۲ تست بک‌اند (۸۹٪) + ۱۵ تست استودیو — bandit/pip-audit صفر
- گزارش‌های بازبینی M19–M21 + به‌روزرسانی FINAL_REPORT (بخش دور دوم)

### Added — M20 (2026-11-14) — دور دوم
- آپدیت تفاضلی: `GET /updates/manifest` (عمومی) + registry پچ‌ها با sha256 + حالت force برای نسخه‌های منسوخ
- وب (استودیو/کیوسک): service worker + بنر «به‌روزرسانی بدون نصب مجدد» (SKIP_WAITING+reload)
- Flutter: `UpdateService` (دانلود patch + تأیید sha256 + fallback full) — **۱۵۲ تست / استودیو ۱۵**

### Added — M19 (2026-11-14) — دور دوم
- بازطراحی IA کلاینت سبک سوپر-اپ: شل ۴ تبی + خانهٔ گریدی ۸ بخش + جست‌وجو + بنر + چک‌این سریع
- صفحات جدید: پیکرسنجی (فقط-خواندنی: نتایج/سوابق/روند)، کیف پول، کلاس‌ها، فروشگاه، تغذیه، پیشرفت، پروفایل
- میکرو-ترنزیشن‌ها: ورود پلکانی، ترنزیشن تب‌ها، فشار کاشی — ۳ تست ویجت

### Added — M18 (2026-11-14) — دور دوم
- مالکیت سطری (`app/security/ownership.py`): کلاینت فقط دادهٔ خودش — ۵ تست نفوذ (R-005)
- ورود پیکرسنجی فقط از ادمین/مربی؛ خواندن نتایج/سوابق/کیف پول برای عضو آزاد شد
- **۱۴۶ تست / ۸۹٪** — همهٔ گیت‌ها سبز

### Added — M11 (2026-11-14)
- docker-compose کامل: FastAPI + Valkey + Ollama + Caddy (با healthcheck و عدم افشای backend)
- Caddyfile با هدرهای امنیتی + سرو فایل‌های استاتیک فشرده‌شده
- Ansible playbook (provisioning تکرارپذیر + بکاپ restic) + اسکریپت فشرده‌سازی ffmpeg
- runbook provisioning — ۱۰۶ تست

### Added — M10 (2026-11-14)
- CI کامل GitHub Actions: lint → test → build → scan → e2e (backend/studio/flutter)
- Deploy با Dokploy (workflow mp-deploy) + Dockerfile.backend + health gate
- اسکریپت + runbook rollback (`runbooks/rollback.md`) — سناریوی تست مستند
- ۵ تست اعتبارسنجی artifacts — مجموعاً ۱۰۱ تست

### Added — M09 (2026-11-14)
- هدرهای امنیتی (CSP/HSTS/nosniff/...) با middleware + تست
- audit log در عملیات حساس (پرداخت، برنامه، چهره، logout-all) — US-406
- چک‌لیست OWASP Top 10 + سیاست دادهٔ بیومتریک (`docs/MuscleParadise/security/`)
- `.env.example` — رفع بحرانی‌های npm (tinypool override) — ۹۶ تست، پوشش ۸۶٪

### Added — M08 (2026-11-14)
- RBAC با casbin — ماتریس نقش/اجازهٔ ۴ نقش + guard سطح روتر (`require_permission`)
- سخت‌سازی auth: تست نفوذ سطحی (401/403)، rotation refresh، خروج از همهٔ دستگاه‌ها (US-404)
- تست‌های RBAC (۳۰) + بازنویسی تست‌های قرارداد با احراز هویت نقش‌دار — ۹۱ تست، پوشش ۸۵٪

### Added — M07 (2026-11-14)
- `mp-app/shared/motion-spec.md` — مشخصات کامل میکرو-ترنزیشن‌ها (زمان‌ها، easingها، الگوها)
- `docs/MuscleParadise/design/design-system.md` — سیستم دیزاین رسمی (توکن‌ها، کامپوننت‌ها، WCAG)
- تست‌های مکانیکی همگام‌سازی توکن‌ها + گیت کنتراست WCAG (۹ تست جدید در Studio)
- احترام به prefers-reduced-motion

### Added — M06 (2026-11-14)
- **MP Studio**: React+Vite+Zustand+Tailwind+Framer Motion — داشبورد KPI، نمودار حضور، جدول اعضا + پنل ۱۴ دامنه، برنامه‌ها، چک‌این زنده، تنظیمات (feature flags) — RTL فارسی، حالت تاریک، glassmorphism، میکرو-ترنزیشن‌ها
- **MP Client (Flutter)**: اپ «برنامهٔ امروز» + چک‌این با Riverpod/flutter_animate + تست‌های ویجت/واحد
- `mp-app/shared/design-tokens.json` — توکن‌های مشترک React/Flutter
- بازرسی UI: موکاپ‌های `docs/MuscleParadise/ui-previews/` قبل از ساخت نمایش داده شد + Live Preview
- کنتراست WCAG برند: همه PASS

### Added — M05 (2026-11-14)
- jobهای APScheduler: انقضای اشتراک، یادآوری تمدید (dedup)، بازآزمایی ۶–۸ هفته
- لاگ ساختاریافتهٔ structlog (JSON برای Grafana/Loki)
- لایهٔ Repository برای membership/payments/assessment (Router→Service→Repository)
- ۱۰ تست جدید (jobها + repositoryها) — مجموعاً ۶۰ تست، پوشش ۸۴٪

### Added — M04 (2026-11-14)
- قرارداد REST نسخه‌دار `/api/v1` — ۹ خانواده endpoint با اسکیمای Pydantic کامل
- app factory + قالب خطای یکپارچه + JWT (access/refresh با rotation) + slowapi روی OTP/لاگین
- جریان کامل OTP (هش‌شده)، عضو/اشتراک/پرداخت/ارزیابی ۱۴ دامنه/JP7/چهره/چک‌این/اعلان/audit/flags
- ۱۵ تست قرارداد — مجموعاً ۵۰ تست، پوشش ۸۴٪

### Added — M03 (2026-11-14)
- مدل‌های SQLAlchemy 2.x (۲۵ مدل، ۲۶ جدول) با branch_id از روز اول + ایندکس‌ها
- migration اولیهٔ Alembic (upgrade از صفر/downgrade تست‌شده) — `db/migrations/`
- `security/crypto.py` — رمزنگاری FaceTemplate با PyNaCl (NFR-3)
- ۳۵ تست (واحد/یکپارچگی/رگریشن) — پوشش ۹۶٪

### Added — M02 (2026-11-14)
- `docs/MuscleParadise/adr/001..004` — مونولیت ماژولار، SQLite→Postgres، موتور قواعد (G8)، YuNet/SFace
- `docs/MuscleParadise/architecture/c4.md` — دیاگرام‌های C4 (Mermaid) در ۴ سطح
- `docs/MuscleParadise/architecture/module-map.md` — مرز ۱۱ ماژول backend + جریان‌های حیاتی

### Added — M01 (2026-11-14)
- `docs/MuscleParadise/PRD.md` — نیازمندی‌های کامل محصول: پرسوناها، تفکیک MVP (F1–F3) از Full (F4–F7)، زنجیره‌های عملیاتی ضدابهام، NFRها، KPIها
- `docs/MuscleParadise/user-stories/{member,coach,reception,manager}.md` — ۲۵ داستان با معیار پذیرش Given/When/Then

### Added — M00 (2026-11-14)
- نصب ECC (Everything Claude Code) با کامیت پین‌شده `432485ba` + ۹ ایجنت
- اسکلپ `mp-app/` (backend/studio/client/kiosk/infra) + CI اولیهٔ GitHub Actions
- `docs/MuscleParadise/MASTER_MAP.md` — نقشهٔ جامع اجرا
- حافظهٔ لوپ: `LEDGER.md`, `STATE.md`, `DECISIONS.md`, `REGRESSIONS.md` (D-001)

## 2026-11-14 — M27 [finn]
- `modules/classes/` + `db/models/classes.py`: کلاس گروهی، رزرو با ظرفیت، لیست انتظار، ارتقا پس از لغو (migration b2c3d4e5f6a1).
- `modules/payments/finance.py` + مسیرهای `/payments/finance/{summary,export.csv,commission}`: خلاصهٔ مالی، CSV حسابداری (ضد CSV-injection)، کمیسیون مربی (payment.coach_id).
- یافته‌های semgrep رفع شد (۰ findings): Escape HTML در render_html، nosem مستند برای ستون‌های SQLAlchemy.
- گیت‌ها: ۱۶۹ pytest سبز، ruff صفر، semgrep صفر، Locust بدون 5xx (429 = لیمیتر فعال).

## 2026-11-14 — M28 [finn]
- `app/sms.py`: Adapter پیامک (dev|webmagfa|kavenegar) + اجبار https + خطا `sms_failed` (بی‌صدا قورت نمی‌دهد). `dev_code` فقط در حالت dev.
- `docs/MuscleParadise/ANDROID-OFFLINE-PLAN.md`: مشخصات صف آفلاین (sync_queue + Idempotency-Key + ترتیب همگام‌سازی + پرداخت آفلاین‌ممنوع).
- `mp-app/client/ci_apk.sh`: pipeline ساخت APK (analyze/test/build + SHA256) — برای CI با Flutter.
- گیت‌ها: ۱۷۴ pytest سبز، ruff صفر، semgrep صفر.

## 2026-11-14 — M29 [finn]
- `engine/autoreg.py` (autoreg-1.0): قانون ۲-برای-۲ + RPE → increase/decrease/maintain با دلیل و نسخهٔ قاعده؛ `POST /api/v1/ai/suggest-weight`.
- `modules/admin/kpis.py` + `GET /api/v1/admin/kpis`: KPI های واقعی (اعضای فعال از اشتراک‌های active، اعضای ۳۰ روز، درآمد، نرخ پر شدن کلاس — ناشناخته ≠ صفر).
- RBAC: نقش `admin` به سیاست casbin اضافه شد.
- گیت‌ها: ۱۸۱ pytest سبز، ruff صفر، semgrep صفر.

## 2026-11-14 — M30 [finn]
- تست مانور بکاپ/بازیابی (`test_backup_drill.py`): بکاپ ← حذف ← بازیابی ← تأیید SHA256 و داده.
- `docs/MuscleParadise/OPS-RUNBOOK.md`: سرویس‌ها، پشتیبان روزانه، بازیابی فاجعه (RTO < ۳۰ دقیقه)، پایش، انتشار دلتا.
- اجرای دوم Locust (۵۰ کاربر/۳۰ ثانیه): ۰ خطا 5xx — `finn/reports/load/M30-smoke-report.md`.

## 2026-11-14 — M31 [finn]
- `modules/face_id/privacy.py` + `GET /api/v1/face/privacy-notice`: متن حریم خصوصی نسخه‌دار (faceid-privacy-1.0) + حق حذف صریح.
- `docs/MuscleParadise/FACEID-PRIVACY-TEXT.md` + `RELEASE-CHECKLIST.md`.
- RBAC: دسترسی member/coach/reception به privacy-notice.
- گیت‌ها: ۱۸۴ pytest سبز، ruff صفر، semgrep صفر.

## 2026-11-14 — بستهٔ نهایی [finn]
- M22–M31 همگی بسته شدند (MASTER_MAP به‌روز شد)؛ FINAL_REPORT بخش ۱۱ افزوده شد.
- `docs/MuscleParadise/delivery-reports/2026-11-14-final.md`: جدول قابلیت/شاهد/شکاف + مسیرهای بسته.
- شرط‌های نهایی: ۱۸۴ تست سبز، ruff صفر، semgrep صفر، Locust بدون 5xx، مانور بکاپ سبز.

## 2026-11-14 — ممیزی داده←تابع←خروجی [finn]
- `tests/integration/test_e2e_dataflow.py`: جریان کامل ورودی‌های عدد/اسم ← توابع ← خروجی‌ها (۱۲ مرحله) — به گیت‌های همیشگی افزوده شد.
- اجرای زندهٔ HTTP + بار فیک (Locust): `finn/reports/audit/2026-11-14-dataflow-audit.md` — صفر 5xx.
- گیت‌ها: ۱۸۵ pytest سبز، ruff صفر، semgrep صفر.

## 2026-11-14 — بستن کارهای باز (مسیر ۲ + LICENSE مالکیتی) [finn]
- **D-022**: LICENSE مالکیتی (`LICENSE` + `NOTICE-THIRD-PARTY.md`) — جایگزین D-015.
- **APK در CI**: `.github/workflows/apk.yml` (Flutter action + ci_apk.sh + آرتیفکت APK/SHA256).
- **Face-ID عمیق**: `modules/face_id/deep.py` — آداپتور ONNX + نگهبان‌های تست‌شده (رد HTML جعلی/حجم مشکوک/قفل چهارشرطه) + `GET /face/deep-status` (۷ تست).
- **UI مالی استودیو**: صفحهٔ Finance — خلاصهٔ مالی، کمیسیون مربی، دانلود CSV با خروجی واقعی/خطای صریح + رفع خطای tsc (vite-env.d.ts).
- گیت‌ها: ۱۹۲ pytest سبز، ruff صفر، semgrep صفر، ۱۵ تست استودیو سبز، tsc پاک.

## 2026-11-14 — APK واقعی + استقرار Docker [finn]
- **APK ساخته شد (CI)**: `mp-app/client/release/` — سه ABI + SHA256 + BUILD-INFO (run 43617637282). رفع: تعارض intl، فونت وزیرمتن (دانلود از منبع رسمی OFL)، importهای theme، آیکن حذف‌شدهٔ Flutter 3.50، scaffold اندروید.
- **استقرار**: Dockerfile (backend/studio) + docker-compose + workflow GHCR (`mp-container`) + `docs/MuscleParadise/DEPLOYMENT.md` (راهنمای مرحله‌به‌مرحله).

## 2026-11-14 — کلاینت واقعی (M32) [finn]
- `members/me` (GET/PUT): پروفایل شخصی واقعی — ساخت خودکار + ویرایش نام/هدف/جنس/قد/محدودیت‌ها (+تست).
- کلاینت: `api_client.dart` + `session.dart` (نشست/توکن واقعی)، `otp_page.dart` (ورود پیامکی)، `intake_page.dart` (پرسش‌نامهٔ هدف/سطح/سابقه/بازهٔ عملکرد/محدودیت‌ها + گیت جمعیتی) + `program_result.dart` (برنامهٔ اختصاصی واقعی از موتور)، پروفایل زنده.
- تست‌های کلاینت: MockClient برای API/نشست؛ مسیر «برنامهٔ اختصاصی» به جریان واقعی وصل شد.

## [0.2.0-client2] — ۲۴ آبان ۱۴۰۵ — نسخهٔ واقعی + امضای پایدار
- **رفع «نصب پکیج شکست خورد»**: کلید انتشار پایدار `mp-release` (ریشه: کلید debug جدید در هر بیلد CI → ردِ به‌روزرسانی).
- **چک‌این واقعی**: QR امضاشده (`/face/qr-token` + `/face/checkin-qr`) + چهره (دوربین → enroll/checkin).
- **دادهٔ واقعی**: برنامه/کیف‌پول/کلاس‌ها/تغذیه/پیشرفت از API با حالت‌های loading/error/empty.
- **UI**: نام حرکت در کاشی (قبلاً شمارهٔ id نشان می‌داد)، آیکون انجام/انجام‌نشده، انیمیشن‌های ورود، لوگوی حرفه‌ای + آیکون لانچر در CI.
- **کیفیت**: ۱۹۳ pytest + ۱۳ تست کلاینت + analyze پاک + چهار job سبز (backend/studio/client/e2e) + بیلد release سبز.
- ساختار REA (mکانیزم امضا/کیفیت) مطالعه و اعمال شد.

## [0.2.0-client3] — ۲۴ آبان ۱۴۰۵ — رفع‌های ارزیابی ساختاری REA
- **R1**: مجوز `INTERNET` به مانیفست release اضافه شد (فقط در debug بود — قطعی کامل API روی دستگاه).
- **R2**: `network_security_config.xml` برای معماری سرور محلی/LAN (targetSdk 36 بدون آن cleartext را می‌بست).
- **R3**: `allowBackup="false"` (حفاظت دادهٔ محلی/توکن‌ها — NFR-3).
- شواهد: `finn/reports/rea/REA-AUDIT.md` · صف جدید: `docs/MuscleParadise/BUILD-QUEUE.md`
