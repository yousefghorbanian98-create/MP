# Handoff نشست — Muscle Paradise

> این فایل **خلاصهٔ جاری برای ادامهٔ کار** است، نه آرشیو گفتگو و نه منبع نهایی وضعیت محصول. پیش از فشرده‌سازی context یا پایان هر کار معنادار، همین snapshot را جایگزین/به‌روز کن؛ تاریخچه را با انباشت transcript طولانی نکن.

## وضعیت جاری — baseline PWA، backlog canonical و Motion evidence (تاریخ مرجع: ۲۰۲۶-۱۱-۲۳)

> این بخش مرجع جاری است؛ بخش‌های پایین‌تر تاریخچه‌اند و وضعیت دیگری از branch/SHA را توصیف می‌کنند. تاریخ ثبت از تاریخ مورد اعتماد Arena گرفته شده؛ ساعت container ناسازگار است و در پایین مشخص شده.

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
