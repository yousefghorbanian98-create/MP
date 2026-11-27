# Handoff نشست — Muscle Paradise

> این فایل **خلاصهٔ جاری برای ادامهٔ کار** است، نه آرشیو گفتگو و نه منبع نهایی وضعیت محصول. پیش از فشرده‌سازی context یا پایان هر کار معنادار، همین snapshot را جایگزین/به‌روز کن؛ تاریخچه را با انباشت transcript طولانی نکن.

## وضعیت جاری — MEM-05 / PWA-34 ثبت بازخورد ست + تریاژ flake + گزارش STALE (UTC 2026-11-27)

```text
CURRENT_BRANCH=arena/3c08bfbd-mp
MEM-05/PWA-34=PARTIAL/NOT_ACCEPTED؛ BLOCKED نیست
MEM05_IDEMPOTENCY=set-feedback: no (کلید/نسخه ندارد؛ تکرار = ردیف تازه) · sync/set-feedback: yes (device_id:client_id + updated_at، LWW)
WRITE_PATH=فقط /programs/sync/set-feedback؛ مسیر بدون کلید صدا زده نمی‌شود
SERVER_TRUTH=پس از نوشتن، آمادگی/شمارش بازخورد از API دوباره خوانده می‌شود
TIMEOUT=abort ⇒ «ثبت نشد»؛ تلاش دوباره همان client_id/updated_at
CLIENT_JOB_FLAKY=yes — دو شکست تاریخی (e22d8db، 107968d-push)؛ اولین push پس از سخت‌سازی (6e69767) سبز شد؛ علت اثبات‌نشده
STALE_ARTIFACTS=بازرسی می‌شوند: dirty ⇒ خطا، کهنگی ⇒ گزارش `STALE <path> recorded/actual`
GITLEAKSIGNORE=۱۰ خط، ثابت؛ قالب تازه `sha256_b64:` جلوی صف بی‌پایان را می‌گیرد
CI_6E69767=سبز در هر دو سطح (PR ۱۲/۱۲ · run سطح push 46071739713 success؛ secret-scan ۱۷s با همان ۱۰ خط)
RELEASE=NO-GO
```

- **MEM-05:** پاسخ گیت با فایل/خط: `modules/programs/schemas.py:103-106` و `service.py:183-197` نشان می‌دهند `POST /programs/set-feedback` کلید/نسخه ندارد و هر ارسال را append می‌کند (آزمون: دو ارسال = ۲ ردیف). قرارداد idempotent از قبل موجود بود: `router.py:134-143` + `service.py:584-700` + ستون‌های `client_id`/`device_id`/`client_updated_at` (`db/models/programs.py:113-116`). پس mock ساخته نشد و از همان مسیر نوشتن استفاده شد.
- **UI:** فرم ست در `/member/today`، کنترل‌ها از antd (Q11 ratchet)، `device_id` پایدار در `localStorage`، کلید `client_id` در همهٔ تلاش‌ها ثابت، و بازخوانی از API پس از ثبت.
- **P1:** روی `107968d` دو run بود: `46055618838` (pull_request، success) و `46055611570` (push، **failure** در `Android debug compile`). لاگ job از API در دسترس نبود؛ job با کش Gradle، `--no-daemon` معادل (`org.gradle.daemon=false`)، heap کوچک‌تر و artifact «client-android-build-log» سخت‌سازی شد. `gh run list` باید همیشه در گزارش بیاید، نه فقط `gh pr checks`.
- **P2:** ادعای قبلی دربارهٔ «بستن ریشه با پیشوند `sha256:`» **نادرست بود** و در سند اصلاح شد؛ قالب جاری `sha256_b64:<44>` است. فایل‌های `*.STALE.json` حالا بازرسی و گزارش می‌شوند (dirty ⇒ خطا).
- شاهد: [`MEM-05 current run`](../../evidence/2026-11-27/MEM-05/current-run.md) و [`client-job-triage`](../../evidence/2026-11-27/CI-FLAKE/client-job-triage.txt). `MEM-01…05`، `INV-02/03`، `SEC-01` partial می‌مانند؛ `PWA-01=PROPOSED/NOT_RUN`؛ release=`NO-GO`.

## وضعیت جاری — MEM-04 / PWA-33 برنامهٔ امروز عضو (UTC 2026-11-27)

```text
CURRENT_BRANCH=arena/3c08bfbd-mp
MEM-04/PWA-33=PARTIAL/NOT_ACCEPTED؛ checkbox canonical باز
MEM04_ROUTE_ACCESS=member=yes — api/routes.json:3369-3385؛ modules/programs/router.py:31-37؛ app/security/ownership.py:23-29
SURFACE=/member/today → MemberTodayProgram روی GET /programs/member/{id} + /readiness
NUMBERS=هر عدد با برچسب «منبع: GET …»؛ engine_version تنها نسخه، approved_at تنها تاریخ، بدون محاسبهٔ کلاینت
EMPTY_STATE=بدون approved → پیام تهی؛ readiness=null → reason سرور؛ پاسخ غیرآرایه → fail-closed
ACCESS_TEST=۳ تست تازه: عضو A روی دادهٔ B در هر چهار مسیر ۴۰۳
LOCAL_GATES=Studio ۴ تست تازه/کل ۳۹۹ pass・۱۵ skip؛ tsc/eslint/build پاک؛ backend ۹ pass
CI=پاس روی tip 27ef138 (۱۲ check؛ شامل secret-scan و گیت digest)؛ REVIEWER/DEVICE=NOT_RUN؛ release=NO-GO
```

- endpoint فرضی ساخته نشد. `GET /api/v1/programs/member/{member_id}`، `/readiness`، `/volume` و `GET /api/v1/programs/{program_id}` از قبل در `api/routes.json` بودند و نقش `member` را مجاز می‌دانستند؛ مالکیت سطری در `app/security/ownership.py:23-29` اعمال می‌شود.
- UI فقط برنامهٔ `approved` را نشان می‌دهد؛ `draft`/`rejected` شمارش وضعیت‌اند، نه برنامه. هیچ KPI/کالری/۱RM/ادعای پزشکی ساخته نشد و هر عدد منبع مکتوب دارد.
- محدودیت‌های قرارداد صریح نوشته شدند: برنامه شمارهٔ نسخهٔ عددی و تاریخ شروع/پایان ندارد؛ `safety_flags="{}"` یعنی غربالگری انجام نشده.
- شاهد: [`MEM-04 current run`](../../evidence/2026-11-27/MEM-04/current-run.md) و [`route-access`](../../evidence/2026-11-27/MEM-04/route-access.txt). همچنان مرورگر/دستگاه واقعی، بازبینی انسانی و CI همین SHA اجرا نشده‌اند؛ `INV-02/03`، `SEC-01`، `MEM-01…04` partial می‌مانند و release=`NO-GO`.

## وضعیت جاری — MEM-03 / PWA-32 تغییر شماره، نشست دستگاه و پاسخ دیررس (UTC 2026-11-27)

```text
CURRENT_BRANCH=arena/3c08bfbd-mp
BRANCH_BASE=ebebef3ad153277f0223c2011efc4f9a9c855654 (main؛ PR #30 در 2026-11-27T16:49:20Z MERGE شد)
STATE_LAST_UPDATED=2026-11-27T17:10:00Z
EVIDENCE_DATE_DIRS=2026-11-23, 2026-11-27
NOTE: یادداشت‌های «PR #30 باز/مرج نشود» در بخش‌های پایین‌تر تاریخی‌اند؛ وضعیت فعلی MERGED است.
MEM-03/PWA-32=PARTIAL/NOT_ACCEPTED؛ checkbox canonical باز
MEMBER_SURFACE=تغییر شماره + نشست‌های دستگاه + logout-all در خانهٔ عضو (نه فقط shell کارکنان)
LATE_CONFIRM_GUARD=PASS محلی با تست واحد؛ نشست حساب دیگر پاک/revoke نمی‌شود
LIVE_PHONE_CHANGE=PASS محلی: ۱ فایل/۱ تست روی API واقعی + SQLite synthetic + DevSmsProvider
PUSHED=3170b6a80029102dafbc28128f2997ee0df5b3f7 روی arena/3c08bfbd-mp (commitهای قبلی: 7deb122، a5e4517، e22d8db)
CI_3170B6A=همان نتیجه: هفت job سبز، فقط secret-scan قرمز (run 46043582882)
CI_E22D8DB=هفت job سبز (studio، backend، docs، live-contract، e2e-api، client-flutter، client-pinned)؛ تنها secret-scan قرمز — همان شکست از قبل موجود روی main
CI_A5E4517=همان نتیجه روی SHA قبلی؛ client-pinned در تلاش اول e22d8db یک‌بار در step کامپایل اندروید شکست و با rerun سبز شد (ناپایدار، نه ناشی از این تغییر)
SECRET_SCAN=RED؛ رفع با دو مسیر مجاز انجام شد (بدون allowlist بر اساس rule/path): پیشوند `sha256:` در generator + ۵ خط fingerprint دقیق برای `ebebef3…` (۵ خط `6593cb4b…` از قبل بود)
CROSSWALK_DIGEST_GATE=افزوده شد و در job `docs` اجرا می‌شود؛ روی d71dbe0 قرمز بود (۲ artifact کهنه، ۲ منبع: `api.ts`، `navigation.ts`) و پس از بازتولید روی درخت تمیز در `9ea9a24` **PASS** (۲ artifact، همهٔ ۶ منبع برابر، `tracked_dirty=false`)
CROSSWALK_STALE=v1 artifactها با `git mv` به `*.STALE.{md,json}` تغییر نام دادند (محتوا دست‌نخورده)
FINISH_PHONE_CHANGE_TEST=PASS (۳ تست تازه در `tests/session.test.ts`؛ با mutation تأیید شد که جابه‌جایی revocation به بالای guard دو تست را قرمز می‌کند)
PR31=draft/open؛ merge ممنوع
REAL_SMS/DEVICE/BROWSER=اجرا نشده؛ release=NO-GO
```

- قرارداد backend از قبل کامل بود؛ endpoint فرضی ساخته نشد. شکاف واقعی سمت محصول بود: `MemberShell` هیچ ورودی تغییر شماره یا مدیریت نشست نداشت و `POST /auth/logout-all` مصرف‌کنندهٔ UI نداشت (در گیت api-coverage با TODO مستثنا بود). اکنون کارت `MemberSecurity` فهرست نشست‌های همان حساب را از `GET /auth/sessions` می‌خواند و «خروج از همهٔ دستگاه‌ها» فقط با تأیید ۲۰۰ سرور انجام‌شده اعلام می‌شود؛ در خطا نشست محلی حفظ و خطای قابل‌تلاش نشان داده می‌شود.
- ریسک پاسخ دیررس: `confirm` موفق که پس از ورود حساب دیگر در همان مرورگر برسد، پیش‌تر `signOut()` را روی نشست تازه اجرا می‌کرد و refresh token آن حساب را هم سمت سرور revoke می‌کرد. `PhoneChangeDialog` اکنون پیش از ارسال `confirm` یک `SessionGuard` (شناسهٔ حساب از `sub` توکن) می‌گیرد و `clearSessionForAccount` فقط در حالت `ended` دست به storage می‌زند؛ `different-account` و `signed-out` هیچ تغییری نمی‌دهند و ادعای خروج هم نمی‌کنند.
- شواهد آزمون محلی: Studio focused **۶ فایل/۴۲ pass**؛ full **۵۵ فایل pass، ۴ skip؛ ۳۹۲ pass، ۱۵ skip**؛ `tsc -b`/`eslint .`/`npm run build` پاس؛ backend مرتبط (`test_m82_phone_change`، `test_wp14_logout_all`، `test_phase4_identity_session`) **۱۸ pass/۱ warning**. قرارداد زندهٔ تازه `tests/liveContractPhoneChange.test.ts` روی Uvicorn محلی **۱/۱ pass**؛ DB مصنوعی شمارهٔ عوض‌شده، `auth_version=2` و دو refresh revoked را نشان داد. جزئیات و logهای خام: [`MEM-03 current run`](../../evidence/2026-11-27/MEM-03/current-run.md).
- CI: job «live-contract» اکنون `MP_ALLOW_DEV_OTP_ECHO=true` را فقط برای سرور synthetic همان job می‌دهد و یک step جدا برای phone-change/logout-all دارد (آخرین مصرف‌کنندهٔ حساب fixture، چون شماره‌اش را عوض می‌کند). این workflow هنوز اجرا نشده است.
- محدودیت‌ها: SMS/provider و دستگاه واقعی، مرورگر/صفحه‌خوان، بازبینی انسانی و CI این شاخه اجرا نشده‌اند؛ تست‌های UI با jsdom و `fetch` stub‌شده‌اند. داده‌های شمارهٔ قدیم/جدید در `phone_change_challenges` بدون مسیر retention پیدا شدند؛ این پرسش **policy حریم خصوصی** است و به‌عنوان نتیجهٔ compliance ثبت نمی‌شود.
- CI روی `e22d8db` (run `46041788457`) و `a5e4517` (run `46040528118`): هر هفت job سبز است، از جمله `live-contract` که step تازهٔ phone-change/logout-all را اجرا کرد؛ تنها `secret-scan` قرمز است و **همان job روی main (`ebebef3`, run `46036816362`) هم قرمز است**. پنج finding همه مقدار ۶۴-hex در نگاشت `source_digests` فایل‌های crosswalk JSON هستند (SHA-256 محتوای source، نه credential). راه‌حل — fingerprint دقیق در `.gitleaksignore`، allowlist باریک، یا تغییر شکل digest در generator — نیازمند تأیید مالک است و در این برش انجام نشد. یکی از تلاش‌ها روی e22d8db در step کامپایل اندروید شکست خورد و با `gh run rerun --failed` سبز شد (ناپایدار؛ همین کد ۲۰ دقیقه قبل سبز بود و لاگ job با EOF دانلود نشد). شاهد: [`pr-ci-a5e4517.txt`](../../evidence/2026-11-27/MEM-03/pr-ci-a5e4517.txt) و [`pr-ci-e22d8db.txt`](../../evidence/2026-11-27/MEM-03/pr-ci-e22d8db.txt). تصمیم retention نیز به‌صورت [ADR-008 (Proposed)](adr/008-phone-change-challenge-retention.md) ثبت شد و پیاده‌سازی نشد.
- **رفع همین دور (بدون راز در شاهد):** `.github/workflows/ci.yml` در job `secret-scan` حالا فقط `File`/`RuleID`/`Line`/`Commit`/`Fingerprint` را چاپ می‌کند و `/tmp/gitleaks-findings.json` را به‌عنوان artifact آپلود می‌کند؛ `.gitleaksignore` پنج خط دقیق برای `ebebef3…` گرفت و `scripts/test_retired_signing_scan.py` حالا هر دو مجموعه (`6593cb4b…` و `ebebef3…`) را assert می‌کند. اسکن واقعی gitleaks در sandbox اجرا نشد (دانلود release شکست می‌خورد)؛ آنچه اجرا شد assert‌های policy روی همان فایل است: [`gitleaks-policy-test.txt`](../../evidence/2026-11-27/MEM-03/gitleaks-policy-test.txt) و [`secret-scan-redacted.txt`](../../evidence/2026-11-27/MEM-03/secret-scan-redacted.txt).
- **گیت تازهٔ digest:** `scripts/verify_crosswalk_digests.py` روی artifact‌های `evidence/**/*-crosswalk.json` (به‌جز `*.STALE.json`) شرط می‌گذارد که `tracked_dirty` صریحاً `False` باشد و digest هر منبع با فایل فعلی بخواند. خروجی روی `d71dbe0`: ۶ خطا در ۲ artifact — همان دو منبع `api.ts`/`navigation.ts` (بزرگ‌تر از گزارش تک‌فایلی مالک) به‌علاوهٔ `tracked_dirty=true`: [`digest-gate-before.txt`](../../evidence/2026-11-27/MEM-03/digest-gate-before.txt). بازتولید روی درخت تمیز در commit بلافاصلهٔ بعد انجام شد (`9ea9a24`): هر دو artifact حالا `tracked_dirty=false` و digestهای `sha256:` دارند و gate پاس می‌شود؛ shاهد: [`digest-gate-after.txt`](../../evidence/2026-11-27/MEM-03/digest-gate-after.txt). نکتهٔ عملی: generator روی درخت tracked dirty با `exit 4` رد می‌کند، پس هر دو artifact روی یک درخت تمیز در `/tmp/cw/*` ساخته و سپس کپی شدند.
- **قاعدهٔ STATE (بدون استثنا):** هر artifact که digest/HEAD آن با HEAD جاری یکی نیست، یا روی درخت تمیز بازتولید می‌شود یا `STALE` در نامش می‌آید؛ تولید digest روی درخت dirty ممنوع است و generator در این حالت `exit 4` می‌دهد.
- بعدی: بازتولید crosswalk روی درخت تمیز و تأیید CI همان SHA، سپس ارزیابی MEM-04 فقط از کد و شاهد همان SHA. `MEM-01`، `MEM-02/PWA-30/31`، `INV-02/03` و `SEC-01` partial می‌مانند؛ `PWA-01=PROPOSED/NOT_RUN`؛ release=`NO-GO`.

## Snapshot پیشین — MEM-01 live member-account contract و identity-negative (UTC 2026-11-27)

```text
CURRENT_BRANCH=arena/5e0f64cf-mp
BASE_REMOTE_HEAD=9cdd96554108d8438fe906a82b233d68e21e0fd8
STATE_LAST_UPDATED=2026-11-27T15:41:18Z
EVIDENCE_DATE_DIRS=2026-11-23, 2026-11-27
NOTE: تاریخ مرجع 2026-11-23 تاریخ شروع برنامه است، نه تاریخ به‌روزرسانی STATE.
MEM-01=PARTIAL/NOT_ACCEPTED؛ checkbox canonical باز
LIVE_MEMBER=PASS محلی: ۴/۴؛ API زندهٔ محلی + SQLite synthetic؛ token چاپ/ذخیره نشد
IDENTITY_NEGATIVE=PASS: ۳/۳؛ User.id به‌جای Member.id و دسترسی به B هر دو رد شدند
TODAY_EMPTY_STATE_TEST=PASS: placeholder صادق/no-mock و AccessDenied برای نقش غیرعضو
PUSH/PR_CI=فقط نتیجهٔ متصل به SHA دقیق شاخه را معتبر بدان؛ گیت محلی جای CI ریموت نیست
PR #30=OPEN/DRAFT/unmerged؛ release=NO-GO
INDEX=۶۰ مسیر staged نامرتبط از قبل حفظ می‌شوند؛ receipt/untrackedها دست‌نخورده
NEXT=شروع بررسی scope کارت MEM-03؛ پیاده‌سازی OTP ادعا نشده
```

- `fetchMe` و `fetchMemberMemberships` در `src/lib/api.ts` از قبل وجود داشتند، پس API helper تغییر نکرد. workflow CI برای fixtureهای synthetic A/B و اجرای live suite با JWT عضو گسترش یافت. شواهد: [`live-contract-member.txt`](../../evidence/2026-11-27/MEM-01/live-contract-member.txt)، [`identity-negative.txt`](../../evidence/2026-11-27/MEM-01/identity-negative.txt).
- گیت‌های محلی: `npm run lint` پاس؛ `memberAccountPage.test.tsx` برابر ۶/۶؛ live client suite برابر ۴/۴ با Uvicorn + SQLite synthetic؛ backend `test_mem01_member_identity.py` برابر ۳/۳ (یک هشدار deprecation قدیمی Starlette/httpx)؛ Ruff/format و workflow YAML/shell syntax پاس. Docs gate **۳۸ Markdown/۶۱۱ لینک/۱۵ Mermaid**، project guide و interaction map **۳۲ سطح/۱۶۳ مسیر/صفر drift** و `git diff --check` پاس؛ push و PR CI این follow-up هنوز باید تأیید شوند.
- Today همچنان placeholder بدون API است و دادهٔ نمونه ندارد؛ test عدم نمایش mock و role denial را قفل می‌کند. مقصد پشتیبانی و endpoint معتبر برنامه در repo تنظیم نشده، پس support link و API error/retry هنوز پیاده‌سازی نشده‌اند و این مسیر accepted نیست.
- `MEM-01`, `PWA-30/31`, `INV-02/03`, `SEC-01` partial/not accepted می‌مانند؛ `PWA-01=PROPOSED/NOT_RUN`, release=`NO-GO`. PR #30 را merge نکن؛ بعد از اتمام این برش، scope ممیزی MEM-03 تغییر شماره/OTP را شروع کن.

## Snapshot قبلی — MEM-01 / برش حساب عضو (reference date: 2026-11-23 UTC; پیش از live-identity follow-up)

- **Branch/source:** فقط `arena/5e0f64cf-mp`. Source/test/live-contract اجرا روی baseline `5828c94c9d875fa5a4c58740611bf800324649f8` انجام شد؛ MEM-01 دقیقاً با allowlist ۴۰ فایلی commit شد: `a7aa5b715de3da021934152b75e17ef67f6f19a5`. Stage-slice helper و allowlists با `cdc989b198737e1d2235eaf570fb023e9306e264`؛ status update `e06a71659517f2ee222be674ab2be7a8fd368c9a`؛ map/diagnostics `1afab65839b325b6a2013443f4d211f899e58c87`؛ و final state record `7833508b2c8dde4d7cb3f86754af71aa6d47815c` push شدند. Remote API تأیید کرد که 7833508 branch head است؛ مسیر `evidence/2026-11-23/MEM-01` روی remote موجود است (۱۵ entry). ۶۰ staged path نامرتبط پس از commit باقی ماندند. هیچ receipt/private یا untracked نامرتبطی باز، copy، پاک یا stage نشده است.
- **Git status (مسیرها عمداً حذف):** MEM-01، helper و interaction-map/CI diagnostics با allowlist‌های دقیق commit/push شدند. اکنون فقط **۶۰ مسیر staged نامرتبط** از قبل باقی‌اند؛ از allowlistها چیزی staged نمانده (`INDEX_ALLOWLISTED_COUNT=0`), **۰ tracked unstaged path**, `PENDING_PUSH=no`. Untracked/receiptهای نامرتبط بررسی یا دست‌کاری نشده‌اند.
- **Mode investigation:** `scripts/crosswalk_v2.py` دارای shebang است اما repo و راهنمایش آن را با `python3` اجرا می‌کنند و هیچ مصرف مستقیم executable پیدا نشد؛ tracked baseline=`100644`. mode ناخواستهٔ `100755` بدون تغییر محتوای کد به `100644` برگشت داده شد و همان مسیر allowlist‌شده دوباره stage شد. `git diff --cached --summary` دیگر mode change نشان نمی‌دهد.
- **MEM-01/PWA-30:** همچنان `PARTIAL/NOT_ACCEPTED`; canonical checkbox باز. `/member` shell راست‌چین است، deep link/history و آزمون‌های OTP/session/logout و staff denial دارد. در این follow-up صفحهٔ خانه به `GET /members/me` واقعی در source وصل شده؛ پروفایل معتبر عضو را می‌خواند و سپس تاریخچه را با `Member.id` دریافتی از سرور درخواست می‌کند. `/member/today` هنوز placeholder صادقانه است؛ هیچ برنامه/تمرین ساختگی نشان داده نمی‌شود.
- **برش حساب / MEM-02 / PWA-31:** implementation و local tests برای profile + membership-history ثبت شده و `PARTIAL/NOT_ACCEPTED` است؛ canonical checkbox باز می‌ماند. UI role/ID را fail-closed می‌کند، loading/error/retry/empty و timezone را نشان می‌دهد؛ API server-side همچنان ownership را بررسی می‌کند. Studio component/App tests از stubbed fetch استفاده کردند؛ backend SQLite/TestClient آزمون جداگانهٔ synthetic است، نه اجرای زندهٔ UI→backend.
- **Tests/build:** focused Studio rerun **۵ فایل/۳۳ تست passed** (`evidence/2026-11-27/MEM-01/studio-focused-tests.txt`); backend TestClient ownership/whoami rerun **۹ passed، ۱ Starlette/httpx warning** (`backend-focused-tests.txt`). Existing live-contract test against local API + synthetic SQLite **۱ file / ۹ passed, 0 failed/skipped** (`live-contract.raw.txt`, exit code log). `scripts/test_stage_slice.py`: **5 passed**; `py_compile` and Ruff passed (`stage-slice-tests.txt`). Older full Studio result: **۵۴ فایل passed، ۲ skipped؛ ۳۷۹ passed، ۱۰ skipped**؛ Vite build/typecheck PASS، 4048 modules؛ selected ESLint/Ruff passed. JSDOM `getComputedStyle`, React `act`, Recharts and Starlette/httpx warnings remain in their respective runs; skips are not passes. Current provenance: [`2026-11-27 run`](../../evidence/2026-11-27/MEM-01/current-run.md).
- **Browser / acceptance limits:** `BROWSER_AVAILABLE=no — libnspr4.so/libnss3.so missing (apt/npm verified)`؛ در این follow-up مرورگر/device/headless اجرا نشد. جایگزین مورد توافق، live-contract موجود در CI علیه API محلی و backend TestClient است. Live-contract با SQLite/fixtures مصنوعی **۹/۹ پاس** شد، اما مسیر حساب جدید `/members/me` → `/members/{Member.id}/memberships` را مستقیماً از UI اجرا نمی‌کند؛ آزمون مالکیت backend همچنان TestClient/SQLite synthetic است. SMS/OTP واقعی، Android/OS/device، screen reader/manual review، reviewer و release gates اجرا نشده‌اند.
- **وضعیت‌های مستقل:** `INV-02/03=PARTIAL/NOT_ACCEPTED`, `SEC-01=PARTIAL/NOT_ACCEPTED`, `PWA-01=PROPOSED/NOT_RUN`, release=`NO-GO`. Canonical PWA-30/31 فقط `PARTIAL/NOT_ACCEPTED` هستند؛ checkboxها باز. آخرین pushed status commit=`7833508b2c8dde4d7cb3f86754af71aa6d47815c`; GitHub API آن را branch head تأیید کرد. Check run قبلی e06a716 ابتدا backend و docs را fail کرد؛ پس از map refresh، `gh pr checks 30 --watch --interval 10` روی 7833508 exit 0 داد و تمام jobهای اصلی/supplemental پاس شدند، از جمله backend/docs/live-contract/e2e-api. شواهد: [`e06 failure`](../../evidence/2026-11-27/MEM-01/pr30-checks-e06a716.txt) و [`7833508 PASS`](../../evidence/2026-11-27/MEM-01/pr30-checks-7833508.txt). CI log download برای failure قدیمی EOF داد؛ local map/backend reproductions پاس‌اند و جزئیات در evidence است. Docs gate پس از final evidence update برابر ۳۸ Markdown/۶۰۹ لینک/۱۵ Mermaid پاس است؛ `PENDING_PUSH=no`, index 60 مسیر نامرتبط دارد. PR #30 draft بماند و merge نشود. سپس طبق ترتیب `MEM-02…MEM-16` و `STAFF-01` ادامه بده، بدون تأیید روتین و بدون ادعای پذیرش.

## Snapshot تاریخی — continuation پذیرش SEC-01 / WEB / crosswalk

- **Branch/source:** فقط `arena/5e0f64cf-mp`. سر اجرای browser/tests، HEAD=`5828c94c9d875fa5a4c58740611bf800324649f8`; build و browser حقیقی headless بودند، ولی working tree حاوی تغییرهای crosswalk/test و untrackedهای قبلی بود. هیچ private receipt یا untracked قدیمی stage/overwrite نشود.
- **CODE_OR_TEST_CHANGED_THIS_CYCLE=yes; LOOP_STALLED=no.** تغییرها: `scripts/crosswalk_v2.py`, `scripts/test_crosswalk_v2.py`, `mp-app/backend/tests/integration/test_ownership.py`, `test_phase5_admin_permissions.py`, `test_qf10_period_report.py`. Ruff این فایل‌ها PASS؛ unit crosswalk `4 passed`; SEC slice `26 passed`; Studio Vitest full `362 passed / 10 skipped`, build PASS (Vite 5.4.21, 4046 modules). هشدارها/skips در گزارش‌ها هستند، pass تلقی نمی‌شوند.
- **WEB browser:** `BROWSER_AVAILABLE=yes` برای Chromium headless 153.0.8010.0 / Playwright Core 1.65.1؛ `WEB_CHECKED_BY_BROWSER=WEB-02…11`. هر شناسه فایل جداگانه دارد زیر `evidence/2026-11-27/WEB-xx/`. نتایج مهم: WEB-03/05 موبایل overflow 569px در viewport 390px؛ WEB-04 axe violations صفر ولی contrast با severity serious incomplete؛ WEB-09 cache هیچ `/api`/fixture خصوصی نداشت و logout توکن‌ها را پاک کرد؛ WEB-10 same-URL worker در waiting و update button، کلیک activate/reload را انجام داد؛ WEB-11 SPA fallback 200 بود اما API proxy با `ECONNREFUSED 127.0.0.1:8000` به `500 text/plain` رسید. Roll-up: `evidence/2026-11-27/WEB-browser-run-summary.md`; raw `browser-run.log` و `studio-build.txt`.
- **SEC-01:** synthetic fixtureها؛ exact A→B `403`, A→A `200`, anonymous حساس `401`, expired/revoked `finance.read` در `/finance/reports/period`=`403 permission_required`, grant فعال=`200`. فقط 26 تست focused، نه full suite یا matrix route×role کامل. `evidence/2026-11-27/SEC-01/current-run.md` و log خام `pytest-focused.txt`.
- **INV v2/v3 same Git HEAD:** v2 member `16 PARTIAL_REVIEW/1 GAP`, staff `12 PARTIAL_REVIEW`, 82 API call sites / 24 dynamic / 0 unmatched dynamic; page imports stats: member/staff/shared records `1/12/2`, edges `0/69/6`, ratios `0.0/5.75/3.0`. v3 member `13/4`, staff `11/1`; comparison in `evidence/2026-11-27/CROSSWALK-v2-v3-comparison.md`. `DYNAMIC_UNCOVERED` exercised by synthetic regression test, none found in scanned product paths.
- **Status/guardrails:** `PWA-01=PROPOSED/NOT_RUN`; SEC-01 and INV-02/03 partial/non-accepted; release=`NO-GO`; PR #30 must not merge. Commit/push for this current batch are still to be recorded; do not switch branch or merge. After this handoff, continue requested MEM-01…16 (then STAFF-01) without routine confirmation.

## Snapshot تاریخی — ادامهٔ پیشین PWA: crosswalk v2 و SEC-01

- **شاخه/remote:** شاخهٔ مجاز `arena/5e0f64cf-mp` فعال است؛ `origin/main=352781043ad2ba202d8b3b459df1ce7e3d914ef7`. merge عادی origin/main روی شاخه `Already up to date` بود و conflict نداشت. STATE checkpoint `f06f2a95305082e01e33b157396f0dfc0128613d` و evidence package `6593cb4bc7f42c9ada4ca7e499fe60124bf00703` روی همان شاخه push شدند. commit اصلاح CI=`3e49232d2118e8212a4d1ddea20fc982da5cd13a` نیز روی remote است؛ هیچ rebase، force-push یا branch switch انجام نشد. PR #30 draft باز است؛ CI نهاییِ همین SHA سبز است و ادغام نشده.
- **INV-02/03 v2:** `scripts/crosswalk_v2.py` از ref `arena/c1fb460b-chat2db` (source commit `155a18b8ff01578d957d9315f88afbf3a8950ef5`) روی target `f06f2a95305082e01e33b157396f0dfc0128613d` اجرا شد. member=`14 PARTIAL_REVIEW / 3 GAP`; staff=`12 PARTIAL_REVIEW / 0 GAP`, برابر شمارش مرجع. v1 byte-for-byte در `evidence/2026-11-27/INV-02-v1/` و `INV-03-v1/` نگه داشته شده است. v2 `${base}` analytics و alias `ALL_STAFF` را نشان می‌دهد، اما `dynamic_sites=0` و `DYNAMIC_UNCOVERED` صادر نشده؛ reviewها خطای detector و scope اسکنر TS را شفاف می‌کنند. rawهای generator دستی patch نشده‌اند.
- **محدودیت و پذیرش:** dynamic templates در `api.ts` هنوز ممکن است جا بیفتند؛ check-in واقعی در Flutter/Dart است و از اسکنر Studio خارج است. تفکیک call-site پنل کارکنان از مصرف عضو manual است. هر دو crosswalk `PARTIAL/NOT_ACCEPTED` می‌مانند؛ permission/ownership اثبات نشده؛ checkboxها باز و `PWA-01=PROPOSED/NOT_RUN` است.
- **SEC-01:** ماتریس static [`978` تصمیم](../../evidence/2026-11-27/SEC-01/rbac-matrix.txt) همهٔ `163` operation / `141` path در manifest را با هر شش نقش از `security.rbac.enforce` سنجید. سه TestClient integration test واقعی، عضو A→B را در members/assessments/payments/chat/checkin بررسی کرد: `3 passed / 0 failed`. کل `pytest -q` در backend روی همان `claimed_sha=tested_sha=f06f2a95305082e01e33b157396f0dfc0128613d` اجرا شد: `1336 passed, 2 skipped, 2 warnings`, exit `0`. ماتریس static، grant/anonymous/ownership یا پاسخ API روی همهٔ خانه‌ها را ثابت نمی‌کند؛ SEC-01 حداکثر `PARTIAL` و checkbox باز است.
- **گاردریل/اثر محصول:** هیچ tracked product source، role, grant, API, DB، Flutter/native workflow یا authorization policy محصول تغییر نکرد. تغییرات فقط به exceptionهای دقیق secret-scan برای پنج source digest تأییدشده، assertion تست آن‌ها، هم‌ترازسازی artifact مستنداتی PWA-00 و docs/evidence محدودند. untracked assets/receipts قدیمی دست‌نخورده و unstaged می‌مانند؛ PWA acceptance بالا نرفته و release=`NO-GO` است.
- **گیت مستندات و PR:** `python3 scripts/docs_gate.py` PASS شد: ۳۸ Markdown، ۶۰۶ لینک محلی و ۱۵ Mermaid. CI اولیهٔ PR #30 روی `6593cb4...` `10 pass/2 fail` بود؛ پنج Gitleaks match دقیقاً source SHA-256های JSON بودند (استثنای محدود + test assertion افزوده شد) و PWA-00 patch با دو backlink DOC-05 در source همگام شد. روی fix SHA=`3e49232d2118e8212a4d1ddea20fc982da5cd13a`, `gh pr checks 30` برابر `12 pass/0 fail/0 pending` است: `mp-ci` pull_request run `45998409658`، push run `45998396424`، `pwa00-doc-quality` run `45998409713`; هر دو step شکست‌خوردهٔ قبلی اکنون PASS هستند. خلاصه و حدود بررسی در `evidence/2026-11-27/SEC-01/pr-30-checks-review.md` و check log در `pr-30-checks-3e49232.txt`. PR هنوز draft/open و merged نشده. پس از CI مرور ترتیبی `WEB-01…WEB-11` انجام شد، اما همه فقط `PARTIAL/NOT_ACCEPTED` و checkboxها بازند: مرز runtime در `evidence/2026-11-27/WEB-01/`, route/deep link در `WEB-02/`, test-map و gapهای WEB-03…11 در `WEB-03-11/queue-review.md`. Electron/browser/Nginx واقعی، browser/OS/device و reviewer غایب `BLOCKED/NOT_RUN`؛ member shell placeholder، `PWA-01=PROPOSED/NOT_RUN`, release=`NO-GO` باقی می‌مانند.

## Snapshot پیشین — baseline اجرای مستنداتی PWA (مرجع: ۲۰۲۶-۱۱-۲۳؛ ثبت‌شده پیش از checkpoint `a3fbf01`)

- **شاخه و فایل‌های محلی — rebaseline ۲۰۲۶-۱۱-۲۳ UTC:** فقط روی `arena/5e0f64cf-mp`؛ `HEAD=e0ae95f48bf8451bd59b972a92c55fed404e6a92`, `origin/arena=3f26e1d6ea05920a23236b368abd4c4ee0580799`, `origin/main=352781043ad2ba202d8b3b459df1ce7e3d914ef7`. HEAD در remote نیست، ولی هر دو parent remote و tree آن با `origin/main` برابر است؛ ۲۴ tracked تغییر README/docs، index خالی، ۳۰۹ untracked پیش از snapshot تازه، صفر tracked product diff. شاهد aggregate پالایش‌شده: `evidence/2026-11-23/INV-01/current-snapshot.txt`; مسیرهای untracked/private/receipt عمداً افشا یا دست‌کاری نشدند. چرخهٔ STATE از صفر revalidation شد: `INV-01` snapshot تازه؛ `DOC-05` docs/Mermaid gates تازه؛ `DOC-06` tests/Ruff تازه؛ `INV-02/03` static reruns تازه. ردیف‌های crosswalk همچنان partial و non-accepted؛ بقیهٔ نتیجه‌های پیشین فقط history محلی‌اند تا gate خودشان دوباره اجرا شود.
- **DOC-05/06 — revalidation چرخهٔ صفر:** مرجع scope و checkboxها [tracker اجرایی](TODO-PWA-RELEASE-2026-11-23.fa.md)، [backlog canonical](TODO-2026-11-16.md#pwa-ui-ux-full-backlog-2026-11-23)، [ADR-007](adr/007-pwa-primary-release.md) و [دفتر اجرا](PWA-EXECUTION-STATE.md) است؛ checkboxها در این چرخه تغییر نکردند. آخرین DOC-05 rerun پس از ویرایش اسناد در 2026-11-27 UTC در `evidence/2026-11-23/DOC-05/docs-gates-reset-rerun.txt`: traceability ۲۴ سند، docs gate ۳۸ Markdown/۶۰۵ لینک/۱۵ Mermaid، guide/map/hygiene/diff PASS؛ Mermaid parser `11.17.2`، ۲۷/۲۷ PASS. DOC-06 در `evidence/2026-11-23/DOC-06/current-cycle-backend-revalidation.txt`: ۳۴ synthetic integration test PASS/۱ warning؛ Ruff check ۹ finding و exit=1، format PASS. هیچ policy یا approval حساس حل نشد؛ این شواهد acceptance/release محصول نیستند.
- **INV-01 و CI:** snapshot تازهٔ sanitized در `evidence/2026-11-23/INV-01/current-snapshot.txt`: ۲۴ tracked docs changes، index خالی، ۳۰۹ untracked پیش از self-record، product-source diff صفر. HEAD محلی در remote branch ref نیست، هر دو parent remote و tree عین `origin/main` است؛ هیچ branch/ref operation انجام نشد. `gh 2.23.0` `gh run list --commit` را نمی‌شناسد؛ فهرست ۱۰۰ run branch با filter دقیق `.headSha==e0ae95f…` خالی بود، workflow dispatch نشد. raw: `ci-current-sha-query.txt`; بعد از push روی SHA نهایی باید `gh pr checks`/`gh run list` تکرار شوند.
- **Baseline بیرونی/محصول:** PR #29 از قبل `MERGED` است؛ تکرار ادغام ممنوع. `PWA-04`, `PWA-11`, `PWA-17` همچنان `PARTIAL` و release `NO-GO`. در این چرخهٔ محلی روی `HEAD=e0ae95f…`، `mp-app/studio`: `npm ci`, lint, build PASS؛ Vitest **۵۲ فایل PASS/۲ SKIP؛ ۳۶۲ تست PASS/۱۰ SKIP**، warnings `act`/JSDOM/Recharts باقی‌اند؛ npm audit چهار advisory گزارش داد و fix اعمال نشد. Flutter/Dart، Playwright و browser binary نیست؛ browser/device، independent review، SMS واقعی، TLS/staging و artifact/container رسمی هنوز `NOT_RUN/BLOCKED`. tracker اکنون ۱۰۴ checkbox دارد: ۹۷ باز، ۷ checked.
- **وضعیت/ترتیب بعدی:** `INV-02` و `INV-03` از ابتدا در چرخهٔ صفر دوباره scan شدند؛ هر دو همچنان `PARTIAL / NOT_ACCEPTED`. v3 عضو همان ۱۷ directory/۶۰ literal API match را یافت؛ Studio build/lint/full Vitest PASS با skips/warnings ثبت‌شده، ولی `/member` placeholder است و Flutter/browser/reviewer gates بازند. Staff rerun: ۱۲ page، ۵۹ endpoint shape، ۳۱/۱۶۳ map، state field ندارد و `members`/`analytics` test ref ندارند. `PWA-01=PROPOSED/NOT_RUN`, checkboxes باز. `INV-04` یک برش ساختاری عضو (۲۱ ردیف statusدار)، `INV-05` یک slice Dashboard KPI/fallback (۱/۳ test PASS، warnings) و `INV-06` یک mapping actor/data/route با ۳۴ integration tests PASS/۲ warnings (rerun: 2026-11-27 UTC) در evidence ثبت کردند؛ هر سه کل کارت بازند. component بی‌شرط KPI را fetch می‌کند؛ اگر Dashboard برای coach/reception render شود، manifest route آنان را مجاز نمی‌داند و API باید fail-closed شود؛ page reachability و UI error از مسیر E2E تأیید نشده و policy/grant تغییر نکرد. گام مستقل بعدی `INV-07` ثبت command/tool/version/count/CI per-job روی SHA دقیق است؛ release `NO-GO`.

وضعیت محلی پالایش‌شدهٔ پس از این برش: `evidence/2026-11-23/INV-06/local-state-sanitized.txt` (مشاهدهٔ 2026-11-27 UTC): branch `arena/5e0f64cf-mp`, HEAD `e0ae95f48bf8451bd59b972a92c55fed404e6a92`, index=0 staged، ۲۴ tracked worktree changes، ۳۲۲ untracked path entries (۱۱۷ زیر `mp-app`; نام‌ها عمداً حذف و محتوایشان بررسی‌نشده)، tracked product-source diff=0. چون محتوای untrackedها معلوم نیست، این snapshot و تست‌ها اثبات candidate پاک یا source بی‌تغییر نیستند؛ stage/commit انجام نشد و HEAD عوض نشد. raw پالایش‌شده در `evidence/2026-11-23/<ID>/`; secret/PII/receipt وارد نشود.


## Snapshot آزمون محلی پیشین — PR #29 ادغام‌شده و smoke اجرایی Nginx (تاریخ مرجع: ۲۰۲۶-۱۱-۲۳)

- **PR #29:** https://github.com/yousefghorbanian98-create/MP/pull/29 — query زندهٔ GitHub وضعیت `MERGED`، head=`3f26e1d6ea05920a23236b368abd4c4ee0580799` و merge commit=`352781043ad2ba202d8b3b459df1ce7e3d914ef7` را برگرداند. هر ۸ check لازم در `mp-ci` run `45917926298` پاس‌اند؛ run `pwa00-doc-quality` با `45917926363` نیز موفق است (هر دو `headSha=3f26e1d6ea05920a23236b368abd4c4ee0580799`). ادغام تکراری انجام نده. GitHub زمان `mergedAt=2026-11-27T04:36:20Z` را گزارش می‌کند که از تاریخ مرجع این handoff (۲۰۲۶-۱۱-۲۳ UTC) جلوتر است؛ دو run CI نیز `createdAt=2026-11-27T00:38:45Z` دارند. ناسازگاری زمانی حل نشده؛ status و merge commit در پاسخ زنده صریح‌اند، اما تاریخ‌ها را با زمان مرجع جابه‌جا نکن.
- **شاخه و همگام‌سازی:** شاخهٔ فعال `arena/5e0f64cf-mp`، `origin/main=352781043ad2ba202d8b3b459df1ce7e3d914ef7` و `HEAD=e0ae95f48bf8451bd59b972a92c55fed404e6a92` است. `git merge --no-edit origin/main` عادی انجام شد؛ هنگام sync tree با `origin/main` برابر و tracked worktree پاک بود. اکنون سه سند handoff/TODO همین ارزیابی tracked-modified هستند؛ merge محلی push نشده. ۲۷۴ مسیر untracked پیشین، از جمله receiptها، دست‌نخورده‌اند؛ smoke script یک فایل untracked تازه افزوده و شمار فعلی ۲۷۵ است. هیچ stage/cleanup انجام نده.
- **Nginx runtime محلی:** سورس upstream Nginx `release-1.27.5` در commit `6ac8b69f06bc10d5503f636da888fa70095b151c` و zlib `v1.3.1` در commit `51b7f2abdade71cd9bb0e7a373ef2610ec6f9daf` فقط در `/tmp` دریافت و build شدند؛ پیکربندی build: `--with-http_realip_module --with-zlib=<pinned-zlib> --without-http_rewrite_module`, سپس `make -j2`; پس از آزمون scratch پاک شد. `scripts/verify_studio_nginx_runtime.py --nginx-bin <nginx-1.27.5>/objs/nginx` و `nginx -t` هر دو PASS. runtime واقعی روی template فعلی `mp-app/studio/nginx.conf` در دو حالت PASS شد: HTML fixture و `--static-root mp-app/studio/dist --mime-types <همان nginx-src>/conf/mime.types`. exact `/api` و `/api/*`، status/content-type و 404، direct `/staff/members` به shell build واقعی، سرو JS/CSS هش‌شده با MIME table upstream همان نسخه، مرز `/apix` و `/apiary`، POST، و trusted/untrusted `X-Forwarded-For` با backend ساختگی و peerهای loopback سنجیده شدند.
- **دامنهٔ شاهد:** این smoke یک باینری واقعی Nginx با server block برگرفته از config پروژه است؛ port، root، upstream و trusted peer در فایل موقت جایگزین شدند. در اجرای دوم، shell و assetهای واقعی `dist` سرو شدند، اما browser اجرا/refresh/hydration نشد. آن را معادل image رسمی `nginx:1.27-alpine`، Docker/container، upstream واقعی backend، TLS، staging یا device نخوان. CI هم برای فایل smoke جدید اجرا نشده است.
- **اعتبارسنجی محلی پس از sync:** Studio را تازه روی همین شاخه آزمودم: `npm test -- --reporter=dot` ⇒ ۵۲ فایل PASS، ۲ SKIP؛ ۳۶۲ تست PASS، ۱۰ SKIP؛ `npm run lint` PASS؛ `npm run build` (شامل `tsc -b`) PASS با ۴٬۰۴۶ ماژول. هشدارهای شناخته‌شدهٔ jsdom (`getComputedStyle(..., pseudoElt)`) و React `act(...)` دیده شدند؛ skip/warning PASS نیستند. از `mp-app/backend/` با Python 3.11 در venv موقت، `python -m pytest tests/regression/test_production_ops.py tests/integration/test_deploy_gate_branches.py -q` ⇒ ۵۱ PASS، یک Starlette/httpx deprecation warning؛ این آزمون YAML/Compose/trusted-proxy invariants را ایستا می‌سنجد، نه container runtime. `ruff check`, `ruff format --check` و `python3 -m py_compile` برای smoke script نیز PASS شدند. گیت اسناد: `docs_gate.py` با ۳۸ Markdown/۵۴۷ لینک محلی/۱۵ Mermaid، project-guide `--check`، interaction-map با ۳۱ سطح/۱۶۳ مسیر/رانش صفر و `git diff --check` PASS. همه local هستند؛ CI تازه‌ای برای script/docs حاضر اجرا نشده.
- **دامنهٔ source:** smoke Nginx و آزمون‌های Studio روی tree هم‌تراز با merge main بودند؛ در این مرحله هیچ فایل محصولی تغییر نکرد. خروجی build/`node_modules` ابزارهای محلی‌اند و release artifact یا پذیرش device محسوب نمی‌شوند.
- **مرز release:** `NO-GO` باقی است. `PWA-04` هنوز `PARTIAL` است (baseline CI/tree یکسان و Studio re-run ثبت شد، اما per-job inventory کامل نیست)؛ `PWA-17` هم `PARTIAL` می‌ماند تا image/container، backend/TLS/staging و browser reload/hydration روی build واقعی سنجیده شوند. browser/device acceptance، review مستقل، SMS واقعی، داده/secret production، deploy/rollback و سرویس واقعی انجام نشده‌اند؛ گیت‌های وابسته به owner، reviewer، دستگاه یا محیط واقعی باز می‌مانند.

## Snapshot پیشین — Motion crosswalk، baseline PWA و شواهد browser emulation

> این snapshot پیش از پیگیری محلی PWA ثبت شده است؛ branch/SHA و آزمون‌های آن به همان زمان محدودند و به وضعیت جاری بالای این handoff تعمیم داده نشوند. محتوای تاریخی Motion حفظ شده تا evidence قبلی از بین نرود.

- **شاخه/حدود:** `arena/5e0f64cf-mp`, `HEAD=d92817f4151ebbafb25425b7b28776a4cc1180dc`; worktree dirty، stage صفر. diffهای نامرتبط و receiptهای private دست‌نخورده‌اند. در این کار stage/commit/push/PR/merge/release/deploy انجام نشد.
- **تصمیم محصول ثبت‌شده، نه بازبینی دوباره:** OQ-01/ADR-007، PWA مشترک React برای عضو و کادر را baseline انتشار اول ثبت می‌کند؛ Flutter/Android حفظ می‌شوند. در این پیگیری OQ-01 دوباره بازبینی/تصویب نشد. این baseline خودش مجوز انتشار یا پذیرش محصول نیست. مرجع: [ADR-007](adr/007-pwa-primary-release.md)، [پرسش‌نامه](architecture/owner-decision-questionnaire-2026-11-23.fa.md)، [دفتر تصمیم](architecture/session-decisions-2026-11-23/DECISION-LOG.md)، [TODO و backlog کامل](TODO-2026-11-16.md#pwa-ui-ux-full-backlog-2026-11-23).
- **Canonical PWA baseline:** ۵۰ parent/شناسه و acceptance/dependencyها حفظ شده‌اند؛ وضعیت منبع ۴۹ `PROPOSED` و یک `BLOCKED` (`PWA-3F`) است و evidence منبع ۵۰ `NOT_RUN`. overlay محلی: `PWA-00 DONE` فقط ثبت تصمیم؛ `PWA-04 PARTIAL`؛ ۴۷ parent `PROPOSED/NOT_RUN`؛ `PWA-3F BLOCKED/NOT_RUN`. شمارش/status acceptance یا release gate ارتقا نیافته است.
- **Motion crosswalk + follow-up:** inventory و hashهای اولیه فقط به snapshot پیش از patch محدود معتبرند؛ [crosswalk](architecture/studio-motion-current-tree-static-crosswalk-2026-11-23.fa.md) baseline، delta، شواهد و manifest نهایی را جدا ثبت می‌کند. Runtime اصلی و lab مستقل VisualConcepts اکنون به `useMotionPreset` وصل‌اند؛ در lab، نشانگر `active-direction` هنگام reduced `layoutId` ندارد و spring با duration صفر خاموش می‌شود. Browser synthetic روی lab با Playwright/Chromium headless **۱۳/۱۳ assertion PASS** داد؛ سپس route اصلی Studio/CheckIn با fixture/token/API کاملاً ساختگی **۱۰/۱۰ assertion PASS** گرفت، شامل tab traversal، scan static/motion behavior، تغییر زندهٔ preference در دو جهت با حفظ focus/state/node و fallback با `matchMedia` غایب. [Screenshot reduced](../../artifacts/motion-availability-qa-2026-11-23/studio-checkin-reduced.png) پالایش‌شده است؛ هر دو اجرا preference را browser-emulated کردند، نه OS. [ماتریس دسترسی + Codespace/device handoff](architecture/motion-pwa-availability-matrix-2026-11-23.fa.md) فهرست کارهای همین sandbox را از review/device/OS/AT/CI/owner gates جدا می‌کند. `MK-PWA-01-FU-01`، `MK-PWA-02` و `O3-08` همچنان `PARTIAL` هستند؛ independent G9 review، OS/device واقعی، screen reader و پذیرش کامل routeهای محصول بازند.
- **CSS/reduced-motion:** `Skeleton` pulse، pulse سایدبار، CSS/Tailwind animations/transitions/scroll و active/group-hover scale guards زیر `prefers-reduced-motion` بررسی/اصلاح شدند؛ دو نمودار Recharts نیز سری/Tooltip animation را خاموش می‌کنند. CSS مستقل VisualConcepts delayها را صفر و hover transform جهت را خاموش می‌کند. Build استاندارد فقط `dist/index.html` می‌دهد؛ build ایزوله با همان Vite config و ورودی lab به temp خارج مخزن نیز موفق شد (۳۳۸۹ module). CSS bundle مستقل (۳۴٬۵۱۱ بایت) در چک ایستای رشته‌ای media query، delayها و hover override را داشت؛ جدا از آن، headless Chromium computed style و رفتار همان entrypoint lab را واقعاً آزمود. این evidence، OS/device QA یا آزمون routeهای اصلی product/PWA نیست.
- **Hashهای VisualConcepts lab/test پس از patch:** `VisualConcepts.tsx`=`e26bf943e62ba85bd727455c17ff1f65fef8832aae8390c10935a4d8dfa7ed6e`; `visual-concepts.css`=`b23f25acdc682728dba9adc6df04c94d67be7e9c52214132bdd1eed930a6863d`; `README.md`=`6d654f25b20ceb4263a4ba7aa7dcdd6bedd88ec6e348b710c0083642691f426b`; `tests/motion.test.tsx`=`3153333649368c7943a3a133fc771719827b33e3f5e5ceb1a74b66649d3992da`. فهرست کامل follow-up و fingerprint در [crosswalk](architecture/studio-motion-current-tree-static-crosswalk-2026-11-23.fa.md) است.
- **گیت‌های Studio:** آخرین targeted: `npm test -- --reporter=dot tests/motion.test.tsx tests/checkInPage.test.tsx` → ۲ فایل، ۳۴/۳۴ PASS؛ آخرین full `npm test -- --reporter=dot`: ۵۰ فایل PASS/۲ SKIP و ۳۴۵ PASS/۱۰ SKIP، صفر fail. `npm run lint` و `npm run build` exit 0؛ Vite 5.4.21/۴۰۴۵ module. JSDOM `getComputedStyle`, React `act(...)` و Recharts width/height صفر warnings باقی‌اند؛ skipها PASS نیستند. همه روی dirty worktree‌اند، نه CI یا SHA تمیز.
- **Chronology:** تاریخ مورد اعتماد Arena `2026-11-23 UTC` است؛ `date -u` پیشین sandbox `2026-11-26T07:48:04Z` داد و با مرجع ناسازگار بود. آخرین full test ساعت `10:13:52` را چاپ کرد اما تاریخ قابل‌اعتماد تازه ندارد؛ wall-clock اجرای ابزارها `CHRONOLOGY_UNKNOWN` بماند. discrepancy merge/package تاریخی نیز باز است.
- **گیت‌های باز:** CI تازه روی همان dirty source هنوز اجرا نشده؛ browser synthetic روی CheckIn فقط یک route/fixture است، نه E2E کامل member/staff. Browser/OS/device فیزیکی و screen reader، PWA install/service-worker/offline/update، API/security/privacy/finance/legal/medical independent review و release Go/No-Go بازند. هیچ‌کدام با lab/headless/browser-emulation/build/unit test بسته نمی‌شوند. فایل‌های receipt خصوصی باز/کپی/در docs درج نشوند.
- **Docs gate/diff و fingerprint:** `python3 scripts/docs_gate.py` روی workspace کامل: PASS، **۲۲ Markdown، ۳۱۵ لینک محلی، ۱۲ Mermaid**؛ روی PR tree شبیه‌سازی‌شده با crosswalk اصلاح‌شده: **۲۲/۲۹۷/۱۲**؛ `git diff --check` exit 0. Git fresh بعد از commit handoff: ۵۸ مسیر tracked تغییرکرده، ۲۶۰ untracked در `git status --porcelain=v1 -uall` (۷۰ receipt خصوصی، ۱۹۰ دیگر)، stage صفر؛ ۱۵۷ مورد زیر `artifacts/`. بخش عمدهٔ untracked artifact از reference/extraction قبلی است و در بستهٔ این کار نیست. Studio tracked-diff SHA-256=`bdedaf8b6ca38dd5a19846017ad2a49ce50f1d4b5c9b0d7874608e1a1aba2aab`؛ ۹ فایل untracked Studio، content-manifest SHA-256=`18665cb8b0f84ee570ff3040f89c073397a00245c90d7f705e96f69bb0f8f2fa`. شاهد کامل و دو فهرست دسترسی در [TODO](TODO-2026-11-16.md#motion-current-tree-static-scan-session) و [ماتریس handoff](architecture/motion-pwa-availability-matrix-2026-11-23.fa.md) هستند.
- **گام بعدی:** در [ماتریس handoff](architecture/motion-pwa-availability-matrix-2026-11-23.fa.md) فهرست Codespace را دنبال کن؛ Codespace/CI فقط پس از انتقال allowlist همان source و تأیید SHA می‌تواند همان tree را اجرا کند و روی branch remote فعلی، diff محلی حاضر نیست. reviewer مستقل/G9 و target browser/OS/device فیزیکی و screen reader باید جداگانه انجام شوند. screenshot synthetic CheckIn ثبت شده، اما multi-device visual QA و full-route E2E انجام نشده‌اند. statusها را `PARTIAL/UNKNOWN` نگه‌دار؛ هیچ baseline یا release gate با این evidence بسته نمی‌شود.

## سابقهٔ پیشین — تأیید merge و MK-PWA-01 (۲۰۲۶-۱۱-۲۳)

- **merge commitها:** GitHub PR [#25](https://github.com/yousefghorbanian98-create/MP/pull/25) `MERGED`؛ head=`b8db8f248606a7dbadd984e123f2d2d65a1d0e1e`، merge commit=`3a4f38ce84c9d5957ca5833b0ba597987159a190`، ref زندهٔ `main` همان merge commit است و والد دوم merge همان head branch است؛ ۱۳ check نمایش‌داده‌شده pass. اما worktree حاضر dirty و index خالی است؛ diff/untrackedهای محلی، از جمله همین دو کار Motion Kit، بخشی از PR نیستند. GitHub زمان merge را ۲۰۲۶-۱۱-۲۵ ثبت کرده (آینده نسبت به تاریخ نشست ۲۰۲۶-۱۱-۲۳)؛ hash/parentها merge را تأیید می‌کنند، ناسازگاری زمان را در گزارش حفظ کن.
- **MK-PWA-01 read-only** کامل شد؛ [گزارش crosswalk، line/hashها و GAP/UNKNOWNها](architecture/studio-motion-mk-pwa-01-inventory-2026-11-23.fa.md)، progress به‌صورت افزایشی در [TODO](TODO-2026-11-16.md) ثبت شد. `useReducedMotion() ?? false`، raw motion بیرون از helper، delayهای مستقیم و نبود guard در CSS/Tailwind یافته‌اند؛ form/focus/live toggle و browser/device behavior هنوز شاهد ندارند.
- **محدودیت/گیت:** هیچ source تغییر نکرد؛ `npm test`/lint/build/browser/device اجرا نشد. `python3 scripts/docs_gate.py` → **19 Markdown، 293 لینک محلی، 12 Mermaid**؛ `git diff --check` موفق. CI سبز PR برای commit mergeشده است، نه کدهای محلی dirty. Studio fingerprint شروع: tracked diff SHA-256 `42d72c9027decf4f0f54dafcddf14a48c79db5e24c98397b67e3b7f35c110866` و status-path SHA-256 `4034f6fefe037878839f2755c65d5a621cbffba78ad638716ba402f621f8e6d3`.
- **اقدام بعدی:** contract محدود MK-PWA-02 (پیشنهاد سقف ۲ فایل: `src/lib/motion.ts` + `tests/motion.test.tsx`, بدون dependency)؛ اجرای کد تا تأیید budget عددی، allowlist، گیت‌های FINN و contract همین parent متوقف است. CSS و component motion در loopهای مستقل؛ Android هنوز آینده است.
- در این بررسی fetch/merge/checkout، stage، commit، push و deploy انجام نشد؛ هیچ فایل قبلی reset/overwrite نشد.

## افزودهٔ ادامهٔ نشست — بررسی Motion Kit v1.1.0 (۲۰۲۶-۱۱-۲۳)

- **وضعیت شاخه:** `arena/5e0f64cf-mp`، HEAD هنگام این بررسی `b8db8f248606a7dbadd984e123f2d2d65a1d0e1e`. تغییرهای محصول، receiptهای خصوصی و اسناد untracked قبلی در worktree حفظ شده‌اند؛ تغییر تازه فقط مستندات/کپی inventory است.
- **ثبت این کار:** [یادداشت فارسی ردیابی‌پذیر Motion Kit](architecture/mp-ui-ux-motion-kit-v1.1.0-review.fa.md)، [inventory دارای اندازه/خط/hash](architecture/mp-ui-ux-motion-kit-v1.1.0-inventory.tsv)، و افزودهٔ `MK-*` در [TODO مرجع](TODO-2026-11-16.md#motion-kit-v110-2026-11-23). آرشیو و extraction در `artifacts/mp-ui-ux-motion-kit-v1.1.0/` است؛ ZIP pinned v1.1.0 با SHA-256=`df95d1ba35d9a6db493fb6335e247075d7df711533df7b617348fec369df546a`؛ ۶۰ عضو، ۵۸ فایل متنی با manifest، دو WOFF2. Hash یا self-report بسته، QA محصول نیست.
- **یافتهٔ مانع:** package شامل تاریخ‌های ۲۰۲۶-۱۱-۲۴ و ۲۰۲۶-۱۱-۲۵ است که از تاریخ جاری این ثبت جلوترند؛ source/clock باید از صادرکننده روشن شود. ادعاهای آزمون/review داخل ZIP اجرا یا مستقل تأیید نشدند. هیچ script اجرا نشد و کد/وابستگی/Flutter/PWA محصول تغییر نکرد.
- **دامنه/مجوز:** `MK-PWA-*` هنوز پیشنهادند؛ نخستین مسیر مجاز بعدی، فقط پس از بررسی owner و TODO/FINN جاری، inventory read-only در `MK-PWA-01` است. `MK-ANDROID-01` فقط آینده است؛ file/toolingهای غیرمحصولی Android backlog feature نیستند.
- **گیت‌ها/اقدام بعدی:** روی این تغییر مستنداتی `python3 scripts/docs_gate.py` → **19 Markdown، 291 پیوند محلی، 12 Mermaid**؛ `git diff --check` موفق. این‌ها فقط گیت‌های مستندات/diff‌اند، نه QA محصول. کار بعدی: مرور owner و در صورت اجازه فقط `MK-PWA-01` read-only؛ در این برش commit، push، merge و deploy انجام نشده‌اند. بخش snapshot قبلی زیر و تمام محتوای آن برای حفظ زمینه دست‌نخورده باقی مانده است.

## snapshot جاری — نشست ۲۰۲۶-۱۱-۲३

- **شاخه و پایه:** `arena/5e0f64cf-mp`؛ پس از fetch غیرمخرب، HEAD محلی با `origin/arena/5e0f64cf-mp` همگام شد (`941eac4`) و فقط plan در commit `bf7701f6a4925ac8691e8de7eaf2663ff2b260e6` commit/push شد. فقط همین شاخه push شد؛ deploy انجام نشده.
- **درخواست جاری:** تدوین برنامهٔ فارسی و نسخه‌دار برای تولید محصول تا آمادگی انتشار، همراه با برنامهٔ خودمختاری عامل AI و گیت‌های شواهد؛ فعلاً فقط plan کلان، نه ساختار ۱۳ لایه یا micro-loop اجرایی.
- **سند اصلی:** [برنامهٔ کلان تولید/AI تا آمادگی انتشار](architecture/ai-autonomous-production-plan-v1-2026-11-23.md)؛ [دانلود مستقیم از GitHub](https://raw.githubusercontent.com/yousefghorbanian98-create/MP/arena/5e0f64cf-mp/docs/MuscleParadise/architecture/ai-autonomous-production-plan-v1-2026-11-23.md). شامل baseline در برابر هدف، جریان‌ها و flagهای فعلی، فازهای G0–G10، OSSهای نامزد با مرز مجوز/هزینه، autonomy levels، ریسک/تصمیم‌های باز و Go/No-Go است. همهٔ checklistهای تأیید خالی‌اند.
- **تعارض‌های بازِ ثبت‌شده:** Android عضو + Studio وب در TODO در برابر PWA هدف در فلوچارت؛ سرور محلی باشگاه + HTTPS ingress در برابر سند قدیمی Full Cloud؛ کارت‌به‌کارت انسانی/فروشگاه نمایش‌محور در برابر اشارهٔ Zarinpal؛ نقش‌های جاری در برابر target سه‌گانه؛ SQLite در برابر PostgreSQL. plan تصمیم مالک را حدس نزده است.
- **تغییرهای این کار:** plan تنها فایل commit/push‌شده است. پیوندهای Architecture Atlas، `docs/README.md` و ثبت plan در `scripts/docs_gate.py` در worktree به‌روز شده‌اند ولی commit نشده‌اند. Handoff نیز برای وضعیت جاری به‌روز شده اما commit نشده. کد محصول، dependency، workflow، زیرساخت و داده در این درخواست تغییر نکردند.
- **حفظ workspace:** پیش از این کار تغییرهای متعدد و فایل‌های untracked در شاخه وجود داشت (از جمله تحلیل/اصلاحات کد قبلی و فایل‌های private receipt)؛ دست نخورده حفظ شده‌اند. plan وضعیت مواردی را که در گزارش تحلیل «اصلاح‌شده در worktree» هستند از پذیرفته‌شدن روی commit/CI جدا می‌کند.
- **شواهد محلی همین کار:** `python3 scripts/docs_gate.py` → **19 Markdown، 322 پیوند محلی، 15 بلوک Mermaid**؛ `git diff --check` موفق. تست محصول/backend، device/E2E، image/CI، build، staging یا production در این کار اجرا نشده‌اند؛ آمادگی انتشار نتیجه‌گیری نمی‌شود.
- **مجوز/کار بعدی:** منتظر بازبینی و تأیید/اصلاح مالک روی plan بمان. فقط اگر مالک تأیید کرد، نسخهٔ بعدی را جداگانه به ساختار ۱۳ لایه و micro-loopها تبدیل کن. نصب ابزار، ایجاد task graph، تغییر کد، استفاده از inference/API بیرونی، خرید، مهاجرت واقعی، push/merge یا deploy از تأیید plan به‌تنهایی مجاز نیست.

## snapshot تاریخی — نشست ۲۰۲۶-۱۱-۱۹

- **شاخه/SHA آغاز:** `arena/a72fbc61-mp` / `28eea71776793098c05c6d3100ab69bc543c98ba`؛ workspace در شروع clean و SHA برابر `origin/main` بود. remote branch مختص این نشست هنوز ایجاد نشده بود. PRهای #3/#4/#5 در GitHub ادغام شده‌اند؛ PR4 payment lookup/QR gate و PR5 README architecture SVG در source حاضرند.
- **CI baseline همان SHA:** [run 44541693998](https://github.com/yousefghorbanian98-create/MP/actions/runs/44541693998) سبز، ۸ job شامل backend, studio, client, client-pinned/Android debug, docs, live-contract, e2e-api و secret-scan.
- **آزمون محلی baseline:** Backend **948 passed / 2 skipped**, coverage **82.95%**؛ Studio **225 passed / 9 skipped** و build موفق؛ Ruff/format موفق. Bandit محلی ۴ هشدار heuristic کم‌اهمیت داد و exit 1؛ `npm audit` چهار advisory (۳ moderate/۱ high؛ fix پیشنهادی major) دارد و خودکار اصلاح نشد. Flutter/Dart/Java/Android SDK/device در PATH نیستند؛ CI همان SHA Flutter و Android debug را سنجیده است.
- **ابزار:** REA `6.9.0` واقعاً با Node portable `24.22.3` اجرا شد: OpenAPI محلی ۱۳۷ operation و تحلیل static نُه فایل Studio؛ تحلیل جزئی است. `rea doctor` unhealthy است (engine/provider و skill identity). ECC pinned SHA `d2ef2680594f9a17526a6e1a2e18b3d242c5d17b` آماده است، ولی این میزبان subagent/child واقعی ندارد؛ QA مستقل انجام نشده. RepoWise برای inventory اولیه لازم نبود و نصب نشد؛ کد به مدل بیرونی ارسال نشد.
- **برش جاری:** QF-00 ادامه دارد؛ `mp-app/backend/scripts/export_routes.py` و `api/routes.json` علاوه بر ۱۲۱ مسیر/۱۳۷ operation، اکنون برای هر operation فیلدهای `guards` و `roles` (مجوز مؤثر `security.rbac.enforce`) را ثبت می‌کنند و `tests/integration/test_routes_access_matrix.py` تازگی آن را می‌سنجد: ۱۲۸ operation با guard، ۹ مسیر عمومی مستند. full Backend **955 passed / 2 skipped**, coverage **82.62%**, Ruff/format، route-guard و Studio API-coverage **4 passed** سبزند.
- **دو شکاف مالکیتی که همین inventory پیدا کرد و رفع شد:** هر عضو می‌توانست پرداخت عضو دیگر را در درگاه آغاز کند (`POST /payments/{id}/start` بدون سنجش مالکیت) و صورتحساب اشتراک عضو دیگر را بخواند (`GET /members/memberships/{id}/invoice` بدون `user`). هر دو با `ensure_record_scope`/`ensure_member_scope` بسته شدند؛ تست red→green در `tests/integration/test_qf00_ownership_gaps.py` (۵ تست) و ۴۴ تست پرداخت/درگاه سبز. جزئیات/حدود در [گزارش baseline QF-00](REPORT-QF-00-BASELINE-2026-11-19.md).
- **وضعیت:** همچنان `IN PROGRESS / GATE BLOCKED`: نگاشت سطح **interaction** (دکمه/فرم/منو → نقش/API/DB/test) و بازبینی نقش‌های کادر/admin کامل نیست و QA مستقل انجام نشده. QF-01 شروع نشده است.
- **CI checkpoint:** run نخست `44551275122` روی `6f236a8` به‌علت یک match redacted از metadata opaque REA fail کرد؛ فقط fingerprint دقیق commit/path/rule/line به `.gitleaksignore` اضافه شد، بدون استثنای rule/path/global یا rewrite تاریخچه. commit `259a621` در run `44553561916` با هر ۸ job سبز شد؛ checkpoint سندی `ae95830` نیز در run `44555108377` با هر ۸ job (از جمله full-history Gitleaks) پاس شد؛ checkpoint سندی `9fb1ea5` در run `44557157005` و برش کد `cbd161b` (ماتریس دسترسی + رفع F1/F2) در run `44562283502` نیز هر دو با هر ۸ job سبز شدند؛ checkpoint سندی `d8e8a9b` هم در run `44564422284` هر ۸ job را موفق کرد. هر commit بعدی تا بررسی run خودش تأییدنشده است. جزئیات در گزارش QF-00 است.
- **تصمیم‌های محصول ۲۰۲۶-۱۱-۱۹ (ثبت‌شده، بدون تغییر کد):** اپ عضو بیرون از باشگاه در دسترس است (سرور محلی + ورودی HTTPS ارزان). فروشگاه **نمایش‌محور** می‌شود: محصول/قیمت/موجودی قابل مشاهده، خرید حضوری؛ سبد و checkout در UI عضو غیرفعال و API fail-closed. کارت‌به‌کارت فقط در ساعات لایو بودن سرور؛ خارج از آن آیکون خاکستری و پیام «خارج از تایم کاری». گیت تازهٔ **Q11**: هیچ کنترل تعاملی UI از صفر کد نمی‌شود و همه از کتابخانهٔ رایگان OSS می‌آیند (نمونهٔ صریح: کلیدهای اعطای قابلیت به ادمین در QF-03/QF-04). جزئیات در [TODO بخش J](TODO-CLOUD-FINANCE-ACCESS.md) و [برنامهٔ QF](PLAN-FINN-ECC-MICROLOOPS-QA.md).
- **Q11 انجام‌شده (۲۰۲۶-۱۱-۱۹):** `antd@5.29.3` + `@ant-design/cssinjs@1.24.0` + `@ant-design/icons@5.6.1` + `react-multi-date-picker@4.5.2` نصب شدند (همه MIT، بدون تلمتری). ریشهٔ Studio با `StyleProvider layer` و `ConfigProvider direction="rtl" locale={faIR}` بسته شد؛ ۸ `<select>`، ۳ دیالوگ دست‌ساز و ۲ `<input type="date">` به کامپوننت کتابخانه مهاجرت کردند و شمارش دست‌ساز در `src/` به صفر رسید (بودجهٔ ratchet: `tests/uiControlBudget.json`). گیت `tests/uiLibrary.test.ts` و شاهد جلالی `tests/jalaliDate.test.tsx` اضافه شدند؛ ۲۳۴ تست سبز. جدول کامل انتخاب/رد: [UI-CONTROLS-Q11](UI-CONTROLS-Q11.md). کامیت‌ها: `781219a` و `19fd9e6`؛ CI اجرای `44600653345` ۸/۸ سبز.
- **بررسی ابزار (۲۰۲۶-۱۱-۱۹):** چهار مخزن ارسالی مالک بررسی و رد شد (به‌جز یک فهرست CC0 به‌عنوان مرجع خواندنی). نتیجه، دلیل و سه الگوی بر‌داشتنی: [AGENT-TOOLING-REVIEWS](AGENT-TOOLING-REVIEWS.md). هیچ dependency تازه‌ای وارد نشد. مخزن `davidondrej/cloudroom` (Apache-2.0) بعداً فرستاده شد: به‌عنوان پلتفرم رد شد، ولی دو مهارتش به گیت پروژه تبدیل شد — **۲.۲ ریسک‌چک پرداخت/قیمت** و **فهرست تصمیم‌های کم‌اطمینان در پایان هر حلقه**.
- **تلهٔ HEAD قدیمی (۲۰۲۶-۱۱-۱۹):** اگر checkout محلی روی commit قدیمی‌تر از شاخهٔ دوردست باشد، کارِ از قبل commit‌شده به‌شکل تغییر commit‌نشده دیده می‌شود — مثلاً ۹۳۱ فایل `.claude` حذف‌شده در `184ed41` و رفع مالکیت پرداخت در `cbd161b` روی HEAD قدیمی «dirty» نشان داده شدند. پیش از هر `git checkout --`/`restore`/`clean`، اول `git rev-parse HEAD refs/remotes/origin/<branch>` را مقایسه کن و فقط اگر HEAD با دوردست یکی بود، دورریختن معنا دارد؛ در غیر این صورت بازگردانی، کار جدیدتر را برمی‌گرداند و حذف‌های عمدی را زنده می‌کند.
- **نقشهٔ کار پیش‌رو (۲۰۲۶-۱۱-۱۹):** ترتیب نهایی فازها، فایل‌های هر فاز، معیار پذیرش، و این‌که هر ایستگاه میکرو‌لوپ با چه کتابخانه/ابزاری حمل می‌شود در [ROADMAP-NEXT-2026-11-19](ROADMAP-NEXT-2026-11-19.md). دو تصمیم تازهٔ مالک در آن ثبت شده: ترتیب اجرا (فرم فروشگاه → گیت QF-00 → فروشگاه نمایش‌محور → هویت → مجوز → پول) و **حذف کامل درگاه پرداخت اینترنتی** از UI و API با حفظ دادهٔ تاریخی.
- **repo wise / diagram / agent memory (۲۰۲۶-۱۱-۱۹):** `repowise 0.61.0` نصب و اجرا شد (AGPL، فقط ابزار توسعه، تلمتری خاموش با `DO_NOT_TRACK=1`، ایندکس ۵۷MB در `.repowise/` و gitignore). مدل معماری ۵۸۳ خطی در `architecture/repowise-model-2026-11-19.dsl` و چهار دیاگرام لایه/مرحله/پول/توپولوژی در [ARCHITECTURE-LAYERS-AND-STAGES](ARCHITECTURE-LAYERS-AND-STAGES.md). حافظهٔ عامل از نوع Markdown با `tigerless-labs/agent-memory` ممکن نشد (`requires-python >=3.12`، محیط ۳.۱۱.۲) و به‌جای آن ذخیره‌گاه تصمیم محلی repowise + اسناد Git استفاده می‌شود. گیت تازهٔ `scripts/repo_hygiene_gate.py` در CI اجرا می‌شود تا ایندکس/`.claude/`/hook خودکار برنگردد. گیت مستندات از ۱۳ به ۱۷ فایل و ۱۳ بلوک Mermaid رسید.
- **اقدام بعدی دقیق (فاز ۰ نقشه):** ۱۹ ورودی خام فرم `Shop.tsx` را به `Form`/`InputNumber` antd ببر و همان loop `shopPage` را با تست قرمز-اول همراه کن؛ سپس نگاشت سطح interaction را شروع کن — برای هر صفحهٔ Studio و مسیر Flutter، فهرست دکمه/فرم/menu را با role، فراخوانی API (از `api/routes.json`)، جدول DB و test موجود تطبیق بده؛ هر action بدون API/test را gap ثبت کن. سپس نقش‌های coach/reception/admin را در همان قالب بازبینی کن. QA مستقل و checkpoint جدید پس از آن. بدون حل گیت QF-00، QF-01 شروع نشود.

## System Atlas — snapshot جدید

- برای README یک نمودار معماری SVG اختصاصی و قابل‌ویرایش و [گراف متنی همراه و شواهد](architecture/system-atlas.md) اضافه شد. این نقشه مفهومی است؛ مسیرهای ناقص/مشروط و نیازمند بررسی با خط‌چین نشان داده شده‌اند و اثبات E2E یا release نیستند.
- شاخهٔ `arena/89881eb8-mp` ابتدا از `5482930587ce18e14f136d78296542a2de5af091` ساخته شد؛ سپس با حفظ تغییرات، `main` روی `a28404194c408e55ecf8a51ea806c0ef91f58c27` در شاخهٔ جاری ادغام شد. PR شمارهٔ ۴ شامل اصلاحات R1/R2 پیش‌تر در همین main ادغام شده بود؛ وضعیت Git و CI نسخهٔ فعلی را جداگانه بررسی کنید.
- فایل‌ها: `README.md`، `docs/MuscleParadise/assets/system-architecture.svg`، `docs/MuscleParadise/architecture/system-atlas.md`، `docs/MuscleParadise/architecture/README.md` و `scripts/docs_gate.py`. تصویر SVG دست‌ساخته است، نه خروجی D2؛ Mermaid همراه برای review نگهداری می‌شود. تصویر در اندازهٔ اصلی و عرض ۷۲۰px محلی render و بصری بررسی شد و Mermaid 11.12.2 بلوک‌های مربوط را parse کرد؛ نمایش در GitHub و موبایل باید جداگانه بررسی شود.

## پیگیری دو یافتهٔ بازبینی — snapshot پیشین

- PR شمارهٔ ۳ با تأیید مالک در `main` روی merge commit `a238fd1dbc672bdcb8fb355e7d9f94aeaea93eb1` ادغام شد. شاخهٔ پیگیری این نشست `arena/95706efd-mp` از همان main به‌صورت fast-forward به‌روز شد؛ برای SHA فعلی و نتیجهٔ CI این پیگیری وضعیت Git/PR را دوباره بخوانید.
- R1: تغییر شناسه یا شروع lookup در `PaymentPanel`، انتخاب و رسید قبلی را پاک می‌کند؛ ورودی هنگام درخواست قفل و فراخوانی هم‌زمان در UI با guard همگام رد می‌شود. تست‌های widget برای جستجوی ناموفق/نامعتبر، شبکه، HTTP، بازیابی و درخواست معلق افزوده شدند؛ با fixture و نه بانک واقعی.
- R2: در `format-qr` اجرای widget test پیش از commit/push است؛ SHA-256 فایل‌های فرمت‌شده بعد از تست تطبیق داده می‌شود و blobهای staged با فایل‌های آزموده تطبیق می‌شوند. تست خودکار synthetic workflow، مسیر موفق و خطای تست و تغییر فایل/مرحله‌بندی را می‌سنجد؛ در زمان نگارش این snapshot، workflow واقعی dispatch نشده است.
- CI پیگیری روی `ccb771422e0dc198f8cebe4d96742e0ef8248163` در [run 44533091544](https://github.com/yousefghorbanian98-create/MP/actions/runs/44533091544) در lint backend متوقف شد؛ فرمت تست جدید محلی با `ruff format` اصلاح و `ruff check .`, `ruff format --check .` و پنج تست synthetic موفق شدند. نتیجهٔ CI commit بعدی را جداگانه روی همان SHA بررسی کنید.
- گراف Mermaid [جریان‌های بازبینی](architecture/pr-review-flows-2026-11-18.md) با رفع دو یافته به‌روز شد؛ گراف RepoWise قبلی یک snapshot تاریخی است و این تغییرات را index نکرده است. این کار به معنی تأیید کامل گردش مالی یا release نیست.

## بازبینی PR و گراف — snapshot تاریخی

- [بازبینی PR شمارهٔ ۳](REPORT-PR-3-REVIEW-2026-11-18.md) روی `da73f2e81bd9e70b9ed395407481fe133a4ca731` در برابر `main`: یافتهٔ P2 در جستجوی پرداخت به‌صورت ایزوله با یک تست شکست‌خورده بازتولید شد؛ پس از lookup ناموفق دکمهٔ بازگشت پرداخت قبلی می‌ماند. workflow دستی فرمت QR نیز قبل از تست push می‌کند. PR باید تا رسیدگی به یافته‌ها draft بماند؛ هیچ کد محصولی در این بازبینی اصلاح نشد.
- [نمودار جریان‌های بازبینی](architecture/pr-review-flows-2026-11-18.md)، [گراف تازهٔ RepoWise](architecture/repowise-pr-review-2026-11-18.dsl) و [scope آن](architecture/repowise-pr-review-scope-2026-11-18.txt) ثبت شده‌اند. RepoWise روی ۵۷۶ blob انتخابی از commit بازبینی‌شده، با scan پاک و بدون مدل/هوک اجرا شد؛ index پس از ساخت گزارش یا commit بعدی دوباره refresh نشده است.
- CI قبلی [run 44511373788](https://github.com/yousefghorbanian98-create/MP/actions/runs/44511373788) برای همان `da73f2e...` هشت job موفق داشت؛ تست کشف R1 بخشی از آن CI نبود. در نشست بعدی status PR و CI همان HEAD را دوباره بخوان، R1/R2 را رسیدگی و سپس بازبینی کن. ادغام و انتشار محصول را یکی نگیر.

## انتقال و پیش‌نیازهای سازنده — snapshot قبلی

- ابتدا [پیش‌نیازها، نصب و محدودهٔ RepoWise](BUILDER-START-AND-REPOWISE.md)، سپس [هندآف تفصیلی](HANDOFF-PROJECT-2026-11-18.md)، [QF](PLAN-FINN-ECC-MICROLOOPS-QA.md)، [TODO](TODO-CLOUD-FINANCE-ACCESS.md) و [نقش‌ها](PROPOSAL-SUBAGENTS-AND-CHECKPOINTS.md) را بخوانید. وضعیت‌های پایین تاریخی‌اند و با `git status`، SHA و CI نشست تازه بررسی می‌شوند.
- شاخهٔ انتقال `arena/b0e55b62-mp`؛ CI آخرین SHA ثبت‌شده `dc572a7c2fbb7ab094297cfec4bd56accca6dc1b` در [run 44507836824](https://github.com/yousefghorbanian98-create/MP/actions/runs/44507836824) هر هشت job موفق؛ نتیجه را به SHA بعدی تعمیم ندهید. QF-00 و QA مستقل همچنان `BLOCKED/NOT RUN`؛ OVها اجرا نشده‌اند و release مجاز/اثبات‌شده نیست.
- RepoWise روی mirror انتخابی ۵۶۴ فایلی و بدون مدل، hook و editor اجرا شد؛ [محدوده](architecture/repowise-transfer-scope-2026-11-18.txt) و [گراف](architecture/repowise-transfer-2026-11-18.dsl) را ببینید. گراف کل repo یا index زنده نیست. raw M113 و تنظیمات محلی محرمانه منتشر نشده‌اند؛ خلاصهٔ پالایش‌شده جای متن خام را نمی‌گیرد. تست policy مستقل ۵۴ passed با یک هشدار تنظیمات بود، نه پذیرش گردش مالی.
- شاخهٔ پیش‌فرض GitHub `main` است؛ نمایش پیش‌فرض صفحهٔ اصلی تا بررسی و ادغام جداگانهٔ تغییرات در `main` به‌روز نمی‌شود. commit/push این انتقال فقط در شاخهٔ مجاز نشست انجام می‌شود و از روی این متن وضعیت فعلی PR را فرض نکنید.

## به‌روزرسانی تاریخی ۲۰۲۶-۱۱-۱۸ — checkpoint محدود کلید قدیمی

- SHA شاخهٔ `arena/b0e55b62-mp` روی GitHub و محلی `4571908c1fdc8dca6a2ba700f8f99f3b52329ab0` شد. پیش از merge غیرمخرب، ۲۵ مسیر remote دقیقاً و استثنای تأییدشدهٔ `.gitleaksignore` عمداً متفاوت بودند؛ merge با راهبرد `ours` تنها پس از اثبات این تطابق انجام شد. ۷۸ فایل dirty/untracked با هش قبل و بعد بررسی شدند و هیچ‌کدام تغییر نکردند. Git pull/reset/force-push یا overwrite فایل‌های محلی انجام نشد. این checkpoint فقط استثنای کلید و آثار لازم آن را منتشر کرد؛ اسناد، شواهد و کدهای محلی باقی‌مانده هنوز checkpoint نشده‌اند.
- CI run `44497749287` روی همان SHA پایان یافت و هر هشت job آن، از جمله secret-scan، تست استثنای دقیق، دو job Flutter/Android، backend، studio، live-contract، docs و e2e-api، موفق شدند. این موفقیت فقط برای همان SHA است، نه تغییرات محلی باقیمانده یا APK release امضاشده. Flutter/Dart محلی اجرا نشد. fingerprint کلید جدید و Actions secrets هنوز تأیید نشده‌اند. QF-00 آغاز نشده است.
- بازبینی تکمیلی هشدارهای M113: هر ۱۳۷ `operation_key` با تابع SHA-256 بر روی مسیر و method خود در REA تطبیق داده شد؛ هش علامت‌خوردهٔ Markdown نیز با SHA-256 فایل OpenAPI همان fixture برابر بود. این بررسی فقط دربارهٔ آن هشدارهاست، نه کل محتوای شواهد. فایل‌های اصلی به سبب تصمیم‌نگرفتن دربارهٔ انتشار امن هنوز محلی و دست‌نخورده‌اند؛ هیچ allowlist جدید برای آن‌ها اعمال نشده است.

## به‌روزرسانی جاری ۲۰۲۶-۱۱-۱۸ — بررسی کلید قدیمی Android

- [گزارش بررسی کلید قدیمی و استثنای محدود](REPORT-OLD-ANDROID-KEY-REVIEW-2026-11-18.md): keystore قدیمی و properties از commit تاریخی بدون احراز هویت قابل دریافت‌اند؛ بررسی metadata تأیید کرد PKCS12 با رمز همان فایل باز می‌شود، اما سوءاستفاده اثبات نشده است. مالک کنارگذاشتن کلید و استثنای دقیق دو یافته را پذیرفت؛ همان دو fingerprint در `.gitleaksignore` محلی افزوده شدند، بدون allowlist سراسری. regression واقعی Gitleaks با fixture ساختگی مثبت/منفی موفق شد و گام آن به workflow محلی اضافه شد؛ اسکن شاخهٔ remote و پنج tag با policy محلی صفر یافته داشت. GitHub و history تغییر نکرده‌اند؛ CI SHA جدید و اثرانگشت کلید جدید هنوز تأیید نشده‌اند. دسترسی Actions همچنان 403 است.

## به‌روزرسانی جاری ۲۰۲۶-۱۱-۱۸ — آماده‌سازی و مانع شروع

- [گزارش آماده‌سازی پیش از loop](REPORT-PRELOOP-READINESS-2026-11-18.md): نقش‌بندی برای آماده‌سازی پذیرفته و ECC انتخاب فعلی است؛ QF-00 و توسعه آغاز نشده‌اند. REA روی OpenAPI ساختگی موفق و doctor کلی ناموفق بود؛ ECC consult واقعی ولی زیراجنت، مدل/host و QA مستقل اثبات نشده‌اند. اصلاح غیرمخرب مقایسهٔ مجوز REA با تست‌های ساختگی انجام شد. checkpoint، تاریخچهٔ حساس، همگام‌سازی امن و یافته‌های اسکن نیازمند رسیدگی‌اند؛ هیچ commit یا push انجام نشد. آثار این نشست هنوز فقط در worktree هستند.

## به‌روزرسانی افزودهٔ ۲۰۲۶-۱۱-۱۸ — تقسیم وظایف و checkpoint هر loop

- [نقش‌ها و وظایف همهٔ ۳۳ میکرولوپ](PROPOSAL-SUBAGENTS-AND-CHECKPOINTS.md) برای آماده‌سازی با اختیار مالک پذیرفته شده‌اند؛ هیچ زیراجنت واقعی یا ساخت محصول در این گام اجرا نشده. ECC انتخاب فعلی نقش‌هاست؛ جایگزین بدون آزمایش واقعی تصویب نشده است.
- مالک خواست پایان **هر** میکرولوپ مستند شود و آثار لازم در GitHub ذخیره شوند؛ بند ۲.۱ [برنامهٔ QF](PLAN-FINN-ECC-MICROLOOPS-QA.md) checkpoint انتخابی، review، scan، commit/push فقط شاخهٔ فعلی، تأیید SHA و ثبت CI را الزام می‌کند. بدون checkpoint امن، شروع توسعهٔ حلقهٔ بعدی مسدود است. repo عمومی است؛ secret، دادهٔ شخصی، binary/cache و هر محتوای ناامن را نباید منتشر کرد.
- مانع شروع امن: HEAD محلی `5482930`، سر شاخهٔ GitHub `8e72de9` (۸ commit جلوتر) و آثار محلی dirty/untracked؛ ابتدا انتقال آثار و همگام‌سازی بدون pull/reset/force-push و بدون تغییر branch باید بررسی و حل شود. هیچ commit/push/merge در این گام انجام نشده؛ اسناد جدید فعلاً محلی‌اند. پیش از هر دستور شروع توسعه، میزبان/مدل واقعی، QA مستقل و checkpoint امن باید احراز شوند.

## به‌روزرسانی افزودهٔ ۲۰۲۶-۱۱-۱۸ — سنجش گزینه‌های رایگان ECC

- [گزارش ارزیابی](REPORT-FREE-ECC-ALTERNATIVES-2026-11-18.md) و [metadata سنجش](../../finn/reports/rea/free-ecc-alternatives-smoke-metadata.json): Superpowers v7.0.2 و Agency Agents pinned و OpenCode 1.19.6 موقتاً خارج پروژه آزمایش شدند. ۵ تست upstream از Superpowers و ۳ تست Agency موفق؛ با provider اسکریپت‌شدهٔ loopback، OpenCode واقعاً skill بارگذاری کرد و برای `API Tester` یک child session جدا ساخت و خروجی ساختگی گرفت. پاسخ‌های provider از پیش برنامه‌ریزی‌شده بودند، نه AI؛ کیفیت، خودمختاری، اجرای TDD و مقایسهٔ واقعی با ECC آزموده نشدند.
- Superpowers در دستورهای upstream، حذف کد پیش از تست، ایجاد branch/worktree و بعضی عملیات Git را مطرح می‌کند؛ محدودیت‌های کاربر و branch مقدم‌اند و این اقدامات خودکار مجاز نیستند. هیچ نصب یا جایگزینی در پروژه انجام نشد؛ REA در این ارزیابی اجرا نشد. گام بعدی مقایسهٔ A/B با مدل مجاز و fixture ساختگی در sandbox امن است؛ هیچ secret و کد پروژه ارسال نشود.

## به‌روزرسانی افزودهٔ ۲۰۲۶-۱۱-۱۸ — صفحهٔ مخزن و انتقال نشست

- [هندآف تفصیلی پروژه و راهنمای نشست جدید](HANDOFF-PROJECT-2026-11-18.md) و [نقشهٔ هدف ابری/مالی/دسترسی](architecture/cloud-finance-access.md) به همراه به‌روزرسانی README، docs hub، C4 و module map آماده شدند؛ این‌ها هدف را از رفتار اثبات‌شده جدا می‌کنند. `AGENTS.md` و `scripts/docs_gate.py` به مسیرهای جدید اشاره می‌کنند.
- در snapshot این کار، HEAD محلی `5482930` و سر شاخهٔ فعلی در GitHub `8e72de9` و ۸ commit جلوتر بود. fetch غیرمخرب و `git read-tree -n -m -u` فقط برای سنجش انجام شد؛ dry-run به علت تغییرات محلی ledger شکست. pull/reset/merge/push انجام نشد. اسناد جدید فعلاً در workspace هستند و برای clone تازه قابل اتکا نیستند؛ شرح راه امن و وضعیت دقیق در هندآف تفصیلی است.
- CI `44391354746` روی `8e72de9`: backend، studio، docs، live-contract، e2e-api و دو client job موفق؛ secret-scan شکست و run کلی ناموفق. `44391379581` برای Android release شکست. هیچ وضعیت CI را به فایل‌های محلی جدید تعمیم نده.
- اعتبارسنجی مستندات در این workspace: `python3 scripts/docs_gate.py` موفق، ۱۲ Markdown و ۱۷۹ لینک؛ `git diff --check` موفق؛ ۱۰ دیاگرام با parser واقعی Mermaid 11.12.2 در محیط موقت parse شدند. رندر واقعی GitHub و CI برای این نسخه اجرا نشده‌اند.
- Repowise binary و index در این sandbox غایب‌اند؛ wheel نسخهٔ 0.61.0 فقط موقتاً برای بررسی دانلود شد. `init --yes` می‌تواند hook/editor setup انجام دهد؛ هیچ نصب، init، refresh، اتصال MCP یا model call انجام نشد. محدودیت و گزینه‌های کم‌اثر برای بررسی بعدی در هندآف تفصیلی ثبت است.

## به‌روزرسانی افزودهٔ ۲۰۲۶-۱۱-۱۸ — تلاش واقعی و ایزولهٔ ECC

- [گزارش smoke test زیراجنت](REPORT-ECC-SUBAGENT-SMOKE.md): Claude Code نسخهٔ 2.1.328 در cwd/HOME موقت، بدون credential یا کد MP، نقش planner برگرفته از ECC را از `--agents` شناخت. بدون `--bare` با `--tools Task` ابزار `Task` نیز در init شناسایی شد؛ با این حال خطای احراز هویت exit 1 و `is_error:true` برگشت و هیچ tool-call یا child output رخ نداد. شواهد metadata در `finn/reports/rea/ecc-{isolated,task-only}-smoke-metadata.json`. این استفاده از پلاگین یا اجرای واقعی زیراجنت نیست.
- قدم بعدی اگر مالک بخواهد: میزبان پشتیبانی‌شده با ورود امن خارج از چت، یا ابزار delegation میزبان Arena؛ سپس تکرار smoke ساختگی با بودجه و مجوز روشن و ثبت parent/child. ارسال کد MP به سرویس مدل بدون اجازهٔ جدا ممنوع.

## به‌روزرسانی افزودهٔ ۲۰۲۶-۱۱-۱۸ — بررسی REA و مسیر زیراجنت ECC

- [گزارش REA/ECC](REPORT-REA-ECC-SUBAGENTS.md): REA واقعاً mirror پالایش‌شدهٔ ۱۵۰۰ فایل پروژه و ۲۵۷۰ فایل checkout ECC را inventory کرد (`partial`)؛ بررسی static سه فایل JS/TS در هر کدام نیز `partial` بود. [شاهد metadata پالایش‌شده](../../finn/reports/rea/project-ecc-orchestration-summary.json)؛ کل پروژه خط‌به‌خط یا امنیتی audit نشده است.
- CLI موقت Claude Code شواهد محلی را نشان داد: plugin `ecc@ecc` نسخهٔ 2.2.3، `enabled:true` و `projectEnabled:false`؛ auth همان CLI `loggedIn:false` و agent-session list برای cwd صفر است. این نتایج دربارهٔ نشست‌های قبلی یا کل حساب کاربر ادعا ندارند. ابزار delegation در رابط فعلی دیده نمی‌شود، هیچ مدل بیرونی یا زیراجنت فراخوانی نشده و هیچ credential خواسته نشده است.
- قدم بعدی در صورت ادامهٔ این موضوع: بررسی شاهد غیرمحرمانهٔ نشست قبلی، یا در میزبان واقعاً پشتیبانی‌شده پس از تأیید provider/هزینه و بدون ارسال کد، smoke test با parent/child tool-call. برای ارسال کد/داده به مدل بیرونی مجوز صریح جدا لازم است. هیچ نصب خودکار، bypass-permissions یا global allowlist انجام نشود.

## به‌روزرسانی افزودهٔ ۲۰۲۶-۱۱-۱۸ — طرح micro-loop و QA

- شاخهٔ فعال `arena/b0e55b62-mp` است؛ دستورهای شاخه/`reset` در متن تاریخی پایین برای این نشست مجاز نیستند. کاربر تنظیم چرخه‌های جداگانهٔ FINN/ECC با QA تکرارشونده در هر برش و ادامهٔ بدون نظارت روتین خواست؛ خروجی [طرح QF-00 تا QF-32](PLAN-FINN-ECC-MICROLOOPS-QA.md) است، نه اجرای توسعه. [تحقیق منشأ OSS](OSS-DEEP-RESEARCH-2026-11-18.md) و [TODO محصول](TODO-CLOUD-FINANCE-ACCESS.md) دامنه و نامزدها را مشخص می‌کنند؛ صف قدیمی و آثار قبلی حفظ شده‌اند.
- ECC `consult` واقعاً اجرا و پیشنهاد heuristic داد، اما هیچ subagent مستقل اجرا نشد؛ REA 6.9.0 برای skill سالم و environment کلی ناسالم گزارش شد. Flutter/Dart/Docker در PATH موجود نیستند؛ CI/دستگاه و همهٔ QAهای ساخت `NOT RUN` هستند. محصول، dependency، داده، deployment یا release تغییر نکرد.
- قدم بعدی: پس از دستور شروع توسعه با حفظ قید گزارش پیش از ساخت، از QF-00 و baseline غیرمخرب شروع و هر برش را همراه QA اختصاصی‌اش تمام کن؛ موانع واقعی را مستند و برش‌های مستقل را بدون سؤال روتین ادامه بده. push، استقرار، خرید، دادهٔ واقعی، انتشار و عملیات مخرب نیازمند مجوز جدا هستند.

## Snapshot فعلی

- **هدف پایدار کاربر:** توسعهٔ محصول با کمک AI، بدون بازخوانی بی‌هدف کل مخزن؛ معماری، تصمیم‌ها و قدم بعدی باید در فایل‌های Git-tracked قابل انتقال باشند.
- **کار این handoff:** راه‌اندازی ورودی ایجنت‌ها و نقشهٔ مستندات؛ مستندات C4، نقشهٔ ماژول‌ها و پنج ADR موجود را کشف و به آن‌ها پیوند بده، نه اینکه دوباره از حافظه بازنویسی شوند.
- **وضعیت این کار:** ساختار مرجع در `AGENTS.md` و `docs/README.md` اضافه شده؛ فهرست‌های معماری/ADR و همین handoff تکمیل شده‌اند. `AGENTS.md` اکنون صریحاً D-033 و مرز اجرای واقعی ECC/REA را می‌گوید. این کار تغییری در منطق runtime محصول ایجاد نمی‌کند.
- **صف محصول:** در snapshot فعلی TODO جاری خودش `docs/MuscleParadise/TODO-2026-11-16.md` را مرجع معرفی می‌کند و نقشه‌های جاری را در همان سند مشخص کرده است. پیش از ادامه، سربرگ آن و وجود TODO جدیدتر را بررسی کن؛ فقط loopی را ادامه بده که واقعاً در مرجع جاری فعال/مجاز است.
- **Repowise بعدی:** `DX-REP-01` در بخش P3 همان TODO ثبت شد؛ زمان مناسبش پیش از epic بزرگ چندنشستی یا انتقال به clone تازه است. فعلاً MCP برای Arena وصل نیست و در وضعیت بدون LLM/full-text بماند.
- **اسناد تاریخی:** `MASTER_MAP.md`, `FINN_LOOP.md`, `READY-TO-RESUME-2026-11-15.md` و گزارش‌های تاریخ‌دار به‌تنهایی صف جاری نیستند. محدودیت‌ها و وضعیت امنیت/انتشار را از TODO و سند امنیتی جاری بخوان؛ این فایل آن‌ها را کپی نمی‌کند.

## Repowise و قابلیت انتقال

- Repowise `0.61.0` در این workspace فقط در `venv/repowise` نصب شده و index محلی زیر `.repowise/` است؛ هر دو مسیر Git-ignored هستند. قاعدهٔ ignore برای `.repowise/` در `.gitignore` تغییر محلیِ موجود از مرحلهٔ setup است؛ آن را حذف نکن.
- index با حالت code-derived و بدون LLM ساخته شده بود: ۱٬۵۸۳ فایل پردازش، ۵۳۶ صفحه، full-text فعال و semantic خاموش؛ هزینهٔ مدل صفر بود.
- اتصال MCP برای Arena Agent Mode انجام نشده است؛ در clone/نشست دیگری وجود این index یا virtualenv را فرض نکن.
- حافظهٔ پایدار و قابل انتقال: این فایل برای اشارهٔ کوتاه، [AGENTS.md](../../AGENTS.md) برای پروتکل ایجنت، و مستندات محصول/معماری لینک‌شده از [docs hub](../README.md) هستند. Repowise فقط شتاب‌دهندهٔ اختیاری است.

## نتیجه و شواهد آخرین کار

- **کارهای نشست:** ورودی مشترک ایجنت‌ها و نقشهٔ معماری/تصمیم‌ها/حافظهٔ نشست ساخته شد؛ سپس `DX-REP-01` به P3 TODO افزوده شد تا تکمیل Repowise در زمان مناسب برنامه‌ریزی شود. C4 و ADRهای موجود دوباره‌نویسی نشدند.
- **مسیرهای تغییرکرده:** `AGENTS.md`, `README.md`, `docs/README.md`, `docs/MuscleParadise/SESSION_HANDOFF.md`, `docs/MuscleParadise/TODO-2026-11-16.md`, `docs/MuscleParadise/architecture/README.md`, `docs/MuscleParadise/adr/README.md`, `docs/MuscleParadise/adr/TEMPLATE.md`, `docs/MuscleParadise/assets/knowledge-atlas.svg`, `scripts/docs_gate.py`, `.github/workflows/ci.yml`.
- **پروتکل واقعی این مسیر:** نصب Repowise، hub/hand-off و DX-REP-01 را عامل اصلی Arena انجام داد؛ هیچ چرخهٔ کامل F.I.N.N، subagent از ECC یا اجرای REA در این کار انجام نشد. بررسی محیط نشان داد `claude`، `claude-code` و `rea` روی PATH نیستند و `.finn/ecc` و `~/toolchain/rea` هم حاضر نیستند. گیت محلی مستندات و بررسی دستی پیوندها اجرا شدند؛ این‌ها جای ECC/REA یا بازبینی مستقل را نمی‌گیرند.
- **اعتبارسنجی مستندات:** `python3 scripts/docs_gate.py` موفق شد: ۷ فایل Markdown، ۹۹ پیوند محلی، ۳ بلوک Mermaid، سرفصل‌های handoff، لینک‌های README و XML/SVG. پس از افزودن DX-REP-01، پیوندهای آن به hub/معماری/هندآف محلی بررسی شدند؛ `git diff --check` نیز موفق بود. job مستندات به CI اضافه شده ولی GitHub Actions در این نشست اجرا نشده؛ runtime/backend/frontend تست نشدند.
- **اثر محصول:** کد یا رفتار runtime تغییر نکرد؛ Repowise مجدداً اجرا نشد و هیچ مدل/embedding استفاده نشد.
- **حفظ workspace:** بستهٔ M63–M99 + M107/M108 روی `origin/arena/4f336f66-mp` است (تا `2ac6ecc`)؛ `evidence/` و گزارش‌های تاریخی `finn/reports/M0*` عمداً untracked ماندند و `.repowise/`/venv در ignore. پیش از ادامه، `git status` و head را با `gh run list --branch arena/4f336f66-mp --limit 1` تطبیق بده — اگر sandbox تازه‌ای checkout را به پایه برگردانده باشد، `git fetch` + `git reset --mixed <head>` کار می‌کند (بدون `--hard`؛ این دقیقاً همان چیزی است که یک بازسازی mid-session را بی‌ضرر کرد).

## اقدام بعدی

1. در نشست بعدی، ابتدا وضعیت Git و این handoff را بخوان؛ سپس `AGENTS.md` و [docs hub](../README.md).
2. **گیت‌های Client/Android را دستی اجرا نکن — `client-pinned` آن‌ها را می‌گیرد (M108).** جاب `client-pinned` در `ci.yml` روی Flutter پین‌شدهٔ devcontainer (پین از `.devcontainer/Dockerfile` پارس می‌شود؛ drift = fail) اجرا می‌کند: `dart format` **گیتِ کشنده** (از M109) · analyze · `test --coverage` · `flutter build apk --debug`. شاهد فعلی روی `57f5579` (run `44355019906`): **156 passed / 0 failed / 0 skipped**، coverage **76.7%** (۳۳۹۳/۴۴۲۶)، apk ساخته شد ⇒ کامپایل Kotlin/Gradle (M87) تأیید؛ `dart format: clean` و گیتش **کشنده** (M109). ٪coverage را با عددِ پیش از M109 (۷۷٫۲٪/۴۱۴۰ خط) مقایسه نکن: فرمت، خطوطِ شمارش‌شده را عوض کرد، پس مخرج عوض شده نه پوشش؛  اعداد از `gh api "repos/<repo>/check-runs/<job-id>/annotations"` خوانده می‌شوند (مسئلهٔ M95: `--log` برای jobهای Flutter چیزی برنمی‌گرداند). **`apk.yml` حذف شده است (AD‑21، ۲۰۲۶‑۱۱‑۲۲)؛** دیگر dispatch نمی‌شود و SEC-01 با حذفش بسته شد.
3. **کار دستیِ باقی‌مانده برای کاربر فقط گوشی است (§۶ runbook).** M109 (فرمت ۶۵ فایل) با workflow `client-format-fix` و PR #1 بسته شد؛ Codespace ریل لازم نیست. اگر روزی لازم شد، `.github/workflows/client-format-fix.yml` الگوی «CI انجام می‌دهد، PR بازبینی می‌شود» است: `git add -u -- '*.dart'` (نه `-A`)، اثبات روی blobهای staged، PR در CI با `gh api -X POST /repos/{}/pulls` باز می‌شود، نه `gh pr create` — و توجه کن که «Allow GitHub Actions to create and approve pull requests» در این مخزن **خاموش** است، پس job token نمی‌تواند PR بسازد (403)؛ workflow شاخه را می‌فرستد و `::warning` می‌دهد و PR را ایجنت/انسان باز می‌کند. هرگز `metadata:` را به `permissions:` اضافه نکن: کلیدِ نامجاز است و کل فایل را بی‌اعتبار می‌کند.
4. **اگر لاگ Codespace/دستگاه از کاربر آمد:** همان را در [runbook M107](runbooks/codespaces-execution.md) با مرحله‌اش تطبیق بده و فقط بر اساس خروجی، status همان loop را عوض کن (M87 کامپایل، M104 startup، M105/M106 ماسک، بُعد دستگاه M89/M90/M98). بدون لاگ، `UNKNOWN` می‌ماند.
4. اگر کاربر قابلیت محصولی مشخصی خواست، مرجع صف جاری را بررسی کن و فقط مستندات معماری/تصمیم و تست‌های همان مسیر را بخوان.
5. اگر scope بعدی هنوز مشخص نیست، از این فایل کار جدید حدس نزن؛ از درخواست فعلی کاربر پیروی کن. تصمیم‌های بازِ مالک که با حدس باز نمی‌شوند، در [صفحهٔ تصمیم‌های مالک](OWNER-DECISIONS.md) به فارسیِ ساده نوشته شده‌اند (کلید امضا، چهره یا کیو‌آر، ادعای بالینی، درگاه زنده، سیاست نگهداری تصویر بدن، ادغام در `main`). هر «BLOCKED/UNKNOWN — منتظر مالک» که اضافه می‌کنی، باید در همان صفحه هم ردیفش باز شود؛ یک یادداشت داخل گزارشِ نشست، تصمیم‌گیرنده را پیدا نمی‌کند.

## قالب به‌روزرسانی برای نشست‌های بعد

جمله‌های نمونه را با شواهد واقعی جایگزین کن و بخش‌های نامربوط را حذف کن:

- **هدف/معیار پذیرش:** چه چیزی باید تمام شود؟
- **وضعیت:** انجام‌شده / نیمه‌تمام / مسدود، با دلیل.
- **فایل‌ها و تصمیم‌ها:** مسیرهای دقیق، و پیوند به ADR در صورت نیاز.
- **شاهد:** فرمان تست/CI و نتیجهٔ دقیق؛ موارد اجرا‌نشده را جدا بنویس.
- **محدودیت/مانع:** فقط مانع واقعی، بدون secret یا دادهٔ شخصی.
- **قدم بعدی دقیق:** اولین فایل/بخش/فرمان امنی که نشست بعد باید سراغش برود.


## افزودهٔ آخر: ارزش‌های نامزد، REA و RepoWise

- کاربر درخواست تطبیق و ورود ارزش‌ها، TODO/میکرولوپ، صفحهٔ GitHub و دیاگرام را داده است. [برنامهٔ OV](PLAN-OSS-VALUE-MICROLOOPS-2026-11-18.md)، [گزارش](REPORT-OSS-VALUE-DEEP-DIVE-2026-11-18.md) و [نقشه](architecture/oss-value-flows.md) در این نوبت ساخته شدند؛ TODO و QF و ماتریس نقش با append به‌روز شدند. `OV-01..11` و همهٔ QFها همچنان `NOT RUN` هستند.
- REA 6.9.0 inventory انتخابی و تحلیل ایستای JS را واقعاً انجام داد، نه تحلیل معنایی خط‌به‌خط همهٔ پروژه‌ها. RepoWise 0.61.0 واقعاً روی mirror گزینشی ۵۲۹ فایل و تاریخچهٔ مصنوعی، بدون مدل/شبکه و بدون hook اجرا شد؛ ۵۱۷ فایل index شد، **index ریشهٔ پروژه refresh نشد**. دادهٔ موقت تضمین بقا ندارد؛ output خام بدون review منتشر نشود.
- کد/asset خارجی وارد و loop محصول اجرا نشده؛ QA مستقل ECC و Flutter/device همچنان اثبات‌نشده‌اند. نبود مجوز داده و محدودیت API RepDB مانع است. گام بعد: بررسی و ثبت شواهد هر برش در سند OV با حفظ QF و checkpoint و بدون کاهش گیت‌ها.
- فقط افزودهٔ README نسبت به HEAD قبلی و سه سند جدید OV، گزارش و دیاگرام با index ایزوله پس از scan و بررسی لینک commit/push شدند: `be9e40e77f31f3b277fa1ce1d34b899d510acf81`، روی همین شاخه؛ remote و HEAD برابرند. [CI run 44505113345](https://github.com/yousefghorbanian98-create/MP/actions/runs/44505113345) برای همان SHA هشت job موفق دارد، شامل Flutter و Android debug؛ نه release/device و نه تغییرات محلی. فایل‌های قدیمی dirty/untracked از جمله TODO و برنامهٔ اصلی QF و همین handoff stage یا منتشر نشدند؛ تغییرات append محلی آن‌ها و محتوای قبلی حفظ شده‌اند. README شاخهٔ GitHub با README محلیِ دارای تغییرهای قدیمی یکسان نیست؛ شاخهٔ اصلی/صفحهٔ پیش‌فرض تغییر نکرد.


## افزودهٔ آخر: آزمایش واقعی میزبان ECC و QA ساختگی

- کاربر اجرای آزمایشی خواست. [گزارش](REPORT-ECC-QA-TRIAL-2026-11-18.md) و [fixture ساختگی](../../finn/fixtures/ecc-qa-smoke/README.md) در commit `dc572a7c2fbb7ab094297cfec4bd56accca6dc1b` روی شاخهٔ فعلی push شدند؛ HEAD و remote برابر و ۴۶ تغییر قبلی همچنان محلی‌اند. CI همان SHA در [run 44507836824](https://github.com/yousefghorbanian98-create/MP/actions/runs/44507836824) هر هشت job موفق است؛ این موفقیت اثبات گیت ECC، QA مستقل، release یا محتوای dirty نیست.
- `Task` و دو نقش موقت در میزبان Claude Code شناخته شدند اما به‌علت احراز هویت exit 1 و بدون tool-use/child؛ هیچ زیراجنت یا QA مستقل اجرا نشد. REA contract ساختگی با دو operation و ECC consult اجرا شدند؛ harness ساختگی کد ناامن را با سه شکست شناسایی و نسخهٔ مقایسه‌ای را با چهار تست گذراند. هیچ کدام QF یا اعتبارسنج پرداخت واقعی نیستند. `rea doctor` کلی unhealthy بود.
- قدم بعد: پیدا کردن میزبان مجاز دارای مدل و شبکه، یا delegation واقعی Arena؛ ثبت parent و هر دو child و QA مستقل با محتوای ساختگی، بدون درخواست credential در چت و بدون ارسال کد MP به سرویس بیرونی پیش از مجوز. تا آن زمان QF-00 و loopهای محصول `NOT RUN/BLOCKED` بمانند.

## افزودهٔ آخر: نوبت دوم ابزارها — گیت دیاگرام، نقشهٔ تست، پاک‌سازی

- گیت سینتکس دیاگرام واقعی شد. `tools/mermaid-check/check.mjs` با پارسر رسمی Mermaid و بی‌مرورگر اجرا می‌شود؛ ۲۳ دیاگرام سبز، حالت شکسته با کد ۱ قرمز. به job `docs` در CI وصل شد.
- نقشهٔ تست‌به‌کد ساخته شد: ۱۵۲۳ تست، ۱۳۴ فایل، ۷۸۶۳ رکورد. `repowise impacted-tests` روی تغییر واقعی نُه تست با پوشش برگرداند و در حالت پوشش‌نداشته `:all` با دلیل داد.
- دو نماد کد مرده با اطمینان ۱۰۰٪ حذف شد: `is_staff` و `AxisCoverage`. ۳۱ یافتهٔ دیگر بدون بررسی حذف نشدند؛ دو موردشان کاذب است.
- پانزده یافتهٔ `doc-drift` دسته‌بندی شد و خط مبنا ثبت شد؛ هیچ‌کدام قابل اصلاح با فایل موجود نبود.
- قدم بعد: تصمیم `498d4c23` (کنترل‌های UI از OSS) هنوز proposed است؛ بعد از رسیدن commit به `main` باید governing شود. گیت بودجهٔ دیاگرام (تعداد بلوک در هر سند) هنوز ساخته نشده است.

## افزودهٔ آخر: فاز ۰ نقشه — خام‌زدایی ورودی‌های فروشگاه

- گیت Q11 روی ورودی خام و textarea هم اعمال می‌شود؛ اول قرمز شد (`src/pages/Shop.tsx: input 14 > بودجهٔ 0`).
- چهارده ورودی با `Input` و `InputNumber` کتابخانهٔ antd جایگزین شد؛ صفر ورودی خام در آن صفحه.
- اعتبارسنجی خالی‌بودن از `required` مرورگر به گارد فارسی داخل handler منتقل شد.
- بدهی دوازده فایل دیگر در `tests/uiControlBudget.json` ثبت شد؛ ratchet فقط کاهش می‌دهد.
- شاهد: `vitest` ۲۳۴/۹، `tsc -b` پاک، `vite build` سبز.
- قدم بعد: فاز ۱ نقشه — نقشهٔ سطح تعامل هر صفحه با API، تست و جدول.

## افزودهٔ آخر: فاز ۱ — نقشهٔ سطح تعامل و گیت آن

- ابزار تازه `scripts/interaction_map.py` نقشه را از سه منبع واقعی می‌سازد: کلاینت استودیو، کلاینت Dart و `routes.json`.
- خروجی: ۳۰ سطح (۱۲ صفحهٔ استودیو + ۱۸ ویژگی کلاینت)، ۸۱ endpoint یکتا، صفر رانش قرارداد.
- گیت در CI با سه حالت قرمز آزموده شد: endpoint خارج از قرارداد، صفحهٔ تازهٔ بی‌تست، نقشهٔ کهنه.
- خط مبنا هفت سطح بی‌تست را قفل کرد؛ عدد فقط می‌تواند کم شود.
- گپ ثبت‌شده: نگاشت مسیر به جدول DB و بازبینی «چه کسی دکمه را می‌بیند» هنوز دستی است.
- قدم بعد: فاز ۲ — فروشگاه نمایش‌محور و endpoint وضعیت باز/بسته.

## افزودهٔ آخر: فاز ۲ — فروشگاه نمایش‌محور (بک‌اند و استودیو)

- `GET /shop/status` اضافه شد؛ منبع حقیقت باز/بسته بودن سرور است، نه ساعت دستگاه.
- نوشتن سبد و تسویه fail-closed شد: پاسخ ۴۰۹ با کد `shop_online_closed` و پیام فارسی.
- پرچم `MP_SHOP_ONLINE_PURCHASE_ENABLED` پیش‌فرض خاموش است؛ M59 با پرچم روشن اجرا می‌شود تا موتور پول بی‌پوشش نماند.
- استودیو بنر بسته‌بودن نشان می‌دهد و تب سبد و دکمهٔ خرید را پنهان می‌کند.
- شاهد: بک‌اند ۹۶۳ قبول / ۲ رد‌شده، استودیو ۲۳۶ قبول / ۹ رد‌شده، `tsc` و build پاک، نقشهٔ تعامل بازتولید شد (۱۳۸ مسیر).
- باقی‌ماندهٔ فاز ۲: کلاینت Flutter (بدون toolchain محلی، ادعا نمی‌شود)، و بستن تب سبد در کلاینت.

## افزودهٔ آخر: فاز ۳ — حذف درگاه پرداخت اینترنتی

- آداپتر زرین‌پال و انتخابگر آن حذف شد؛ `payment_gateway` حالا `manual` (پیش‌فرض)، `mock` یا `sandbox` است و دو حالت آزمونی در production رد می‌شوند.
- متدهای مجاز پرداخت: نقدی، کارت‌خوان، کارت‌به‌کارت، کیف‌پول. درگاه اینترنتی ۴۲۲ می‌گیرد.
- مسیر `start` در حالت manual با ۴۰۹ و کد `online_gateway_removed` بسته است؛ دادهٔ تاریخی خواندنی ماند.
- استودیو: گزینهٔ درگاه و جریان authority حذف شد؛ دکمهٔ «تأیید دریافت نقدی/کارت‌خوان» جایش را گرفت.
- تست‌های `test_q6_gateway` و `test_sandbox_bank` بازنویسی شدند (متد `card_to_card`)، حذف نشدند.
- شاهد: بک‌اند ۹۶۹ قبول / ۲ رد‌شده، استودیو ۲۳۶ قبول / ۹ رد‌شده، `tsc` و build پاک.

## افزودهٔ آخر: فاز ۴ (نیمهٔ اول) — مرزهای نشست

- باگ: `verify_otp` برای کاربر غیرفعال توکن صادر می‌کرد؛ حالا ۴۰۱ و مصرف کد.
- شش تست تازه در `test_phase4_identity_session.py`: یک قرمز اول و پنج رگرسیون.
- شاهد: بک‌اند ۹۷۵ قبول / ۲ رد‌شده؛ `ruff` پاک.
- باقی‌مانده: نشست Flutter و مدیریت دستگاه‌های فعال.

## افزودهٔ آخر: فاز ۴ (نیمهٔ دوم) — مدیریت دستگاه‌ها

- `GET /api/v1/auth/sessions`: فهرست نشست‌های فعالِ خودِ کاربر با `id`، `device_info`، `created_at`، `expires_at` و `current`. هش توکن (`token_hash`/`sid`) هرگز برنمی‌گردد؛ شناسهٔ عمومی `RefreshToken.id` است.
- `DELETE /api/v1/auth/sessions/{id}`: ابطال یک دستگاه؛ نشست کاربر دیگر ۴۰۴ می‌گیرد (وجودش لو نمی‌رود) و نشست منقضی/ابطال‌شده هم ۴۰۴.
- `rbac`: دو policy تازه برای `member` — `GET /auth/sessions` و `DELETE /auth/sessions/*`.
- تست‌ها: `test_phase4b_device_sessions.py` (۵ تست، قرمز اول چون endpoint نبود) + `tests/deviceSessions.test.tsx` (۴ تست با `fetch` واقعیِ stub‌شده تا مسیر URL دیده شود).
- استودیو: بخش «دستگاه‌های فعال» در صفحهٔ تنظیمات؛ نشست جاری برچسب «این دستگاه» و بدون دکمهٔ ابطال؛ ابطال فقط پس از پاسخ سرور و با بازخوانی فهرست.
- شاهد: بک‌اند ۹۸۰ قبول / ۲ رد‌شده (۹۷۸ + ۲ مسیر‌آرتیفکت پس از بازتولید `api/routes.json`)، استودیو ۲۴۰ قبول / ۹ رد‌شده، `tsc -b` و `npm run build` پاک، `ruff check`/`ruff format --check` پاک، قرارداد ۱۲۴ مسیر / ۱۴۰ عملیات.

## افزودهٔ آخر: فاز ۵ — نقش و مجوز شخصی (QF-02/03/04)

- QF-02: `POST|DELETE /admin/users/{id}/role` فقط با `super_admin`. پیش‌تر `admin` هم می‌توانست نقش بدهد؛ آن مسیر ارتقای سطح بود.
- QF-03: `admin_permissions` + `app/security/grants.py`. کلیدهای شناخته‌شده: `finance.write`، `finance.read`، `reports.confidential`، `roles.manage`، `flags.write`. کلید ناشناخته ۴۰۰ `unknown_permission`، هدف مالک ۴۰۰ `owner_needs_no_permission`، نبود ردیف = ۴۰۳ `permission_required`.
- پول برای `admin`/`manager` پیش‌فرض بسته است؛ `reception`/`coach`/`member` دست‌نخورده‌اند (RBAC خودشان). مالک همیشه مجاز است.
- استودیو: `AdminPermissions.tsx` در تنظیمات — انتخاب کاربر/کلید/مدت، جدول وضعیت مؤثر (فعال/منقضی/سلب‌شده)، سلب با تأیید؛ برای غیرمالک هیچ درخواستی نمی‌فرستد و رندر نمی‌شود.
- شاهد: بک‌اند **۹۸۷ قبول / ۲ رد‌شده**، استودیو **۲۴۴ قبول / ۹ رد‌شده**، `tsc -b` و build پاک، `ruff` پاک، قرارداد **۱۲۷ مسیر / ۱۴۴ عملیات**، migration drift سبز.

## افزودهٔ آخر: فاز ۶ (لوپ اول) — کارت‌به‌کارت با فیش

- آپلود فیش: `POST /payments/{id}/receipt` (multipart) — فقط عضو صاحب پرداخت، نوع از محتوا با Pillow، سقف ۵ مگابایت، فایل خصوصی `var/receipts/<random>.<ext>` با `0600`؛ پاسخ ۲۰۲ + `review_id` + TTL ۴۸ ساعت.
- تأیید/رد: `POST /payments/{id}/approve|reject` با مجوز `finance.write`؛ تأیید یک تراکنش است (پرداخت + رسید + اشتراک `plan_key` + اعلان + audit)، منع تأیید پرداخت ساختهٔ خود.
- idempotency: `idempotency_key` + ایندکس یگانهٔ جزئی؛ درخواست تکراری همان پرداخت را برمی‌گرداند.
- استودیو: `ReceiptQueue` در صفحهٔ مالی؛ تأیید/رد با antd، بدون خوش‌بینی؛ خطای سرور نمایش داده می‌شود.
- شاهد: بک‌اند **۹۹۹ قبول / ۲ رد‌شده**، استودیو **۲۴۸ قبول / ۹ رد‌شده**، `tsc -b` و build پاک، `ruff` پاک، قرارداد **۱۲۹ مسیر / ۱۴۷ عملیات**، سناریوها در `docs/MuscleParadise/evals/phase6-money-scenarios.md`.
- `BLOCKED`: انتقال واقعی پول بانکی/تأیید کارت‌به‌کارت با شاهد انسانی؛ آپلود از کلاینت Flutter (toolchain محلی نیست).

## افزودهٔ آخر: فاز ۷ (گیت مالکیت) و فاز ۸ (outbox)

- فاز ۷: `test_phase7_member_scope_sweep.py` — ۱۷ مسیر GET با `{member_id}` از قرارداد زنده خوانده و با توکن عضو دیگر آزموده می‌شود؛ ۱۹ قبول. دو تست متا جلوی «سبزیِ توخالی» را می‌گیرد.
- فاز ۸: outbox تراکنشی `modules/outbox/service.py` + `jobs/outbox_relay.py` + migration `e3f4a5b6c7d8`؛ رویداد پول در همان commit، claim انحصاری، retry/backoff، dead-letter، dedup. پنج تست.
- QF-21 inbox: `modules/outbox/inbox.py` + `inbox_messages` (migration `f4a5b6c7d8e9`)؛ تحویل تکراری ← `duplicate`، خطای handler ← rollback پیام، رقابت ← کلید یکتا. relay نمونه از inbox رد می‌شود.
- شاهد: بک‌اند **۱۰۲۷ قبول / ۲ رد‌شده**، `ruff` پاک، قرارداد بدون تغییر مسیر (**۱۲۹ مسیر / ۱۴۷ عملیات**).
- `BLOCKED`: push/SMS واقعی، PostgreSQL در استقرار، امضای release، دستگاه اندروید، Flutter toolchain.

## افزودهٔ آخر: فاز ۶ لوپ ۲–۳ (دفتر پول QF-05، هزینهٔ خارجی QF-06)

- **دفتر پول (`QF-05`):** `ledger_entries` (migration `a5b6c7d8e9f0`) با مبلغ **علامت‌دار**، `kind` در charge/pay/refund/reversal، کلید idempotency با ایندکس یکتای جزئی، `reverses_entry_id`/`reversed_by_entry_id`؛ `wallet_charge`/`wallet_pay` در همان commit ردیف می‌نویسند. `GET /payments/ledger/{member_id}` (با `ensure_member_scope`) و `POST /payments/ledger/{entry_id}/reverse` (دلیل ۳–۲۰۰ نویسه، `finance.write`، audit `ledger_reversal`، ۴۰۰ برای معکوس تکراری). `reconcile()` مجموع دفتر را با موجودی کیف‌پول می‌سنجد.
- **هزینهٔ خارجی (`QF-06`):** `expenses` + `expense_revisions` (migration `b6c7d8e9f0a1`)؛ هشت دستهٔ ثابت، مبلغ ≥ ۱۰۰۰ ریال، حذف **نرم**، هر اصلاح/حذف دلیل اجباری دارد و قبل/بعد را در تاریخچه نگه می‌دارد. `GET /expenses?from=&to=` جمع بازه و تفکیک دسته را برمی‌گرداند؛ نوشتن `finance.write` و خواندن `finance.read` **جدا** هستند.
- **استودیو:** `LedgerPanel` در صفحهٔ مالی (موجودی/تطبیق/معکوس‌سازی با دلیل؛ بدون درخواست در mount) و صفحهٔ تازهٔ «هزینه‌ها» با کنترل‌های antd و تقویم جلالی + مدال دلیل.
- **شاهد:** بک‌اند **۱۰۴۶ قبول / ۲ رد‌شده**، استودیو **۲۶۲ قبول / ۹ رد‌شده**، `ruff` و `tsc -b`/build پاک، قرارداد بازتولید‌شده **۱۳۳ مسیر / ۱۵۳ عملیات**، نقشهٔ تعامل ۳۱ سطح / رانش صفر، migration drift صفر. تست‌ها: `test_phase6b_ledger.py` (۹)، `test_phase6c_expenses.py` (۹)، `tests/ledgerPanel.test.tsx` (۶)، `tests/expensesPage.test.tsx` (۸).
- **QF-10 (بسته):** گزارش سود/زیان دوره‌ای با بازگشت‌ها — `GET /finance/reports/period` (هفته/ماه/سال جلالی تهران)، ستون `payments.refunded_at`، صفحهٔ مالی با نمودار recharts و هشدار «ناقص» برای بازگشت بی‌تاریخ.
- **فیش خصوصی هزینه (بسته):** `POST/GET /expenses/{id}/receipt` با همان اعتبارسنجی فیش پرداخت؛ یک فایل برای هر هزینه؛ migration `632164e8c647`.
- **باقی‌مانده:** انتقال واقعی پول بانکی همچنان `BLOCKED`؛ M4/G5 و G2 منتظر تصمیم مالک.

## افزودهٔ آخر: فاز ۸ لوپ ۳–۶ (گزارش زمان‌بندی‌شده، پروکسی معتمد، worker/متریک، نگهداری)

- **QF-23:** `report_runs` + `modules/reports/schedule.py`؛ idempotency روی `(job_key, run_date)` با سبد روزِ `Asia/Tehran`، اعداد فقط با `finance.read`، ممیزی بدون مبلغ، cron ۰۰:۱۰ تهران. ۷ تست.
- **QF-26:** `app/security/proxy.py` — `X-Forwarded-For` فقط از peer معتمد، پیمایش راست‌به‌چپ، fail-closed؛ کلید rate-limit همان IP است. `MP_TRUSTED_PROXIES` در DEPLOYMENT. ۶ تست.
- **QF-27:** `worker_heartbeats` + `modules/outbox/health.py`؛ heartbeat در هر دور relay، gaugeهای صف در `/metrics`، `/health/ready` با `MP_REQUIRE_WORKER`. ۶ تست + جدول هشدار در OPS-RUNBOOK.
- **QF-28:** `modules/privacy/retention.py`؛ پیش‌نمایش/اجرای حذف دادهٔ منقضی فقط `super_admin`، ممیزی `retention_run` بدون دادهٔ شخصی، پول/دفتر/هزینه دست‌نخورده. ۵ تست + بخش کدشده در DATA-RETENTION.
- **شاهد:** بک‌اند **۱۰۶۹+ قبول / ۲ رد‌شده** (پس از رفع دو خطای شمارش در همین نشست: `oldest_pending_age` منفی و مسیر `/metrics`)، `ruff` پاک، قرارداد **۱۳۸ مسیر / ۱۵۸ عملیات**، نقشهٔ تعامل ۳۱ سطح / رانش صفر، drift صفر.
- **`BLOCKED`:** هشدار واقعی Prometheus/Alertmanager، Valkey برای rate-limit توزیع‌شده، تأیید حقوقی مدت‌های نگهداری، push/ایمیل گزارش، PostgreSQL/backup، امضا و دستگاه.

## افزودهٔ آخر: QF-32 — جاروی انتشار

- `tests/integration/test_phase8_release_sweep.py` یک جریان پول end-to-end را در یک نسخه می‌سنجد: مجوز ← شارژ ← پرداخت نقدی و `verify` ← هزینه ← گزارش روزانه (`net = دریافت − هزینه`) ← تطبیق دفتر ← نگهداری (صفر حذف) ← معکوس‌سازی (موجودی صفر، گزارش snapshot ثابت).
- **شاهد نهایی این شاخه:** بک‌اند **۱۰۷۱ قبول / ۲ رد‌شده**، استودیو **۲۶۲ قبول / ۹ رد‌شده**، `ruff`/`tsc -b`/build پاک، قرارداد **۱۳۸ مسیر / ۱۵۸ عملیات**، نقشهٔ تعامل ۳۱ سطح/رانش صفر، `deploy_gate` ۱۲/۰/۰، migration drift صفر، CI شاخه ۸/۸ سبز (commit `2e6685e`).
- **گیت انتشار باز می‌ماند:** امضا/دستگاه/بانک واقعی/PostgreSQL+pgBackRest/ابر/تأیید مالک `BLOCKED`.

## یک‌دست‌سازی شاخه‌ها (۲۰۲۶-۱۱-۲۰)

- هر سه شاخهٔ دوردست عقب‌افتاده بررسی و **مرج نشدند**؛ دلیل با اندازه‌گیری ثبت شده: ۲۱۱ و ۲۴۱ کانفلیکت، بازگشت ۹۲۹/۵۱ فایل `.claude/`، افزودن ۵۵/۵۹ مگابایت keystore+APK (که `main` عمداً ندارد) و عقب‌بودن کد (۲۲۶ خط از `payments/service.py` فعلی در شاخه نیست).
- Inventory: هیچ کار یکتایی گم نشد؛ همهٔ فایل‌های دامنه در `main` هستند (۳۷۹+۸۷ و ۱۵۰+۷۲ عیناً/تقریباً عیناً) و تنها فایل‌های «غایب» `data/mock.ts` و `AnimatedCounter.tsx` هستند که عمداً حذف شده‌اند.
- اقدام: تگ‌های `archive/arena-{86fc9529,a0408b29,4f336f66}-mp` + حذف چهار شاخهٔ دوردست (شامل `arena/3b2b9471-mp` که کاملاً در `main` بود). اکنون `origin` فقط `main` دارد.
- جزئیات، جدول شاهد و دستور بازیابی: [BRANCH-CONSOLIDATION-2026-11-20](BRANCH-CONSOLIDATION-2026-11-20.md).

## قاعدهٔ شاخه (تصمیم مالک ۲۰۲۶-۱۱-۲۰)

- **یک تنه:** `main` تنها شاخهٔ دائمی؛ توسعه در یک شاخهٔ کوتاه‌عمر، merge، و حذف همان شاخه در همان لحظه.
- **وضعیت لحظه:** `origin` فقط `main` دارد: `arena/d70c5b7a-mp` (مرج‌شده در `24b2bba`) حذف شد؛ سه شاخهٔ فسیل قبلی هم با تگ آرشیو پاک شده بودند.
- **بهای پذیرفته‌شده:** هر push مستقیم به `main` ریسک شکستن تنه را دارد ⇒ قاعده: فقط PR + CI سبز. تاریخچه با merge commit (نه squash) نگه داشته می‌شود تا revert ساده باشد.
- **تنظیم دستی لازم:** GitHub → Settings → General → «Automatically delete head branches» (توکن ما 403 می‌گیرد).
- جزئیات و دستورها: بخش ۷ [TOOLING-RUNBOOK](TOOLING-RUNBOOK.md)؛ شاهد فسیل‌ها: [BRANCH-CONSOLIDATION-2026-11-20](BRANCH-CONSOLIDATION-2026-11-20.md).
