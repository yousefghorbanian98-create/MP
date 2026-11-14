# Changelog

همهٔ تغییرات مهم این پروژه در این فایل ثبت می‌شود. قالب: [Keep a Changelog](https://keepachangelog.com/) + نسخه‌بندی معنایی.

## [Unreleased]

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
