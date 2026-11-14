# Changelog

همهٔ تغییرات مهم این پروژه در این فایل ثبت می‌شود. قالب: [Keep a Changelog](https://keepachangelog.com/) + نسخه‌بندی معنایی.

## [Unreleased]

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
