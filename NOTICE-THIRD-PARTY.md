# اجزای شخص ثالث (NOTICE) — MuscleParadise

همهٔ اجزای زیر رایگان/متن‌باز هستند و مجوز خودشان بر آن‌ها حاکم است (E12 — فقط رایگان واقعی):

## بک‌اند (mp-app/backend)
| جزء | مجوز | کاربرد |
|---|---|---|
| FastAPI | MIT | چارچوب API |
| Uvicorn | BSD-3 | سرور ASGI |
| SQLAlchemy 2 | MIT | ORM |
| Alembic | MIT | مهاجرت دیتابیس |
| Pydantic 2 | MIT | اعتبارسنجی |
| PyJWT | MIT | توکن JWT |
| passlib | BSD-3 | هش رمز |
| pyotp | BSD-3 | OTP |
| python-casbin | Apache-2.0 | RBAC |
| structlog | Apache-2.0/Apache-2.0 | لاگ |
| APScheduler | MIT | زمان‌بند وظایف |
| slowapi | MIT | لیمیتر نرخ |
| PyNaCl | Apache-2.0 | رمزنگاری قالب چهره |
| httpx | BSD-3 | کلاینت HTTP |
| python-multipart | Apache-2.0 | آپلود فایل |

## ابزار توسعه/کیفیت
| جزء | مجوز | کاربرد |
|---|---|---|
| pytest | MIT | تست |
| ruff | MIT | لینت/فرمت |
| Locust | BSD-3 | تست بار با کاربران فیک |
| Semgrep (OSS) | LGPL-2.1 | اسکن امنیتی |

## استودیو (mp-app/studio) و کلاینت (mp-app/client)
- React + Vite (MIT) — استودیوی ادمین
- Flutter/Dart (BSD-3) — کلاینت اندروید
- فونت وزیرمتن (Vazirmatn) — SIL OFL 1.1

## مدل‌های هوش مصنوعی
هیچ مدل وزن‌داری در مخزن موجود نیست (سیاست `model_lock` — D-008). پیش از استقرار، مجوز هر مدل جداگانه تأمین و در همین فایل اضافه می‌شود.

## داده‌ها و کاتالوگ‌های ورودی

| منبع | مجوز | کاربرد | ردیابی |
|---|---|---|---|
| [yuhonas/free-exercise-db](https://github.com/yuhonas/free-exercise-db) | **The Unlicense** (مالکیت عمومی) | کاتالوگ ۸۷۶ حرکتی سامانهٔ ۱۴ توانایی (M33) | `mp-app/backend/data/external/free_exercise_db/SOURCE.md` — commit `f00c92c` + sha256. **G9:** ۱۷ حرکت × ۲ فریم (۳۰۰×۳۰۰، بازفشرده از همان commit) در `mp-app/backend/static/exercises/` — همان Unlicense |
