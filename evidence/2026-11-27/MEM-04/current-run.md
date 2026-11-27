# MEM-04 / PWA-33 — برنامهٔ امروز عضو (برش ۲۰۲۶-۱۱-۲۷ UTC)

وضعیت کارت: `PARTIAL/NOT_ACCEPTED` — checkbox canonical باز. این برش فقط یک سطح واقعی را وصل می‌کند و هیچ KPI/کالری/ادعای پزشکی نمی‌سازد.

## ۱) پاسخ پرسش دسترسی (precondition)

`member = yes` — با فایل/خط در [`route-access.txt`](route-access.txt): `api/routes.json` نقش `member` را برای هر چهار مسیر مجاز می‌داند و `app/security/ownership.py:23-29` مالکیت سطری را اعمال می‌کند (۴۰۳ برای دادهٔ عضو دیگر). تست اجراشده: [`backend-access-tests.txt`](backend-access-tests.txt) → ۹ pass (۳ تازه + ۶ مالکیت).

## ۲) چه چیزی وصل شد

- `mp-app/studio/src/lib/api.ts` → `fetchMemberPrograms()` + تایپ‌های `MemberProgram`/`MemberProgramWeek`/`MemberProgramExercise` روی همان `ProgramOut` واقعی.
- `mp-app/studio/src/components/MemberTodayProgram.tsx` (تازه) در صفحهٔ `/member/today` رندر می‌شود (`App.tsx`).
- کدام برنامه: فقط `status === "approved"` و جدیدترین (بالاترین `id`) نمایش داده می‌شود. `draft`/`rejected` فقط به‌عنوان شمارش وضعیت سرور می‌آید.

## ۳) منبع هر عدد (بدون استثنا)

| عدد/مقدار | منبع | یادداشت |
|---|---|---|
| نسخهٔ برنامه | `engine_version` از `GET /api/v1/programs/member/{member_id}` | قرارداد عدد «نسخه» ندارد؛ فقط همین رشته |
| تاریخ | `approved_at` از همان پاسخ | برنامه تاریخ شروع/پایان ندارد؛ پس «امروز» حدس زده نمی‌شود |
| هدف و وضعیت | `goal`, `status` از همان پاسخ | متن سرور |
| هفته/روز/ست/تکرار/درصد بار/استراحت | همان پاسخ (`weeks[].exercises[]`) | هیچ محاسبه‌ای در کلاینت نیست |
| آمادگی | `GET …/readiness` → `score`, `band`, `recommendation`, `missing_signals` + `rule_version` | اگر `readiness === null` فقط `reason` سرور نشان داده می‌شود |
| غربالگری ایمنی | `safety_flags` | `{}` یعنی «انجام نشده»، نه «بی‌خطر» — همین متن روی صفحه است |

هر بلوک، برچسب `منبع: GET …` را همراه دارد؛ در تست هم assert شده است.

## ۴) حالت‌های تهی/خطا (fail-closed)

- بدون برنامهٔ تأییدشده → پیام تهی + (در صورت وجود) شمارش برنامه‌های در انتظار تأیید؛ هیچ عدد برنامه‌ای رندر نمی‌شود.
- `readiness === null` → «آمادگی: سنجیده نشد» + `reason` سرور؛ هیچ امتیازی نیست.
- خطای شبکه/۴۰۳ روی فهرست برنامه → پیام صریح و بدون هیچ داده‌ای.
- پاسخ غیرآرایه (نقض قرارداد) → پیام نقض قرارداد؛ «فهرست خالی» جعل نمی‌شود.

## ۵) اجراها (این sandbox)

- `npx vitest run tests/memberTodayProgram.test.tsx` → ۴ pass ([`studio-member-today-tests.txt`](studio-member-today-tests.txt))
- کل مجموعهٔ استودیو → ۵۶ فایل pass / ۴ skip؛ ۳۹۹ تست pass / ۱۵ skip ([`studio-full-tests.txt`](studio-full-tests.txt))
- `npx tsc -b` / `npx eslint .` / `npm run build` → پاک ([`studio-tsc.txt`](studio-tsc.txt)، [`studio-eslint.txt`](studio-eslint.txt)، [`studio-build.txt`](studio-build.txt))
- بک‌اند: `pytest tests/integration/test_mem04_member_program_access.py tests/integration/test_ownership.py` → ۹ pass ([`backend-access-tests.txt`](backend-access-tests.txt))
- `python3 scripts/interaction_map.py --check` → pass (۳۲ سطح/۱۶۳ مسیر/۰ رانش)

## ۶) محدودیت‌ها (نباید به‌عنوان پذیرش خوانده شوند)

- هیچ مرورگر/دستگاه واقعی و بازبینی انسانی اجرا نشده؛ تست‌های UI در jsdom با `fetch` stub‌شده‌اند.
- «برنامهٔ امروز» به معنی انتخاب روز واقعی نیست: قرارداد تاریخ شروع ندارد و UI هم آن را جعل نمی‌کند.
- `meals`/تغذیه در این برش دست نخورد؛ `MEM-08` جداست و `meals: []` به‌عنوان «برنامهٔ کامل» تفسیر نمی‌شود.
- CI همین SHA هنوز اجرا نشده؛ ادعای سبزی تا آن لحظه مجاز نیست.

## ۷) CI همین شاخه (متصل به SHA)

- روی tip `27ef138` (و پیش از آن `e0c9104`): `gh pr checks 31` → **هر ۱۲ check سبز**، شامل `secret-scan` و `Documentation links and handoff` (که گیت تازهٔ digest را اجرا می‌کند). خروجی خام: [`pr31-checks-27ef138.txt`](pr31-checks-27ef138.txt).
- ران‌های متصل: `46054318564`، `46054323525`، `46054323556` روی `27ef138` — همه `completed/success`؛ `46052340944`، `46052361131`، `46052361152` روی `e0c9104` — همه `success`.
- این green فقط یعنی گیت‌های CI روی همان SHA پاس‌اند؛ جای مرورگر/دستگاه واقعی، بازبینی انسانی و پذیرش محصول را نمی‌گیرد. `MEM-04/PWA-33` همچنان `PARTIAL/NOT_ACCEPTED` است.
