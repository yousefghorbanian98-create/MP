# خط پایه اندازه‌گیری‌شده (BASELINE)

> WP 0.1 — **بخشی**. این سند با اندازه‌گیری روی commit `662ff88` (base ممیزی) ساخته شده،
> نه روی HEAD فعلی؛ کامیت‌های ممیزی خودِ اعداد را تغییر داده‌اند و مقایسهٔ «قبل» باید از base باشد.
> ستون «تأیید ابزار دوم» (الحاقیهٔ A1، بخش ۶) برای مقایسه با radon/lizard/semgrep است.

## الف) ruff ۰٫۱۷٫۶ روی `mp-app/backend` (commit 662ff88، `--no-cache`)

| اندازه‌گیری | نتیجه | exit | زمان (ms) |
|---|---|---|---|
| `ruff check .` با پیکربندی فعلی (۸ خانواده: E,F,W,I,N,UP,B,SIM) | All checks passed! | 0 | 52–58 |
| `ruff check --select ALL .` | ۱۱٬۷۷۸ یافته، ۱۰۴ قاعدهٔ متمایز، ۱٬۰۱۰ قابل‌رفع خودکار (۹۹۶ unsafe) | 1 | 296 |
| `ruff format --check .` | ۳۷۸ فایل پیش‌تر قالب‌بندی‌شده | 0 | 57 |

## ب) شمارش قاعده‌های مرتبط با یافته‌ها (همان commit)

| قاعده | تعداد | یافته / تابع / محل | وضعیت در ممیزی |
|---|---|---|---|
| `C901` (سقف ۱۰) | ۱۵ | `app/config.py:128` = **۲۸**؛ `engine/axis_prescription.py:43` = ۲۱؛ `modules/payments/manual_transfer_policy.py:45` = ۲۰؛ `engine/churn_risk.py:22` = ۱۸؛ `app/deps.py:42` = ۱۱ | F‑15 |
| `TRY400` | ۶ | `app/sms.py:66,69,72,99,102,105` | **F‑29** |
| `DTZ011` | ۳ | `modules/axis_assessment/service.py:31`، `modules/nutrition/service.py:124,182` | **F‑28** |
| `DTZ001` | ۱ | `tests/regression/test_manual_transfer_policy.py:165` | F‑28 (تست) |
| `S310` | ۶ | `app/sms.py:52,61,94` + `eval/llm_column.py:59,100,107` | **F‑29** (سه مورد اول) |
| `S608` | ۰ | — (`ruff check --select S608` بدون یافته؛ semgrep تنها گیت F‑22 است) | F‑22 |
| `S105` | ۳ | `app/config.py:16`، `modules/auth/schemas.py:46`، `tests/integration/test_m67_studio_auth.py:37` | ریشهٔ F‑02 (اولی) |
| `RUF100` (بلااثر) | **۷۲** | بیشترین: `scripts/dast.py` ۵، `cache/store.py` ۵، `scripts/seed_s3c_m39.py` ۴، `db/migrations/…c3f01ab129e2…` ۴ | WP 0.9 |
| `ERA001` | ۱۱ | همه کامنت فارسی مستندساز (راستی‌آزمایی‌شده) | پیکربندی: ignore |
| `RUF001` | ۲۳۰ | متن فارسی | پیکربندی: ignore |
| `S101` | ۲٬۷۳۶ | `assert` در تست‌ها | per-file-ignore |
| `PLC0415` | ۹۸۸ | import تنبل | ignore |
| `TRY003` | ۳۶۰ | پیام فارسی inline | ignore |
| `EM101` | ۳۰۹ | پیام فارسی inline | ignore |
| `SLF001` | ۲۵ | دسترسی خصوصی | بررسی |
| `PLW0603` | ۷ | `global` در logging/observability/profiling | F‑03 |

## ج) اختلاف‌های اندازه‌گیری با الحاقیهٔ A1 (باید در برنامه اصلاح شوند)

| مورد | الحاقیه | اندازه‌گیری | تصمیم |
|---|---|---|---|
| `RUF100` | ۳۹ | **۷۲** | عدد اندازه‌گیری‌شده ملاک است؛ گیت WP 0.9 = ۰ |
| قاعده‌های متمایز `--select ALL` | ۱۰۸ | **۱۰۴** | ملاک: اندازه‌گیری |
| `S105` | ۴ مورد | **۳** (تست `test_production_ops.py:44` در base flag نمی‌شود) | ملاک: اندازه‌گیری |
| `logging.error` در `sms.py` | «`logging.error`» | در کد `log.error` است؛ TRY400 شش مورد را تأیید می‌کند | تأیید شد |
| `ruff-recommended.toml` (۴٬۵۶۴ بایت، ادعای «commit شده در مخزن ممیزی») | — | **در این مخزن وجود ندارد** | باید از روی مشخصات الحاقیه بازسازی شود (WP 0.9) |
| `BASELINE.md` با ۴۹ ردیف (WP 0.1) | — | پیش از این موجود نبود؛ این سند نسخهٔ بخشی است | ۴۹ ردیف هنوز ناقص |
