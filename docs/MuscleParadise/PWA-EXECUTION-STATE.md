# وضعیت اجرای PWA — دفتر چرخه‌ها و شواهد

CURRENT_BRANCH=arena/5e0f64cf-mp
REMOTE_HAS_MY_COMMIT=yes
MAIN_HEAD=352781043ad2ba202d8b3b459df1ce7e3d914ef7
BRANCH_AHEAD_OF_MAIN=9
LAST_KNOWN_EVIDENCE=evidence/2026-11-27/INV-02, INV-03, SEC-01 (on branch) / evidence/m60 (on main)

> **نوع سند:** دفتر اجراییِ افزایشی؛ نه ADR، نه مرجع مستقل برای تعریف acceptance، و نه ادعای QA/release. شناسه‌ها و معیارهای هر کارت از tracker و backlog canonical پیروی می‌کنند.
> **تاریخ مرجع:** ۲۰۲۶-۱۱-۲۳ UTC. این تاریخ با timestampهای GitHub آینده‌نما که در handoff ثبت شده‌اند تعارض دارد؛ آن تعارض حل‌نشده باقی می‌ماند.

## منابع canonical و تقدم

- **تصمیم محصول:** [ADR-006](adr/006-shared-react-pwa.md) و [ADR-007](adr/007-pwa-primary-release.md)، همراه [دفتر تصمیم‌های مالک](OWNER-DECISIONS.md).
- **پذیرش و ترتیب کارت‌ها:** [TODO اجرایی انتشار PWA](TODO-PWA-RELEASE-2026-11-23.fa.md) و [backlog canonical پنجاه parent](TODO-2026-11-16.md#pwa-ui-ux-full-backlog-2026-11-23).
- **خلاصهٔ نشست:** [SESSION_HANDOFF](SESSION_HANDOFF.md)؛ این فایل وضعیت بین چرخه‌ها را ثبت می‌کند و جایگزین آن دو صف نمی‌شود.
- **شواهد:** مسیرهای پالایش‌شدهٔ `../../evidence/<تاریخ-مرجع>/<ID>/`؛ تاریخ مرجع پوشه را با marker زمان واقعی اجرا (و محدودیت‌های آن) جدا ثبت کنید؛ هر نتیجه فقط به همان command، toolchain، checkout و SHA/worktree fingerprint تعلق دارد.

در تعارض، تصمیم scope با ADR/تصمیم مالک، متن acceptance با کارت canonical، رفتار با کد و تست همان مسیر، و status اجرایی با آخرین شاهد پالایش‌شده تعیین می‌شود. Snapshotهای تاریخی، دیاگرام‌ها، screenshotها، artifact package، mock، skipped test و CI روی SHA دیگر acceptance محصول را ثابت نمی‌کنند.

## ادامهٔ جاری — INV-02/03 v2 و ماتریس SEC-01 (۲۰۲۶-۱۱-۲۷ UTC)

- **شاخه و همگام‌سازی:** `CURRENT_BRANCH=arena/5e0f64cf-mp`; `origin/main=352781043ad2ba202d8b3b459df1ce7e3d914ef7`. پس از fetch، `git merge --no-edit origin/main` پاسخ `Already up to date` داد؛ تعارض صفر و main از قبل در ancestry شاخه بود. remote branch، checkpoint مستنداتی `f06f2a95305082e01e33b157396f0dfc0128613d` را دارد؛ `MAIN_HEAD` و شاخص‌های branch در پنج خط ابتدای این سند ثبت‌اند. PR #29 با squash merge ادغام شد؛ عدم ancestry commitهای شاخه به‌تنهایی به معنی حذف محتوا از main نیست. یک commit نهایی evidence/docs و push آن پس از gateها در همین شاخه برنامه‌ریزی شده است؛ تاریخچه rewrite نمی‌شود.
- **INV-02/03 v2:** [crosswalkهای خام](../../evidence/2026-11-27/INV-02/member-capability-crosswalk.md) و [کارکنان](../../evidence/2026-11-27/INV-03/staff-page-crosswalk.md) با `scripts/crosswalk_v2.py` روی SHA=`f06f2a95305082e01e33b157396f0dfc0128613d` اجرا شدند؛ هر دو worktree با tracked docs dirty و untracked بوده، product tracked source تغییر نداشت. v1 byte-for-byte در `INV-02-v1/` و `INV-03-v1/` حفظ شد. شمارش‌ها: member `PARTIAL_REVIEW=14/GAP=3`; staff `PARTIAL_REVIEW=12/GAP=0`.
- **حد v2:** Analytics در `adminApi.ts` و alias `ALL_STAFF` اکنون در output دیده می‌شوند. ولی `dynamic_sites=0` و هیچ `DYNAMIC_UNCOVERED` تولید نشد؛ regex در template interpolation قطع می‌شود و check-in نمونهٔ prompt در source فعلی وجود ندارد (Flutter route در scope scanner TS نیست). مرور دستی فقط در reviewهای جدا ثبت شد؛ rawها patch نشدند. هر دو crosswalk `PARTIAL/NOT_ACCEPTED` می‌مانند؛ تفکیک consumer عضو از پنل کارکنان دستی است؛ اشارهٔ تستی، اجرای تست یا مجوز نیست.
- **SEC-01 matrix:** [`rbac-matrix.txt`](../../evidence/2026-11-27/SEC-01/rbac-matrix.txt) همهٔ `163` operation / `141` path در `routes.json` را با شش نقش در تابع `security.rbac.enforce` سنجید؛ `978` تصمیم policy در همان SHA=`f06f2a9...`. این جدول static policy است، نه HTTP پاسخ، grant/owner scope یا anonymous matrix.
- **SEC-01 negative و full pytest:** سه TestClient integration تست منفی عضو A→B در `members`, `assessments`, `payments`, `chat`, `checkin` را پاس کردند (`3 passed/0 failed`, یک warning). کل suite در `mp-app/backend` روی `claimed_sha=tested_sha=f06f2a95305082e01e33b157396f0dfc0128613d` اجرا شد: `1336 passed, 2 skipped, 2 warnings`, exit `0`. گزارش‌ها در [`SEC-01`](../../evidence/2026-11-27/SEC-01/role-server-slice-v2.md) هستند. SEC-01 فقط `PARTIAL` است؛ ماتریس static جای test HTTP برای تمام route×role/resource را نمی‌گیرد و checkbox باز می‌ماند.
- **سابقه و گاردریل:** slice قدیمی `90 passed/2 warnings` در `evidence/2026-11-23/SEC-01/` مربوط به اجرای ثبت‌شده در `2026-11-23 UTC` روی SHA=`352781043ad2ba202d8b3b459df1ce7e3d914ef7` است؛ آن شاهد از run فعلی جداست. هیچ role/grant/API/DB/Flutter/native source تغییر نکرد. `PWA-01=PROPOSED/NOT_RUN`, checkboxهای INV/SEC باز و release `NO-GO` هستند.
- **گیت‌های مستندات:** `python3 scripts/docs_gate.py` پس از ثبت و stage خروجی‌ها PASS شد: ۳۸ Markdown، ۶۰۶ local links، ۱۵ Mermaid؛ `git diff --check` و `git diff --cached --check` نیز PASS. transcript در `evidence/2026-11-27/SEC-01/docs-gate.txt` و `diff-check.txt` است. این گیت‌ها فقط کیفیت مستندات را می‌سنجند، نه acceptance محصول.
- **گام بعدی:** پس از commit/push evidence محدود و draft PR به main، صف `WEB-01…WEB-11` را طبق acceptance ادامه دهید؛ browser/OS/device/reviewer خارج از محیط `BLOCKED/NOT_RUN` می‌ماند و PWA/release ارتقا نمی‌یابد.

## Snapshot پیشین — بازنشانی اجرا پس از بررسی remote (۲۰۲۶-۱۱-۲۳ UTC)

- **شاخه/گراف مشاهده‌شده:** شاخهٔ فعال `arena/5e0f64cf-mp`؛ `HEAD=e0ae95f48bf8451bd59b972a92c55fed404e6a92`؛ `origin/arena/5e0f64cf-mp=3f26e1d6ea05920a23236b368abd4c4ee0580799`؛ `origin/main=352781043ad2ba202d8b3b459df1ce7e3d914ef7`. HEAD در هیچ remote-tracking ref مشاهده‌شده نیست؛ tip شاخهٔ مجاز و `origin/main` هر دو ancestor آن هستند؛ والدهای HEAD همان دو tip و tree آن عیناً با tree `origin/main` برابر است. این فقط اثبات ancestry/tree است، نه remote witness برای مستندات/evidence محلی.
- **Worktree تازه:** ۲۴ tracked تغییر، همه README/docs؛ index خالی؛ ۳۰۹ untracked پیش از افزودن snapshot جاری و ۳۱۰ شامل همان snapshot؛ صفر tracked diff زیر `mp-app/`. مسیرهای untracked، به‌ویژه receiptها، عمداً در transcript منتشر نشده‌اند و دست‌نخورده می‌مانند. fingerprint و شمارش sanitized در [`INV-01/current-snapshot.txt`](../../evidence/2026-11-23/INV-01/current-snapshot.txt).
- **معنای «STATE از صفر»:** این چرخه statusهای قبلی را خودکار به ارث نمی‌برد. محتوای موجود فقط در workspace محلی است؛ هیچ فایل/شاهدی از روی حافظه بازسازی یا به‌عنوان شاهد remote معرفی نمی‌شود. ثبت‌های قبلی حفظ‌اند، اما `DONE/PASS` مستنداتی هم تا اجرای دوبارهٔ gate مربوط در این چرخه فقط سابقه‌اند. checkboxهای canonical دست‌نخورده می‌مانند؛ status محصول/release ارتقا نمی‌یابد. cursor جاری از اولین مورد باز پس از snapshot، یعنی `INV-02`، ادامه می‌دهد.
- هیچ checkout/reset/clean/branch switch، stage انبوه، commit یا push در preflight انجام نشد؛ شاخهٔ نشست تغییر نمی‌کند. `PR #29` قبلاً `MERGED` است و دوباره ادغام نمی‌شود؛ release همچنان `NO-GO` است.
- **گاردریل ثابت:** یک PWA مشترک React در `mp-app/studio/`؛ Flutter/Android، Electron و همهٔ workflow/testهای native حفظ شوند؛ شش نقش و تک‌باشگاه، SQLite فعلی، کارت‌به‌کارت با تطبیق انسانی، Shop نمایش‌محور، QR با اعتبارسنجی server-side و بدون face recognition، فقط fixture ساختگی و UI کتابخانهٔ موجود.

## صف و وضعیت

| ترتیب | شناسه/گروه | وضعیت این دفتر | شاهد/یادداشت |
|---:|---|---|---|
| 1 | `DOC-01…DOC-04` | `DONE` در tracker پیشین | رجیستر تصمیم‌های باز و اصلاحات تاریخی ثبت شده‌اند؛ این دفتر status آن‌ها را دوباره ارزیابی نمی‌کند. |
| 2 | `DOC-05` — ردیابی تصمیم‌ها و مرز شاهد | `PASS — docs-only, local; remote-DONE pending` | Re-run در 2026-11-27 UTC (directory baseline `2026-11-23`) در `../../evidence/2026-11-23/DOC-05/docs-gates-reset-rerun.txt`: traceability ۲۴ سند، docs/guide/map/hygiene/diff و Mermaid syntax ۲۷/۲۷ PASS؛ هیچ پذیرش محصولی ادعا نشده. |
| 3 | `DOC-06` — عدم حدس در تصمیم‌های حساس | `PASS — مرزبندی مستنداتی محلی; Ruff blocker ثبت‌شده` | Re-run در `../../evidence/2026-11-23/DOC-06/current-cycle-backend-revalidation.txt`: ۳۴ تست synthetic پاس/۱ warning؛ Ruff check همان ۹ فایل ۹ finding و exit=1؛ format پاس؛ هیچ policy یا approval انسانی حدس/اجرا نشد. remote-DONE pending. |
| 4 | `INV-01` — snapshot غیرمخرب | `PASS local — snapshot only; remote-DONE pending` | [`current-snapshot.txt`](../../evidence/2026-11-23/INV-01/current-snapshot.txt): HEAD=`e0ae95f…` در remote شاخه نیست؛ tree با `origin/main` برابر؛ ۲۴ tracked docs change، index خالی، ۳۰۹ untracked پیش از self-record؛ ۰ tracked product diff. هیچ فایل private فهرست/باز نشد. |
| 5 | `INV-02` — crosswalk کامل عضو (`PWA-01`) | `PARTIAL — crosswalk draft / NOT_ACCEPTED` | Crosswalk ۲۱ ردیفی/۱۷ feature؛ v3 rerun=۶۰/۶۰ literal shape-match (`../../evidence/2026-11-23/INV-02/member-static-inventory-v3-rerun.txt`). Studio روی dirty worktree با tracked product-source diff=0: `npm ci`, lint, build PASS؛ ۵۲ فایل/۳۶۲ تست PASS و ۲ فایل/۱۰ test skip (`studio-current-cycle-validation.txt`). این clean-tree/provenance claim نیست: snapshot جاری ۱۱۷ untracked path entry زیر `mp-app` دارد (نام‌ها حذف، محتوا بررسی‌نشده؛ `../../evidence/2026-11-23/INV-06/local-state-sanitized.txt`). Flutter toolchain، browser/device و reviewer در دسترس/اجرا نشدند؛ `/member` placeholder، policy/safety blockers پابرجا. checkbox باز، canonical `PWA-01=PROPOSED/NOT_RUN`. |
| 6 | `INV-03` — crosswalk کارکنان | `PARTIAL — static route/API/role inventory / NOT_ACCEPTED` | Script rerun: ۱۲ Studio page، ۵۹ endpoint shape، map ۳۱ surface/۱۶۳ operation، state field ندارد و `members`/`analytics` test ref ندارند؛ DB owner/error/persistence و action behavior هنوز ناقص. شاهد جاری `../../evidence/2026-11-23/INV-03/staff-crosswalk-static-rerun.txt`; checkbox باز. |
| 7 | `INV-04…INV-09` — وضعیت چهارگانه و inventory/acceptance باقی‌مانده | `INV-04/05/06 PARTIAL — scoped slices verified; full cards open` | `../../evidence/2026-11-23/INV-04/member-status-slice.txt`; `../../evidence/2026-11-23/INV-05/dashboard-current-cycle-test.txt`; `../../evidence/2026-11-23/INV-06/dashboard-actor-data-slice.txt` (۳۴ backend tests/۲ warnings). Staff/data surfaces و field-level ownership gaps بازند؛ همهٔ checkboxes باز؛ next independent `INV-07` CI baseline capture for exact candidate. |
| 8 | `SEC-01…SEC-10` | `NOT_STARTED` در این چرخه | fixture و source محلی فقط؛ policy/independent review بیرونی جدا می‌ماند. |
| 9 | `WEB-01…WEB-11` | `NOT_STARTED` در این چرخه | اجرای browser روی build واقعی لازم است؛ emulation یا screenshot جای دستگاه/OS نیست. |
| 10 | `MEM-01…MEM-16`, `STAFF-01…STAFF-08`, `QA-01…QA-09` | `NOT_STARTED` در این چرخه | هر مورد طبق acceptance و گیت وابستگی خودش. |
| 11 | `OPS-01…OPS-14`, `PRIV-01/02` | `NOT_STARTED` در این چرخه | محیط/اپراتور/مقصد واقعی یا reviewer غایب ⇒ `BLOCKED/UNKNOWN`، نه PASS. |

Statusهای product-parent از tracker تغییر نمی‌کنند مگر evidence مستقیم همان کارت روی candidate ثبت شود: `PWA-04`, `PWA-11` و `PWA-17` همچنان `PARTIAL`; `PWA-00` فقط ثبت تصمیم است. شواهد Nginx build‌شده با upstream ساختگی، unit/mock/headless یا CI روی commit دیگر هیچ‌یک این statusها را به acceptance کامل ارتقا نمی‌دهد.

## ثبت چرخه‌ها

### DOC-05 — ردیابی تصمیم‌ها

- **Acceptance canonical:** در اسناد جاری به ADR/TODO مربوط لینک شود؛ دیاگرام، screenshot، handoff package و Option 03 به‌صراحت طراحی/مرجع، نه شاهد پیاده‌سازی، باشند؛ اسناد تاریخی بی‌صدا حذف/بازنویسی نشوند.
- **دامنهٔ مرور:** tracker و backlog PWA، ADR-006/007، handoff، docs/architecture index، اسناد Option 03 و PWA تاریخی، برنامهٔ تولید، و crosswalkهای PWA/Motion که برای وضعیت جاری ارجاع می‌شوند. اسناد تاریخی با الحاقیهٔ تاریخ‌دار cross-link می‌شوند؛ متن snapshot و خود assetها حفظ می‌شوند.
- **وضعیت چرخهٔ صفر:** `PASS local — مستندات فقط; remote-DONE pending`. ۲۴ سند PWA/تصمیم/راهنما به ADR/TODO/tracker/state مربوط cross-link شدند؛ Option 03 و نمودارها/screenshotها مرجع طراحی، نه شاهد اجرای PWA، برچسب خوردند. متن تاریخی دست‌نخورده ماند و فقط الحاقیهٔ تاریخ‌دار افزوده شد.
- **Traceability audit:** [`traceability_audit.py`](../../evidence/2026-11-23/DOC-05/traceability_audit.py) فقط marker-presence را روی ۲۴ سند PASS گزارش کرد؛ مقصد لینک‌ها و Mermaid/SVG جداگانه با `docs_gate.py` سنجیده شدند. نخستین audit نبودن block تازهٔ handoff را یافت؛ پس از افزودن block دوباره PASS شد. خروجی نهایی پس از اصلاح handoff در `../../evidence/2026-11-23/DOC-05/doc-gates-after-handoff-fix.txt` است؛ اجرای پیشین با شکست marker در handoff حفظ شده است.
- **گیت‌های مستندات:** روی worktree dirty با `HEAD=e0ae95f48bf8451bd59b972a92c55fed404e6a92`: ۳۸ Markdown، ۶۰۵ لینک محلی، ۱۵ Mermaid؛ project-guide `--check`, interaction-map (۳۱ سطح/۱۶۳ مسیر/رانش صفر), hygiene و `git diff --check` همگی PASS. raw/fingerprint در `../../evidence/2026-11-23/DOC-05/doc-gates-after-handoff-fix.txt`؛ نتیجه فقط مستندات است، نه product QA.
- **Revalidation چرخهٔ صفر (local-only; run 2026-11-27 UTC):** `docs-gates-reset-rerun.txt` روی همان HEAD و worktree مستنداتی dirty: traceability ۲۴ سند PASS؛ `docs_gate.py` ۳۸ Markdown/۶۰۵ لینک/۱۵ Mermaid PASS؛ project-guide `--check`, interaction-map ۳۱/۱۶۳/drift=0، repo hygiene و `git diff --check` PASS؛ Mermaid syntax gate با Node `v22.22.3`, npm `10.9.8`, Mermaid `11.17.2`، ۲۷/۲۷ diagram PASS. نسخهٔ کامل command/output در `../../evidence/2026-11-23/DOC-05/docs-gates-reset-rerun.txt`. این gateها فقط مستندات‌اند.
- **نتیجهٔ پذیرش:** `PASS local — DOC-05 scope only`; تا commit/push و شاهد remote `DONE` نیست؛ هیچ implementation/browser/device/release claim.

### DOC-06 — تصمیم‌های حساس را حدس نزنید

- **Acceptance canonical:** نگهداری داده، مشاهده/حذف سلامت، تعریف سود/درآمد، تطبیق بانکی، مدت اعتبار QR و مجوزهای جزئی فقط از منبع مصوب اجرا شوند؛ جزئیات ناکافی ⇒ `BLOCKED/UNKNOWN`.
- **وضعیت چرخهٔ صفر:** `PASS local — ثبت no-guess boundary; Ruff failure disclosed; remote-DONE pending`؛ مواردی که نیاز به مالک، reviewer یا پذیرش کارت مستقل دارند صریحاً باز می‌مانند. این بسته نه approval حقوقی/مالی است و نه مجوز تغییر code policy.

| حوزه | منبع/شاهد مشاهده‌شده | حکم امن / وضعیت |
|---|---|---|
| Retention و حذف سلامت | `DATA-RETENTION.md` خودش را پیش‌نویس مهندسی می‌نامد؛ جدول ثابت ۳۶ماهه/سایر مدت‌ها مجوز حقوقی نیست. `modules/privacy/retention.py` فقط audit/inbox/read notifications/report runs را کد می‌کند؛ comment همان module و سربرگ `test_phase8_privacy.py` می‌گویند report runs حذف نمی‌شود، اما implementation قدیمی‌تر از ۷۳۰ روز را حذف می‌کند و fixture تست این ردیف را نمی‌آزماید. | تعارض سند/code/test و نبود review حقوقی/حریم (`OD-05=BLOCKED`)؛ policy واقعی نگهداری، right-to-erasure و دادهٔ سلامت `BLOCKED/UNKNOWN`. هیچ retention/delete تازه‌ای اجرا نشد. |
| مشاهده/حذف سلامت و بیومتریک | test privacy صریحاً حذف به درخواست عضو را خارج از scope می‌گذارد؛ کلید `reports.confidential` در code وجود دارد اما ماتریس کامل دسترسی/حذف نیست. عکس پیشرفت بدن در ADR-007 از scope انتشار اول خارج است و face recognition سروری نیز خارج scope است. | دسترسی/مدت/درخواست حذف دادهٔ سلامت تا review مجاز `BLOCKED`; سیاست بیومتریک قدیمی authority فعال نیست؛ هیچ مسیر face/health تازه‌ای فعال نشد. |
| تعریف درآمد/سود | `TODO-CLOUD-FINANCE-ACCESS.md` تعریف حسابدار برای درآمد شناسایی‌شده/هزینه/سود را باز می‌گذارد. `modules/reports/period.py` امروز paid/refunded/expenses را طبق کد جمع و `profit=net−expenses` می‌کند؛ UI `PeriodReportPanel` در `complete=false` سود را unknown می‌کند، اما این فرمول code behavior است نه accounting sign-off. | تعریف حسابداری/مالی رسمی `BLOCKED`; incomplete را سود قطعی/صفر نخوان؛ test fixture پذیرش حسابدار یا بانک نیست. |
| تطبیق بانکی | تصمیم محصول کارت‌به‌کارت با بررسی انسانی و منبع بانکی مستقل است؛ رسید به‌تنهایی proof واریز نیست. مقصد/منبع/ساعات/اپراتور عملیاتی در `OD-07=OPEN` هستند و live merchant در scope نیست. | تطبیق واقعی و فعال‌سازی مالی `BLOCKED` تا actor/مرجع مستقل مجاز؛ هیچ حساب/بانک/provider واقعی استفاده نشد. |
| TTL QR | source `create_checkin_qr_token` در `jwt.py` زمان `exp=now+2 minutes` می‌سازد و TODO canonical M65 دو دقیقه ثبت کرده است؛ Option 03 قدیمی `30s` را نادرست می‌گوید. integration tests expiration/replay/ownership را می‌آزمایند، نه TTL دقیق token تازه‌ساخته‌شده. | **رفتار فعلی source:** دو دقیقه؛ **مدت پذیرفته‌شدهٔ محصول:** `UNKNOWN/BLOCKED` تا `MEM-10`/QA. erratum تاریخی ثبت شد، کد تغییر نکرد. |
| مجوزهای جزئی | ADR-007/OQ-03 شش نقش را نگه می‌دارند؛ `grants.py`/`route_policy.py` و تست‌های مربوط بخشی از guardها را می‌پوشانند، نه inventory کامل route×role×permission×ownership. `OD-02=OPEN`, `PWA-02=NOT_RUN`. | نقش/grant تغییر نمی‌کند؛ ماتریس و پذیرش کامل `BLOCKED/UNKNOWN` تا کارت/تصمیم مربوط. |

- **آزمون محدود مرتبط (همه synthetic):** از `mp-app/backend/` روی `HEAD=e0ae95f48bf8451bd59b972a92c55fed404e6a92`, Python `3.11.2`, pytest `9.2.0`: پنج فایل `test_phase8_privacy.py`, `test_m65_qr_security.py`, `test_qf10_period_report.py`, `test_phase5_admin_permissions.py`, `test_routes_effective_guards.py` ⇒ `34 passed, 1 warning`. raw اجرای بازتولیدشده: `../../evidence/2026-11-23/DOC-06/backend-privacy-qr-tests-rerun.txt`. این testها سطح‌های اشاره‌شده را پوشش می‌دهند؛ policy/owner/reviewer/device/live-bank پذیرش نمی‌شود؛ diff محصول backend خالی ماند.
- **Ruff شفافیت:** `ruff 0.17.6` روی ۹ فایل مرتبط: `ruff check` **failed** با ۹ finding (`TC001/TC002` import-type rules، `RUF059` متغیر استفاده‌نشده)؛ `ruff format --check` روی همان ۹ فایل **pass**. هیچ source/test تغییر نکرد و fix ناامن خارج از DOC-06 اجرا نشد؛ بنابراین lint را PASS گزارش نکن. raw: `../../evidence/2026-11-23/DOC-06/backend-ruff-check-final.txt`, `backend-ruff-format-check-final.txt`.
- **محل شواهد:** `../../evidence/2026-11-23/DOC-06/`؛ شامل test raw، source crosswalk، Ruff stdout/stderr/exit code و marker audit.
- **Revalidation چرخهٔ صفر (همه synthetic):** Python `3.11.2`, pytest `9.2.0`: ۵ integration file ⇒ `34 passed, 1 warning`؛ Ruff `0.17.6`: `check` همان ۹ فایل `exit=1` با ۹ finding موجود (`TC001/TC002`, `RUF059`)، `format --check` `exit=0` (۹ فایل). هیچ Ruff auto-fix یا source/test edit انجام نشد. Raw: `../../evidence/2026-11-23/DOC-06/current-cycle-backend-revalidation.txt`; Ruff failure مانع ادعای lint PASS است، نه مجوز تضعیف گیت.
- **نتیجهٔ پذیرش:** `PASS local — ثبت مرز و blockerها برای DOC-06`; تا push و remote witness `DONE` نیست. تمام approvalهای سیاستی/حساس `BLOCKED/UNKNOWN/OPEN` و release `NO-GO` باقی‌اند.

### INV-01 — snapshot غیرمخرب

- **Acceptance canonical:** branch/HEAD، وضعیت tracked و untracked، نسخهٔ ابزارها و CI ثبت شوند؛ secret/PII چاپ نشود؛ هیچ `pull/reset/clean` یا stage/delete روی untracked خصوصی انجام نشود.
- **وضعیت چرخهٔ صفر:** `PASS local — snapshot only; remote-DONE pending`. branch=`arena/5e0f64cf-mp` (base اعلام‌شده `35d4b35184b4148c658b415bd009fc076bf24e00`)، `HEAD=e0ae95f48bf8451bd59b972a92c55fed404e6a92`, `origin/main=352781043ad2ba202d8b3b459df1ce7e3d914ef7`؛ relation کامل در snapshot تازه ثبت شد.
- **Worktree زمان snapshot پیشین (تاریخی):** ۲۴ tracked path تغییرکرده، همه در README/docs؛ index خالی؛ ۲۹۳ untracked غیر از خود فایل snapshot. عددهای قدیمی ۱۵۷ artifact/۱۱۲ زیرپوشهٔ receipt به همان زمان محدودند؛ هیچ نامی در این دفتر نمی‌آید.
- **Snapshot تازهٔ چرخهٔ صفر:** ۲۴ tracked change همگی README/docs، index خالی؛ ۳۰۹ untracked پیش از افزودن `current-snapshot.txt` و ۳۱۰ دربرگیرندهٔ همان فایل؛ صفر tracked product diff. فهرست و محتوا باز/چاپ نشدند؛ شاهد sanitized در `../../evidence/2026-11-23/INV-01/current-snapshot.txt`. HEAD local در remote ref نیست؛ ancestry و tree-equality در همان transcript مستند شده‌اند.
- **Toolchain ثبت‌شده:** Git `2.39.5`, Node `v22.22.3`, npm `10.9.8`, Python `3.11.2`, pytest `9.2.0`, Ruff `0.17.6`, gh `2.23.0`.
- **CI query چرخهٔ صفر:** GitHub CLI `2.23.0` از `gh run list --commit` پشتیبانی نمی‌کند (exit=1)؛ fallback `gh run list --branch arena/5e0f64cf-mp --limit 100 ... --jq 'map(select(.headSha == e0ae95f…))'` موفق شد و `[]` داد. بنابراین در ۱۰۰ run اخیرِ شاخه، run منطبق با local HEAD دیده نشد؛ هیچ workflowای dispatch نشد. خام: `../../evidence/2026-11-23/INV-01/ci-current-sha-query.txt`. پس از push باید روی SHA ریموت، `gh pr checks` و `gh run list` دوباره اجرا شوند.
- **محل شاهد:** `../../evidence/2026-11-23/INV-01/snapshot.txt`؛ خروجی status به‌شکل aggregate امن و فهرست فقط tracked docs در آن ثبت است. هیچ pull/reset/clean/stage/commit/push/deploy در INV-01 انجام نشد.
- **نتیجهٔ پذیرش:** `PASS — non-destructive snapshot only`; inventory crosswalk، QA و release جدا هستند.

### INV-02 — crosswalk عضو (`PWA-01`)

- **Acceptance canonical:** تمام قابلیت‌های Flutter به رفتار، API، صفحه/route React موجود یا `GAP`، role/data-owner، test/evidence و یکی از `CURRENT/GAP/TARGET/BLOCKED` وصل شوند. canonical `PWA-01` هنوز `PROPOSED/NOT_RUN` است.
- **Crosswalk draft:** [`member-capability-crosswalk.md`](../../evidence/2026-11-23/INV-02/member-capability-crosswalk.md) همهٔ ۱۷ directory عضو را در ردیف‌های رفتاری map می‌کند، policy targetهای ADR-007 را از وضع فعلی جدا می‌سازد، و routeهای تأییدنشده را `TBD` می‌گذارد. نتیجه `PARTIAL / NOT_ACCEPTED`; tracker checkbox باز می‌ماند.
- **Source evidence:** v3 literal scan ۱۷ directory، ۳۱ فایل/۹٬۵۰۱ خط feature، ۱۴ GoRouter path، ۲۸ test file موجود و ۶۰ call-site را به method/path shape manifest تطبیق داد؛ `api/routes.json` دارای ۱۴۱ path/۱۶۳ operation است. v2 چهار `ref.watch(apiClientProvider)` را از دست می‌داد و به‌عنوان baseline coverage superseded است. raw: `../../evidence/2026-11-23/INV-02/member-static-inventory-v3.txt`; manifest/source/test hashes همان‌جا.
- **React و ownership boundary:** `/member` هنوز `MemberRoutePending` بدون member-data است؛ guard برنامه، member را از `/staff/*` رد می‌کند. Manifest roles/scopes با handler/service/model برای ownership cross-read شده، اما `owner_scope` اثبات runtime/negative authorization نیست. پنج/چند ردیف policy/safety حساس `BLOCKED` مانده‌اند؛ staff pages، diagrams و test-file presence معادل flow/member acceptance نیستند.
- **گیت‌های audit ایستای اولیه:** هنگام ساخت crosswalk، Flutter/React/backend tests/build، browser/device، error/persistence E2E و reviewer/product-owner sign-off اجرا نشدند؛ این گزاره به همان snapshot اولیه محدود است.
- **Revalidation چرخهٔ صفر:** scan v3 دوباره اجرا شد؛ نتیجه همچنان ۱۷ feature directory، ۳۱ فایل/۹٬۵۰۱ خط، ۱۴ route، ۲۸ test-file presence و ۶۰/۶۰ literal API shape-match (`member-static-inventory-v3-rerun.txt`). `npm ci`, `npm run lint`, `npm run build` و کل `npm test -- --reporter=dot` روی Studio با product-source diff صفر موفق شدند: ۵۲ test file PASS/۲ SKIP، ۳۶۲ test PASS/۱۰ SKIP؛ warnings JSDOM/React `act`/Recharts بدون layout باقی‌اند. raw شامل install audit (۴ advisory) و خروجی کامل در `studio-current-cycle-validation.txt` است؛ هیچ dependency/source/lockfile تغییر نکرد.
- **گیت‌های پذیرش باز:** Flutter/Dart و browser binary/Playwright موجود نیست؛ Flutter/browser/device، member route/ownership/error/persistence E2E و reviewer acceptance `NOT_RUN/BLOCKED`. `/member` هنوز placeholder؛ بنابراین `INV-02=PARTIAL/NOT_ACCEPTED`, checkbox باز و `PWA-01=PROPOSED/NOT_RUN` بدون تغییر. هیچ تغییر Flutter/native، role, DB, checkout یا biometric انجام نشد.

### INV-03 — crosswalk کارکنان

- **وضعیت:** `PARTIAL — static route/API/role/test inventory, NOT_ACCEPTED`; مسیر مستقل staff باقی می‌ماند و checkbox باز است. اسکریپت corrected `../../evidence/2026-11-23/INV-03/staff_crosswalk_audit.py` route keyها را با kind+name جدا می‌کند تا collision با Flutter surface هم‌نام رخ ندهد؛ raw `staff-crosswalk-static.txt` شامل ۱۲ Studio page، route، endpoint/manifest roles و test reference است.
- **گیت فعلی:** `interaction_map.py --check` PASS با ۳۱ surface/۱۶۳ contract/drift صفر. اعضا و role-restricted APIs در map دیده می‌شوند، اما map برای هر صفحه state/loading/empty/error/persistence و DB-owner ندارند. `members` و `analytics` test reference ندارند؛ سایر testها فقط در scan حاضر شمرده شدند، اجرا نشدند. ۶۹ operation manifest در هیچ interaction surface ثبت نشده‌اند؛ این absence dead-code proof نیست.
- **Revalidation چرخهٔ صفر:** `staff_crosswalk_audit.py` دوباره اجرا شد؛ ۱۲ Studio page، ۵۹ endpoint shape و manifest map ۳۱ surface/۱۶۳ operation، ۶۹ operation بدون surface (absence به‌تنهایی dead-code نیست)، `interaction_map_has_state_field=False` و دو صفحهٔ `members`/`analytics` بدون test reference. خروجی `../../evidence/2026-11-23/INV-03/staff-crosswalk-static-rerun.txt`; فقط static/source scan است.
- **باقی‌مانده:** behavior-level actor/role→route/API/permission→model/ownership→state/error→test-ID matrix، test negative/evidence و reviewer acceptance. PWA-01 canonical/status از این static inventory تغییر نمی‌کند؛ full `INV-04…INV-09` هنوز باز است.
- **بازتولید و بازبینی source در ادامهٔ جاری:** [`INV-02 raw + review`](../../evidence/2026-11-27/INV-02/review.md) و [`INV-03 raw + review`](../../evidence/2026-11-27/INV-03/review.md) از SHA جداشدهٔ `352781043ad2ba202d8b3b459df1ce7e3d914ef7` ثبت شدند. خروجی خام و hashها حفظ شده‌اند؛ بازبینی دستی false-negativeهای dynamic template را تشخیص داد، اما هیچ تست محصول یا مجوزی اجرا نشد. هردو کارت partial/non-accepted و checkbox باز؛ `PWA-01=PROPOSED/NOT_RUN`.

### INV-04 — برش ساختاری statusهای عضو (کل کارت باز)

- **Acceptance canonical:** برای هر capability یکی از `CURRENT/GAP/TARGET/BLOCKED` به‌همراه owner/scope، test موجود/لازم، فایل/line و منبع داده؛ صرف وجود صفحه/API کافی نیست.
- **برش انجام‌شده:** [`member-status-slice.txt`](../../evidence/2026-11-23/INV-04/member-status-slice.txt) روی crosswalk `INV-02` تأیید کرد ۲۱/۲۱ ردیف member یک status دارند و ستون‌های Flutter source/API/owner/React/test-reference خالی نیستند: `CURRENT=0`, `GAP=12`, `TARGET=4`, `BLOCKED=5`. این یک structural status slice است، نه full `INV-04`.
- **Blocker:** crosswalk فیلد row-specific «test لازم» ندارد، test-referenceها فقط presence هستند، صفحه‌های کادر در این slice پوشش داده نشده‌اند و ownership/runtime منفی/positives اجرا نشده؛ `INV-04` و checkbox باز می‌ماند.

### INV-05 — Dashboard KPI/fallback (برش مستقل؛ کل inventory باز)

- **Acceptance canonical:** hard-coded/mock data، silent fallback، controls بی‌اثر، local-only state و KPI بی‌منبع شناسایی شوند؛ fixture با دادهٔ واقعی اشتباه نشود.
- **برش بررسی‌شده:** `Dashboard.tsx` از `fetchKpis` و `fetchAttendance` استفاده می‌کند؛ KPI از `/admin/kpis`، حضور از `/admin/attendance`; `useApi` سه حالت loading/error/data و `needsSession` را جدا نگه می‌دارد. `null` برای ظرفیت «نامعلوم» است؛ پیام zero attendance فقط پس از پاسخ حاوی عدد صفر می‌آید؛ خطا به‌صورت متن خطا می‌ماند. fixtureهای تست صرفاً synthetic هستند و هیچ مقدارشان در evidence کپی نشده.
- **تست:** `npm test -- tests/dashboard.test.tsx --reporter=dot` روی `HEAD=e0ae95f48bf8451bd59b972a92c55fed404e6a92`: ۱ فایل/۳ تست PASS، یک سری React `act(...)` warnings؛ raw `../../evidence/2026-11-23/INV-05/dashboard-current-cycle-test.txt`.
- **Blocker/حد:** فقط Dashboard KPI/fallback/error بررسی شد؛ سایر ۱۲ Studio page، Flutter/member, backend data provenance و source-less KPIها هنوز inventory نشده‌اند. `INV-05`/checkbox باز می‌ماند.

### INV-06 — Dashboard actor/data/route slice (کل کارت باز)

- **Acceptance canonical:** actor، داده، scope/ownership، مجوز و مسیر direct API برای هر view/mutation/file/export/job/event map شود.
- **برش بررسی‌شده:** [`dashboard-actor-data-slice.txt`](../../evidence/2026-11-23/INV-06/dashboard-actor-data-slice.txt) سه GET dashboard/KPI/attendance/member-summary را با endpoint-specific guards/roles، router permission dependency، model/source و single-club scope کنار هم می‌گذارد. KPI از `Member/Membership/Payment/GymClass/ClassBooking` و حضور از `CheckIn` aggregate می‌شود؛ `members-summary` روی `Member/User/Membership` staff list است. هیچ row-owner claim برای club-wide staff endpoint ساخته نشد.
- **تست منفی/مثبت همان برش:** `dashboard-actor-data-tests.txt`, rerun در 2026-11-27 UTC؛ Python 3.11.2/pytest 9.2.0: ۳ فایل، ۳۴ passed/۲ warning (Starlette/httpx deprecation و InsecureKeyLengthWarning برای JWT تستی)؛ temp SQLite فقط. anonymous/member denial و چند positive staff read، KPI admin/null-capacity و empty attendance پوشش دارند؛ کل نقش‌ها×مسیرها آزموده نشده‌اند. فایل خام header تاریخ مرجع مسیر evidence را دارد، نه زمان اجرای آزمون.
- **Blocker/حد:** component `Dashboard.tsx` بدون role gate، `fetchKpis` را فراخوانی می‌کند؛ اگر برای coach/reception render شود، current `security/rbac.py` policy برای آنان KPI allow ندارد و `require_permission()` route/method enforcement را انجام می‌دهد؛ پاسخ باید fail-closed شود. page reachability و error UI از UI تا API به‌صورت E2E تأیید نشده؛ تغییر grant/policy انجام نشد. باقی Studio/Flutter/member, download/export/file/event/job و field-level ownership هنوز map/test نشده؛ `INV-06` و checkbox باز؛ next مستقل `INV-07` CI evidence per-job روی exact SHA.
- **Snapshot Git پالایش‌شده (2026-11-27 UTC):** [`local-state-sanitized.txt`](../../evidence/2026-11-23/INV-06/local-state-sanitized.txt): همان branch/HEAD، index خالی، ۲۴ tracked worktree changes، ۳۲۲ untracked path entry (۱۱۷ زیر `mp-app`؛ نام‌ها عمداً حذف و محتوا بررسی‌نشده)، tracked product-source diff صفر. untrackedها را نمی‌توان به candidate پاک یا source بی‌تغییر نسبت داد؛ stage/commit انجام نشد.

## قرارداد شواهد و checkpoint

- برای هر چرخه raw output پالایش‌شده در `evidence/2026-11-23/<ID>/` نگه‌داری شود؛ secret، PII، token، receipt، دادهٔ واقعی و فهرست مسیرهای خصوصی وارد سند یا evidence نشود.
- هر PASS باید command، نتیجهٔ دقیق، SHA و نسخهٔ ابزار را داشته باشد؛ skip/mock، preview، آزمون تاریخی یا CI روی SHA دیگر PASS نیست. برای worktree dirty، همان محدودیت و hash/fingerprint تغییرات ثبت شود.
- بعد از هر ۵ آیتم یا پیش از push، این دفتر، handoff و tracker با شواهد همان revision همگام شوند. هیچ CI، browser/device، reviewer، operator، staging، SMS/provider، bank reconciliation، backup/restore یا production evidence که اجرا نشده `UNKNOWN/NOT_RUN/BLOCKED` می‌شود.
- در هر مشکل واحد، پس از سه تلاش ناموفق پیاپی آن را `BLOCKED` و دلیل دقیق را ثبت کن و سراغ کار مستقل بعدی برو؛ گیت یا تست را تضعیف نکن.

## گیت‌های بیرونی باز

Browser/OS/device فیزیکی، screen reader، نسخه/مدل دقیق، reviewer مستقل حقوقی/پزشکی/مالی، SMS/provider واقعی، تطبیق بانکی، میزبان/staging، backup خارج‌میزبان و آزمون restore/RPO/RTO، secret/key عملیاتی، deploy/rollback و release همچنان `UNKNOWN/BLOCKED/NOT_RUN` تا ثبت شاهد مجاز همان موردند. این فایل مجوز دسترسی، ایجاد secret، استفاده از دادهٔ واقعی، deploy، release یا merge نیست.
