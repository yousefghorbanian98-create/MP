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
| R-010 | `tests/integration/test_m45_admin_attendance.py` (۹ تست) | M45: endpoint حضور/خلاصهٔ اعضا نبود؛ `days_left` کف می‌گرفت (۳ روز → ۲) | 2026-11-15 | ✅ فعال |
| R-011 | `tests/integration/test_m45_programs_list.py` (۵ تست) | M45: صفحهٔ برنامه‌ها mock بود و فهرست برنامه در API نبود | 2026-11-15 | ✅ فعال |
| R-012 | `tests/integration/test_m45_checkin_feed.py` (۵ تست) | M45: جریان ورودها mock بود؛ ورود رد‌شده پنهان می‌شد | 2026-11-15 | ✅ فعال |
| R-013 | `tests/api.test.ts` (۷ تست استودیو) | M45: کلاینت API نباید در خطا به mock برگردد؛ null ≠ ۰ | 2026-11-15 | ✅ فعال |
| R-014 | assistant هیچ‌کدام از workflowها نباید شاخهٔ ثابت داشته باشد | CI به `arena/a0408b29-mp` هاردکد بود → روی شاخهٔ جاری diagnostics را push نمی‌کرد | 2026-11-15 | ✅ فعال (`github.head_ref \|\| github.ref_name`) |
