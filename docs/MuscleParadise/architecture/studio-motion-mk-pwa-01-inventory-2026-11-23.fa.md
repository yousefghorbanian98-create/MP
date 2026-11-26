# MK-PWA-01 — موجودی read-only حرکت در Studio

**ثبت:** ۲۰۲۶-۱۱-۲۳ · **نتیجهٔ حلقه:** `PASS — inventory/read-only فقط` · **نتیجهٔ کیفیت محصول:** شامل چند `GAP` و `UNKNOWN`؛ هیچ معیار کیفیتی با PASS بسته نشده است.

> **یادداشت snapshot بعدی — turn جاری:** hash helper ثبت‌شده در این inventory (`2b9861a4…`) دیگر برابر محتوای dirty tree نیست. `src/lib/motion.ts` کنونی `19db976f3f2858521be00060916b0827557e205ac45cf4136115ee078059f246` و `tests/motion.test.tsx` کنونی `74a4b247f464c2e9e84876b64fa5bcf107e846014d532762442a4f57c21013d0` هستند؛ تست targeted همان نسخه 17/17 پاس شد. نسخهٔ فعلی hook با `useSyncExternalStore`، SSR/reduced محافظه‌کار و subscription زنده فرق دارد؛ بنابراین GAPهای توصیف‌شده در این گزارش فقط snapshot hashشدهٔ پایین را شرح می‌دهند، نه helper فعلی. این گزارش درجا بازنویسی نشده؛ در زمان ثبت این یادداشت، crosswalk تازهٔ read-only در `MK-PWA-01-FU-01` (TODO واحد) `PROPOSED/NOT_RUN` بود. تغییر hash/کد در diff محلی از قبل وجود داشت و زمان/نویسندهٔ آن از شواهد آن turn تعیین نمی‌شود. هیچ browser/device یا review مستقل انجام نشده است.

این سند inventoryِ شاخهٔ Studio/PWA را روی working tree حاضر می‌کند؛ به‌معنای تغییر محصول، تصویب design، پذیرش PWA، نصب‌پذیری، یا QA مرورگر/دسترس‌پذیری نیست. هیچ کد، dependency، تست، build یا مرورگر در همان snapshot اجرا/تغییر نشد. یادداشت package مرجع جداست: [Motion Kit v1.1.0](mp-ui-ux-motion-kit-v1.1.0-review.fa.md).

> **پیوست محدود evidence — تاریخ مرجع Arena: ۲۰۲۶-۱۱-۲۳؛ wall-clock sandbox نامطمئن:** helper/test current-tree و hashها در [پیگیری TODO](../TODO-2026-11-16.md#motion-current-tree-static-scan-session) به‌روز شده‌اند؛ `MK-PWA-01-FU-01` اکنون `PARTIAL` است، نه `PROPOSED/NOT_RUN`. پیگیری بعدی `Skeleton` را با `motion-reduce:animate-none` اصلاح و حضور rule را در CSS build زیر `@media (prefers-reduced-motion: reduce)` تأیید کرد؛ targeted tests **۲۲/۲۲** و full suite **۳۲۹ پاس/۱۰ skip** شدند، lint/build نیز پاس. افزون بر آن، [crosswalk ایستای درخت فعلی](studio-motion-current-tree-static-crosswalk-2026-11-23.fa.md) برای direct Framer، shared components، CSS/Tailwind، test و lab جدا ثبت شد. این‌ها اجرای همان working tree dirty هستند؛ browser computed-style/E2E/device و independent review همچنان انجام نشده‌اند. گزارش تاریخی hashشده درجا بازنویسی نشده و هیچ‌یک از این شواهد Motion/PWA acceptance یا release را نمی‌بندند.

## ۱. آیا commit شاخه merge شده بود؟

GitHub را با `gh` و refهای زنده را با `git ls-remote` خواندم؛ چیزی fetch، merge یا checkout نشد.

| شاهد | مقدار مشاهده‌شده |
|---|---|
| PR | [#25 — MP: hardening changes, architecture docs, and PWA-00 checks](https://github.com/yousefghorbanian98-create/MP/pull/25) |
| State / head | `MERGED`; head=`b8db8f248606a7dbadd984e123f2d2d65a1d0e1e`, همان HEAD محلی و ref دوردست `arena/5e0f64cf-mp` |
| Merge commit | `3a4f38ce84c9d5957ca5833b0ba597987159a190`; همان ref زندهٔ `origin/main`. GitHub API دو parent آن را `35d4b35184b4148c658b415bd009fc076bf24e00` و `b8db8f248606a7dbadd984e123f2d2d65a1d0e1e` گزارش می‌کند؛ پس head این شاخه در merge commit حاضر است. |
| Checks | `gh pr checks 25` برای PR جاری ۱۳ check نمایش داد؛ **همه pass** (از جمله backend، Studio، Flutter، Android debug compile، e2e-api، docs، live-contract و secret-scan). این CI به commit head مربوط است، نه تغییرهای محلی commit‌نشده. |
| اختلاف زمان | API زمان merge را `2026-11-25T15:29:19Z` می‌گوید؛ این دو روز بعد از تاریخ نشستِ اعلام‌شدهٔ `2026-11-23` است. Hash/parent/refها merge را تأیید می‌کنند، اما ناسازگاری زمانی باید برای منشأ timestamp در نظر گرفته شود، نه بی‌صدا توجیه شود. |

**مرز مهم:** commitهای شاخه merge شده‌اند؛ ولی تمام diffهای فعلی workspace merge نشده‌اند. `git status` در این برش تعداد زیادی تغییر tracked و فایل untracked نشان می‌دهد و index خالی است. به‌ویژه فایل‌های Studio ذکرشده در بخش ۲ و اسناد تازهٔ این کار محلی/unstaged هستند و در PR #25 نیستند. نتیجه: شاخهٔ commit‌شده merge شده، نه تمام کارهای فعلیِ روی دیسک. به‌علت dirty بودن workspace، local `main` را به‌روزرسانی نکردم و branch را جلو نبردم.

## ۲. baseline و تمامیت بررسی read-only

- branch=`arena/5e0f64cf-mp`; HEAD=`b8db8f248606a7dbadd984e123f2d2d65a1d0e1e`; ref دوردست همان branch=`b8db8f...`; ref زندهٔ `main`=`3a4f38ce...`.
- پیش از قرائت، SHA-256 کل diffهای tracked=`ec0e2ec4ab7dbe4e09b6afd9a86daf6bcd8f07ebc375a2bdda2349b926f5a986` و digest فهرست status کامل=`8d5bff57542eba75b7b356a2ccd327858a44a75a7d86e7764d2bbfacffabf20d` ثبت شد. برای Studio در شروع همین inventory: diffهای tracked SHA-256=`42d72c9027decf4f0f54dafcddf14a48c79db5e24c98397b67e3b7f35c110866`؛ فهرست status pathها SHA-256=`4034f6fefe037878839f2755c65d5a621cbffba78ad638716ba402f621f8e6d3`. این fingerprintها وضعیت dirty قبلی را ثبت می‌کنند، نه commit یا clean baseline.
- مسیرهای مرتبطی که از قبل در status تغییرکرده بودند: `src/main.tsx`، `src/styles/index.css`، `tailwind.config.js`، `pages/CheckIn.tsx`, `Dashboard.tsx`, `Finance.tsx`, `Members.tsx`, `Programs.tsx`, `Shop.tsx` و `components/UpdateBanner.tsx`; `tests/checkInPage.test.tsx` نیز untracked است. هیچ‌یک از این diffها در این loop بازنویسی نشد.
- خط‌ها از ۱ و روی بایت‌های فعلی working tree خوانده شده‌اند. جدول hash پایین برای traceability همان بایت‌هاست؛ برای فایل‌های `M`/`??`، hash را به محتوای mergeشدهٔ HEAD نسبت نده.
- دادهٔ رسید خصوصی، credential، API واقعی، server، browser و PWA install/offline آزمایش نشدند. اسکریپت‌های Motion Kit هم اجرا نشدند.

### hash فایل‌های شاهد در working tree این inventory

| Path | SHA-256 |
|---|---|
| `mp-app/studio/src/lib/motion.ts` | `2b9861a4efd3520b7d996786eab24843c95b65c39904fc24a141d84528ed5c7c` |
| `mp-app/studio/src/App.tsx` | `4dcdc6749ac6fb7fe2b92bbf47a542a5e6f43693a9f98224f04833d7f1d05007` |
| `mp-app/studio/src/components/Feedback.tsx` | `505681f46f98d49f57c007c96f85c6f3a74fd5c9b3633873eb490659c0e0a7b6` |
| `mp-app/studio/src/components/UpdateBanner.tsx` | `24ddeff5fba36fd27efd7ad426161bb7104b6964fe10a69b18b0cdecbc7dee3a` |
| `mp-app/studio/src/components/TopBar.tsx` | `ed567317b523ce521b2e325dd826fff147dcd0f59161fb9ed67c48607315c187` |
| `mp-app/studio/src/components/Sidebar.tsx` | `e9c38262467cd2dc10748f8474f85836684297140fe53f143f032c3253031c63` |
| `mp-app/studio/src/components/ScheduleTimeline.tsx` | `5c2e175b6e5d6825489a331da032e7f68a54953a3611951c2cd36c2fb616c36e` |
| `mp-app/studio/src/components/MemberTable.tsx` | `9dbb89d160747e37da886f8788a9e87f7cd37e6b69db13cdcb832e58d500f597` |
| `mp-app/studio/src/components/KpiCard.tsx` | `7029265e50b414927480d34705b0b3b80cb4c258e28834a1b73b6dd7a2d839d3` |
| `mp-app/studio/src/pages/CheckIn.tsx` | `864b8ce8786617b5ecd22ebe8d02edc373d2cb9a4f2b2e5535882e1071a3acc0` |
| `mp-app/studio/src/pages/Dashboard.tsx` | `96dd035a7ebba4063f479a3a2929c20e3be0bea83a0ab015a6873c4047ae4e65` |
| `mp-app/studio/src/pages/Finance.tsx` | `73b23afabee755059497c917adeb80f717865b00f3d4aa6c3b75edc73473bd4b` |
| `mp-app/studio/src/pages/Members.tsx` | `111ac72fdffc9d8e6d443acdfb168bcf8163de3aaba6c3bc79a092df032333a2` |
| `mp-app/studio/src/pages/Programs.tsx` | `9e1755226d30545742a43254de1d0e3bf3d5dc5d93bb045fbc421a6bc86beb1c` |
| `mp-app/studio/src/pages/Settings.tsx` | `7f4877bd905dea986ada7fb56b849607e62d7f53af551849ead1df7201ee2535` |
| `mp-app/studio/src/pages/Shop.tsx` | `7cd3c8b95527da6e9d25cb7175c405fbe89786603b52387a60562ba746424dba` |
| `mp-app/studio/src/styles/index.css` | `eff3cdc9caa149eaea855a7c105b5c41767b3d160575b2d16d95ba84f82b2cbe` |
| `mp-app/studio/tailwind.config.js` | `8f7b4aa26a169c4c353e8822d202027d072634b274a112dbb4771b85a64fed03` |
| `mp-app/studio/tests/motion.test.tsx` | `f519ac49f1ef060835d46524eda968345437d7f721fcb4dc6d01f3fab168af57` |
| `mp-app/studio/tests/a11y.test.tsx` | `6cd9217c111b00c1b1ff49cdabaabbf7b4898687e2372840ebac9d39d5840aef` |
| `mp-app/studio/tests/checkInPage.test.tsx` *(untracked)* | `da18738cbab51720bd8d626b701ab77687b164ed4906f9a86fcc80f354485021` |

## ۳. crosswalk کد و شاهد موجود

| مسیر/خط | حالت/دادهٔ UI | حرکت و focus/draft | تست یا شاهد فعلی | ارزیابی |
|---|---|---|---|---|
| `src/main.tsx` L24–45; `src/App.tsx` L38–73 | App در client با `createRoot`; وضعیت session `checking/unauthenticated/authenticated`; ۱۲ route از store | `useReducedMotion()` روی wrapper کل صفحه؛ route با `key={page}` و `AnimatePresence mode="wait"`. در reduced، ورود/خروج تقریباً فوری؛ اگر hook `null` باشد ternary به حالت عادی می‌افتد و route حرکت می‌کند. focus به heading منتقل نمی‌شود/در همین مسیر مدیریت نشده است. | `tests/a11y.test.tsx` L177–183 فقط وجود نام hook را می‌سنجد. | برای خود wrapper مسیر کاهش وجود دارد؛ رفتار focus روی navigation و حفظ scroll/input پس از تعویض route شاهد ندارد (`UNKNOWN`). |
| `src/lib/motion.ts` L28–36, L70–124 | preset مشترک `rise/fade/slide/press/hover/stagger` | `buildPreset(true)` در L81–95 x/y/scale را حذف، feedback را حفظ و stagger را صفر می‌کند؛ در حالت normal tokenهای x/y/scale و سقف stagger=12. اما L123–124 مقدار `null` را `false` می‌کند؛ در نتیجه نبود مقدار صریح preference به حالت متحرک می‌افتد. | `tests/motion.test.tsx` L19–69 منطق pure/زمان‌ها را می‌سنجد. hook در L64–69 فقط boolean/crash را می‌سنجد؛ تغییر زندهٔ preference آزموده نشده. | policy خالص reduced خوب‌تعریف شده؛ unknown و live change شکاف شواهد/رفتارند. |
| `src/pages/Dashboard.tsx` L17–21, L58–132؛ `components/KpiCard.tsx` L21–47؛ `MemberTable.tsx` L71–105؛ `ScheduleTimeline.tsx` L63–83 | KPI، حضور، جدول عضو و کلاس‌ها از hookهای API؛ empty/error state موجود. | ریشهٔ صفحه preset می‌گیرد؛ KPI/ردیف عضو/خط زمان childهای داخل صفحه‌اند و خودشان raw `motion.*` دارند. Kpi `delay=index*.08` + hover-y؛ MemberTable ردیف‌ها x و `i*.05`؛ ScheduleTimeline x و `i*.06`. کلید MemberTable برابر `member_id` است. | `motion.test.tsx` فقط فایل صفحهٔ Dashboard را در گیت source می‌خواند؛ bodyهای component جداگانه را نه. | coverage صفحه، childها را تضمین نمی‌کند؛ این سه کامپوننت در reduced/unknown، live toggle و سقف delay شاهد رفتاری ندارند. |
| `src/pages/CheckIn.tsx` L21–25, L29–71, L86–120 | feed واقعی/empty/error/loading؛ اسکنر تصویرسازی‌شده، state دکمهٔ start/stop | خود کارت از preset؛ loop اسکن در reduced به خط ایستا تبدیل می‌شود (L43–55). feed key=`checkin_id` (L87–90)؛ اما L90 preset slide و L91 کل `transition` را با `{ delay: i * .08 }` جایگزین می‌کند. با ۲۰ ورودی، ردیف آخر ۱٫۵۲ ثانیه delay می‌گیرد و در reduced نیز این delay از helper صفر عبور نمی‌کند. | `tests/checkInPage.test.tsx` L42–56 feed/SLO/دکمه را با `matchMedia=false` می‌سنجد؛ reduced=true/تغییر preference/DOM motion را نمی‌سنجد. این test untracked است. | loop اسکن شرط reduced دارد؛ delay فهرست gap مستقیم است. ادعای performance یا دوربین/اسکن واقعی وجود ندارد. |
| `src/pages/Finance.tsx` L29–43, L92–102, L114–127, L145–179 | خلاصهٔ مالی، پاسخ کمیسیون و خطا؛ دو input کنترل‌شدهٔ coachId/rate در L147–159 | wrapper preset دارد؛ کارت خلاصه/نتیجه/خطا raw opacity+y دارند. دو دکمه در L106/L161 hover/active scale CSS دارند. فرم controlled است ولی بازسازی آن هنگام تغییر preference آزموده نشده. | `motion.test.tsx` منطق preset را دارد، اما state مالی یا reduced UI را render نمی‌کند؛ CI PR مربوط به head mergeشده، worktree dirty فعلی نیست. | حرکت ثانویه در صفحهٔ مالی خارج از policy مشترک است؛ state/focus preservation `UNKNOWN`. این ثبت تغییر محاسبه/پرداخت نیست. |
| `src/pages/Members.tsx` L16–21, L82–90, L142–164, L200–212 | انتخاب عضو، تاریخچه/ماتریس و empty state؛ کلیدهای `member_id`/`axis` پایدارند. | `motionPreset.slide` ورودی پنل؛ `exit={{opacity:0,x:-20}}` و spring در L87–88 مستقل از reduced باقی می‌ماند. width barها در L149–155 reduced را تا مدت صفر رعایت می‌کنند؛ empty state در L201–210 raw fade است. | گیت source test وجود hook در صفحه را می‌سنجد؛ render واقعی با selection/reduced/focus و exit retention یافت نشد. | حرکت بخشی canonical است و بخشی raw؛ خروج محتوای عضو هنگام تغییر selection/session فقط ریسک بررسی بعدی است، نه یافتهٔ اثبات‌شدهٔ leak یا مجوز امنیتی. |
| `src/pages/Programs.tsx` L33, L88–90, L144–147, L217–220 | فهرست draft/approved/rejected، کلید `p.id` و فیلترها | root و کارت از `motionPreset.rise`; کارت‌ها از `motionPreset.stagger(i)` استفاده می‌کنند که در حالت reduced صفر است. | `motion.test.tsx` وجود hook را می‌سنجد؛ component testِ reduced/stable focus/form در این inventory دیده نشد. | الگوی مشترک بهتر از raw cases؛ render/browser evidence و state preservation هنوز لازم است. |
| `src/pages/Settings.tsx` L30, L74, L99–133 | flags با کلید `f.key`; دکمهٔ toggle دارای `aria-pressed` و disabled هنگام busy | wrapper preset دارد؛ هر ردیف raw opacity+x و `delay=i*.04`؛ thumb یک spring layout مستقل. لیست از منبع سرور می‌آید و سقف تعداد در UI اینجا اعمال نشده. | test موجود motion صفحه را در source gate می‌شناسد، ولی تغییر preference، delay cap یا focus toggle را render نمی‌کند. | ردیف‌ها/کنترل‌ها reduced policy را دور می‌زنند و تأخیر سقف‌دار نیست. |
| `src/pages/Shop.tsx` L64–65, L151–185, L243–293 | تب/فیلتر، جست‌وجو و product card؛ کلید محصول `p.id`; cart و خرید مطابق پاسخ سرور | tab indicator transition reduced=0 در L172–181 و کارت‌ها از preset rise. در عوض hover تصویر `scale(1.03)` در L254 و دکمهٔ cart `active:scale` در L287 بیرون از policy هستند؛ input جست‌وجو controlled در L207–212. | motion source gate نام صفحه را دارد؛ test renderِ preference، محصول/جست‌وجو/focus را پوشش نمی‌دهد. | بخشی reduced شده؛ CSS hover/press و حفظ query/focus هنگام preference change بی‌شاهد است. |
| `src/pages/Analytics.tsx` L15–16, L54–111 | لیدربورد/churn با empty/error و keyهای member/key | cards از `motionPreset.rise`; stagger دستی در این بازه نیست. | motion source test وجود hook را می‌سنجد. | reuse helper مشهود؛ UX واقعی در reduced هنوز با browser/device سنجیده نشده. |
| `src/components/TopBar.tsx` L71–79; `Sidebar.tsx` L65–87; `UpdateBanner.tsx` L4–36 | عنوان route، nav pill/status و بنر update | TopBar x+fade ثابت؛ Sidebar spring layout و pulse CSS؛ UpdateBanner y-spring در ورود/خروج؛ هیچ‌کدام helper/reduced prop مشترک در همین فایل ندارند. | تست `motion.test.tsx` گیت کامپوننت‌های مشترک را اسکن نمی‌کند؛ `a11y.test.tsx` هم فقط App را می‌بیند. | gap component-scope؛ تغییر Service Worker/update از scope این inventory نیست. |
| `src/components/Feedback.tsx` L74–135; `src/styles/index.css` L52–79; `tailwind.config.js` L63–80 | toast/error status؛ skeleton loading؛ کنترل‌ها و loading shimmer | Toast L77–108 duration=0 و exit بدون transform در reduced؛ اما `Skeleton` از `animate-pulse` و کلاس `.skeleton` از `animate-shimmer` استفاده می‌کنند؛ CSS پایه `transition-all`/active-scale دارد؛ Tailwind shimmer/pulse-soft بی‌پایان تعریف شده. در CSS محصول `prefers-reduced-motion` دیده نشد. | `rg` تنها media query reduced را در `src/visual-concepts/visual-concepts.css` L462–463 پیدا کرد؛ آن stylesheet بخشی از visual concept است و `main.tsx` آن را import نمی‌کند. هیچ testِ `getComputedStyle`/motion-reduce CSS در این loop اجرا/کشف نشد. | Toast بخشی از مسیر reduced دارد؛ CSS مشترک، skeleton/shimmer و chrome سراسری gap هستند. وجود media query در mock منفصل درمان global نیست. |

### یافته‌های اولویت‌دار

- **`GAP-01` — unknown preference، تأییدشده در static code:** `useMotionPreset()` در `src/lib/motion.ts` L123–124 مقدار `null` را با `false` یکی می‌کند. بنابراین هر حالتی که hook نتواند preference را بخواند، از دید این helper مجوز حرکت است؛ contract پیشین reduced/unknown را محافظه‌کار تعریف کرده بود.
- **`GAP-02` — direct motion بیرون از helper، تأییدشده:** raw animation در KpiCard، MemberTable، ScheduleTimeline، TopBar، Sidebar، UpdateBanner، Settings rows، childهای Finance و Members exit وجود دارد. تست منبع فعلی فقط هشت page را می‌گردد و به‌تنهایی تضمین نمی‌کند این childها یا shared chrome policy را رعایت کنند.
- **`GAP-03` — delay و reduced list، تأییدشده:** `CheckIn.tsx` L91 transition را با delay دستی override می‌کند؛ `MemberTable`, `Settings` و `ScheduleTimeline` نیز per-item delay مستقل دارند. Helper سقف ۱۲/صفر reduced دارد، ولی همهٔ مصرف‌کننده‌ها از آن استفاده نمی‌کنند.
- **`GAP-04` — CSS motion، تأییدشده در source:** قواعد product stylesheet/Tailwind برای shimmer, pulse, transition و press scale media guard مستندشده‌ای ندارند. CSS داخل `visual-concepts` تنها lab جداست.
- **`EVIDENCE-GAP-05` — live setting، focus/draft و render، هنوز UNKNOWN:** unit pure وجود دارد؛ hook تنها Boolean را می‌سنجد؛ تست فعلی `CheckIn` فقط `matchMedia=false` دارد. هیچ شاهدی در این inventory تغییر `false→true→false`، unmount cleanup، preservation فرم/focus، reduced CSS محاسبه‌شده یا browser/device واقعی را اثبات نمی‌کند.
- **`RISK-06` — retention هنگام exit، بررسی‌نشده:** `AnimatePresence` و exit برای پنل عضو/route وجود دارد. ممکن است محتوا هنگام transition عادی یک فریم/مدت exit در DOM بماند؛ بدون تست و بررسی قرارداد دسترسی نباید آن را نه leak قطعی و نه مرز امنیتی خواند. اگر authorization/revoke در scope آمد، loop مجزای امنیت/مالک لازم است.

## ۴. حدود آزمون و دسته‌بندی status

- `src/lib/motion.ts` و تست‌های source فوق **خوانده شدند؛ اجرا نشدند**. `npm test`, `npm run lint`, `npm run build`, CI جدید، browser/E2E و device run در این برش اجرا نشد.
- PR #25 checkهای سبز را برای SHA `b8db8f...` دارد؛ تغییرهای dirty/unstaged حاضر تحت آن checkها نبوده‌اند. pass بودن CI merge را تأیید می‌کند، نه reduced-motion کنونی در working tree.
- `src/visual-concepts/**` را به کد زندهٔ App نسبت ندادم: `main.tsx` در L1–45 `App` و `styles/index.css` را import می‌کند و visual concept stylesheet را import نمی‌کند. دربارهٔ امکان دسترسی HTML جداگانه از کل build، خارج این inventory است.
- Service Worker، offline/install/update، role/auth/API/DB و Android بیرون scope هستند. هیچ ادعای PWA installable، امنیت، کیفیت دسترس‌پذیری، یا «کلاس جهانی» مطرح نمی‌شود.

## ۵. نتیجهٔ حلقه، stop و پیشنهاد برای micro-loop بعد

`MK-PWA-01` به‌عنوان **خواندن و crosswalk با صفر تغییر source** کامل است؛ شواهد بالا نشان می‌دهد به‌جای `NO_CHANGE_NEEDED` چند gap محدود و قابل‌آزمون وجود دارد. این نتیجه خودکار مجوز patch نیست.

پیشنهاد اول برای contract بعدی، کوچک و جدا: فقط unknown/fallback preference در `src/lib/motion.ts` و تست متناظر `tests/motion.test.tsx` (حداکثر **۲ فایل**، بدون dependency/network/API/route/DB)، با AC برای null/unsupported→reduced، تغییر زنده در صورت contract هدف، cleanup، و حفظ input/focus در fixture. بعد از آن، CSS reduced-media و دسته‌های raw motion حلقه‌های جدا باشند. این سقف دو فایل **پیشنهاد** است، نه بودجهٔ ازپیش‌تأییدشده؛ `G1–G9`، پنج گیت، تعداد تلاش و reviewer/owner در contract مستقل باید پیش از تغییر کد تعیین شوند.

**Stop:** تا ثبت contract مشخص با parent canonical، allowlist، budget عددیِ صریح، baseline/test منفی، reviewer مستقل و مجوز همان loop، هیچ فایل source تغییر نکند. اگر شاهد live behavior یا ابزار لازم نیست، همان مورد `UNKNOWN/BLOCKED` بماند. loopهای بعدی را در حیطهٔ PWA/Studio نگه دار؛ مسیر Android و kit preview همچنان مستقل‌اند.
