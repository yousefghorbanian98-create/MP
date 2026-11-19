# M113 — گزارش شواهد REA و وضعیت اجرایی

> این نسخهٔ انتقالی خلاصه است: شواهد خام `m113/` و یک اثرانگشت از گزارش محلی در Git منتشر نشده‌اند. اعداد و محدودیت‌ها را از گزارش زیر بخوانید؛ برای تحلیل مجدد fixture مستقل لازم است.

تاریخ: 2026-11-18. محیط: شاخه `arena/b0e55b62-mp`، HEAD محلی `5482930587ce18e14f136d78296542a2de5af091` با تغییرات قبلی و فایل‌های untracked. هیچ دادهٔ واقعی بانک یا فیش برای این بررسی استفاده نشده است.

## دامنه و روش

REA 6.9.0 با Node 24.22.3 روی سه artifact محلی اجرا شد؛ خروجی خام فقط در workspace پیشین، نه این clone، و طرح در [`PLAN-MANUAL-TRANSFER.md`](../../../docs/MuscleParadise/PLAN-MANUAL-TRANSFER.md). این شواهد، اجرای استاتیک در زمان بررسی‌اند و آزمون امنیت، صحت کسب‌وکار یا گردش end-to-end نیستند. مسیرهای مطلق داخل JSON مشخصات محیط اجرا هستند، نه وابستگی برای استفادهٔ محصول.

| ابزار/ورودی | شاهد | نتیجه و حدود |
|---|---|---|
| `inspect-api-contract` روی `app.main.app.openapi()` تولیدشده از workspace | `m113/openapi.json`, `api-evidence.json`, `api-summary.json` | ۱۲۱ path و ۱۳۷ operation اعلام‌شده؛ unresolved path item دیده نشد. فقط قرارداد اعلام‌شده، نه اجرای route یا اثبات auth. اثرانگشت فایل در گزارش خام محلی نگه داشته شده است. |
| `inspect-sqlite-database --schema-scope database` روی فایل SQLite ساختگی و خالی حاصل `Base.metadata.create_all` | `m113/sqlite-evidence.json` | دید کامل schema در همان فایل ساختگی؛ جدول‌های `payments`, `wallet_transactions`, `orders`, `order_items`, `payment_gateway_configs`. این فایل مهاجرت یا دیتابیس واقعی را اثبات نمی‌کند. SHA256 دیتابیس ساختگی: `21f094b13f45ca526b1a796e3b8291ec6f61945e94b710248fedf6a12d79219b`. |
| `analyze-javascript-application mp-app/studio/dist --detail summary` | `m113/studio-evidence.json`, `studio-summary.json` | خروجی ابزار موفق اما تحلیل application و semantic ناقص بود: worker هنگام تحلیل bundle اصلی سقف heap حدود ۱۰۲۴ MiB را پشت سر گذاشت، یک فایل JS بررسی نشد و unknownها باقی‌اند. `complete-within-view` در summary تنها نمایش بخش انتخاب‌شده است، نه کامل‌بودن تحلیل. هیچ کد JS اجرا نشد. |

ساخت Studio با `npm ci --no-audit --no-fund && npm run build` موفق بود (۱۰۲۸ ماژول؛ هش `dist/assets/index-L3OlCw3z.js`: `2fd8ff3e28b22caea15d2f457403d9ecb88910693f363795560695659b0a00d6`). هش JSONها ممکن است با بازتولید به دلیل metadata و مسیر تغییر کند. نصب‌کنندهٔ مشترک REA/ECC با exit 1 در اختلاف skill محلی متوقف شد؛ فایل موجود حفظ شد. CLI REA به‌صورت مستقل کار کرد، اما ثبت MCP و Repowise MCP در دسترس نبودند. promptهای ECC خوانده شدند؛ subagent مستقل اجرا نشده است.

## یافته‌های قابل پیگیری

1. `card` فعلی کارت‌خوان حضوری است، نه کارت‌به‌کارت. تنظیم درگاه `card_to_card` به‌تنهایی گردش واریز/فیش یا تسویه را ایجاد نمی‌کند. ماشین حالت جدید عمداً به هیچ مسیر موجودی وصل نشده است.
2. در `modules/shop/service.py`، checkout پس از ساخت سفارش و تغییر موجودی `payments.create_payment` را فرامی‌خواند؛ این تابع commit داخلی دارد. نباید بدون بازآرایی و تست، اتمی‌بودن کل فرایند یا safe retry را مفروض گرفت.
3. `verify_payment` مسیر دستی فعلی را تسویه می‌کند؛ مسیر جدید باید از دورزدن گیت بررسی بانکی محافظت شود.
4. فیش، OCR، شمارهٔ پیگیری یا SMS به‌تنهایی مدرک تسویه نیستند. طرح، تأیید انسانی مجاز بر مبنای منبع بانکی مستقل را الزام می‌کند.

## اجرای محلی micro-loop و شواهد

- M113-0: طرح، تحقیق مجوزها و این گزارش نوشته شدند؛ پوشش REA برای Studio **ناقص** و MCP غایب است.
- M113-1: `modules/payments/manual_transfer_policy.py` یک تابع مستقل و بدون side-effect ارائه می‌کند. `tests/regression/test_manual_transfer_policy.py`: اجرای `./.venv/bin/pytest -q tests/regression/test_manual_transfer_policy.py` برابر **54 passed**؛ ruff check و format برای همین دو فایل موفق. آزمون‌ها حالت‌های پایانی، deadline، مبلغ دقیق، مدرک بانکی، رد و ورود نامعتبر را پوشش می‌دهند. این تست‌ها اتمی‌بودن، نقش، persistence، API، storage یا رقابت را اثبات نمی‌کنند. ترتیب red-first به‌صورت شاهد ثبت نشده؛ ادعای TDD کامل نمی‌شود.
- آزمون محلی همزمان با مجموعه‌های پرداخت/فروشگاه: `pytest -q tests/regression/test_manual_transfer_policy.py tests/integration/test_m59_shop.py tests/integration/test_sandbox_bank.py` برابر **119 passed**.
- کل backend: `./.venv/bin/pytest -q` برابر **943 passed, 2 skipped**, با 29 warning. این نتیجه برای workspace فعلی است نه CI یا تأیید گردش M113.
- Studio: `npm test -- --run` برابر **220 passed, 9 skipped**؛ هشدارهای React act وجود داشت. این مجموعه پیش از ادغام UI کارت‌به‌کارت است.
- M113-2 تا M113-12: **پیاده‌سازی و گیت‌ها اجرا نشده‌اند**. UI، مدل/مهاجرت، API، ذخیره‌سازی فیش، تأیید، ledger، concurrency PostgreSQL و release همگی باقی‌اند. تا آن زمان هیچ مسیر کارت‌به‌کارت را نباید فعال یا production-ready تلقی کرد.

## گیت‌های بیرونی باز

Flutter/Dart/Android محلی در دسترس نبودند؛ CI تازه برای این تغییرات اجرا نشده است. گیت‌های رازهای قابل دسترس در history و امضای release جداگانه باز هستند؛ داشتن کلید جدید به معنی پاک‌شدن history نیست. دسترسی به تنظیم secrets/variables در بررسی قبلی 403 بود. تست دستگاه واقعی و Repowise index refresh هم انجام نشده‌اند. نمودار Mermaid نسخه‌شده جایگزین قابل‌ردیابی است، نه ادعای refresh سرویس.
