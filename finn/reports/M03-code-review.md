# گزارش code-reviewer — M03 (دیتابیس)

## دامنهٔ بازبینی
مدل‌های SQLAlchemy (۲۵ مدل)، migration اولیهٔ Alembic، security/crypto.py، تست‌ها

## یافته‌ها
| # | سطح | یادداشت |
|---|-----|---------|
| 1 | ✅ OK | branch_id در همهٔ ۱۲ جدول اصلی + ایندکس + تست رگریشن R-001 (مکانیکی) |
| 2 | ✅ OK | FaceTemplate فقط embedding رمزنگاری‌شده (PyNaCl SecretBox) — تست roundtrip/tamper/wrong-key |
| 3 | ✅ OK | migration از صفر → downgrade → upgrade سبز (۲۶ جدول) |
| 4 | 🔧 Fixed | server_default رشته‌ای → func.now() (درس LEDGER #3) — رفع شد و تست سبز |
| 5 | ✅ OK | ایندکس‌های کلیدی: users.phone (unique)، checkins(member, created_at)، payments(member, status) |

## Blockerها: **ندارد** ✅
## گیت‌ها: تست ۳۵ سبز | پوشش ۹۶٪ | ruff صفرخطا | bandit/pip-audit تمیز
