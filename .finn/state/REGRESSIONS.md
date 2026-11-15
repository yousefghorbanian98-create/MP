# FINN Regressions — رجیستری تست‌های رگریشن
> هر باگ رفع‌شده = حداقل یک تست رگریشن اینجا ثبت و در همهٔ چرخه‌های بعدی اجرا می‌شود.
| شناسه تست | مسیر فایل تست | باگ مرتبط | تاریخ افزودن | وضعیت |
|-----------|----------------|-----------|---------------|--------|
| R-001 | mp-app/backend/tests/regression/test_branch_id.py | دام M03: فراموشی branch_id در جدول‌های اصلی | 2026-11-14 | ✅ سبز |
| R-002 | mp-app/backend/tests/unit/test_models.py::test_otp_stores_hash_not_plain | دام M08: ذخیرهٔ خام OTP (پیشگیرانه) | 2026-11-14 | ✅ سبز |
| R-003 | mp-app/backend/tests/unit/test_crypto.py | NFR-3: رمزنگاری embedding چهره | 2026-11-14 | ✅ سبز |
| R-004 | mp-app/backend/tests/integration/test_api_contract.py (client fixture: limiter.reset) | آلودگی شمارندهٔ rate-limit بین تست‌ها (شکست در اجرای کامل) | 2026-11-14 | ✅ سبز |

## R-005. کش، چک مالکیت را دور می‌زد (M18)
مسیر early-return کش در `get_member` قبل از `ensure_member_scope` اجرا می‌شد ← عضو با کش گرم می‌توانست پروفایل دیگران را بخواند (۲۰۰ به‌جای ۴۰۳). تست دائمی: `test_member_cannot_read_other_members_data`. قانون: **هر گارد دسترسی باید قبل از هر cache-read باشد.**

| R-006 | `docs/MuscleParadise/finn/install-toolchain.sh` (خودآزمای `bash -n` + اجرای واقعی) | D-025: پین روی فورک منسوخ + نبود بازتولیدپذیری ابزار | 2026-11-15 | ✅ فعال — در فاز ۰ هر نشست اجرا/بررسی می‌شود |
| R-007 | `.finn/ecc-commit.txt` باید با `git -C .finn/ecc rev-parse HEAD` و بالادست `affaan-m/ECC` بخواند | D-025: انحراف منبع ECC | 2026-11-15 | ✅ فعال |
| R-008 | وجود `.claude/agents/{planner,architect,tdd-guide,code-reviewer,security-reviewer,build-error-resolver,e2e-runner,refactor-cleaner,doc-updater}.md` | D-025: نصب ناقص ایجنت‌ها | 2026-11-15 | ✅ فعال (خود اسکریپت هم چک می‌کند) |
| R-009 | وجود `.claude/skills/reverse-engineer-anything/SKILL.md` | D-026: REA بدون skill | 2026-11-15 | ✅ فعال |
