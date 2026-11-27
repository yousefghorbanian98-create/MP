# INV-03 — بازبینی source برای crosswalk v2 کارکنان

> **وضعیت:** `PARTIAL / NOT_ACCEPTED`. این review فقط یافته‌های خروجی static را با source cross-check می‌کند؛ role navigation معادل مجوز server، تست end-to-end یا پذیرش صفحه نیست.

## منشأ و خروجی

- Generator از `yousefghorbanian98-create/Chat2DB`, ref=`arena/c1fb460b-chat2db`, مسیر `docs/mp-inv-redo/crosswalk_v2.py` دریافت شد؛ commit منبع clone شده `155a18b8ff01578d957d9315f88afbf3a8950ef5` و SHA-256 فایل اجراشده `4457ee38fb660adf9c4d87cd0c10e5374249e33eb1f441d257f5c061964f9311` است. API Contents با 404 پاسخ داد؛ نسخهٔ همان ref با clone shallow از GitHub دریافت و قبل از اجرا بازبینی شد.
- Target اجرا `HEAD=f06f2a95305082e01e33b157396f0dfc0128613d`, branch=`arena/5e0f64cf-mp` بود. Worktree tracked-dirty و دارای ۱۴۵ مسیر untracked بود؛ source SHAها در [JSON خام](staff-page-crosswalk.json) ثبت شده‌اند. هیچ tracked file زیر `mp-app/` تغییر نکرده بود.
- برای حفظ artifactهای v1، شش فایل آن‌ها byte-for-byte در [`../INV-03-v1/`](../INV-03-v1/) نگه داشته شدند.
- شمارش v2: `PARTIAL_REVIEW=12`, `GAP=0`, `DYNAMIC_UNCOVERED=0`; با مرجع اعلام‌شده برای staff روی `main@3527810` برابر است. `GAP=0` به معنی پذیرش یا پوشش همهٔ رفتارها نیست.

## Cross-check با source

- **`${base}` در analytics:** v2 در ردیف `analytics` دو call-site از [adminApi.ts](../../../mp-app/studio/src/lib/adminApi.ts#L43-L49) و [adminApi.ts](../../../mp-app/studio/src/lib/adminApi.ts#L128-L132) ثبت می‌کند (`2/4` APIها؛ consumer=`adminApi.ts`). این false-negative مربوط به call-site خام v1 را برطرف می‌کند. این بررسی تنها وجود call-site است؛ نقش مؤثر، grant، دادهٔ برگشتی و اجرای تست را ثابت نمی‌کند.
- **Alias `ALL_STAFF`:** v2 aliasهای نقش را باز کرده است؛ `roleNav.ts` آن را با شش نقش، از جمله `member`، تعریف می‌کند ([تعریف](../../../mp-app/studio/src/lib/roleNav.ts#L26-L33)، [مصرف dashboard/chat/checkin](../../../mp-app/studio/src/lib/roleNav.ts#L39-L46)). این mapping فقط navigation/UI است. `App.tsx` guard `isStaffRole` دارد و `/member` همچنان placeholder است؛ alias به‌تنهایی route reachability یا server enforcement را ثابت نمی‌کند.
- **مسیرهای پویا:** خروجی `dynamic_sites=0` است و هیچ `DYNAMIC_UNCOVERED` نداریم. مسیرهای template در [api.ts](../../../mp-app/studio/src/lib/api.ts#L673-L673)، [api.ts](../../../mp-app/studio/src/lib/api.ts#L939-L939)، [api.ts](../../../mp-app/studio/src/lib/api.ts#L1046-L1046) و [api.ts](../../../mp-app/studio/src/lib/api.ts#L1259-L1259) وجود دارند. regexهای capture در [crosswalk_v2.py](../../../scripts/crosswalk_v2.py#L52-L57) قبل از `$` متوقف می‌شوند؛ بنابراین برچسب dynamic از این sourceها تولید نشده و بخش متغیر ممکن است از شمارش مصرف جا بماند. فایل raw و آمار اسکریپت دست‌نخورده‌اند.
- تفکیک staff/member دستی می‌ماند: `adminApi.ts`/`api.ts` و بعضی componentها مشترک‌اند؛ call-site کارکنان را نمی‌توان فقط از روی pathname به سطح عضو نسبت داد.

## قواعد تفسیر و نتیجه

- عبارت «v1 سه false-negative داشت؛ v2 آن‌ها را رفع کرد.» برای Analytics/`${base}` و alias نقش در این اجرا تأیید شد؛ مسیرهای پویا اما به‌صورت `DYNAMIC_UNCOVERED` علامت نخورده‌اند. پس ادعای رفع هر سه مورد به‌طور کامل تأیید نمی‌شود. ابزار طبق دستور دستی patch نشد.
- **v2 همچنان مجوز و مالکیت را اثبات نمی‌کند؛ سقف `PARTIAL_REVIEW` است.** `tests` فقط اشارهٔ متنی است؛ هیچ test به‌خاطر این crosswalk اجرا نشده بود.
- **تفکیک call-site عضو از پنل کارکنان دستی است و باقی می‌ماند.**
- مسیرهای پویا باید `DYNAMIC_UNCOVERED` باشند، نه GAP کاذب یا PASS؛ این run چنین برچسبی صادر نکرد (`dynamic_sites=0`). این محدودیت ثبت شده و پوشش تلقی نمی‌شود.

`INV-03=PARTIAL/NOT_ACCEPTED`; checkbox باز، `PWA-01=PROPOSED/NOT_RUN`, و release `NO-GO` باقی است.

## الحاقیهٔ بازتولید — ۲۰۲۶-۱۱-۲۷ UTC (HEAD `9ea9a24a622104408df2de632e3977aa3dcad3ba`)

- artifact روی **درخت تمیز** بازتولید شد (`tracked_dirty=False`، `untracked=0`)؛ digestها با پیشوند `sha256:`.
- دو منبع کهنه (`studio/src/lib/api.ts`، `studio/src/lib/navigation.ts`) به‌روز شدند؛ علت، تغییر همین فایل‌ها در commit‌های همین شاخه بود، نه تغییر artifact.
- شمارش بدون تغییر: `PARTIAL_REVIEW=12`. ستون اشارهٔ تست حداکثر ۴ نام الفبایی است؛ نبودِ یک نام در ستون به معنی نبود فایل نیست.
- محدودیت‌ها بدون تغییر: مجوز/مالکیت و رفتار خطا/ماندگاری اثبات نشده، `dynamic_sites=0`، `INV-03=PARTIAL/NOT_ACCEPTED`، checkbox باز، release `NO-GO`.

شاهد عددی: [`digest-gate-after.txt`](../MEM-03/digest-gate-after.txt).
