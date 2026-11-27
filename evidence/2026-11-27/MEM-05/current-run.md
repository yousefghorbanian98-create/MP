# MEM-05 / PWA-34 — ثبت تمرین/feedback (برش ۲۰۲۶-۱۱-۲۷ UTC)

وضعیت کارت: `PARTIAL/NOT_ACCEPTED` — checkbox canonical باز. `MEM-05` **BLOCKED نیست**، چون قرارداد idempotent واقعی وجود دارد.

## ۰) پاسخ پرسش گیت (قبل از هر UI)

**آیا `POST /programs/set-feedback` شناسهٔ یکتا/شمارهٔ نسخه می‌گیرد یا فقط «آخرین ست» را به‌روز می‌کند؟**

این مسیر **نه شناسهٔ یکتا دارد، نه شمارهٔ نسخه**، و «آخرین ست» را هم به‌روز نمی‌کند — هر ارسال ردیف **تازه** می‌سازد:

- `mp-app/backend/modules/programs/schemas.py:103-106` — `SetFeedbackIn = {member_id, program_id, entries[]}`؛ هیچ `set_id`/`client_id`/`version`/`idempotency_key` نیست.
- `mp-app/backend/modules/programs/schemas.py:87-100` — هر entry فقط `movement_id, weight, target_reps, reps_done, rir, soreness, sets_done, notes`.
- `mp-app/backend/modules/programs/service.py:183-197` — برای هر entry یک `db.add(SetFeedback(...))` و سپس `commit()`؛ هیچ جست‌وجوی تکراری/`upsert` نیست.
- `mp-app/backend/modules/programs/service.py:199-204` — بعد از commit، `apply_suggestions(...)` روی هفتهٔ بعد اعمال می‌شود؛ ارسال دوباره یعنی اعمال دوباره.
- شاهد اجرایی: `test_unkeyed_set_feedback_endpoint_duplicates_on_retry` (در `tests/integration/test_mem05_set_feedback_idempotency.py`) دو بار همان درخواست را می‌فرستد → **۲ ردیف**.

**ولی** یک قرارداد idempotent از قبل وجود دارد و ساخته نشد:

- `mp-app/backend/modules/programs/router.py:134-143` — `POST /programs/sync/set-feedback` با `SyncIn{member_id, items[]}`.
- `mp-app/backend/modules/programs/router.py:113-127` — `class SyncItemIn` شامل `client_id` (۱..۶۴، خط ۱۱۴)، `device_id` (خط ۱۱۸)، `updated_at` (خط ۱۱۹).
- `mp-app/backend/modules/programs/service.py:584-700` — کلید رکورد `device_id:client_id` است؛ `resolve_batch` با LWW تصمیم می‌گیرد؛ همان نوشتهٔ دوباره (`conflict_resolved`, `winner=server`) در `unchanged_keys` گزارش می‌شود، نه به‌عنوان اعمال تازه.
- `mp-app/backend/db/models/programs.py:113-116` — ستون‌های `client_id`, `device_id`, `client_updated_at` روی `set_feedbacks` وجود دارند.

⇒ نتیجه: برای نوشتن از `sync/set-feedback` استفاده می‌کنیم؛ `set-feedback` (بدون کلید) صدا زده نمی‌شود.

## ۱) چه چیزی ساخته شد

- `mp-app/studio/src/lib/feedbackQueue.ts` (تازه): `device_id` پایدار در `localStorage` (`mp_device_id`)، ساخت `client_id` یکتا، و `buildPendingWrite` که `client_id` + `updated_at` **همان تلاش** را نگه می‌دارد.
- `mp-app/studio/src/lib/api.ts`: `syncSetFeedback()` + تایپ‌های `SetFeedbackSyncItem`/`SetFeedbackSyncResult`؛ `postJson` حالا `AbortSignal` می‌گیرد و **Abort را از «اتصال برقرار نشد» جدا** می‌کند («زمان پاسخ سرور گذشت — ثبت نشد»).
- `mp-app/studio/src/components/SetFeedbackForm.tsx` (تازه، کنترل‌ها از antd طبق Q11): فرم ست (حرکت/بار/تکرار هدف/تکرار انجام‌شده/RIR/درد).
- `MemberTodayProgram`: فرم زیر برنامهٔ تأییدشده رندر می‌شود و `onRecorded` آمادگی را **از API** دوباره می‌خواند؛ شمارش `data_counts.feedback_rows` سرور روی صفحه نمایش داده می‌شود.

## ۲) الزامات و پاسخ هرکدام

| الزام | وضعیت | شاهد |
|---|---|---|
| اتصال به «شناسه و نسخهٔ درست» | شناسهٔ برنامه (`program.id` از پاسخ سرور) + `device_id:client_id` + `updated_at` به‌عنوان نسخهٔ نوشته | تست `posts the idempotent sync payload…` — `program_id: 512` |
| persist سمت سرور و بازخوانی از API | `onRecorded` → `readiness.reload()`؛ شمارش `feedback_rows` از سرور ۰ → ۱ | همان تست، خط `بازخوردهای ثبت‌شده در سرور: ۱` |
| timeout مبهم = شکست صریح | abort با `AbortController` + پیام «زمان پاسخ سرور گذشت — ثبت نشد»؛ `onRecorded` صدا زده **نمی‌شود** | تست timeout با مهلت واقعی ۱۵ms |
| دوبار ارسال → idempotent | دکمه در حال ارسال disabled + `inFlight` guard + کلید ثابت | همان تست timeout (دو درخواست، **همان** `client_id`/`updated_at`) |
| retry رکورد تکراری نسازد | سرور همان کلید را `unchanged` برمی‌گرداند؛ تست بک‌اند ۱ ردیف | `test_sync_set_feedback_is_idempotent_for_the_same_write` |

## ۳) اجراها

- `pytest tests/integration/test_mem05_set_feedback_idempotency.py tests/integration/test_mem04_member_program_access.py tests/integration/test_ownership.py` → **۱۴ pass** ([`backend-idempotency.txt`](backend-idempotency.txt)).
- `npx vitest run tests/setFeedback.test.tsx` → **۴ pass**؛ کل استودیو **۵۷ فایل pass / ۴ skip، ۴۰۳ تست pass / ۱۵ skip**.
- `tsc -b` / `eslint .` / `npm run build` → پاک.
- mutation (نه ادعا): حذف `abort` ⇒ تست timeout قرمز؛ ساخت کلید تازه در هر تلاش ⇒ قرمز ([`guard-mutation-test.txt`](guard-mutation-test.txt)).

## ۴) محدودیت‌ها (پذیرش نیست)

- هیچ دستگاه/مرورگر واقعی و هیچ صف آفلاین واقعی (SQLite محلی روی دستگاه) اجرا نشد؛ `device_id` فقط در `localStorage` همان مرورگر ساخته/نگه داشته می‌شود.
- `sets_done`/`notes` در فرم ست فعلی پر نمی‌شوند (قرارداد پشتیبانی می‌کند؛ UI این برش آن‌ها را ندارد).
- «نسخه» به معنای نسخهٔ برنامه (engine_version) در نوشتن بررسی نمی‌شود؛ اگر برنامه بین نمایش و ثبت تأیید مجدد شود، نوشتن به `program_id` همان برنامه می‌رود ولی نسخه در قرارداد قید نمی‌شود — این یک شکاف واقعی قرارداد است، نه چیزی که با کلاینت جعل شود.
- CI همین SHA هنوز اجرا نشده.
