# 🗺️ نقشهٔ کلی پروژهٔ Muscle Paradise — سند جامع اجرا (Master Map)

> نسخه: ۱.۰ | تاریخ: ۲۰۲۶-۱۱-۱۴ | وضعیت: فعال
> این سند «نقشهٔ راه» کامل پروژه است: هر چیزی که باید ساخته شود، هر گیتی که باید سبز شود، و هر قولی که داده شده — اینجا مکتوب است تا هیچ‌چیز فراموش نشود.
> اسناد مرجع: `FINN_LOOP.md` (پروتکل اجرا) + `16_LAYER_PRODUCTION_PLAN.md` (طرح فنی) — هر دو در `docs/MuscleParadise/`

---

## ۱. چشم‌انداز محصول (یک پاراگراف)

**Muscle Paradise (MP)** یک «سیستم‌عامل باشگاه» local-first است: اپ موبایل عضو (MP Client / Flutter) + پنل مربی-مدیر (MP Studio / Electron+React) + کیوسک داخل باشگاه + ورود با تشخیص چهره (YuNet/SFace + liveness) + موتور قواعد قطعی برنامه‌ریزی تمرین و تغذیه (ACSM/NSCA) که LLM (Ollama) فقط «توضیح» می‌دهد و هرگز عدد نمی‌سازد. بک‌اند: FastAPI مونولیت ماژولار روی SQLite (مسیر مهاجرت به Postgres). برند: زمرد `#00B86A` + طلایی `#FFD700` روی `#0B0F14` با کارت‌های شیشه‌ای (glassmorphism)، رابط فارسی RTL کامل، فونت Vazirmatn، حالت تاریک پیش‌فرض.

```
┌──────────────┐  ┌──────────────┐  ┌───────────────┐
│  MP Studio   │  │  MP Client   │  │  کیوسک باشگاه  │
│ Electron+    │  │  Flutter     │  │  Flutter Web   │
│ React+Zustand│  │ Riverpod+drift│  │  (همان Client) │
└──────┬───────┘  └──────┬───────┘  └───────┬───────┘
       └─────────────────┼──────────────────┘
                         ▼  HTTPS/JSON (OpenAPI /api/v1)
              ┌──────────────────────┐
              │  FastAPI Backend     │ ← مونولیت ماژولار + Valkey + APScheduler
              │  (پورت 8751)          │
              └──────────┬───────────┘
        ┌────────┬───────┼────────┬──────────┐
        ▼        ▼       ▼        ▼          ▼
   موتورقواعد  Ollama  سرویسچهره  پرداخت/    محتوا
   ACSM/NSCA   (توضیح) YuNet/    کیف‌پول    wger/OFF
                        SFace    زرین‌پال    /USDA
```

---

## ۲. محیط اجرا — محدودیت‌ها و تصمیم‌های ثبت‌شده

| ابزار | وضعیت محیط | تصمیم (ثبت در DECISIONS.md) |
|-------|-----------|------------------------------|
| Python 3.11.2 + pip | ✅ موجود | بک‌اند FastAPI + pytest + ruff + bandit |
| Node 22 + npm | ✅ موجود | MP Studio با Vite + React + Vitest |
| Flutter/Dart SDK | ❌ موجود نیست (دانلود SDK از هاست مجاز ممکن نیست) | پروژهٔ Flutter کامل + تست‌ها **نوشته و commit** می‌شوند؛ گیت‌های اجرایی آن به `flutter analyze/test` در CI (GitHub Actions) منتقل می‌شوند. مستند DECISIONS ثبت می‌شود. |
| Docker | ❌ موجود نیست | فایل‌های docker-compose/Ansible نوشته و اعتبارسنجی YAML می‌شوند؛ اجرای استک در CI/سرور هدف. |
| مرورگر headless (Playwright/Chromium) | ❌ قابل دانلود نیست | اسکرین‌شات UI: (۱) موکاپ‌های باکیفیت تولیدشده **قبل از ساخت UI** به کاربر نمایش داده می‌شود؛ (۲) پس از ساخت، **Live Preview** واقعی اپ در مرورگر کاربر بالا می‌آید؛ (۳) تست‌های E2E در CI با Playwright اجرا می‌شوند. |
| git + gh | ✅ موجود | هر میکرو-چرخه = یک commit + **push فوری به شاخهٔ جاری** (حفظ در برابر پاک‌شدن سندباکس) |

**قانون حفاظت داده:** بعد از **هر** میکرو-چرخه، `git push origin arena/a0408b29-mp` اجباری است (قول به کاربر). مستندات فقط زیر `docs/MuscleParadise/`، کد فقط زیر `mp-app/`، پوشهٔ `ce-app/` هرگز دست نمی‌خورد.

---

## ۳. چیدمان نهایی مخزن (ساختار هدف)

```
MP/
├── mp-app/                          # تمام کد محصول
│   ├── backend/
│   │   ├── app/                     # FastAPI app factory, config, logging(structlog)
│   │   │   ├── main.py, config.py, deps.py, logging.py
│   │   ├── api/v1/                  # قرارداد REST نسخه‌دار + OpenAPI + slowapi
│   │   │   ├── router.py + endpointهای هر ماژول
│   │   ├── modules/                 # مونولیت ماژولار (Router→Service→Repository)
│   │   │   ├── membership/ assessment/ programs/ payments/
│   │   │   ├── face_id/ notification/ auth/ nutrition/ content/
│   │   │   └── ai_engine/           # موتور قواعد قطعی + پل Ollama (فقط توضیح)
│   │   ├── db/                      # SQLAlchemy 2.x models + Alembic migrations
│   │   ├── security/                # JWT, RBAC(casbin), crypto بیومتریک (PyNaCl), audit log
│   │   ├── jobs/                    # APScheduler: یادآوری تمدید، بازآزمایی 6-8 هفته
│   │   ├── cache/                   # لایهٔ Valkey (با invalidation) + fallback درون‌حافظه
│   │   └── tests/                   # pytest (واحد/یکپارچگی/رگریشن) + coverage ≥70%
│   ├── studio/                      # MP Studio — Electron + React + Vite + Zustand
│   │   ├── src/ (components, features, stores, lib, styles)
│   │   ├── electron/ (main, preload)
│   │   └── tests/ (Vitest)
│   ├── client/                      # MP Client — Flutter (موبایل + PWA/کیوسک)
│   │   ├── lib/ (core, features, shared widgets, router)
│   │   ├── test/ (flutter_test) + integration_test/
│   │   └── pubspec.yaml
│   ├── kiosk/                       # حالت کیوسک (Flutter Web profile + config)
│   └── infra/                       # docker-compose, Caddyfile, Ansible, monitoring
│       ├── docker-compose.yml, Caddyfile, ansible/, monitoring/ (Prometheus/Grafana)
├── docs/MuscleParadise/
│   ├── MASTER_MAP.md                # همین سند
│   ├── FINN_LOOP.md, 16_LAYER_PRODUCTION_PLAN.md   # اسناد مرجع (کپی مرجع)
│   ├── PRD.md, user-stories/        # لایهٔ 1
│   ├── adr/NNNN-*.md                # ADR-001..00N (لایهٔ 2+)
│   ├── architecture/ (C4 متنی، ERD، دیاگرام Mermaid)
│   ├── api/ (قراردادها)، runbooks/ (لایهٔ 13)، testing/ (استراتژی)
│   └── CHANGELOG.md, CONTRIBUTING.md, README.md
├── finn/
│   └── FINAL_REPORT.md              # فقط در M17 — با شواهد واقعی
├── .finn/state/                      # LEDGER.md, STATE.md, DECISIONS.md, REGRESSIONS.md
├── .claude/agents/                   # ۹ ایجنت ECC
└── .github/workflows/ci.yml          # lint→test→scan→build
```

---

## ۴. نقشهٔ میکرو-چرخه‌ها (M00 → M17) — همه‌چیز برای «فراموش‌نشدن»

قرارداد هر چرخه: **Forge** (planner→architect→tdd-guide→پیاده‌سازی→build-error-resolver) → **Inspect** (code-reviewer→تست کامل→e2e-runner) → **Normalize** (refactor-cleaner→security-reviewer→رفع نهایی) → **Next** (doc-updater→LEDGER/STATE→commit+push).
گیت‌های ۹گانهٔ پایان هر چرخه (build سبز، پوشش ≥۷۰٪ بدون کاهش، lint صفرخطا، bandit+pip-audit بدون بحرانی جدید، گزارش code-reviewer بدون Blocker، رگریشن‌ها سبز، مستندات+CHANGELOG به‌روز، LEDGER بدون درس تکراری، یک commit با پیام `mp(Mxx): <summary> [finn]`) — **همه اجباری**.

| چرخه | لایه | خروجی ملموس (deliverables) | گیت کلیدی | وضعیت |
|------|------|------------------------------|-----------|-------|
| **M00** | بوت‌استراپ | نصب ECC (۹ ایجنت) + اسکلپ `mp-app/` + `.gitignore` + CI سبک + اولین commit/push | چک‌لیست ۳.۵ فاز صفر همه ✓ | ⬜ |
| **M01** | ۱ — PRD | `PRD.md` + user-stories (عضو/مربی/پذیرش/مدیر) با Given/When/Then + تفکیک MVP (F1–F3) از Full (F4–F7) + شاخص‌های موفقیت | هر story معیار پذیرش دارد؛ مفاهیم مبهم → زنجیرهٔ عملیاتی | ⬜ |
| **M02** | ۲ — معماری | ADR-001..004 (مونولیت ماژولار، SQLite→Postgres، موتور قواعد، YuNet/SFace) + C4 متنی + مرز ماژول‌ها | هر ADR «پذیرفته»؛ ساختار `modules/` مشخص | ⬜ |
| **M03** | ۳ — دیتابیس | مدل‌های SQLAlchemy 2.x (Member/Membership/Payment/Assessment14Domain/DomainScore/JacksonPollock/FaceTemplate/CheckIn/WorkoutProgram/ProgramWeek/Exercise/NutritionPlan/MealItem/Offer/Campaign/User/RefreshToken/AuditLog/FeatureFlag) + Alembic از صفر + ایندکس‌ها + `branch_id` از روز اول + رمزنگاری FaceTemplate (PyNaCl) | migration از صفر سبز؛ تست بازیابی بکاپ (restic) مستند | ⬜ |
| **M04** | ۴ — قرارداد API | `/api/v1/` نسخه‌دار + اسکیمای Pydantic برای همه endpointها + OpenAPI/Swagger + slowapi روی OTP/لاگین | مستند Swagger کامل؛ rate-limit تست‌شده | ⬜ |
| **M05** | ۵ — بک‌اند هسته | ماژول‌های membership/assessment/programs/payments/face_id/notification/nutrition با الگوی Router→Service→Repository + APScheduler + structlog | پوشش ≥۷۰٪؛ منطق تجاری فقط در service | ⬜ |
| **M06** | ۶ — فرانت‌اند | **MP Studio** (Electron+React+Vite+Zustand) + **MP Client** (Flutter+Riverpod+go_router+drift) — ⚠️ **نخست: نمایش اسکرین‌شات/موکاپ UI به کاربر + Live Preview** | RTL کامل فارسی؛ حالت تاریک default؛ کنتراست برند چک‌شده | ⬜ |
| **M07** | ۷ — دیزاین سیستم | design tokens مشترک (JSON) + shadcn/Tailwind + Framer Motion + flutter_animate + Vazirmatn + میکرو-ترنزیشن‌ها + glassmorphism | فقط یک سیستم کامپوننت React (shadcn)؛ توکن‌ها sync | ⬜ |
| **M08** | ۸ — احراز هویت | OTP (pyotp) + JWT access/refresh با ابطال + RBAC (casbin: عضو/مربی/پذیرش/مدیر) + «خروج از همهٔ دستگاه‌ها» | OTP فقط هش‌شده؛ تست نفوذ سطحی auth سبز | ⬜ |
| **M09** | ۹ — امنیت | چک‌لیست OWASP هر endpoint + هدرهای امنیتی (Caddy/middleware) + audit log + رضایت‌نامه بیومتریک + رمزنگاری FaceTemplate + سیاست حداقل‌سازی/حق حذف | bandit + pip-audit بدون بحرانی جدید؛ پنتست فقط staging مصنوعی | ⬜ |
| **M10** | ۱۰ — CI/CD | GitHub Actions (lint→test→build→scan→deploy) + Dokploy + feature_flags در دیتابیس + rollback مستند | pipeline سبز؛ rollback تست‌شده (سناریو) | ⬜ |
| **M11** | ۱۱ — زیرساخت | docker-compose (FastAPI+Valkey+Ollama+Caddy) + Caddyfile + Ansible provisioning + ffmpeg pipeline فایل استاتیک | بالاآمدن استک با یک دستور (در CI/srv)؛ YAML معتبر | ⬜ |
| **M12** | ۱۲ — کش/کارایی | Valkey cache + invalidation (کش قدیمی هرگز نمایش داده نشود) + lazy loading + فشرده‌سازی media + بودجهٔ عملکرد | تست invalidation سبز | ⬜ |
| **M13** | ۱۳ — مانیتورینگ | Prometheus+Grafana+GlitchTip + آلارم‌ها (نه فقط داشبورد) + health-check هر ۵ دقیقه (ntfy) + SLO «گیت < ۲ ثانیه (۹۹٪)» + runbook | یک سناریوی خرابی شبیه‌سازی → آلارم آتش می‌گیرد | ⬜ |
| **M14** | ۱۴ — تست کامل | هرم تست: pytest (واحد زیاد) + Vitest + Playwright E2E (مسیرهای حیاتی «ثبت‌نام→پرداخت→چک‌این» و «تأیید برنامه توسط مربی») + k6 (بار گیت) | E2E مسیرهای حیاتی سبز؛ بودجهٔ پوشش حفظ | ⬜ |
| **M15** | ۱۵ — AI محصول | موتور قواعد قطعی (ACSM/NSCA: بار/ست/تکرار فقط از rules) + پل Ollama (فقط توضیح/انگیزش) + n8n workflows + الزام تأیید مربی + ارزیابی ۱۰ نمونه‌ای | **G8**: هیچ مسیری LLM را بدون موتور قواعد به عدد نمی‌رساند | ⬜ |
| **M16** | ۱۶ — مستندات | README + CONTRIBUTING + CHANGELOG (Keep a Changelog) + دیاگرام‌های Mermaid + runbookها + onboarding | مستندات با کد همگام | ⬜ |
| **M17** | یکپارچگی نهایی | اجرای کامل همه تست‌ها + E2E + اسکن امنیت نهایی + تست بار + **`finn/FINAL_REPORT.md` با شواهد واقعی** + آماده‌سازی release | هیچ گیت قرمزی باقی نمانده؛ LEDGER بدون آیتم باز بحرانی | ⬜ |

---

## ۵. نقشهٔ UI/UX — قول‌های کلاس جهانی (به‌خصوص M06/M07)

**الزام کاربر (غیرقابل مذاکره):** «وقتی به ساخت UI/UX رسیدی، اول اسکرین‌شات بده تا ببینم چه ساخته می‌شود.» → در آغاز M06/M07:
1. موکاپ‌های باکیفیت از محیط‌های کلیدی (داشبورد Studio، صفحهٔ عضو، کیوسک، گیت چهره) **تولید و نمایش داده می‌شود**؛
2. سپس UI دقیقاً مطابق همان زبان بصری ساخته می‌شود؛
3. پس از ساخت، **Live Preview** واقعی در مرورگر کاربر بالا می‌آید.

**زبان بصری (Design Language):**
- پالت: زمرد `#00B86A` / طلایی `#FFD700` / پس‌زمینهٔ `#0B0F14` / کارت‌های glassmorphism (blur + border نورانی)
- تایپوگرافی: Vazirmatn (فارسی) + tabular numbers؛ سلسله‌مراتب تیتر مشخص
- RTL کامل فارسی + تقویم جلالی + ریال
- **میکرو-ترنزیشن‌ها:** Framer Motion (Studio) — page transitions، stagger lists، spring hover، animated counters، skeleton shimmer، micro-feedback دکمه‌ها؛ flutter_animate (Client) — fade/slide/scale، hero transitions، animated progress rings
- حالت تاریک default؛ کنتراست WCAG (زمرد/طلایی روی تیره)
- ریزجزئیات: focus rings، نشانگرهای وضعیت زنده، toastهای نرم، انیمیشن نمودارها، حالت خالی (empty state) با تصویرسازی، loading skeleton

**صفحه‌های کلیدی برای موکاپ/اسکرین‌شات:** (۱) ورود/OTP با گیت چهره، (۲) داشبورد Studio (KPI + نمودار)، (۳) کارت عضو + ارزیابی ۱۴ دامنه، (۴) برنامهٔ تمرین هفتگی، (۵) صفحهٔ امروز عضو در موبایل، (۶) کیوسک چک‌این.

---

## ۶. نقشهٔ تست و کیفیت (گیت‌های همیشگی)

| لایه | ابزار | گیت |
|------|-------|-----|
| بک‌اند | pytest + pytest-cov | پوشش ≥ ۷۰٪ بدون کاهش؛ هیچ تست skip/ignore |
| Studio | Vitest | تست‌های واحد کامپوننت‌ها/storeها سبز |
| Client | flutter_test (در CI) | تست‌های ویجت/منطق نوشته‌شده؛ اجرا در CI |
| E2E | Playwright (در CI) + تست‌های API-سطحی در pytest | مسیرهای حیاتی سبز |
| لینت/فرمت | ruff (Python) + eslint/prettier (TS) | صفرخطا |
| امنیت | bandit + pip-audit + npm audit | بدون بحرانی جدید |
| بار | k6 (سناریوی گیت) | بدون فروپاشی؛ SLO < ۲s |

---

## ۷. نقشهٔ حافظهٔ لوپ (ضدتکرار) — ماشین‌آلات

| فایل | نقش | قاعده |
|------|------|--------|
| `.finn/state/LEDGER.md` | درس‌ها/باگ‌ها/قانون‌های «هرگز…» | آغاز هر چرخه کامل خوانده شود؛ فقط append؛ درس تکراری = شکست چرخه |
| `.finn/state/STATE.md` | وضعیت جاری | هر گام به‌روز شود |
| `.finn/state/DECISIONS.md` | تصمیم‌های خودمختار | هر ابهام = یک رکورد |
| `.finn/state/REGRESSIONS.md` | رجیستری تست رگریشن | هر باگ = یک تست واقعی |
| `docs/MuscleParadise/adr/` | ADR معماری | هر تصمیم لایهٔ ۲/۳/۴ |

**پروتکل دیباگ:** حداکثر ۳ تلاش رفع برای هر خطا → بعد از سومین شکست: rollback به آخرین کامیت سبز + بازطراحی با planner (نه تکرار روش قبلی). خطای محیطی: ۳ تلاش با تأخیر → مسیر جایگزین + ثبت DECISIONS.

---

## ۸. ترتیب اجرایی و نقاط بازرسی (Checkpoint)

```
Phase-0: نصب ECC ──► M00 ──► M01 ──► M02 ──► M03 ──► M04 ──► M05
                                                              │
        M06 ◄── ⚠️ بازرسی UI: موکاپ/اسکرین‌شات به کاربر ◄─────┘
        │
        ▼
M07 ──► M08 ──► M09 ──► M10 ──► M11 ──► M12 ──► M13 ──► M14 ──► M15 ──► M16 ──► M17
                                                                        │
                                        FINAL_REPORT.md ◄──────────────┘
```

- **push به GitHub بعد از هر میکرو-چرخه** (حفاظت در برابر پاک‌شدن سندباکس) ✅
- **بازرسی UI/UX در M06/M07** — نمایش اسکرین‌شات قبل از ساخت ✅
- **توقف ممنوع** (G1) — فقط دو گزارش مجاز: پایان موفق یا مانع خارج از کنترلِ حل‌نشده پس از ۳ تلاش.

---

## ۹. خطرها و دام‌های شناخته‌شده (از اسناد مرجع — هوشیار باش)

| دام | پیشگیری |
|-----|----------|
| نصب ناقص ECC | تأیید ۹ ایجنت قبل از M01 |
| نیازمندی مبهم («شخصی‌سازی خوب») | تبدیل به زنجیرهٔ ورودی→موتور→خروجی→تأیید مربی در PRD |
| وسوسهٔ میکروسرویس | ADR-001 مونولیت ماژولار |
| فراموشی `branch_id` | از روز اول در همهٔ جدول‌های اصلی (تست رگریشن) |
| شروع بدون نسخه‌بندی API | `/api/v1` از M04 |
| controller فربه | منطق فقط در service (code-reviewer چک می‌کند) |
| ذخیرهٔ خام OTP | فقط هش (تست رگریشن امنیتی) |
| قاطی‌کردن shadcn و DaisyUI | فقط shadcn/ui |
| LLM عدد بار می‌سازد | G8 — موتور قواعد داور نهایی |
| داشبورد بدون آلارم | M13 سناریوی خرابی شبیه‌سازی می‌شود |
| مستندات رهاشده | doc-updater در هر چرخه + CHANGELOG |
| کش بدون invalidation | تست invalidation اجباری M12 |

---

## ۱۰. خروجی نهایی (Definition of Done کل پروژه)

1. ✅ M00 تا M17 همگی Done با همهٔ گیت‌های ۹گانه
2. ✅ `finn/FINAL_REPORT.md` شامل **شواهد واقعی**: خروجی تست‌ها، درصد پوشش، نتایج اسکن امنیت، فهرست ADRها، وضعیت LEDGER
3. ✅ LEDGER بدون آیتم باز بحرانی
4. ✅ همهٔ کامیت‌ها push شده به شاخهٔ جاری (`arena/a0408b29-mp`)
5. ✅ UI/UX کلاس جهانی با میکرو-ترنزیشن‌ها + اسکرین‌شات‌های نمایش‌داده‌شده به کاربر در فاز UI

---

## ۱۱. دفتر پیشرفت (این جدول با هر چرخه به‌روز می‌شود)

| چرخه | تاریخ | وضعیت | کامیت | یادداشت |
|------|-------|-------|-------|---------|
| Phase-0 | 2026-11-14 | ✅ Done | 432485ba (ECC) | نصب ECC — ۹ ایجنت تأیید شد |
| M01 | 2026-11-14 | ✅ Done | bfbe12b | PRD + ۲۵ user-story |
| M02 | 2026-11-14 | ✅ Done | ea50bb8 | ADR-001..004 + C4 + مرز ماژول‌ها |
| M03 | 2026-11-14 | ✅ Done | dab312a | مدل‌ها + Alembic + crypto — ۳۵ تست، پوشش ۹۶٪ |
| M04 | 2026-11-14 | ✅ Done | 854e2ed | قرارداد /api/v1 + OTP/JWT + rate-limit — ۵۰ تست، پوشش ۸۴٪ |
| M05 | 2026-11-14 | ✅ Done | 5065361 | هسته: jobs + structlog + Repository — ۶۰ تست، پوشش ۸۴٪ |
| M06 | 2026-11-14 | ✅ Done | cafe6db | فرانت‌اند Studio/Client + بازرسی UI (موکاپ+Live Preview) |
| M07 | 2026-11-14 | ✅ Done | c9129e1 | دیزاین سیستم: توکن‌ها + motion-spec + تست sync |
| M08 | 2026-11-14 | ✅ Done | c4bc19f | احراز هویت: casbin RBAC + rotation + logout-all — ۹۱ تست |
| M09 | 2026-11-14 | ✅ Done | 63476af | امنیت: هدرها + audit + OWASP + سیاست بیومتریک — ۹۶ تست |
| M10 | 2026-11-14 | ✅ Done | 106c794 | CI/CD: Actions + Dokploy + rollback — ۱۰۱ تست |
| M11 | 2026-11-14 | ✅ Done | da0d5a3 | زیرساخت: compose + Caddy + Ansible — ۱۰۶ تست |
| M12 | 2026-11-14 | ✅ Done | 1d2365b | کش: Valkey + invalidation + fallback — ۱۱۱ تست |
| M13 | 2026-11-14 | ✅ Done | 9ef150f | مانیتورینگ: متریک + آلارم + SLO گیت + incident — ۱۱۹ تست |
| M14 | 2026-11-14 | ✅ Done | 553bb70 | تست نبرد + لبه‌ها + k6 + POST /programs/from-engine — ۱۲۵ تست / ۸۸٪ |
| M15 | 2026-11-14 | ✅ Done | 25b4758 | هوش مصنوعی: موتور قواعد قطعی + توضیح متنی (G8) — ۱۳۵ تست / ۸۹٪ |
| M16 | 2026-11-14 | ✅ Done | 611e76f | پرداخت: درگاه + رسید/فاکتور + کیف‌پول اتمیک — ۱۴۱ تست / ۸۹٪ |
| M17 | 2026-11-14 | ✅ Done | 7901409 | تحویل نهایی: FINAL_REPORT + backfill بازبینی‌ها + PyJWT — ۱۴۱ تست / ۸۹٪ |
| M00 | 2026-11-14 | ✅ Done | 23c6296 | بوت‌استراپ: اسکلپ + CI + state |

## 🔄 دور دوم — لوپ به‌روزشده (۲۰۲۶-۱۱-۱۴، به‌درخواست مالک)

الگوی مرجع: سوپر-اپ اسنپ (خانهٔ دسته‌بندی‌شده با گرید سرویس‌ها + ناوبری تبی). قواعد جدید مالک:
(۱) دو برنامهٔ جدا: ادمین/مربی ↔ کلاینت — (۲) ورود دادهٔ پیکرسنجی فقط از ادمین؛ کلاینت فقط نتایج/سوابق/پیشرفت خودش — (۳) کلاینت صرفاً محدود به پروفایل خودش — (۴) همهٔ اپ‌ها آپدیت تفاضلی داشته باشند.

| چرخه | عنوان | شرح | وضعیت |
|------|-------|-----|-------|
| M18 | سیاست دادهٔ سخت‌گیرانه | مالکیت سطری (row-level): کلاینت فقط دادهٔ خودش؛ ثبت پیکرسنجی فقط نقش‌های staff؛ خواندن نتایج/پیشرفت برای صاحب داده + تست نفوذ | ⬜ |
| M19 | خانهٔ دسته‌بندی‌شده (IA سبک اسنپ) | بازطراحی کلاینت: گرید بخش‌ها (برنامهٔ من/پیکرسنجی/تغذیه/چک‌این/کیف پول/پیشرفت/کلاس‌ها/فروشگاه) + جست‌وجو + بنر اعلان + ناوبری ۴ تبی + صفحات نتایج/سوابق/پیشرفت پیکرسنجی | ⬜ |
| M20 | آپدیت تفاضلی (Delta) | endpoint نسخه + delta manifest؛ Flutter: patch دلتا (code-push سبک)؛ وب (استودیو/کیوسک): service worker + assets هش‌دار — بدون حذف/نصب مجدد | ⬜ |
| M21 | یکپارچه‌سازی دور دوم | تست سراسری سیاست داده + بازبینی امنیتی + به‌روزرسانی FINAL_REPORT | ⬜ |

---

> این سند زنده است و با پیشرفت کار به‌روز می‌شود. هیچ‌چیز خارج از این نقشه فراموش نخواهد شد.
