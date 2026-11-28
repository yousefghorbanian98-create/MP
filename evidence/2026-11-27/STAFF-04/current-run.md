STAFF-04 (PWA-43) — کلاس/حضور برای کارکنان (ROUND 3/9)
=======================================================

وضعیت: **PARTIAL** — صفحهٔ کارکنان با ظرفیت/شمارش رزرو و جریان واقعی حضور
ساخته شد و با ۴ تست + ۱ mutation قفل شد. دو بخش صریحاً بسته (نه ادعا) شدند:
roster نام‌دار و «تأیید حضور توسط مربی».

## چه ساخته شد

- صفحهٔ تازهٔ `classes` در Studio (`src/pages/Classes.tsx`) با:
  - **ظرفیت و رزرو از سرور:** `GET /api/v1/classes` ⇒ `capacity` / `confirmed` /
    `waitlisted` / `seats_left` (`modules/classes/service.py:198-211`). هیچ
    عددی در مرورگر جمع/تفریق نمی‌شود؛ «ظرفیت پر» از `seats_left=0` سرور می‌آید.
  - **جریان واقعی حضور:** `GET /api/v1/admin/checkins` ⇒ وضعیت هر ردیف از
    `result` سرور (`ok` ⇒ «در باشگاه (باز)»/«ورود ثبت‌شده در سرور»، غیر آن ⇒
    «رد شد» + `denial_reason` سرور). `is_open` هم از سرور می‌آید.
  - **بدون دکمهٔ «حاضر شد»:** صفحه هیچ درخواست نوشتنی نمی‌فرستد (تست ثابت
    می‌کند همهٔ درخواست‌ها GET‌اند و دکمه‌ای با نام «حاضر» وجود ندارد).
- نقشهٔ صفحه: `PAGE_IDS += classes` · `App.tsx pages` · `roleNav.PAGE_RULES.classes`
  (staff-only؛ عضو در اپ عضو مسیر `/member/classes` دارد) · آیتم Sidebar.
- تست اختصاصی: `mp-app/studio/tests/staffClasses.test.tsx` (۴ تست) و
  `staffRouteMapBaseline.withoutDedicatedTest: ["members","analytics"] → ["analytics"]`
  (ratchet فقط کوچک می‌شود).

## GAP و تصمیم‌های بسته‌شده

- **`GAP: roster نام‌دار وجود ندارد.`** هیچ مسیری رزروهای یک کلاس را با نام
  عضو برنمی‌گرداند: در `api/routes.json` هیچ `GET /classes/{id}/bookings` نیست
  و `modules/classes/router.py` فقط `GET /classes`، `POST /classes`،
  `POST /classes/book`، `POST /classes/cancel` دارد. صفحه roster جعلی نمی‌سازد
  و نبودش را در UI می‌نویسد.
- **`GAP: تأیید حضور توسط مربی endpoint ندارد.`** `POST /face/checkin` فقط با
  هویت خودِ عضو معنا دارد (چهره/QR همان عضو) و مسیر staff-محور برای «حاضر کردم
  این عضو را» وجود ندارد. بنابراین UI دکمه نمی‌سازد (قاعدهٔ MEM-12: دکمه ادعای
  حضور نیست) و فقط جریان ثبت‌شده را نشان می‌دهد.
- **`DEVICE_REQUIRED` (خارج از این فضا):** اسکن واقعی QR/چهره و بررسی
  screen-reader دستگا‌هی؛ در این دور صرفاً جریان داده سنجیده شد.

## جهش (خروجی خام: `mutation-proof.txt`)

- **M9** — `const accepted = true` (وضعیت مستقل از `result` سرور):
  **۱ failed / ۳ passed** — تست «سرور result=denied ⇒ رد شد» قرمز شد.
- **M8** (بک‌اند، همین فایل): افزودن allow برای member روی یک مسیر **POST**
  کارکنان ⇒ گیت مالکیت **۲ failed / ۵۹ passed**؛ یعنی sweep جدید POST هم
  واقعاً کار می‌کند.

## باز (ادعا نمی‌شود)

- ساخت/ویرایش کلاس از UI (سرور `POST /classes` دارد، صفحه فعلاً فقط نمایش است).
- رزرو/لغو رزرو توسط پذیرش از این صفحه (endpoint هست، UI نه) — کار دور بعد.
