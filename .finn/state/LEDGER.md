# FINN Ledger — درس‌ها، باگ‌ها و قوانین «هرگز تکرار نشود»
> هر ایجنت در آغاز «هر» میکرو-چرخه این فایل را کامل می‌خواند. هیچ خطی حذف نمی‌شود؛ فقط اضافه می‌شود.

| # | تاریخ | چرخه | نوع (باگ/درس/تصمیم) | شرح | قانون جدید (هرگز...) | تست رگریشن |
|---|-------|------|----------------------|------|----------------------|-------------|
| 1 | 2026-11-14 | Phase-0 | درس | دانلود از raw.githubusercontent.com در محیط ممکن نیست؛ gh api با Accept raw جایگزین موفق بود | هرگز برای دریافت فایل از raw.githubusercontent.com استفاده نکن — از gh api استفاده کن | — |
| 2 | 2026-11-14 | M00 | تصمیم | Flutter/Docker/مرورگر در محیط نیستند (D-002..004) | هرگز گیت اجرایی قابل‌اجرا در محیط را به «بعداً» موکول نکن — مسیر جایگزین + CI تعریف کن | — |
| 3 | 2026-11-14 | M03 | باگ | server_default="CURRENT_TIMESTAMP" به‌صورت رشتهٔ خام ذخیره می‌شود (ValueError isoformat) | هرگز server_default رشته‌ای برای DateTime استفاده نکن — فقط func.now() یا sa.text() | R-002 (OTP hash) + تست‌های مدل |
| 9 | 2026-11-14 | M33-c2 | درس | اجرای alembic با DATABASE_URL بی‌اثر است (prefix تنظیمات MP_ است) ← برخورد با mp.db موجود (init_db بدون نسخهٔ alembic) | هرگز مهاجرت را بدون MP_DATABASE_URL روی دیتابیس تازه اجرا/آزمایی نکن | اجرای upgrade head روی DB تازه در گزارش M33-c2 |
| 10 | 2026-11-14 | M36-c2 | باگ فرایندی | `pytest | tail -1` کد خروجی را می‌پوشاند — ۳ تست شکسته commit/push شد | هرگز زنجیرهٔ گیت را بدون `set -o pipefail` با pipe نبند — exit code واقعی لازم است | اصلاحیهٔ 8696566 (semantics lower_better هم در همین حین پیدا شد) |
| 4 | 2026-11-14 | M08 | باگ | Annotated["User", ...] با TYPE_CHECKING در FastAPI resolve نمی‌شود (query param شد) + keyMatch2 فقط «/*» وایلدکارت دارد | هرگز forward-ref رشته‌ای در CurrentUser استفاده نکن — import واقعی؛ هرگز «foo*» به‌جای «foo/*» در policy casbin ننویس | R-004 + تست‌های RBAC |
| 23 | 2026-11-16 | M67 | باگ امنیت نشست | logout فقط refresh را revoke می‌کرد ولی access JWT همان نشست تا انقضا 200 می‌داد؛ pre-fix API test این را بازتولید کرد | در نشست‌های جدید، access token را با `sid` متصل به hash refresh row نگه‌دار؛ auth dependency ردیف active/unexpired را بررسی کند تا rotation/logout access همان نشست را باطل کند؛ legacy بدون `sid` جداگانه گزارش شود | `mp-app/backend/tests/integration/test_m67_studio_auth.py` + `mp-app/studio/tests/session.test.ts` + گزارش M67 |
| 24 | 2026-11-16 | M67 | باگ concurrency نشست | refresh دیررس پس از logout access/refresh را دوباره در localStorage می‌نوشت؛ پاسخ دیررس logout یا 401 دیررس retry نشست تازه را پاک می‌کرد؛ refresh شکست‌خوردهٔ تب قدیمی نیز tokenهای چرخیدهٔ تب دیگر را پاک می‌کرد؛ هر چهار با تست pre-fix قرمز شدند | هر تغییر نشست generation جدید بسازد؛ پاسخ async نشست قبلی پس از logout/login/rotation حق ذخیره یا پاک‌سازی token جاری را ندارد؛ logout را فقط پیش از await محلی پاک کن و پس از پاسخ شبکه storage را پاک نکن | `mp-app/studio/tests/session.test.ts` (R-017) |
| 25 | 2026-11-16 | M70 | درس گیت نقش | UI می‌تواند کنترل super_admin-only را برای admin پنهان کند، اما نقش payload/token در مرورگر مرز دسترسی نیست | role payload را فقط برای UX/menu بخوان؛ route/API حساس باید backend 403 را نگه دارد؛ تست admin منفی و super_admin مثبت را برای هر کنترل حساس اضافه کن؛ access token را از helper مشترک بخوان | `mp-app/studio/tests/settingsRole.test.tsx`, `roleNav.test.tsx`, backend `test_m46_security_matrix.py`; گزارش M70 |
| 26 | 2026-11-16 | M72 | درس/داده | API اشتراک `days_remaining` ندارد؛ تبدیل پاسخ غیرلیستی به `[]` وضعیت خطای قرارداد را به «بدون اشتراک» تبدیل می‌کند؛ timezone و مرز `expires_at` باید صریح باشند | اعداد را از تاریخ واقعی قرارداد محاسبه کن؛ پاسخ نامعتبر را خالی جا نزن؛ مرز `expires_at` و UTC را با تست ثابت کن؛ static parse را جای اجرای Flutter گزارش نکن | `mp-app/client/test/membership_test.dart` + `home_banner_test.dart` (تست‌ها نوشته شدند، runtime هنوز UNKNOWN) |
| 27 | 2026-11-16 | M73 | باگ دسترسی/داده | `GET /nutrition/*` مجاز بود ولی member برای `POST /nutrition/food-logs` 403 می‌گرفت؛ integration آن را بازتولید کرد. چربی دیتاست upstream اندازه‌گیری مستقیم نیست | برای نوشتن member مجوز را فقط روی endpoint دقیق باز کن و `ensure_member_scope` را نگه دار؛ مقدار منبع را با estimate/measurement اشتباه نکن؛ تست self + cross-member و no-plan-write بنویس | `mp-app/backend/tests/integration/test_m49_food_logging.py`; 25 backend/data tests passed; Client widget not run |
| 28 | 2026-11-16 | M74 | باگ مالکیت | `classes/cancel` و `classes/book` member_id بدنه را بدون تطبیق با توکن می‌پذیرفتند؛ دو تست پیش از fix هر دو 200 گرفتند | هر endpoint member-scoped باید `ensure_member_scope` را در service بررسی کند؛ UI برای action نیاز به status owner-only در GET دارد؛ duplicate/status/capacity را پس از عمل دوباره از API بگیر | `mp-app/backend/tests/integration/test_m74_class_cancel.py`; 46 backend/RBAC passed; Client widget unrun |
| 29 | 2026-11-16 | M75 | باگ مالکیت | اعلان‌ها RBAC مسیر داشتند اما service، صاحب member/notification را نمی‌سنجید؛ cross-member list و mark-read هر دو پیش از fix 200 بودند | روی read/write رکورد member-scoped، مالکیت را با user جاری در service enforce کن؛ unread فقط از `read_at` واقعی بیاید؛ API error را به inbox خالی تبدیل نکن | `mp-app/backend/tests/integration/test_m75_notifications.py`; 65 notification/reminder/chat/RBAC passed; Client widget unrun |
| 30 | 2026-11-16 | M76 | درس/داده | readiness endpoint فقط از feedback واقعی score می‌سازد؛ نبود برنامه/بازخورد با `readiness=null` پاسخ می‌دهد؛ score قواعد تمرینی تشخیص پزشکی نیست | از API و member نشست استفاده کن؛ `null` را صفر نساز؛ دلیل، missing signals و شمار داده را حفظ کن؛ برای توصیهٔ غیرکلینیکی disclaimer بگذار و پس از feedback تازه‌خوانی کن | `mp-app/backend/tests/unit/test_readiness.py`, `test_m48_feedback_applied.py`; 22 passed, 7 deselected; Client widget unrun |
| 31 | 2026-11-16 | M77 | درس/داده | گزارش volume بین «برنامه» و «بازخورد hard sets» فرق می‌گذارد؛ `effective_sets` بدون source می‌توانست اجرای واقعی را وانمود کند | source_of_number/data_state را کنار مقدار نشان بده؛ MV/MEV/MAV/MRV را با سطح انتخابی و source API بگیر؛ API error را volume صفر نکن؛ بدون نیاز dependency نمودار وارد نکن | `mp-app/backend/tests/integration/test_m48_volume_api.py`, `test_load_attribution.py`; 13 passed; Client widget unrun |
| 32 | 2026-11-16 | M78 | باگ مجوز/داده | member self weigh-in با endpoint موجود 403 می‌گرفت؛ TDEE به وزن و روزهای غذا نیاز دارد؛ API با دادهٔ ناکافی null/none می‌دهد | فقط `POST /nutrition/weight-logs` را دقیق مجاز کن و service owner guard را حفظ کن؛ هر عدد TDEE/delta از API؛ null را صفر/حدس نکن؛ وزن امروز idempotent و واحد kg/range را روشن کن | `mp-app/backend/tests/integration/test_m78_adaptive_nutrition_client.py`, `test_m49_adaptive_nutrition.py`, RBAC matrix; 74 passed; Client widget unrun |
| 33 | 2026-11-16 | M79 | درس تطبیق | M62/D4 همان `/bodycomp` و JP7 API واقعی را مصرف می‌کرد، اما M5 عضو هنوز line chart نداشت؛ Assessment14 نیز feature جداست | reuse route/provider/endpoint؛ فقط نمودار عضو را از `measurements[].sum_mm`/تاریخ API بساز؛ زیر دو اندازه‌گیری نمودار نده؛ Assessment14 را با JP7 ادغام نکن؛ runtime را تا Flutter gate unknown نگه‌دار | `finn/reports/m79-jp7-crosswalk.md`; chart assertions در `bodycomp_real_data_test.dart`, `assessment14_page_test.dart` موجود ولی runtime اجرا‌نشده |
| 34 | 2026-11-16 | M80 | lesson امنیت/API | `/admin/checkins` staff feed چندعضوی است و برای member history مجاز نیست؛ self path نباید شناسهٔ عضو از caller بگیرد | از `GET /members/me/checkins` با member ID استخراج‌شده از نشست، role gate، where member_id و pagination استفاده کن؛ deniedها را از تاریخچهٔ خود پنهان نکن | `finn/reports/m80-member-checkin-history.md`; 52 backend/RBAC passed; Client widget test static-checked, Flutter runtime unrun |
| 35 | 2026-11-16 | M80 retest / toolchain gate | security regression | جعل `member_id` در query مسیر self-history با 403 مسدود است؛ artifact مسیر API پس از اضافه‌شدن endpoint باید regenerate شود؛ نصب Flutter در sandbox به‌خاطر egress محدود و نبود SDKهای لازم انجام نشد | هر تغییر route را با `scripts/export_routes.py` بازتاب بده؛ هیچ Flutter gate را سبز اعلام نکن مگر runtime روی همین کد اجرا شده باشد؛ گزارش محدودیت نصب را با منبع/checksum و آزمون‌های انجام‌شده ثبت کن | `test_m80_member_checkin_history.py`; backend 811 passed/1 skipped; Ruff/py_compile green; Dart static 55/0; Flutter analyze/test/APK unrun; `finn/reports/flutter-sdk-provisioning.md` |
| 36 | 2026-11-16 | Flutter source retry | درس/محیط | به درخواست کاربر upstream، Flutter China, Runflare, Myket, TarazERP و Pub mirrors همگی جداگانه آزمایش شدند؛ shell TLS/EOF شکست خورد؛ PackageDownloader asset روی release-assets قطع شد؛ npm/PyPI SDK نام‌ها موجود نیستند | هر منبع را برای آرشیو و Pub endpoint جداگانه آزمایش کن و checksum فقط پس از دریافت bytes بزن؛ metadata/fetch-page یا کد static را با نصب/runtime اشتباه نگیر؛ در صورت نبود SDK/runtime، M78/M79/M80 را صریحاً اجرا‌نشده نگه‌دار | `finn/reports/flutter-sdk-provisioning.md`; no Flutter archive/package cache installed; M78/M79/M80 runtime still unrun |
| 37 | 2026-11-16 | M82 | باگ هم‌زمانی یکتایی | تست preflight duplicate به‌تنهایی پنجرهٔ race میان SELECT و UPDATE را نمی‌گرفت؛ SQLite/PostgreSQL ممکن است unique violation را هنگام اجرای UPDATE بدهند نه commit | رسیدگی IntegrityError را روی خود UPDATE و commit بگذار؛ بعد rollback و فقط اگر شماره واقعاً به حساب دیگر وصل شده پاسخ 409 بده؛ fake-SMS race را میان preflight و UPDATE inject کن | `mp-app/backend/tests/integration/test_m82_phone_change.py::test_phone_change_maps_unique_constraint_race_to_conflict`; backend full 810 passed/2 skipped |
| 38 | 2026-11-16 | M83 | درس مالی/مالکیت/پایدارسازی صفحه | `GET /payments` فهرست `Payment`هاست، نه کامل‌ترین دفتر credit/debit؛ balance query جدا هم می‌توانست هم‌زمان با ledger page snapshot متفاوت ببیند؛ order بی‌صریح قابل اتکا نیست | مانده را از credit−debit روی `wallet_transactions` بساز؛ balance و ردیف‌های صفحه را در یک SQL statement بخوان، `id DESC` را همراه cursor `< before_id` صریح کن، scope را در service enforce کن و Client قبل از نمایش member/row identity را با نشست تطبیق دهد | `mp-app/backend/tests/integration/test_m83_wallet_ledger.py`; `mp-app/client/test/wallet_history_test.dart`; backend full 812 passed/2 skipped; Flutter widget runtime unrun, M83 UNKNOWN |

## ۵. (M14) DB فایل بین اجراها زنده می‌ماند
فیکسچر client باید در هر تست `settings.database_url` را به فایل تازه ببرد + `reset_engine()` + `init_db()`؛ وگرنه UNIQUE collision با دادهٔ اجرای قبل. شمارندهٔ شناسه هم باید time-based باشد.

## ۶. (M14) قرارداد status code پروژه: همهٔ POSTها 200
روترهای ما status_code صریح ندارند → 200 برمی‌گردانند؛ تست‌ها نباید 201 انتظار داشته باشند (مگر صریح تغییر کند).

## ۷. (M16) انتساب صفت به تابع قبل از def
سطر `_staff.counter = itertools.count(...)` قبل از تعریف `_staff` ← NameError در import. همیشه انتساب‌های متا بعد از بدنهٔ تابع بیاید (سه بار تکرار شد — الگوی استاندارد کن).

## ۸. (M18-plan) str.replace بی‌صدا no-op می‌شود
اگر متن جست‌وجو پیدا نشود، replace هیچ خطایی نمی‌دهد و فایل بدون تغییر می‌ماند (۶ به‌روزرسانی MASTER_MAP این‌طوری از دست رفت). همیشه بعد از replace با assert/count تأیید کن.

## ۹. (M53-Phase0) پین روی فورک ثالث = قفل روی نسخهٔ کهنه
`install-ecc.sh` کامیت `432485ba` از `WorldFlowAI/everything-claude-code` را پین کرده بود — فورکی که آخرین
کامیتش ۲۰۲۶-۰۱-۲۳ بود، در حالی که بالادست `affaan-m/ECC` تا ۲۰۲۶-۱۱-۰۶ پیش رفته بود (۷۱ ایجنت در برابر ۹).
بازتولیدپذیری درست است، اما **منبع باید بالادست رسمی باشد، نه فورک ثالث.**
→ **قانون:** `ECC_REPO` فقط `https://github.com/affaan-m/ECC.git`. هر ابزار دیگر هم از مخزن اصلی سازنده.

## ۱۰. (M53-Phase0) نصب ابزار در `node_modules` = ناپدیدشدن در snapshot
`node_modules` در snapshotها ضبط نمی‌شود و در `.gitignore` است. پس `rea-agents` نمی‌تواند «یک‌بار نصب و تمام» باشد.
→ **قانون:** هر ابزار بیرون‌مخزنی باید اسکریپت بازتولید idempotent داشته باشد (`docs/MuscleParadise/finn/install-toolchain.sh`).
   مسیر نصب: `~/toolchain/` (خارج از مخزن) و ارجاع فقط از طریق اسکریپت.

## ۱۱. (M53-Phase0) REA روی Node سیستم بالا نمی‌آید
Node سیستم `22.22.3` است، اما REA حداقل `22.23.4` می‌خواهد. `rea --version` با پیام نسخه **exit code ۰** برمی‌گرداند
(exit ≠ 0 نیست!) — یعنی اسکریپت‌ها بدون بررسی خروجی نمی‌فهمند شکست خورده است.
→ **قانون:** REA همیشه با `~/toolchain/node-linux-x64/bin/node` صدا زده شود. هرگز فرض نکن exit code صفر = موفقیت؛ خروجی را هم بخوان.

## ۱۲. (M53-Phase0) بستهٔ `node-linux-x64` npm فقط باینری `node` دارد (بدون npm)
`npm pack node-linux-x64@X` یک پوشهٔ `package/` می‌دهد که باید به `node-linux-x64/` تغییر نام یابد، و `bin/` آن فقط `node` دارد.
→ برای نصب پکیج با آن Node باید `npm` سیستم را جداگانه صدا زد.

## ۱۳. (M45) `timedelta.days` کف می‌گیرد — روز باقی‌مانده اشتراک کم‌نمایی می‌شد
`(expires - now).days` برای ۲٫۹ روز باقی‌مانده `2` برمی‌گرداند، نه `3`؛ آزمون این را گرفت.
→ **قانون:** برای «روز باقی‌مانده»/«مدت تا مهلت» همیشه `math.ceil(total_seconds()/86400)` استفاده کن، نه `.days`.

## ۱۴. (M45) endpoint جدید بدون policy در casbin = ۴۰۳ برای همه
`GET /admin/attendance` ساخته شد ولی `POLICIES` نقش `coach` را نداشت ← همه ۴۰۳ گرفتند.
همان باگ خانوادهٔ REA (#3: نبود policy برای `/ai`).
→ **قانون:** ساخت هر روتر جدید = افزودن هم‌زمان ردیف‌های policy برای هر نقشی که باید دسترسی داشته باشد + یک تست ۴۰۳ برای نقشِ نباید.

## ۱۵. (M45) `dict(rows)` روی چندستونه ValueError می‌دهد
`dict(db.execute(select(A.id, A.name, A.phone)).all())` با «dictionary update sequence element #0 has length 4» می‌شکند.
→ **قانون:** برای چند ستون از dict-comprehension استفاده کن: `{r[0]: r for r in rows}`.

## ۱۶. (M45) REA روی پوشهٔ حاوی `node_modules` عملاً گیر می‌کند
پس از `npm ci` در استودیو، `analyze-javascript-application <dir>` بیش از ۱۰ دقیقه طول کشید (۷۱۸۷ فایل به‌جای ۲۶).
→ **قانون:** برای REA همیشه `--source-paths-json` با فهرست دقیق فایل‌های سورس بده؛ نه پوشهٔ کامل.

## ۱۷. (M45) mock پنهان = ادعای دروغ در UI
صفحهٔ اعضا «۸۶٪ پایبندی» و نمرات ۱۴ محور را از `(id * 7 + i * 3) % 5` می‌ساخت؛ صفحهٔ چک‌این «۱٫۴ ثانیه / ۹۹٪ زیر ۲ ثانیه» را هاردکد داشت.
→ **قانون:** هر عددی در UI باید origin مشخص در API داشته باشد؛ نبود داده = «نامعلوم»، نه عدد.

## ۱۸. (M61) «دکمهٔ موجود» ≠ «دکمهٔ کارکننده» — سه لایه، سه باگ
`checkin_page.dart` دو دکمه داشت. لایهٔ UI می‌گفت هست، لایهٔ rbac می‌گفت ۴۰۳
(`member` فقط `DELETE /face/enroll/*` داشت)، و لایهٔ schema می‌گفت ۴۲۲
(بدنه `{member_id,image_base64}` در برابر `{member_id,method}`). هیچ تستی
بین این سه لایه قرار نداشت، پس سه سالِ «کار می‌کند» هیچ‌وقت باورپذیر نبود.
→ **قانون:** برای هر دکمه که به API می‌رود، یک تست باید **بدنه و مسیر** را با
   schema سرور بسنجد؛ در تست بک‌اند، نقش واقعی همان دکمه را صدا بزند.
   (تست `test_m61_face_member_gate.py` + `face_consent_gate_test.dart`)

## ۱۹. (M61) گیت «هر مسیر مصرف‌کننده دارد» فقط طولِ متن را می‌سنجید
`apiCoverage.test.ts` استثناها را به‌صورت `Record<string, string>` نگه می‌داشت و
تنها `reason.length > 5` را assert می‌کرد. چهار ردیف جملهٔ خوش‌ساخت داشتند برای
مصرف‌کننده‌ای که وجود نداشت (`logout`, `privacy-notice`, `notifications`,
`memberships/plans`).
→ **قانون:** هر استثنا باید **قابل بازرسی** باشد: یا رشته‌ای که در کد کلاینت
   واقعاً پیدا می‌شود، یا `external` نام‌برده. متنِ دلیل به‌تنهایی شاهد نیست.
   (اثبات: با گذاشتن `evidence: "/totally-not-in-the-code"` تست قرمز شد)

## ۲۰. (M61) `items[0]` به‌جای انتخاب کاربر — هم‌سایه با پنلی که درست بود
`Programs.tsx` پنل حجم را با `items[0].member_id` سوار می‌کرد، در حالی که
`ReadinessPanel` کنارش از `selectedMemberId` می‌خواند. مربی عضو B را انتخاب
می‌کرد و دو پنل دو عضو نشان می‌دادند.
→ **قانون:** هر پنل عضو-محور باید از یک منبع واحد (`selectedMemberId`) بخواند؛
   `items[0]` و مشابهش در کد عضو-محور ممنوع (تست: `programsPage.test.tsx`).

## ۲۱. (M64) diagnostics نباید به مخزن push شوند
workflowهای CI قبلاً روی failure، branch را fetch/reset می‌کردند و گزارش را commit/push می‌کردند؛ این کار token نوشتنی را به jobهای lint/test می‌داد و می‌توانست workspace runner را دور از branch trigger تغییر دهد.
→ **قانون:** خروجی شکست را artifact کوتاه‌عمر نگه دار؛ اگر delivery واقعاً نیاز به write دارد، آن را به job مستقلِ بعد از build منتقل کن، trigger و ref را محدود کن، و مجوز write را فقط همان job بده. اعلان‌گر read-only هرگز token این jobها را نمی‌گیرد.

## ۲۲. (M65) JWT role claim به‌تنهایی مرز QR/access نیست
`/face/qr-token` قبلاً access JWT با role=`checkin-qr` می‌ساخت و `/face/checkin-qr` هر payload دلخواهی را می‌پذیرفت؛ integration test روی HEAD همان توکن را access bearer دانست، اشتراک/مالکیت را دور زد و replay ثبت کرد.
→ **قانون:** هر توکن با منظور متفاوت باید type/audience و عمر مستقل داشته باشد؛ subject را با actor مالک‌محور بسنج؛ token را یک‌بارمصرف با nonce تصادفی و قید یکتای دیتابیس ببند؛ فقط nonce-hash را ذخیره کن. تست pre-fix باید اول با رفتار ناامن قرمز شود، سپس regression بعد از fix سبز.

## ۲۳. (M71) متن شبیه route مصرف‌کننده نیست
گیت قدیمی `apiCoverage.test.ts` مسیر را با جست‌وجوی substring می‌پوشاند؛ comment، string توضیحی و wildcard بیش‌ازحد می‌توانستند خروجی را سبز/نادرست کنند. یک client path پویا مثل `/payments/{id}/receipt` نباید route ثابت `/payments/invoice/{member_id}` را پوشش دهد.
→ **قانون:** callهای TypeScript را با AST و Dart را پس از حذف comment/string token کن؛ route parameter فقط سمت تعریف backend wildcard است؛ exception باید به route فعلی اشاره کند و دلیلِ external یا TODO روشن داشته باشد. چون `routes.json` فقط path دارد، از این گیت دربارهٔ HTTP verb، schema یا runtime ادعا نکن. Regression: `mp-app/studio/tests/apiCoverage.test.ts`.

## ۲۴. (M81 / M71) Riverpod provider-chain هم API call واقعی است
گیت دارت فقط alias محلی `api.get(...)` را می‌شمرد و `ref.read(apiClientProvider).post(...)`/`ref.watch(...).get(...)` را نمی‌دید؛ اجرای جاری به‌خاطر `/classes/book` این منفی کاذب را آشکار کرد و چند مسیر واقعی M74/M75 نیز از exceptionهای TODO خوانده می‌شدند.
→ **قانون:** هر scanner مصرف API در Flutter باید call را از expression provider واقعی بشناسد، نه فقط نام متغیر `api`; probe واقعی برای `read/watch(apiClientProvider).<method>` نگه دار و TODO را به call evidence ارتقا بده، نه این‌که مسیر فعال را exception کنی. Regression: `mp-app/studio/tests/apiCoverage.test.ts` (4 passed؛ full Studio 217 passed/9 skipped). M81 Flutter widget test همچنان runtime-UNKNOWN تا Codespaces.

## ۲۵. (M97) drift باید روی هر دو مسیر provisioning سنجیده شود، و restore باید تمرین‌پذیر باشد
`alembic check` فقط «DB مهاجرت‌کرده = مدل» را می‌سنجد؛ DBای که dev/test با `Base.metadata.create_all` می‌سازد بیرون آن سنجش بود، و `restore` فایل‌های الحاقی را در مسیرهای زنده می‌نوشت، پس «مانور روی scratch» عملاً وجود نداشت.
→ **قانون:** برای هر تغییر schema، هر دو مسیر (migrations و `create_all`) را در یک تست جدول/ستون/ایندکس مقایسه کن؛ baseline نصب‌های قدیمی فقط با `alembic stamp head` + `alembic check`، نه `ALTER TABLE` دستی؛ تاریخچه باید یک head داشته باشد (گیت، نه احتیاط شفاهی). هر ابزار operational که فایل می‌نویسد باید حالت «فقط بررسی» (`verify`) و مقصد موقت (`--extras-to`) داشته باشد و تستِ رگرسیون «فایل زنده عوض نشد» بدهد. گیت‌ها را با تزریق خرابی راستی‌آزمایی کن تا سبزِ توخالی نشود. Regression: `mp-app/backend/tests/integration/test_m97_migrations_and_backup.py`.

## ۲۶. (M90) پاسخ ۲۰۰ هم می‌تواند دادهٔ اشتباه باشد — کلاینت باید مالکیت را تأیید کند
endpoint رسید مالکیت را در سرویس چک می‌کند، ولی اگر روزی آن چک برداشته/اشتباه شود، UI قبلی بی‌سؤال‌پرسیدن رسیدِ عضو دیگر را نشان می‌داد. `order_id` و `member_id` پاسخ حالا با درخواست/نشست تطبیق می‌شود و عدم تطابق = خطا، نه نمایش.
→ **قانون:** هر read مالکیت‌محور در Flutter باید «این رکورد مال این نشست است؟» را تأیید کند و در عدم تطابق fail closed شود؛ هیچ عددی در کلاینت تصحیح نمی‌شود (جمع ناهمخوان نمایش داده می‌شود، نه یکسان). گیت `apiCoverage` را با exception بی‌مصرف کهنه‌اش نکن: مصرف واقعی Client را در همان تست ثبت کن. Regression: `mp-app/client/test/shop_orders_receipt_test.dart`.

## ۲۷. (M98) ادعای haptics/دسترس‌پذیری با «صدا زدن تابع» ثابت نمی‌شود
`HapticFeedback` در نسخه‌های مختلف SDK مسیر متفاوتی می‌رود (`HapticFeedback.vibrate` در برابر `VibrationEffect.vibrate`)؛ اگر تست فقط `expect(called, isTrue)` روی تابع ما می‌داد، نه رفتن پالس به پلتفرم و نه خاموش‌بودنش اثبات نمی‌شد.
→ **قانون:** بازخورد لمسی/حرکتی را پشت یک رابط تزریق‌پذیر بگذار، در تست ویجت fake بزن (ترتیب/تعداد)، و لایهٔ سیستمی را با `setMockMethodCallHandler` روی messenger بسنج؛ «کاهش حرکت» را از `MediaQuery.disableAnimations` بخوان و skip کن، نه حذف؛ و پالس را بعد از نتیجهٔ سرویس بفرست. Regression: `mp-app/client/test/motion_haptics_test.dart`.

## ۲۸. (M90/M98) گیتِ بدون SDK «pass» نیست؛ اولین اجرای واقعی CI چهار شکست داد
`dart_gate.py` (Tree-sitter) ۷۲ فایل را ۰ یافته گزارش کرد، ولی `client-flutter` در run `44293699567` گفت: **146 passed / 4 failed** — یک خطای کامپایل (`setMockMethodCallHandler<void>`: آن متد در این SDK ژنریک نیست)، یک بلوکه‌شدن `setState` پشت `await` کانال پلتفرم، و دو ادعای تست که با متن واقعیِ رندرشده نمی‌خواندند (انتظارِ مبلغ بدون «ریال»؛ `textContaining('جمع اقلام')` که جملهٔ اختلاف را هم می‌گرفت).
→ **قوانین:** (۱) تا وقتی analyzer/test واقعی اجرا نشده، وضعیت loop `UNKNOWN` است و شمارش فایل‌های gate هرگز در گزارش «analyze pass» نوشته نمی‌شود؛ (۲) ادعای ویجت‌تست باید با رشته‌ای سنجیده شود که از خودِ ویجت خوانده شده (یا fixture با مقادیر متمایز که `findsOneWidget` واقعاً یکی باشد)؛ (۳) بازخورد اختیاری هرگز نباید قبل از state-update await شود (D-051)؛ (۴) API سطح پلتفرم را در تست pin کن (`debugDefaultTargetPlatformOverride`) تا no-op بودن روی runner، جای «درست کار کردن» را نگیرد. push بعدی: `07ff2ed → 484fcd8 → 41ae143 → c672737`.
درست‌کردنِ چهار شکست در run `44295081645` سبز نشد: **154 passed / 2 failed** و هر دو شکست، تست messenger بود که **۱۰ دقیقه timeout** خورد — `pumpEventQueue()` داخل `testWidgets` زیر FakeAsync روی `Future.delayed` واقعی می‌خوابد. پس قانون پنجم: در تست ویجت زمان را فقط با چیزی که خودِ tester جلو می‌برد تخلیه کن (`runAsync` + `pump`)؛ یک تست «آویز» گیت را فقط fail نمی‌کند، کل job را ۳ برابر می‌کند.

## ۲۹. (M107) «اینجا نمی‌شود» یعنی راهِ اجرای بیرونی بنویس، نه اینکه ادعا را نرم کنی
سه loop (M87 کامپایل، M104 startup، M105/M106 ماسک) ماه‌ها `UNKNOWN` ماندند چون در sandbox ابزار نبود. راه درست نه پایین‌آوردن معیار بود نه «روی شبیه‌ساز دیده شد»؛ راه درست یک **دستور کار اجرا‌شدنی** بود که انسان در محیط درست اجرا کند و لاگ را برگرداند.
→ **قانون:** هر بار که مانع، «نبود ابزار در این محیط» است: (۱) مرز را دقیق بنویس — کدام گیت با Codespace حل می‌شود و کدام هرگز (device/USB/KVM); (۲) commands را با خروجیِ موردِانتظار و قالب بازگشت شماره‌دار کن تا «اجرای ناقص» از «سبز» قابل‌تمایز بماند; (۳) هر اسکریپتِ ساخت‌آماده‌ای که خودت نتوانسته‌ای اجرا کنی را با حالت پیش‌فرض «انجام نده» و opt-in بنویس (checksum حدسی ممنوع، license acceptance صریح); (۴) هیچ status را پیش از دیدن لاگ عوض نکن.

## ۳۰. (M108) کاری را که «فقط انسان می‌تواند» اول به CI ببر، بعد انسان را درگیر کن
سه loop (M87 compile، M90/M98 روی SDK پین‌شده، coverage کلاینت) ماه‌ها منتظر « Codespace کاربر» ماندند. یک بازبینی ساده — *آیا این گیت واقعاً به محیط کاربر نیاز دارد یا به یک job ۵ دقیقه‌ای؟* — سه‌تایشان را از صف انسانی بیرون آورد و **M87 را از `UNKNOWN` درآورد**. و در همان بازبینی معلوم شد یکی از «هرگز اجرا نشده»های من (`pip-audit`) از قبل در CI بلاکینگ بوده.
→ **قانون:** پیش از آنکه کاری را به کاربر بسپاری، بنویس کدام ابزار/اجازه در این محیط کم است و آیا همان چیزی در GitHub Actions هست (runner اندرویدپیش‌فرض + Flutter پین‌شده ≈ Codespace، بدون هزینهٔ container و بدون token کاربر). هر «ad-hoc human run» که به‌صورت job درنمی‌آید، دفعهٔ بعد هم دوباره دستی است و شاهدش هم گم می‌شود. اعداد را در `::notice`/step summary بگذار تا از API قابل‌بازخوانی باشند.

## ۳۱. (M109) «نمی‌شود» را لایه‌لایه بسنج، بعد به انسان بگو
جوابِ صادقانه‌ی «Codespace تو را نمی‌توانم ران کنم» ماه‌ها ایستاد و *درست* بود. آنچه عوضش کرد یک جمله نبود، یک جدول بود: ساختنِ codespace مجاز / ورودِ SSH غیرمجاز / dispatchِ workflow و PR مجاز. لایهٔ سوم همان کاری را کرد که به لایهٔ اول نسبت داده شده بود — و یک بدهیِ ۶۵ فایلی در یک بعدازظهر صفر شد، با PR که بعداً merge شد.
→ **قانون:** پیش از واگذاری هر کاری به انسان، بنویس دقیقاً کدام capability لازم است (ابزار؟ اجازه؟ شبکه؟ بدن؟) و هرکدام را جدا بسنج. «اجازهٔ ساختن» با «اجازهٔ ورود» یکی نیست، و «نمی‌توانم در محیط تو اجرا کنم» هیچ‌وقت به معنی «CI نمی‌تواند» نبود. کارهایی که واقعاً بدن/دستگاه می‌خواهند را صریح همان‌جا نگه دار — و بگو چرا.


## ۳۲. (M110) «با mock تست شد» وقتی meaningful نیست که mock حالت ندارد
«درگاه کامل شد» با `MockGateway` قابل اثبات نبود: mock به هر authority خوش‌ساخت «پرداخت شد»
می‌گفت — انصرافِ کاربر، پرداخت‌نشده، replay و timeout شبکه در آن وجود نداشتند. راه درست نه
«باور کردنِ mock» بود نه «منتظرِ درگاه واقعی نشستن»؛ ساختنِ یک **بانک صندباکس** بود: سرویس HTTP
مستقل با state واقعی و همان قرارداد، رایگان و آفلاین. همان تست‌ها بعداً بدون بازنویسی روی
درگاه واقعی سوار می‌شوند، و دو تستِ تازه (۱۰۳ِ «امضای درست + پول نیامده» و 5xx⇒unavailable)
دقیقاً جاهایی‌اند که mock هیچ‌وقت نمی‌دید.
→ **قانون:** هر جای‌گزای آزمون یک تصمیم صریح می‌خواهد: stateless یا stateful؟ اگر صحتِ نتیجهٔ
تو به «حالتِ طرف مقابل» وابسته است، جای‌گزای in-process بی‌حالت **نمی‌تواند** گواه باشد؛ یک
فیک stateful محلی بنویس و قراردادش را از پاسخ‌های واقعیِ همان سرویس بگیر (این‌جا: ۱۰۰/۱۰۱/۱۰۲/
۱۰۳/−۱ و ۲۵۵/۲۵۴). هزینه‌اش یک فایل است، ارزشش این است که ادعای «کامل» بدون شناسهٔ تاجر هم
راستی‌آزمایی دارد. و یادداشتِ همان‌روز: استارت‌لت `RedirectResponse` را **۳۰۷** می‌فرستد؛ برای
شبیه‌سازیِ bank-returnِ واقعی صریحاً ۳۰۲ بده، وگرنه مرورگرِ آزمون فرم را به merchant دوباره POST
می‌کند و باگ در لایهٔ «فیک» پنهان می‌شود.

## ۳۳. بازبینی مجدد «آیا CI می‌تواند؟» (۲۰۲۶-۱۱-۱۸)

این یادداشت اصلاحِ شاهدهای قدیمی است، نه پاک‌کردنِ درس‌های تاریخی بالا. run `44381628350`
روی `66bfe14`، jobهای `client-flutter` و `client-pinned` را موفق اجرا کرد؛ همچنین
`backend`، `studio`، `live-contract`، `docs` و `e2e-api` موفق بودند. `secret-scan` شکست خورد.
گزارش `finn/reports/m108-ci-pinned-gates.md` شاهد شمارش ۱۵۶/۰/۰ و build debug روی `2ac6ecc` است.

- ردیف‌های ۲۶ و ۲۷–۳۴ و ۳۸ و یادداشت M81: بخش Flutter analyze/widget runtime که در زمان
  ثبت «unrun/UNKNOWN» بود، برای کد آن زمان با suite سبز CI و گزارش M108 اجرا شده است؛ این
  فقط شاهد آن suite است، نه تأیید سخت‌افزار، production یا هر معیار جداگانهٔ محصول.
- M87: CI کامپایل debug را اجرا کرده؛ persistence بعد از restart روی گوشی و سیاست رمزنگاری
  همچنان نامعلوم‌اند. M88 و M89 از این حیث بسته نمی‌شوند؛ scan فیزیکی را CI بدون گوشی اثبات نمی‌کند.
- M68: تصمیم توزیع مشخص است اما دو رمز واقعی کلید امضای تاریخی هنوز یافتهٔ فعال‌اند؛
  CI می‌تواند آن‌ها را شناسایی کند، نه لغو یا حذفشان را بدون نقض دستور فعلی انجام دهد.
- M69: scope تصمیم‌گیری شده، اما ادعای تشخیص چهرهٔ واقعی و مجوز مدل را از QR یا CI نتیجه نمی‌گیریم.
  M85/M92/M93 و بخش live در M91، تصمیم/اعتبار واقعیِ انسانی یا تاجر می‌خواهند؛ suite مصنوعی
  جای آن را نمی‌گیرد. M94/M96 به پیاده‌سازی و سیاست‌های مرتبط نیاز دارند، نه فقط runner.
- اجرای بعدی `44382752177` برای کد جدید روی `5ff6d5d`: backend، studio، docs و live-contract
  موفق؛ دو job Flutter به‌دلیل شکست تست QR و secret-scan به‌دلیل دو یافتهٔ واقعی ناموفق بودند.
  هر ادعای سبزی برای کد جدید منوط به اجرای مجدد همان gateهاست.
