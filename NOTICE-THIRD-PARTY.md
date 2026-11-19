# اجزای شخص ثالث (NOTICE) — MuscleParadise

اجزای فهرست‌شده با مجوز upstream/PyPI و releaseهای قفل‌شده در این مخزن تطبیق داده شده‌اند (E12 — فقط رایگان واقعی). این NOTICE جای SBOM کامل imageهای پایه یا ممیزی همهٔ مجوزهای transitively نصب‌شده را نمی‌گیرد؛ آن بازبینی هنوز باقی است.

## بک‌اند (mp-app/backend)
| جزء | مجوز | کاربرد |
|---|---|---|
| FastAPI | MIT | چارچوب API |
| Uvicorn | BSD-3 | سرور ASGI |
| SQLAlchemy 2 | MIT | ORM |
| Alembic | MIT | مهاجرت دیتابیس |
| Pydantic 2 | MIT | اعتبارسنجی |
| PyJWT | MIT | توکن JWT |
| pyotp | BSD-3 | OTP |
| python-casbin | Apache-2.0 | RBAC |
| structlog | Apache-2.0/Apache-2.0 | لاگ |
| APScheduler | MIT | زمان‌بند وظایف |
| slowapi | MIT | لیمیتر نرخ |
| limits | MIT | storage/الگوریتم rate-limit مشترک |
| redis-py | MIT | اتصال به Valkey از طریق Redis protocol |
| prometheus-client | Apache-2.0 | exposition استاندارد + multiprocess metrics |
| asgi-correlation-id | MIT | request ID برای ASGI و لاگ |
| PyNaCl | Apache-2.0 | رمزنگاری قالب چهره |
| httpx | BSD-3 | کلاینت HTTP |
| python-multipart | Apache-2.0 | آپلود فایل |

## استقرار و امنیت
| جزء | مجوز | کاربرد |
|---|---|---|
| Valkey 9.1.3 | BSD-3-Clause | cache و storage مشترک rate-limit در هر دو Compose |
| Prometheus 3.16.0 | Apache-2.0 | جمع‌آوری و ارزیابی ruleها |
| redis_exporter 1.97.0 | MIT | export کردن وضعیت Valkey به Prometheus |
| Caddy 2.11.9 | Apache-2.0 | TLS/reverse proxy و Studio در stack `infra` |
| Ollama 0.40.16 | MIT | runtime محلی اختیاری؛ هیچ وزن مدلی در image/repo قفل نیست |
| Gitleaks CLI 8.30.1 | MIT | اسکن secret در کل Git history؛ binary رسمی با checksum، بدون GitHub Action نامشخص |

ثبت مجوز از upstream: [Valkey](https://github.com/valkey-io/valkey), [Prometheus](https://github.com/prometheus/prometheus), [redis_exporter](https://github.com/oliver006/redis_exporter), [Caddy](https://github.com/caddyserver/caddy), [Ollama](https://github.com/ollama/ollama), [Gitleaks](https://github.com/gitleaks/gitleaks). نسخه‌های Compose و CI باید با همین جدول هماهنگ بمانند.

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

## ابزارهای ایجنت توسعه
| جزء | مجوز | منشأ/ردیابی |
|---|---|---|
| — (حذف شد) | MIT | ECC (`affaan-m/ECC`، کامیت `d2ef2680…`) در ۲۰۲۶-۱۱-۱۹ از مخزن حذف شد؛ هیچ فایل ECC در این پروژه توزیع نمی‌شود و attribution آن لازم نیست. سابقه در گزارش‌های تاریخی است. |
| REA skill | MIT | کپی محلی در `tools/rea-skill/reverse-engineer-anything/`; متن upstream license در `tools/rea-skill/reverse-engineer-anything/LICENSE-REA` (کامیت مجوز: `bb5278c7e2d5b0a423a63858c8b3c9682232e2d2`; نسخهٔ دقیق منبع محتوای محلی ثبت نشده) |

## مدل‌های هوش مصنوعی
هیچ مدل وزن‌داری در مخزن موجود نیست (سیاست `model_lock` — D-008). پیش از استقرار، مجوز هر مدل جداگانه تأمین و در همین فایل اضافه می‌شود.

## داده‌ها و کاتالوگ‌های ورودی

| منبع | مجوز | کاربرد | ردیابی |
|---|---|---|---|
| [yuhonas/free-exercise-db](https://github.com/yuhonas/free-exercise-db) | **The Unlicense** (مالکیت عمومی) | کاتالوگ ۸۷۶ حرکتی سامانهٔ ۱۴ توانایی (M33) | `mp-app/backend/data/external/free_exercise_db/SOURCE.md` — commit `f00c92c` + sha256. **G9:** ۱۷ حرکت × ۲ فریم (۳۰۰×۳۰۰، بازفشرده از همان commit) در `mp-app/backend/static/exercises/` — همان Unlicense |
