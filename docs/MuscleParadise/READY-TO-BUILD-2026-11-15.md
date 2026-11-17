# READY-TO-BUILD — وضعیت ابزارها، مطالعهٔ میکرو-لوپ‌ها و نقشهٔ ادامه

> snapshot: ۲۰۲۶-۱۱-۱۵ | شاخهٔ آن زمان: `arena/86fc9529-mp` | وضعیت FINN در آن snapshot: **READY**
> این سند «حافظهٔ آماده‌سازی» تاریخی است؛ READY/صف آن به شاخهٔ جاری منتقل نمی‌شود. صف جاری فقط در `TODO-2026-11-16.md` و نقشه‌های فعال تعیین می‌شود.
> طبق D-033، هر loop فعالِ `READY` بدون نظارت روتین ادامه می‌یابد؛ تصمیم برگشت‌پذیر ثبت، blocker واقعی محلی می‌شود و کار مستقل ادامه می‌یابد. دستورهای قدیمی push منسوخ‌اند؛ push/release/deploy مجاز نیست.

---

## ۱. خلاصهٔ اجرایی (سه خط)

1. **ECC از منبع رسمی بازنصب شد** (`affaan-m/ECC` v2.2.3): ۷۱ ایجنت + ۳۱۴ اسکیل + ۹۸ فرمان + ۲۳ بستهٔ قوانین — قبلاً یک فورک ۱۰ ماه عقب با ۹ ایجنت نصب بود.
2. **REA واقعی نصب شد** (`morluto/rea` v6.9.0) با skill و MCP پروژه‌ای. اولین استفادهٔ واقعی **دو گپ جدید** پیدا کرد (نسخهٔ APK و سیاست cleartext) و سه ادعای ممیزی قبلی را تأیید کرد.
3. **مطالعهٔ کامل M00–M44 انجام شد**؛ نقشهٔ اجرایی M45 به بعد با ارجاع به endpointهای واقعی نوشته شد.

---

## ۲. چه نصب شد — قبل و بعد

### ۲.۱ ECC

| | قبل | بعد |
|---|---|---|
| منبع | `WorldFlowAI/everything-claude-code` (فورک) | **`affaan-m/ECC`** (بالادست رسمی) |
| کامیت | `432485ba` — ۲۰۲۶-۰۱-۲۳ | `d2ef2680` — ۲۰۲۶-۱۱-۰۶ |
| ایجنت | ۹ | **۷۱** |
| اسکیل | ۱۱ | **۳۱۴** (۶۲۰ فایل) |
| فرمان | ۱۵ | **۹۸** |
| قوانین | ۸ فایل تخت | **۲۳ بستهٔ زبانی/چهارچوبی** (`common`, `python`, `dart`, `typescript`, `react`, …) |
| hooks | ۵ bash ساده | **۹ فایل** با `hooks.json` تولیدی + dispatcher |

**۹ ایجنت قرارداد FINN همه هستند** و غنی‌تر: `planner` از ۳۰ خط به ۲۲۱ خط رسید و یک «Prompt Defense Baseline» دارد
(ضد دستکاری نقش، ضد نشت راز، ضد تزریق دستور از محتوای بیرونی) — مستقیماً روی امنیت این پروژه اثر دارد.

**اسکیل‌های مستقیماً مرتبط با پشتهٔ MP که تازه در دسترس‌اند:**
`fastapi-patterns` · `python-testing` · `python-patterns` · `dart-flutter-patterns` · `flutter-dart-code-review` ·
`react-patterns` · `react-testing` · `database-migrations` · `postgres-patterns` · `api-design` · `security-review` ·
`competitive-platform-analysis` · `competitive-report-structure` · `ai-regression-testing` · `eval-harness`

ایجنت‌های تخصصی که مستقیماً به‌کار می‌آیند: `fastapi-reviewer` · `python-reviewer` · `flutter-reviewer` ·
`dart-build-resolver` · `react-reviewer` · `database-reviewer` · `silent-failure-hunter` ·
`pr-test-analyzer` · `performance-optimizer` · `spec-miner`

### ۲.۲ REA

| مورد | مقدار |
|---|---|
| نسخه | 6.9.0 |
| محل | `~/toolchain/rea` (بیرون مخزن — با اسکریپت بازتولید می‌شود) |
| Node | پرتابل ۲۴.۲۲.۳ (`~/toolchain/node-linux-x64`) — چون سیستم `22.22.3` بود و REA حداقل `22.23.4` می‌خواهد |
| skill | `.claude/skills/reverse-engineer-anything/` (SKILL + ۸ مرجع تخصصی) |
| MCP | `.mcp.json` پروژه (gitignored — مسیر مطلق دارد) |
| موتور native | نصب نشد — **لازم نیست** (D-027) |

**اسکریپت بازتولید واحد:** `docs/MuscleParadise/finn/install-toolchain.sh` (`all|ecc|rea`، idempotent، تست‌شده).

---

## ۳. REA در عمل — اولین استفادهٔ واقعی چه پیدا کرد

### ۳.۱ تأیید ممیزی قبلی (روی APK واقعی، پارسر مستقل)

| ادعا | نتیجه |
|---|---|
| `INTERNET` در مانیفست release | ✅ موجود |
| `networkSecurityConfig` | ✅ موجود (`@7F100001` + فایل XML) |
| `allowBackup="false"` | ✅ برقرار |
| `debuggable=false` | ⚠️ صفت در مانیفست نیست — فقط inference از پیش‌فرض AGP |

**پس ادعای «سخت‌شدگی تأییدشده» در `REA-AUDIT.md` بیش از شاهدش ادعا کرده بود.** این دقیقاً همان چیزی است که REA برای آن است.

### ۳.۲ دو گپ **جدید**

1. **ناسازگاری نسخه:** APK منتشرشده `versionName 0.1.0` دارد، اما ریلیز گیت‌هاب `v0.2.0-client3` است.
2. **سیاست cleartext بیش از حد باز:** `network_security_config.xml` با `base-config cleartextTrafficPermitted="true"`
   **همهٔ** ترافیک HTTP را مجاز می‌کند، در حالی که کامنت خودش می‌گوید «فقط سرور محلی». باید `domain-config` برای بازه‌های LAN باشد.

### ۳.۳ ناسازگاری در شواهد قدیمی

فایل‌های `finn/reports/rea/*.json` هش APK **قبلی** (`fba3e666…`) را دارند، در حالی که APK فعلی `2ab56399…` است.
یعنی آن گزارش‌ها به build قبل از `edfa16c` تعلق دارند و روی نسخهٔ منتشرشده معتبر نیستند. → باید بازسازی شوند.

### ۳.۴ تحلیل استودیو (Electron/JS)

۳۹ فایل، ۳۲۷ گره گراف، **صفر مسیر IPC**، فقط `mpStudio.version` روی `window`، `contextIsolation: true`، `nodeIntegration: false`.
یعنی سطح حمله حداقلی است — و هر قابلیت بومی آینده باید کانال IPC جدید با اعتبارسنجی sender بسازد.

**پرونده‌ها:** `finn/reports/rea/2026-11-15-REA-AUDIT-VERIFY.md` (گزارش) + سه JSON شاهد.

---

## ۴. مطالعهٔ میکرو-لوپ‌ها — روش ساخت تا امروز

### ۴.۱ قالب هر میکرو-چرخه

```
Forge (ساخت با ایجنت مربوطه)
   ↓
Inspect (تست + lint + eval + REA)
   ↓
Normalize (رفع، ثبت درس در LEDGER، رگریشن در REGRESSIONS)
   ↓
Next (گزارش محلی و ثبت وضعیت؛ push خودکار/فوری ندارد)
```

هر میکرو سه کامیت جزئی دارد (`c1` موتور/API، `c2` رابط کاربری، `c3` تست + شاهد). هیچ کامیتی بدون تست سبز نمی‌رود.

### ۴.۲ چه ساخته شد (M00 → M44)

| بلوک | محتوا | وضعیت |
|---|---|---|
| M00–M17 | بوت‌استراپ، اسکلت backend/studio/client، ۱۲ migration، ۹ گیت کیفیت، گزارش پایانی | ✅ |
| M18–M31 | ۱۴ ماژول دامنه، موتور قواعد (axis/scoring/prescription/nutrition/safety/autoreg)، چک‌این QR+چهره، پرداخت، KPI | ✅ |
| M33–M40 | «۱۴ توانایی»: ارزیابی ۱۴ محوری، تولید برنامه، تغذیه، Community، پایلوت | ✅ |
| M41 | پلن‌های جنسیت‌محور (بانوان ۳۷ روزه) + صورتحساب | ✅ |
| M42 | لیدربوردهای مدیریتی + ثبت خروج (checked_out_at) | ✅ |
| M43 | admin pass (اعطا/ابطال نقش) + یکسان‌سازی کامل مجوز روی casbin + DENIES + D-005 | ✅ |
| M44 | موتور ریسک ریزش (۹ قاعده، دلیل‌دار) + API + کارت استودیو | ✅ |
| **M45** | **استودیو روی API واقعی (حذف mock)** | ⬜ بعدی |
| M46 | گزارش کارکرد مربیان | ⬜ |

### ۴.۳ وضعیت کیفی واقعی (از `REA-REVIEW-2026-11-15.md`)

۲۷۹ تست بک‌اند · eval درصد ۴/۴ (طلایی ۲۱۱۲/۲۱۱۲) · eval تجویز ۳/۳ صفر نقض · `ruff check` صفر · `tsc` صفر · vitest ۱۸ · تک‌head خطی `f1a2b3c4d5e6`.

### ۴.۴ قرمزهای CI (واقعی و کوچک)

| Job | علت | رفع |
|---|---|---|
| backend | `ruff format --check` → ۵۲ فایل | `ruff format .` |
| client-flutter | `test/set_feedback_sheet_test.dart` با `package:mp_app/...` (نام پکیج: `mp_client`) | ۵ خطا + ۱ تست فیل → یک ویرایش |
| studio | ✅ | — |

تست‌ها خودشان سبزند (۲۹۸ backend). **کد سالم است؛ قرمزی از فرمت و نام پکیج است.**

---

## ۵. بزرگ‌ترین گپ باقی‌مانده — با شاهد کد

استودیو **فقط** در صفحهٔ Analytics به API واقعی وصل است. پنج صفحهٔ دیگر روی دادهٔ ساختگی‌اند:

| صفحه | منبع فعلی | endpoint واقعی که باید استفاده شود |
|---|---|---|
| Dashboard | `kpis` از `src/data/mock.ts` | `GET /api/v1/admin/kpis` ✅ موجود (M29) |
| Members | `members` از `appStore` (mock) | `GET /api/v1/members` ✅ موجود |
| Finance | دادهٔ mock | `GET /api/v1/payments/finance/summary` ✅ موجود (M27) |
| CheckIn | mock | `analytics.py` داده دارد، **endpoint لیست حضور ندارد** → باید ساخته شود |
| Programs | mock | `GET /api/v1/programs` ✅ موجود |

**نکتهٔ مهم:** چهار endpoint از پنج مورد **همین حالا آماده‌اند**. یعنی M45-c1 (اعضا/مالی) و M45-c2 (برنامه‌ها)
عمدتاً کار فرانت‌اند است، نه بک‌اند. فقط «حضور» یک endpoint جدید لازم دارد.

این همان باگ دستهٔ E13 است: داشبورد عدد نشان می‌دهد که از DB نمی‌آید.

---

## ۶. نقشهٔ M45 (پیشنهاد اجرایی)

### M45-c1 — اعضا + مالی
- `src/lib/apiClient.ts` عمومی بساز (پایه، توکن، `AuthError`) — `adminApi.ts` الگو دارد
- `stores/appStore.ts`: حذف `mockMembers`، دریافت از `GET /members`، حالت loading/error/empty
- `pages/Finance.tsx` (یا معادل): `GET /payments/finance/summary`
- شاهد: `vitest` با fetch مسخره‌شده + اسکرین‌شات واقعی

### M45-c2 — حضور + برنامه‌ها
- **endpoint جدید:** `GET /api/v1/admin/attendance?from=&to=` (از `CheckIn`، با `checked_out_at`) + مجوز casbin + تست
- `pages/Programs.tsx`: `GET /programs` + `GET /programs/{id}`
- شاهد: تست integration برای endpoint جدید + R-00x رگریشن

### M45-c3 — E2E + بازنمایی صادقانه
- Playwright e2e-api: ورود → داشبورد → اعضا → برنامه‌ها با API واقعی
- ممیزی: **هیچ عددی در UI بدون منبع داده نماند**؛ هر جای mock باقی‌مانده صریحاً برچسب «نمونه» بگیرد
- به‌روزرسانی `OUTPUT-AUDIT` و قاعدهٔ S3b/S3c

---

## ۷. TODO کامل (به ترتیب اجرا)

### P0 — قبل از هر قابلیت
- [ ] `ruff format .` روی بک‌اند (۵۲ فایل)
- [ ] فیکس ایمپورت `mp_app` → `mp_client` در `test/set_feedback_sheet_test.dart`
- [ ] `setuptools >= 84.1.0` (PYSEC-2026-3447) در `pyproject.toml`/CI
- [ ] تأیید سبزی هر چهار job CI (backend, studio, client-flutter, e2e-api)

### P1 — M45 (استودیو واقعی)
- [ ] c1: اعضا + مالی از API واقعی
- [ ] c2: endpoint حضور + برنامه‌ها
- [ ] c3: E2E + ممیزی «هیچ عدد بی‌منبع»

### P2 — M46 (گزارش مربیان)
- [ ] c1: موتور محاسبه (حضور/درآمد/کمیسیون)
- [ ] c2: گزارش در استودیو
- [ ] c3: تست + rule-evidence

### P3 — رفع گپ‌های REA (کوچک، سریع)
- [ ] همگام‌سازی `versionName` با تگ ریلیز در `apk.yml`
- [ ] `domain-config` باریک برای cleartext (LAN فقط)
- [ ] `android:debuggable="false"` صریح در مانیفست release
- [ ] `audit-release-exposure` در چک‌لیست انتشار
- [ ] بازسازی `finn/reports/rea/*.json` روی APK فعلی

### P4 — صف محصول (از `BUILD-QUEUE.md`)
G1 بازخورد ست‌به‌ست → G2 نشانگر حجم → G5 ثبت غذا → G3 تغذیهٔ سازگار → G6 روند JP7 → Q4 صف آفلاین → G7 سنک LWW →
G4b مقایسهٔ LLM با قواعد → G9 کتابخانهٔ حرکات → G12 غذای ایرانی → نسخهٔ وب → G8 چت مربی → G13 مدل آمادگی →
آنالیز سگمنتال → G10 داشبورد KPI → G11 یادآوری → Q5 صیقل UI → Q7 مستندات → Q6 درگاه پرداخت (آخر)

### خارج از دامنه (D-024)
❌ تماس ویدیویی · ❌ iOS (نسخهٔ وب جایش) · ❌ کپی محتوای مالکیتی رقبا · ❌ دیکامپایل رقبای بسته

### نیازمند انسان
⏸️ پایلوت میدانی ۷ روزهٔ M40

---

## ۸. قوانین پابرجا (چک‌لیست هر چرخه)

1. F.I.N.N: Forge → Inspect → Normalize → Next؛ هیچ گیتی با قرمزی رد نمی‌شود.
2. هر باگ = یک تست رگریشن در `REGRESSIONS.md` (الان R-001…R-009).
3. آغاز هر چرخه: خواندن کامل `.finn/state/LEDGER.md` (۱۲ درس اکنون).
4. هر میکرو با شواهد محلی ثبت شود؛ commit فقط طبق اختیار شاخهٔ جاری و بدون push خودکار/فوری.
5. حداکثر ۳ تلاش برای هر خطا؛ سپس loop وابسته را `FAIL`/`BLOCKED` ثبت، آثار workspace را حفظ و به loop مستقل بعدی برو. هیچ `reset --hard`/`clean` یا ادعای subagent بدون اجرا مجاز نیست.
6. قبل از ساخت هر چیز: Grep/Glob برای Anti-Dup.
7. LLM عدد نمی‌سازد (G8) — همهٔ اعداد از موتور قواعد.
8. **جدید (G11):** هر ادعای بازبینی یا `evidence_id` REA دارد یا صریحاً «بازبینی دستی» برچسب می‌خورد.
9. REA فقط روی اهداف خودی + رقبای متن‌باز/عمومی؛ دیکامپایل بستهٔ رقبا ممنوع.
10. دادهٔ واقعی، کلید، و `node_modules` هرگز در گیت.

---

## ۹. آمادگی — یک نگاه

| لازم | وضعیت |
|---|---|
| Python ۳.۱۱ + pip | ✅ |
| Node ۲۲ (برای استودیو) | ✅ |
| Node ۲۴.۲۲.۳ پرتابل (برای REA) | ✅ |
| git + gh (احراز هویت) | ✅ |
| ECC ۷۱ ایجنت | ✅ |
| REA 6.9.0 + skill + MCP | ✅ |
| اسکریپت بازتولید ابزار | ✅ `install-toolchain.sh` |
| نقشهٔ M45 با endpointهای واقعی | ✅ |
| Flutter SDK | ❌ (گیت‌ها در CI — طبق D-002) |
| Docker | ❌ (در CI/سرور هدف — طبق D-003) |

**نتیجه: آماده‌ام. اولین حرکت = P0 (سبزکردن CI)، بعد M45-c1.**
