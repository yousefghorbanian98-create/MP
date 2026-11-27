# INV-02 — بازبینی source برای crosswalk v2 عضو

> **وضعیت:** `PARTIAL / NOT_ACCEPTED`. این review تفسیر source از خروجی خام v2 است؛ هیچ ردیفی را دستی اصلاح یا به `CURRENT` ارتقا نمی‌دهد و پذیرش PWA را ثابت نمی‌کند.

## منشأ و خروجی

- Generator از `yousefghorbanian98-create/Chat2DB`, ref=`arena/c1fb460b-chat2db`, مسیر `docs/mp-inv-redo/crosswalk_v2.py` دریافت شد؛ commit منبع clone شده `155a18b8ff01578d957d9315f88afbf3a8950ef5` و SHA-256 فایل اجراشده `4457ee38fb660adf9c4d87cd0c10e5374249e33eb1f441d257f5c061964f9311` است. API Contents با 404 پاسخ داد؛ نسخهٔ همان ref با clone shallow از GitHub دریافت و قبل از اجرا بازبینی شد.
- Target هر دو اجرا `HEAD=f06f2a95305082e01e33b157396f0dfc0128613d`, branch=`arena/5e0f64cf-mp` بود. این worktree tracked-dirty بود و ۱۴۵ مسیر untracked داشت؛ SHAهای source ورودی در [JSON خام](member-capability-crosswalk.json) ثبت شده‌اند. هیچ tracked file زیر `mp-app/` تغییر نکرده بود.
- برای حفظ byte-for-byte خروجی v1، شش artifact آن به [`../INV-02-v1/`](../INV-02-v1/) کپی شدند؛ hash فایل‌های crosswalk با hashهای ثبت‌شدهٔ v1 برابر است. خروجی و review v2 مستقل از archive هستند.
- شمارش v2: `PARTIAL_REVIEW=14`, `GAP=3`, `DYNAMIC_UNCOVERED=0`; با اعداد مرجع اعلام‌شده برای member روی `main@3527810` برابر است. این برابری شمارش‌ها، صحت همهٔ ردیف‌ها یا پوشش کامل را ثابت نمی‌کند.

## Cross-check با source

- **`${base}` در `adminApi.ts`:** v2 این الگو را می‌گیرد؛ در [INV-03 v2](../INV-03/staff-page-crosswalk.md) ردیف `analytics` به `PARTIAL_REVIEW` رسیده و `adminApi.ts` با دو مسیر analytics ثبت شده است. این یافته، false-negative مربوط به call-site در v1 را برای آن دو مسیر رفع می‌کند؛ نه مجوز سرور را.
- **Alias نقش:** v2 مقدار `ALL_STAFF` را از [roleNav.ts](../../../mp-app/studio/src/lib/roleNav.ts#L26-L46) باز کرده و در ۱۲ rule خروجی نقش غیرخالی دارد. این‌ها ruleهای navigation/UI هستند، نه تصمیم مؤثر API، RBAC، grant یا مالکیت.
- **مسیرهای پویا:** خروجی این اجرا `dynamic_sites=0` دارد و هیچ ردیفی `DYNAMIC_UNCOVERED` نشده است. در source، [api.ts](../../../mp-app/studio/src/lib/api.ts#L673-L673) مسیر پویای `/programs/member/${memberId}/volume`، [api.ts](../../../mp-app/studio/src/lib/api.ts#L939-L939) مسیر `/nutrition/member/${memberId}/adaptive`، [api.ts](../../../mp-app/studio/src/lib/api.ts#L1046-L1046) مسیر readiness و [api.ts](../../../mp-app/studio/src/lib/api.ts#L1259-L1259) مسیر reminders دارند. الگوهای capture در [crosswalk_v2.py](../../../scripts/crosswalk_v2.py#L52-L57) `$` را از گروه مسیر حذف می‌کنند؛ پس بخش متغیر قطع می‌شود و detector موجود dynamic بودن را ثبت نمی‌کند. در نتیجه، `today` همچنان `GAP` و `notifications` همچنان `GAP` است و این شمارش‌ها نباید به‌عنوان نبود مصرف واقعی تعبیر شوند.
- مسیر نمونهٔ prompt، `${API_BASE}/members/${id}/checkins`، در source فعلی پیدا نشد. مسیر واقعی عضو در Flutter، [member_checkin_history.dart](../../../mp-app/client/lib/features/checkin/member_checkin_history.dart#L14-L20)، `/members/me/checkins` با query interpolation در Dart است؛ اسکنر v2 فقط `mp-app/studio/src/*.ts*` را می‌خواند، پس این مسیر را بررسی نمی‌کند. ردیف `checkin` در crosswalk v2 یک call-site کارکنان برای `/admin/checkins` دارد؛ وجود اشارهٔ تست `test_m80_member_checkin_history.py` در ستون تست، مصرف PWA عضو را ثابت نمی‌کند.

## قواعد تفسیر و نتیجه

- عبارت «v1 سه false-negative داشت؛ v2 آن‌ها را رفع کرد.» فقط برای `${base}`/Analytics و alias `ALL_STAFF` در این اجرا تأیید شده است؛ برای مسیرهای پویا تأیید نشد. طبق دستور، generator دستی patch نشد.
- **v2 همچنان مجوز و مالکیت را اثبات نمی‌کند؛ سقف `PARTIAL_REVIEW` است.** اشارهٔ تستی صرفاً نام فایل/مسیر است، نه اجرای test.
- **تفکیک call-site عضو از پنل کارکنان دستی است و باقی می‌ماند.** `api.ts` و `adminApi.ts` مشترک‌اند و مصرف یک staff page را نمی‌توان به صفحهٔ عضو تعمیم داد.
- قرارداد مورد انتظار `DYNAMIC_UNCOVERED` به‌جای `GAP` یا `PASS` در خروجی این نسخه تحقق نیافت: در این run هیچ dynamic call-site علامت نخورد. این شکاف به‌عنوان blocker روش ثبت می‌شود؛ نه با ویرایش خام پنهان می‌شود و نه به PASS تبدیل.

`INV-02=PARTIAL/NOT_ACCEPTED`; checkbox باز، `PWA-01=PROPOSED/NOT_RUN`, و release `NO-GO` باقی است.
