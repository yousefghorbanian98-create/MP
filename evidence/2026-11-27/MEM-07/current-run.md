# MEM-07 / PWA-36 — «ارزیابی و روند» در مسیر عضو (2026-11-27)

```text
BRANCH=arena/3c08bfbd-mp  (base main@7c4771f)
MEM-07/PWA-36=PARTIAL/NOT_ACCEPTED (checkbox TODO باز است)
MEM07_CONTRACT: unit=yes(ضمنی، _mm) · measured_at=yes · comparable=yes → BLOCKED نیست
NEW_ENDPOINT=no — همان GET /api/v1/assessments/jp7/member/{id}/trend
PHOTO_IMPLEMENTED=no (نه در کد، نه در UI)
```

## پاسخ قرارداد (پیش از UI، با `grep -n` واقعی)

فایل کامل: [`contract-answer.txt`](contract-answer.txt).

| پرسش | پاسخ | فایل/خط |
|---|---|---|
| `measured_at` در هر اندازه‌گیری؟ | **بله** | `modules/assessment/service.py:193` (+ `first_at`/`last_at` در `276-277`، `span_days` در `278`) |
| `unit` در پاسخ؟ | **بله، ضمنی** — هر عدد یکای خود را در نام فیلد دارد: `sum_mm:194`، `delta_mm:281`، `delta_mm_per_week:282`، `first_sum_mm/last_sum_mm:279-280`، `interpretation.threshold_mm:292`؛ کلید جدا به نام `unit` وجود ندارد | `service.py:147` (`JP7_SUM_CHANGE_MM = 2.0`) |
| «قابل مقایسه بودن» صریح است یا فقط سری زمانی؟ | **صریح** — `trend: None` وقتی کمتر از دو اندازه‌گیری است (`service.py:204`) + `data_state: "insufficient_measurements"` (`211`) در برابر `"trend_available"` (`300`) + `interpretation.status` و `threshold_mm` و `confidence` | `service.py:150-302` |
| ownership | `ensure_member_scope` در خط `170` همین تابع؛ تست ۴۰۳ موجود: `tests/integration/test_m50_jp7_trend.py:205` | — |

نتیجه: هیچ عددی اختراع نشد و BLOCKED لازم نبود. UI فقط وقتی عدد پیشرفت می‌سازد که
`data_state == "trend_available"` **و** `trend != null`.

## کاری که انجام شد

1. `studio/src/components/MemberJp7Trend.tsx` (تازه):
   - شناسهٔ عضو از `GET /members/me` (قاعدهٔ MEM-04)، نه از کلاینت.
   - عدد پیشرفت **فقط** در حالت قابل‌مقایسه؛ در بقیهٔ حالت‌ها متن صریح
     «این پاسخ «قابل مقایسه» نیست؛ پس هیچ عدد پیشرفتی (نه صفر) ساخته نمی‌شود.»
   - `data_state` ناشناخته (مثل `stale`) ⇒ `data-comparable="no"` حتی اگر `trend` پر باشد.
   - هر عدد با واحد («میلیمتر») و تاریخ اندازه‌گیری (تقویم شمسی، `formatMemberDateTime`)
     و منبع (`GET /api/v1/assessments/jp7/member/{member_id}/trend`).
   - `body_fat_pct === null` ⇒ «قفل (نمایش داده نمی‌شود)»، نه صفر و نه عدد ساختگی.
   - فهرست خالی ⇒ «این «پیشرفت صفر» نیست؛ یعنی داده‌ای ثبت نشده است.»
   - عکس پیشرفت بدن: نه پیاده‌سازی، نه رندر؛ جملهٔ صریح روی صفحه و هیچ `<img>` (تست).
   - ۴۰۳ (`ForbiddenError`) ⇒ fail-closed با `role="alert"` و بدون هیچ عددی.
2. مسیر عضو: `MemberPage = "home" | "today" | "progress"`، مسیر `/member/progress`
   (`lib/navigation.ts`)، آیتم ناوبری «ارزیابی و روند» و رندر در `App.tsx`.
   → این تغییر `navigation.ts` را که **منبع crosswalk** است عوض می‌کند، پس بازتولید
   artifactها در commit بعدی انجام شد (به‌عمد جدا، تا digest روی درخت تمیز باشد).
3. `tests/memberJp7Trend.test.tsx` (تازه، ۷ تست): واحد+تاریخ+منبع، تفکیک
   `insufficient`/`stale`/موفق، ۴۰۳، سری خالی، درصد چربی قفل/سرور، نبودِ `<img>`.

## نتیجه‌ها

```text
vitest tests/memberJp7Trend.test.tsx   → 7 passed
vitest (کل)                            → 62 فایل (58 pass / 4 skip) · 438 تست (423 pass / 15 skip)
tsc -b / eslint .                      → پاک / پاک
interaction_map --check                → 32 سطح، 163 مسیر، رانش صفر
docs_gate                              → 38 فایل/625 لینک/15 Mermaid
```

## همچنان باز (چرا PARTIAL)
- اجرای واقعی روی دستگاه/مرورگر و «مقایسهٔ دو ارزیابی» از نمای محصول انجام نشده.
- ارزیابی ۱۴ محوری (`/axis-assessments/...`) و گزارش سگمنتال در این برش UI عضو ندارند؛
  این برش فقط JP7 trend را پوشش می‌دهد (دامنهٔ صریح، نه ادعای کامل).
- reviewer مستقل برای تفسیر سلامت (`MEM-06`/`MEM-07`) ندارد → `UNKNOWN`.
