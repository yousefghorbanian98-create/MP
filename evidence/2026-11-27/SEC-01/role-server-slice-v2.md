# SEC-01 — ماتریس تصمیم RBAC و برش منفی API

> **وضعیت:** `PARTIAL / NOT_ACCEPTED`. ماتریس زیر تمام operationهای manifest را با هر شش نقش در policy engine سنجیده و تست‌های منفی واقعی API برای پنج حوزهٔ خواسته‌شده اجرا کرده است؛ به‌تنهایی دسترسی مؤثر هر route، مالکیت همهٔ منابع، فایل/export، anonymous، grant یا acceptance امنیتی را ثابت نمی‌کند.

## اجرای دقیق و provenance

- `claimed_sha=tested_sha=f06f2a95305082e01e33b157396f0dfc0128613d`; branch هنگام اجرا `arena/5e0f64cf-mp`. همان SHA در JSONهای crosswalk، ماتریس و خلاصهٔ pytest درج شده است.
- pytest کامل در `mp-app/backend` با Python 3.11.2 و pytest 9.2.0 اجرا شد: `/tmp/mp-backend-venv/bin/python -m pytest -q`; شروع `2026-11-27T12:00:11Z`، پایان `2026-11-27T12:03:20Z`; exit `0`; `1336 passed, 2 skipped, 2 warnings` در `185.72s`. `claimed_sha` و `tested_sha` در [`test-run-summary.txt`](test-run-summary.txt) برابرند؛ خروجی کامل در [`pytest-full-output.log`](pytest-full-output.log).
- دو warning: `StarletteDeprecationWarning` برای استفادهٔ `httpx` با `starlette.testclient` و `InsecureKeyLengthWarning` برای HMAC key تستی ۹ بایتی. هیچ‌یک به‌عنوان permission/security acceptance تعبیر نمی‌شوند.
- tracked product-source diff زیر `mp-app/` در شروع این دور صفر بود؛ ماتریس generator، crosswalk و testها source محصول را تغییر ندادند. fixtureها و SQLite هر تست موقت/ساختگی‌اند؛ هیچ production data یا credential استفاده نشد.

## ماتریس کامل تصمیم policy

- [`rbac-matrix.txt`](rbac-matrix.txt) از هر **۱۶۳ operation** در `mp-app/backend/api/routes.json`، شامل **۱۴۱ path**، یک سطر برای هر یک از شش نقش تولید می‌کند: **۹۷۸ سطر method × path × role × decision**. قالب مسیرها همان placeholderهای `{...}` manifest را نگه می‌دارد.
- تابع تصمیم واقعی `security.rbac.enforce(role, path, method)` از `mp-app/backend/security/rbac.py` فراخوانی شد؛ generator قابل‌بازتولید در [`generate-rbac-matrix.py`](generate-rbac-matrix.py) است. hashهای `routes.json` و `rbac.py` در ابتدای ماتریس ثبت شده‌اند.
- جمع خروجی policy: `member=88 ALLOW / 75 DENY`, `coach=85/78`, `reception=72/91`, `manager=158/5`, `admin=159/4`, `super_admin=163/0`.
- چون کل ۱۶۳ operation استفاده شد، operationهای finance/payment، assessment/health، chat/checkin، receipt/file و export موجود در manifest بیرون نماندند. ناشناس جزء ۶ نقش درخواستی نیست و در این جدول ارزیابی نشده است.
- **حد صریح:** این جدول فقط `enforce()` را روی method/path manifest فراخوانی می‌کند. فهرست `routes.json.roles/always_roles`, dependency/guardهای FastAPI، grantهای `finance.*` و انقضا/لغو آن‌ها، anonymous policy، owner scope/ABAC، تصمیم‌های service، نتیجهٔ HTTP و تطبیق route template با router را ارزیابی نمی‌کند. بنابراین «ALLOW» در جدول معادل پاسخ `200` یا اثبات مجوز مؤثر نیست؛ آن را با ماتریس کامل HTTP اشتباه نگیرید.

## تست منفی واقعی API: عضو A در برابر دادهٔ عضو B

آزمون‌های انتخابی با FastAPI `TestClient`، JWT fixture، پایگاه SQLite موقت و دادهٔ synthetic اجرا شدند؛ این‌ها unit-only نیستند. خروجی command در [`negative-api-tests.log`](negative-api-tests.log) است: **۳ test function passed، ۰ failed** (یک هشدار deprecation). هر پنج حوزهٔ درخواستی پوشش دارند:

| حوزه | endpoint/رفتار assert‌شده | نتیجه |
|---|---|---|
| members | عضو A برای `GET /api/v1/members/{B}` و memberships عضو B | `403` |
| assessments | عضو A برای `GET /api/v1/assessments/member/{B}` | `403` |
| payments | عضو A برای invoice و wallet عضو B | هر دو `403` |
| chat | عضو A برای GET پیام‌های گفتگوی متعلق به B و POST پیام در همان گفتگو | هر دو `403` |
| checkin | پاسخ self-history عضو A شامل `checkin_id` عضو B نیست؛ تلاش برای انتخاب `member_id=B`، خواندن member B و attendance feed محدود به B رد می‌شوند | عدم افشای B در collection؛ درخواست‌های cross-scope `403` |

فرمان انتخابی شامل `test_member_cannot_read_other_members_data`, `test_member_history_is_self_scoped_paginated_and_keeps_denials` و `test_member_cannot_read_someone_elses_conversation` است. هیچ پاسخ حاوی دادهٔ B برای عضو A دریافت نشد؛ اگر یکی از assertionها `200` یا دادهٔ B می‌دید، test fail می‌شد. نتیجه فقط به endpointها و fixtureهای همین testها تعلق دارد، نه همهٔ routeهای ماتریس.

## سابقه و تفسیر وضعیت

- شاهد slice قبلی در [`../../2026-11-23/SEC-01/`](../../2026-11-23/SEC-01/) به‌درستی در `test-run-summary.txt` تاریخ اجرای `2026-11-23 UTC` و target SHA=`352781043ad2ba202d8b3b459df1ce7e3d914ef7` را اعلام می‌کند؛ این evidence تاریخی است و با اجرای جدید روی SHA `f06f2a9...` ادغام یا جایگزین نشده است.
- این run یک ماتریس **تصمیم static policy** کامل و یک برش **HTTP negative** انتخابی دارد؛ grantهای حساس، positive role matrix روی همهٔ routeها، anonymous، همهٔ file/export/resource/job، branch/club scope و independent review همچنان بازند. در هیچ‌کدام `CURRENT` یا release readiness ادعا نمی‌شود.
- هیچ role, grant, API, route, DB, Flutter یا native workflow تغییر نکرد؛ checkbox `SEC-01` باز است و status آن حداکثر `PARTIAL`. `INV-02/03=PARTIAL/NOT_ACCEPTED`, `PWA-01=PROPOSED/NOT_RUN`, release=`NO-GO`.

گام بعدی این بخش: ماتریس HTTP واقعی برای route/action/resource و grant/owner edge cases را فقط با fixtureهای مصوب و denial assertions گسترش دهید؛ برای نقش/مالکیت حساس، نبود تصمیم مرجع را `BLOCKED/UNKNOWN` نگه دارید.
