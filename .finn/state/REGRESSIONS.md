# FINN Regressions — رجیستری تست‌های رگریشن
> هر باگ رفع‌شده = حداقل یک تست رگریشن اینجا ثبت و در همهٔ چرخه‌های بعدی اجرا می‌شود.
| شناسه تست | مسیر فایل تست | باگ مرتبط | تاریخ افزودن | وضعیت |
|-----------|----------------|-----------|---------------|--------|
| R-001 | mp-app/backend/tests/regression/test_branch_id.py | دام M03: فراموشی branch_id در جدول‌های اصلی | 2026-11-14 | ✅ سبز |
| R-002 | mp-app/backend/tests/unit/test_models.py::test_otp_stores_hash_not_plain | دام M08: ذخیرهٔ خام OTP (پیشگیرانه) | 2026-11-14 | ✅ سبز |
| R-003 | mp-app/backend/tests/unit/test_crypto.py | NFR-3: رمزنگاری embedding چهره | 2026-11-14 | ✅ سبز |
| R-004 | mp-app/backend/tests/integration/test_api_contract.py (client fixture: limiter.reset) | آلودگی شمارندهٔ rate-limit بین تست‌ها (شکست در اجرای کامل) | 2026-11-14 | ✅ سبز |
