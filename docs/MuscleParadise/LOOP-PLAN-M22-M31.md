# نقشهٔ لوپ سوم — M22 تا M31 | «میکرو-لوپ‌های کلاس جهانی با مأموریت ECC»

> وضعیت این سند: **آرشیوی/تاریخی** (طرحی که در ۲۰۲۶-۱۱-۱۴ تصویب شده بود)؛ آن تصویب تاریخچه است، نه فعال‌سازی برای شاخهٔ جاری. صف/نقشهٔ جاری در `TODO-2026-11-16.md` تعیین‌کننده است.
> اصل D-033 بر هر loop از این بازه که صریحاً در صف جاری `READY` شود حاکم است: اجرای خودمختار بدون نظارت روتین، ثبت تصمیم‌های محدود/برگشت‌پذیر و توقف فقط loop وابسته روی blocker واقعی. این سند به‌تنهایی loop را فعال نمی‌کند.
> قواعد قدیمی push به `arena/a0408b29-mp`، push خودکار و سطح L2/تأیید کاربر **منسوخ و غیرقابل‌اجرا** هستند. در شاخهٔ جاری push/release/deploy/rollback، پرداخت واقعی، DB تولید و دست‌کاری آثار موجود مجاز نیست؛ فرایند ECC/S1–S9 زیر صرفاً محتوای تاریخی/مرجع است.

## ۰. فلسفهٔ لوپ
هر «میکرو-لوپ» = یک واحد قابل تحویل با چرخهٔ تاریخی:
`spec (ردیف نیازمندی + شاهد) → build → gates (تست/ایستا) → بازبینی واقعی در صورت دسترسی → fix → گزارش محلی`
- سطح استقلال و branch/push از سیاست سراسری D-033 و صف جاری می‌آیند، نه L2 تاریخی: loop فعال `READY` بدون نظارت روتین پیش می‌رود؛ تصمیم محدود/برگشت‌پذیر ثبت می‌شود، blocker غیرقابل‌حدس فقط همان loop را `BLOCKED`/`UNKNOWN` می‌کند.
- «بازبینی ECC» فقط در صورت اجرای واقعی ابزار/ایجنت ادعا می‌شود؛ اگر در دسترس نیست، نبود شاهد صریح می‌ماند. هر test/gate همچنان اجباری است؛ push/release/deploy انجام نمی‌شود.

## ۱. ایجنت‌های ECC — مأموریت مرحله‌به‌مرحله
| ایجنت | مأموریت در هر میکرو-لوپ | ابزار/مرجع |
|---|---|---|
| **ECC-1 کد/معماری** | معماری تمیز، تست واحد/یکپارچه، کارایی، بازاستفاده (E12)، بدون چرخ‌سازی | pytest+ruff، vitest، flutter test |
| **ECC-2 امنیت/داده** | مالکیت/RBAC، E09 (دادهٔ واقعی هرگز در Git)، E10، اسکن آسیب‌پذیری | semgrep (rulepack رسمی)، bandit، pip-audit، npm audit، Strix (اختیاری) |
| **ECC-3 علم/شواهد** | E13/E14: هر ادعا ← شاهد؛ قواعد نسخه‌دار؛ بدون ضریب از حافظه؛ وضعیت ۱۳ محور | چک‌لیست E01–E14، الگوهای scientific-agent-skills |
| **ECC-4 اخلاق/حقوق** | مجوزها/notice، حریم خصوصی، محدودیت جمعیتی، ممنوعیت LLM-تجویزکننده (E04/E08) | REUSE-INVENTORY، سیاست مجوز (D-015) |
| **ECC-5 جهان‌اول UX** | DESIGN.md + چک‌لیست وب + ۴ وضعیت + motion + RTL/فارسی | `design/DESIGN.md`، `design/web-interface-guidelines.checklist.md` |

## ۲. مراحل کیفی ثابت هر میکرو-لوپ (S1–S9)
| مرحله | چه | منبع ادغام‌شده |
|---|---|---|
| S1 spec | ردیف نیازمندی + شاهد مورد انتظار + حدود (الگوی spec فین-لوپ) | finna/Finn-loop |
| S2 build | «اول موجود» — بدون بازنویسی قابلیت سالم؛ هر OSS ورودی ← ثبت E12 | دستور کاربر + E12 |
| S3 gates | pytest+ruff+bandit+pip-audit / vitest+eslint / flutter analyze+test | موجود |
| S3b **بازبینی خروجی‌ها (اجباری)** | هر دکمه/فرم/مسیر جدید ← خروجی ملموس + ثبت در `OUTPUT-AUDIT` + تست دودی در گزارش | درخواست کاربر ۲۰۲۶-۱۱-۱۴ |
| S3c **دود بار** | هر میکرو با endpoint/مسیر جدید ← Locust کوتاه (۱۰ کاربر/۱۰s) — «کرش زیر بار» ممنوع | `tests/load/locustfile.py` + گزارش M22-smoke |
| S4 design | بازبینی UI: DESIGN.md + چک‌لیست Vercel + taste/motion (وب) یا §۶ (فلاتر) | vercel-labs/web-interface-guidelines، Leonxlnx/taste-skill، nextlevelbuilder/ui-ux-pro-max-skill، اصول motion |
| S5 security | semgrep rulepack + (اختیاری) Strix headless در محیط دارای LLM محلی | semgrep/semgrep-rules، usestrix/strix |
| S6 science | چک‌لیست E01–E14 + «بدون ادعای بدون شاهد» + زنجیرهٔ داده←قاعده←شاهد←تصمیم | k-dense-ai/scientific-agent-skills (الگوها) |
| S7 rights | مجوز/notice/حریم؛ اثبات «بدون دادهٔ واقعی» در diff | E08/E09 |
| S8 e2e | Playwright سناریوی بحرانی (ورود/چک‌این/برنامه) — browser-use وقتی درایور موجود است | browser-use/browser-use (الگو)، Playwright (هسته) |
| S9 report | گزارش میکرو-لوپ در LEDGER + به‌روزرسانی MASTER_MAP؛ گزارش/commit محلی فقط طبق اختیار جاری، بدون push | رویهٔ تاریخی M00–M21 |

## ۳. نقشهٔ منابع → وضعیت ادغام (۲۸ منبع بررسی‌شده ۲۰۲۶-۱۱-۱۴)
| منبع | یافته (repo/سایت) | تصمیم | کاربرد |
|---|---|---|---|
| Web design guideline | vercel-labs/web-interface-guidelines (MIT) | ✅ **ادغام شد** | `design/web-interface-guidelines.checklist.md` — مرحلهٔ S4 |
| Awesome design.md | الگوی DESIGN.md | ✅ **ادغام شد** | `design/DESIGN.md` — قرارداد طراحی |
| Taste skill | Leonxlnx/taste-skill | ✅ **ادغام (چک‌لیست)** | قواعد anti-generic در S4/DESIGN.md |
| UI UX Pro Max skill | nextlevelbuilder/ui-ux-pro-max-skill | ✅ **ادغام (چک‌لیست)** | الگوهای طراحی در S4 |
| Finn-loop | finna/Finn-loop | ✅ **ادغام (فرایند)** | چرخهٔ spec→build→review→merge + برچسب تأیید |
| Hermes (مغز اجرایی) | HakimOuah/hermes-orchestration + graseeuh/HERMES | ✅ **ادغام (فرایند)** | سطوح L0–L5، گیت تأیید، بازرس مستقل |
| Ruflo | ruvnet/ruflo | ✅ **الگو (hooks)** | انضباط کیفیت قبل/بعد عملیات + hook گیت |
| Scientific agent skills | k-dense-ai/scientific-agent-skills | ✅ **الگو (S6)** | شواهد‌محوری + تفکر انتقادی + Mermaid |
| Diagram design | استاندارد Markdown+Mermaid | ✅ **ادغام** | نمودار معماری در گزارش‌ها (Mermaid) |
| Find skills | rohitg00/skillkit + jpwang1208/find-skills-x | ✅ **فرایند** | قبل از ساخت هر چیز: جست‌وجوی skill رایگان (قاعدهٔ چرخ) |
| Strix (امنیت) | usestrix/strix (Apache-2.0) | ✅ **مرحلهٔ S5 (اختیاری)** | pentest هوشمند وقتی LLM محلی/کلید موجود است |
| Browser-use | browser-use/browser-use (MIT) | ✅ **مرحلهٔ S8 (اختیاری)** | e2e هوشمند؛ هسته = Playwright |
| AgentMemory | rohitg00/agentmemory (Apache-2.0) | 🟡 آینده | حافظهٔ مشترک ایجنت‌ها؛ فعلاً `.finn/` کافی است |
| OmniRoute | df4p/omniroute (MIT) | 🟡 آینده | زیرساخت LLM چندتأییدکننده برای لایهٔ D-007 — نه اکنون |
| n8n-workflows | n8n (Sustainable Use License) | ❌ **دامنهٔ قبلی منسوخ — ADR-005** | یادآور تمدید/SMS به n8n واگذار نمی‌شود؛ فقط اعلان CI read-only مجازِ آینده است. Backup workflowهای خود n8n هم فقط با instance واقعی، مخزن خصوصی و بازبینی export |
| Dockploy → **Dokploy** | Dokploy/dokploy | ✅ **M30** | مدیریت/استقرار سرور محلی + **بکاپ خودکار دیتابیس** |
| Skiper UI | skiper-ui (shadcn) | ✅ (از قبل D-005) | کامپوننت‌های پولیش استودیو |
| Vengeance UI | Ashutoshx7/VengeanceUI (رایگان) | ✅ مرجع | میکروتعامل‌های استودیو/فرود (با E12) |
| Framer Motion | framer/motion | ✅ (از قبل D-005) | استاندارد motion در استودیو |
| 21st.dev | 21st.dev | ✅ مرجع | الگوهای micro-interaction (§۴ DESIGN.md) |
| Vgpu + shader-for-interfaces | vercel-labs/vgpu، v2space-labs/shader-for-interfaces (MIT) | 🟡 انتخابی | افکت‌های GPU فقط صفحات فرود — با fallback/reduced-motion |
| Particles by Casberry | پلی‌گراند WebGL | 🟡 مرجع | فقط الهام بصری صفحهٔ فرود |
| Originkit | originkit.dev | 🟡 مرجع | میکروتعامل‌های کلیک/هَوِر |
| Daisy UI | saadeghi/daisyui | ❌ رد | تداخل با shadcn (D-005) — فقط مرجع جایگزین |
| Animaster Lib | animasterlib.dev | ❌ **رد — پولی** | قانون هزینهٔ صفر منابع (تصمیم قطعی کاربر) |
| Getlayers | aanthill/getlayers + getlayers.ai | ✅ الگو | «قرداد + enforcement» (hooks خواندن DESIGN.md) — محتوای پولی استفاده نشد |
| Design motion principal | اصول ۱۲گانه + Motion Primitives | ✅ **ادغام (§۴ DESIGN.md)** | قواعد زمان‌بندی/منحنی/تعادل افکت |
| Soup github | **یافت نشد** | ⚪ نامعلوم | اگر نام دقیق‌تری دهید بررسی می‌شود |

## ۴. مایل‌استون‌ها و میکرو-لوپ‌ها

### M22 — ترمیم فوری + بهداشت (۳ میکرو)
| میکرو | کار | ECC | DoD |
|---|---|---|---|
| c1 | 🔴 `MpColors.info` + فعال‌سازی `flutter analyze` در CI | 1,5 | کامپایل کلاینت سبز |
| c2 | ⚠️ CORS allowlist محیطی + رفع useless-inner-function | 2 | semgrep wildcard-cors بسته شود |
| c3 | rate-limit ورود + بازیابی رمز (توکن یک‌بارمصرف) | 2 | تست نفوذ ساده + تست واحد |

### M23 — دادهٔ بنیادین (۴ میکرو)
c1 مهاجرت Alembic + baseline | c2 بکاپ/بازیابی خودکار + تست restore | c3 لایهٔ جلالی (API+کلاینت) + فیلد `quality/method` یکنواخت (E02) | c4 سیاست نگهداری/حذف داده (E10) + رمزگذاری در سکون
- ECC: 1,2,3 | گیت: E01/E02/E10 + drill بکاپ

### M24 — گزارش محرمانهٔ ۸بخشی (۳ میکرو)
c1 نگاشت رسمی ۱۴↔۱۳ محور + ماتریس پوشش حرکات (بدون جمع دوبارهٔ بار) | c2 بازنویسی report_generator به قرارداد ۸بخشی (HTML چاپی + JSON — D-020) با زنجیرهٔ داده←قاعده←شاهد←تصمیم | c3 snapshot مصون (تغییر پروفایل بی‌ردپا نسازد) + نمونهٔ ساختگی تست
- ECC: 1,3,4 | گیت: E02/E03/E14 + قالب `templates/rule-evidence.template.json`

### M25 — گیت جمعیتی + ورودی پویا (۳ میکرو)
c1 گیت صریح توقف تولید خودکار مسیرهای پشتیبانی‌نشده (کودک/بارداری/معلولیت/بیماری/آسیب) + ماتریس وضعیت هر مسیر (شواهد/قاعده/ارزیابی/نظارت/آزمون — D-016) | c2 ورودی هدف‌محور با سؤال تکمیلی پویا | c3 پروتکل ایمنی سالمند (بار کمتر/گرم‌کردن/معیار توقف)
- ECC: 3,4 | گیت: E04/E05 — مسیر فاقد پشتوانه = غیرقابل تولید، نه «عمومی + هشدار»

### M26 — انقلاب UX / کلاس جهانی (۴ میکرو)
c1 Vazirmatn + RTL حرفه‌ای + توکن‌سازی کامل (DESIGN.md §۱–۳) | c2 چهار وضعیت loading/empty/error/offline در همهٔ صفحات | c3 motion pass: انتقال‌های صفحه، Hero، شمارندهٔ متحرک KPI، haptic (§۴) | c4 میکروتعامل‌های 21st.dev/Vengeance + اسکرین‌شات در `ui-previews/`
- ECC: 5 (با 1) | گیت: DESIGN.md §۹ + چک‌لیست Vercel + reduced-motion

### M27 — بیزینس باشگاه (۴ میکرو)
c1 خرید/تمدید عضویت از اپ شاگرد (کیف‌پول+درگاه) | c2 رزرو/لیست انتظار کلاس از اپ + تقویم هفتگی | c3 کمیسیون/حق‌الزحمهٔ مربی | c4 گزارش مالی/ماندگاری + خروجی CSV حسابداری
- ECC: 1,2 | وابسته: M23 (داده) | یادآوری محصولی در APScheduler/سرویس اعلان MP می‌ماند؛ n8n برای پیام عضو استفاده نمی‌شود (ADR-005)

### M28 — اندروید/آفلاین/عملیات سبک (۴ میکرو)
c1 صف آفلاین + همگام‌سازی (حضور/چک‌این) با حل تعارض | c2 OTP پیامکی (پنل ایرانی) + بازیابی رمز کامل | c3 خط لولهٔ APK + امضای release در CI | c4 HTTPS داخلی + بستهٔ استقرار سرور محلی (اسکریپت+راهنمای فارسی)
- ECC: 1,2 | گیت: آفلاین‌محور (D-018)

### M29 — هوشمندی تمرین (۴ میکرو)
c1 KPI اجرای ست‌ها (RPE/خستگی) در checkin | c2 «پیشنهاد وزن بعدی با دلیل» (الگوی GymCoach MIT — ثبت E12 کامل) | c3 autoregulation/deload (قاعدهٔ نسخه‌دار) | c4 تعمیم پیکرسنجی به ۷ محل J-P (D-012) — **خام mm فقط، معادله قفل تا مرجع مستقل**
- ECC: 1,3 | گیت: E06/E07 — تغییر با دادهٔ واقعی، نه تصادفی

### M30 — عملیات و پایداری (۴ میکرو)
c1 Dokploy/compose + بکاپ خودکار + drill بازیابی | c2 تست بار (اوج باشگاه) + پایش/هشدار | c3 e2e کامل (Playwright سناریوهای بحرانی) | c4 راهنمای عملیات فارسی + مانیتورینگ
- ECC: 1,2 | گیت: S8 + گزارش بار

### M31 — Face-ID + انتشار (۳ میکرو)
c1 ماژول Face-ID (اثبات‌شده — `finn/reports/faceid-evidence/`) طبق تصمیم آیندهٔ کاربر | c2 متن حریم خصوصی/شرایط (فارسی/ایران) + لاگ دسترسی دادهٔ حساس | c3 تصمیم LICENSE + چک‌لیست انتشار
- ECC: 2,4 | گیت: E08/E09/E10 — تصویر چهره هرگز در Git/لاگ

## ۵. قواعد اجرایی لوپ
1. هر micro-loop باید گزارش محلیِ شواهدمحور در `finn/reports/` داشته باشد؛ commit فقط اگر در شاخهٔ جاری مجاز/لازم باشد. push اجباری/خودکار نیست و در scope جاری ممنوع است.
2. هر UI ← DESIGN.md §۹ ؛ هر ادعا ← شاهد (E14)؛ هر OSS ← ثبت E12 (commit/file/symbol/license/diff/tests).
3. دادهٔ واقعی هرگز در Git/تست/لاگ/REA (E09) — فقط ساختگی.
4. گیت‌های J-P، مسیرهای جمعیتیِ بی‌شاهد و داده به مدل بیرونی (E04/E11) دور زده نمی‌شوند؛ loop وابسته `BLOCKED`/`UNKNOWN` می‌ماند و loopهای مستقل ادامه می‌یابند.
5. نظارت/مشورت روتین کاربر گیت اجرا نیست. تصمیم فنی/طراحیِ محدود و برگشت‌پذیر با دلیل ثبت می‌شود؛ تصمیم مادیِ غیرقابل‌حدس سؤال‌پرسیدن را توجیه نمی‌کند و به blocker محلی تبدیل می‌شود.
6. کیفیت «کلاس جهانی» = عبور از S4 + DESIGN.md §۹ در هر تغییر UI — نه ادعای بدون اسکرین‌شات.

## ۶. داشبورد پایش
- `MASTER_MAP.md`: وضعیت هر میکرو (⏳/🔄/✅)
- `.finn/state/LEDGER.md`: شماره‌گذاری سراسری ادامه می‌یابد (#۹ به بعد)
- `DECISIONS.md`: D-021 به بعد
- گزارش milestone: `finn/reports/Mxx-code-review.md` + به‌روزرسانی FINAL_REPORT
