# آمادگی از سرگیری ساخت — ۲۰۲۶-۱۱-۱۵ (پس از M45)

> شاخه: `arena/86fc9529-mp` · وضعیت FINN: **READY** · CI: **سبز (۴/۴)**

---

## ۱. پاسخ کوتاه به «آیا همه چیز آماده است؟»

**بله برای از سرگیری ساخت.** با سه استثنای صادقانه که در بخش ۷ آمده.

| شرط | وضعیت |
|---|---|
| زنجیرهٔ ابزار لوپ (ECC + REA) | ✅ نصب و تأییدشده |
| بک‌اند روی این ماشین اجرا می‌شود | ✅ ۳۱۷ تست سبز محلی |
| استودیو روی این ماشین اجرا می‌شود | ✅ tsc صفر + ۳۰ تست |
| CI | ✅ **هر ۴ job سبز** (run 43733055890) |
| mock در استودیو | ✅ حذف شد (REA تأیید کرد) |
| گپ‌های Android | ✅ رفع و تأییدشده |

---

## ۲. روندهای شخصی‌سازی — شناخت کامل

شش زنجیرهٔ قطعی شناسایی شد. همه در `mp-app/backend/engine/` و همه **بدون LLM در اعداد** (G8).

### زنجیرهٔ ۱ — ورودی هدف‌محور/نیازمحور
`modules/population/intake.py` — سؤال پایه ثابت نیست؛ برای هر هدف سؤال تکمیلی متفاوت:

| هدف | سؤال‌های تکمیلی |
|---|---|
| hypertrophy | حجم اخیر · تحمل حجم · عضلات اولویت‌دار |
| strength | حرکات هدف · رکورد اخیر · تکنیک مشاهده‌شده |
| fat_loss | روند وزن ۳ ماه |

قاعدهٔ سخت: `population/gates.py` — مسیر بدون پشتوانه **متوقف** می‌شود، نه «عمومی + هشدار»
(کودک، بارداری، معلولیت، بیماری ← `gated_no_auto_generation`).

### زنجیرهٔ ۲ — ارزیابی ۱۴ محوری
آزمون میدانی ← نمره با منبع (نرم‌های استناددار) ← تصمیم هر محور:
`direct` / `maintain` / `covered` / `refer` / `unknown` — و `unknown` واقعی است، نه صفر.

### زنجیرهٔ ۳ — تجویز محورآگاه
`engine/axis_prescription.py` (`axis-prescription-1.0`):
- `direct` ← حرکت اختصاصی از نردبان محور با ۳ ست
- `maintain` ← سطح بالاتر با ۲ ست
- `covered` ← پوشش از حرکت دیگر، یا «حامل چندمحوره»
- **بودجهٔ خستگی هفتگی**: عبور از سقف ← اول `maintain` بریده می‌شود، سپس `covered` — **هرگز `direct`**
- قانون «یک حرکت، چند محور، یک‌بار بار» (`load-attribution-1.0`)

### زنجیرهٔ ۴ — تنظیم خودکار بار
`engine/autoreg.py` (`autoreg-1.0`) — «قانون ۲ برای ۲»: RIR ≥ ۲ ← +۲٫۵ کیلو؛ RIR = ۰ یا تکرار کم ← −۵ کیلو.

### زنجیرهٔ ۵ — بازخورد ست‌به‌ست
`engine/set_feedback.py` (`set-feedback-1.0`): RIR/درد هر ست ← وزن از autoreg، حجم از قواعد درد
(درد ≥ ۷ ← کاهش یک ست). هر پیشنهاد `reason` + `rule_version` دارد.

### زنجیرهٔ ۶ — جنسیت‌محور
`engine/gender_plans.py` — پلن بانوان ۳۷ روزه جدا، با سیاست صورتحساب مستقل.

**الگوی مشترک همه:** ورودی نامعتبر ← **خطای صریح**؛ خروجی همیشه `reason` + `rule_version`؛ مبهم = `unknown`.

---

## ۳. Mirror فلاتر — یافته و تصمیم

**در مخزن هیچ پیکربندی mirror یافت نشد:** بدون `FLUTTER_STORAGE_BASE_URL`، بدون `PUB_HOSTED_URL`،
بدون `pubspec.lock` با URL سفارشی، و Gradle فقط `google()` + `mavenCentral()` دارد.

**در این sandbox:** `pub.dev`، `storage.googleapis.com`، `download.flutter.io` و آینه‌های
(`tuna.tsinghua`، `aliyun`) همه **غیرقابل‌دسترس** هستند؛ فقط npm/PyPI/GitHub باز است. پس
SDK فلاتر قابل نصب نیست و کد Dart فقط در CI اجرا می‌شود (همان تصمیم D-002).

**عملیاتی‌سازی mirror (برای وقتی لازم شد):** اسکریپت `docs/MuscleParadise/finn/install-toolchain.sh`
باید با دو متغیر اجرا شود:

```bash
export FLUTTER_STORAGE_BASE_URL=https://<mirror-host>
export PUB_HOSTED_URL=https://<mirror-host>/pub
bash docs/MuscleParadise/finn/install-toolchain.sh flutter   # بخش flutter (در نسخهٔ بعدی)
```

تا آن زمان، مسیر سبز این است: **کد Dart ← commit ← CI** (که الان سبز است).

---

## ۴. ابزارهای نصب‌شده در این نوبت

| ابزار | نسخه | مسیر | نقش |
|---|---|---|---|
| ECC | `d2ef2680` (v2.2.3) | `.finn/ecc` + `.claude/` | ۷۱ ایجنت، ۳۱۴ اسکیل، ۹۸ فرمان |
| REA | 6.9.0 | `~/toolchain/rea` | بازبینی با Evidence |
| Node پرتابل | 24.22.3 | `~/toolchain/node-linux-x64` | REA به ≥22.23.4 نیاز دارد |
| **semgrep** | 1.185.0 | `/tmp/tools/venv` | گیت امنیت CI |
| **locust** | 2.47.0 | `/tmp/tools/venv` | دود بار |
| **shellcheck** | 0.11.0 | `/tmp/tools/venv` | گیت اسکریپت |
| **ruff** | 0.17.5 | backend `.venv` | lint + format |
| **bandit** | (dev deps) | backend `.venv` | اسکن امنیت |
| **pyaxmlparser** | — | `/tmp/tools/venv` | خواندن مانیفست APK |
| backend venv | — | `mp-app/backend/.venv` | ۴۱ پکیج، ۳۱۷ تست سبز |
| studio node_modules | — | `mp-app/studio/node_modules` | ۲۷۷ پکیج، ۳۰ تست |

⚠️ `/tmp/tools/venv` در snapshot نمی‌ماند. بازسازی: `pip install semgrep locust shellcheck-py pyaxmlparser`.

---

## ۵. اشکال‌هایی که به ایجنت‌های ECC سپرده و رفع شد

| اشکال | ایجنت (نقش) | رفع | شاهد |
|---|---|---|---|
| `ruff format` — ۵۲ فایل | `build-error-resolver` | `ruff format .` | format ۰ خطا |
| تست Dart با `package:mp_app` | `build-error-resolver` | → `mp_client` | client-flutter **سبز** |
| `setuptools` آسیب‌پذیر | `security-reviewer` | `>=84.1` در pyproject | pip-audit در CI |
| CI به شاخهٔ قدیمی push می‌کرد | `code-reviewer` | `head_ref \|\| ref_name` | diagnostics روی شاخهٔ درست |
| endpoint بدون policy → ۴۰۳ | `security-reviewer` | ۴ ردیف policy | تست ۴۰۳ دارد |
| `days_left` کف می‌گرفت | `tdd-guide` | `math.ceil` | `test_members_summary_expiring_window` |
| mock در ۵ صفحهٔ استودیو | `architect` + `tdd-guide` | ۴ endpoint + کلاینت API | REA: `mock.ts` در گراف نیست |
| `--` داخل کامنت XML | `build-error-resolver` | بازنویسی کامنت | XML well-formed |

---

## ۶. تأیید REA که گپ‌ها رفع شدند

جزئیات: `finn/reports/rea/2026-11-15-REA-GAP-CLOSURE.md`

| گپ | تأیید |
|---|---|
| mock حذف شد | تحلیل JS با ۲۶ فایل سورس ⇒ `src/data/mock.ts` **غیرحاضر** · `ev_a3e81c13…` |
| `debuggable=false` | `ET.parse(manifest)` → `False` (**observation** نه inference) |
| `allowBackup=false` / `INTERNET` / `networkSecurityConfig` | همه تأیید شدند |
| cleartext | کامنت به واقعیت پلتفرم اصلاح شد + مهار واقعی در `ApiClient` (۴ تست) |
| `versionName` | `pubspec: 0.2.0+2021` + CI از تگ می‌خواند |

**باز (صادقانه):** APK جدید با این اصلاحات **هنوز ساخته نشده**. ادعای «در APK منتشرشده رفع شد» تا بیلد بعدی معتبر نیست.

---

## ۷. سه استثنای صادقانه

1. **Flutter SDK محلی نیست** — کد Dart فقط در CI اجرا می‌شود. ۴ تست شبکه‌ای که امروز نوشتم
   **محلی اجرا نشدند**؛ اولین اجرایشان در بیلد بعدی CI است.
2. **`alembic check` drift دارد** — ۱۴ عملیات (نبود-index روی ۷ جدول + nullable ناسازگار در
   `gym_classes`/`class_bookings`). این drift **پیش از M45** وجود داشت؛ من مدلی اضافه نکردم.
   نیازمند یک migration در M46.
3. **APK تازه ساخته نشده** — اصلاحات Android در سورس‌اند، نه در آرتیفکت.

---

## ۸. قدم بعدی (M46)

```
M46-c1  موتور محاسبهٔ کارکرد مربی (حضور/درآمد/کمیسیون) + تست
M46-c2  گزارش در استودیو از API واقعی
M46-c3  تست + rule-evidence + migration برای drift
```

سپس صف محصول: G1 بازخورد ست‌به‌ست ← G2 نشانگر حجم ← G5 ثبت غذا ← G3 تغذیهٔ سازگار ← G6 روند JP7 ← …

**قواعد پابرجا:** هر میکرو = یک commit `mp(Mxx): … [finn]` + push · هر باگ = تست رگریشن ·
هیچ گیتی با قرمزی رد نمی‌شود · LLM عدد نمی‌سازد · هر ادعای بازبینی باید `evidence_id` داشته باشد (G11).
