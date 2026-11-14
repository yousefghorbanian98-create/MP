# Muscle Paradise (MP) — سیستم‌عامل باشگاه

<p align="center"><b>Muscle Paradise</b> — اپ موبایل عضو + پنل مربی/مدیر + کیوسک داخل باشگاه + ورود با تشخیص چهره + موتور برنامه‌ریزی شخصی تمرین و تغذیه</p>

> 📖 شروع کنید: [`docs/MuscleParadise/MASTER_MAP.md`](docs/MuscleParadise/MASTER_MAP.md) — نقشهٔ کامل اجرا
> 🛠️ پروتکل اجرا: [`docs/MuscleParadise/FINN_LOOP.md`](docs/MuscleParadise/FINN_LOOP.md) — چرخهٔ Forge → Inspect → Normalize → Next
> 📐 طرح فنی: [`docs/MuscleParadise/16_LAYER_PRODUCTION_PLAN.md`](docs/MuscleParadise/16_LAYER_PRODUCTION_PLAN.md)

## ساختار

| مسیر | محتوا |
|------|--------|
| `mp-app/backend/` | FastAPI — مونولیت ماژولار (پورت 8751) |
| `mp-app/studio/` | MP Studio — Electron + React + Vite + Zustand (مربی/مدیر) |
| `mp-app/client/` | MP Client — Flutter (عضو/کیوسک/PWA) |
| `mp-app/infra/` | docker-compose، Caddy، Ansible، مانیتورینگ |
| `docs/MuscleParadise/` | PRD، ADRها، معماری، runbookها |
| `finn/` | گزارش نهایی اجرا (FINAL_REPORT.md) |

## برند

زمرد `#00B86A` · طلایی `#FFD700` · پس‌زمینه `#0B0F14` · glassmorphism · فارسی RTL · Vazirmatn · حالت تاریک

## وضعیت

در حال ساخت خودکار طبق پروتکل FINN Loop — میکرو-چرخه‌های M00 تا M17.
