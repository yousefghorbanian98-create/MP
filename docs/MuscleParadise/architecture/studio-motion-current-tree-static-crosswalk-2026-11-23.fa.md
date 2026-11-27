# Studio Motion — crosswalk ایستای درخت فعلی

**تاریخ مرجع ثبت:** ۲۰۲۶-۱۱-۲۳ UTC (مرجع Arena) · **شاخه:** `arena/5e0f64cf-mp` · **HEAD:** `d92817f4151ebbafb25425b7b28776a4cc1180dc` · **base:** `35d4b35184b4148c658b415bd009fc076bf24e00`

> این سند دو snapshot را از هم جدا می‌کند: بخش‌های ۱–۷ inventory ایستای پیش از patch محدود بعدی‌اند؛ بخش ۸ اصلاحات source/test و fingerprint نهایی worktree را ثبت می‌کند. «جاری» در جدول‌های قبلی یعنی همان snapshot بررسی‌شده، نه کد پس از بخش ۸. این گزارش تأیید مستقل نیست و هیچ‌یک از ۵۰ parent canonical، browser/device gate، دسترس‌پذیری محصول، release یا Go/No-Go را PASS نمی‌کند. source helper نسبت به فایل inventory تاریخی `studio-motion-mk-pwa-01-inventory-2026-11-23.fa.md` (که در آن checkpoint منتشر نشده) drift کرده؛ hashهای آن را به این دو snapshot تعمیم نده. تاریخ ساعت container با مرجع Arena اختلاف داشت؛ wall-clock دقیق اجرای ابزارها `CHRONOLOGY_UNKNOWN` است.
>
> **ردیابی canonical (الحاقیهٔ DOC-05):** تصمیم پلتفرم در [ADR-007](../adr/007-pwa-primary-release.md)، پذیرش در [backlog canonical](../TODO-2026-11-16.md#pwa-ui-ux-full-backlog-2026-11-23)، صف/گیت‌ها در [tracker](../TODO-PWA-RELEASE-2026-11-23.fa.md) و status این checkout در [دفتر اجرا](../PWA-EXECUTION-STATE.md) است. hashها و حکم `CURRENT/GAP` در بدنه به snapshotی که صریحاً ثبت شده محدودند؛ این سند را بدون scan تازه به HEAD فعلی نسبت نده.

## ۱. محدوده و هویت snapshot

- بررسی read-only با `rg` روی `mp-app/studio/src/**/*.{ts,tsx,css}` و `tailwind.config.js` انجام شد؛ تمام importهای مستقیم `framer-motion`، مصرف‌کنندگان `useMotionPreset` و تعریف/مصرف animationهای CSS/Tailwind ردیابی شدند. فایل‌های `node_modules/` و `dist/` به‌عنوان source محصول شمرده نشدند؛ package نصب‌شده فقط برای توضیح رفتار hook بررسی شد.
- hash diff tracked درخت Studio در شروع/پایان این inventory: `d08481dca3e11a4ab19b9f634b8039eafdac1d320dcf2e10d654b25a6a79c253`. ۹ فایل untracked Studio با content-manifest SHA-256=`76b4f9896449ae6f5a398b45b562ddf79ac9c6cd79680aa21ba7bc7f3a5b4b1a` وجود داشتند. فایل‌های نامرتبط، به‌ویژه محتوای private رسید، باز/کپی یا مستند نشدند.
- این inventory source code را تغییر نداد. تغییر محدود قبلی Skeleton از قبل در working tree بود: `Feedback.tsx` SHA-256=`0fe5b03d45cd48b520978f7d1485885b8fef2afab1bb4fca4fc0c42314914404` و `components.test.tsx` SHA-256=`e21d38a907caa60f307706b9a4e5c78f8adecd8b2950ba8c1200d048ed03bc51`.
- سطح شاهد جاری helper: `src/lib/motion.ts` SHA-256=`19db976f3f2858521be00060916b0827557e205ac45cf4136115ee078059f246`; `tests/motion.test.tsx` SHA-256=`74a4b247f464c2e9e84876b64fa5bcf107e846014d532762442a4f57c21013d0`.

## ۲. قرارداد helper و مسیرهای خارج از آن

| سطح | خواندن جاری از source | شاهد/حکم |
|---|---|---|
| Helper واحد | `src/lib/motion.ts:28–119,122–228`: `buildPreset(true)` جابه‌جایی/scale و hover/press را حذف، fade کوتاه را نگه می‌دارد و stagger را صفر می‌کند؛ حالت عادی stagger را روی index ۱۲ سقف می‌کند. `useMotionPreset()` از `useSyncExternalStore` استفاده می‌کند؛ SSR و نبودن/خطای `window.matchMedia`، `MediaQueryList` بی‌رویداد قابل پاک‌سازی، خطای `matches` یا subscription ناموفق به fallback محافظه‌کار `reduced=true` می‌روند. modern و legacy listener پشتیبانی و cleanup می‌شوند. | **CURRENT برای رفتار helper در source/unit test.** `tests/motion.test.tsx:103–228` منطق pure، fallback/exception/unsupported، SSR، تغییر `false→true→false`، حفظ draft/focus و cleanup را می‌سنجد. این شواهد مرورگر نیستند. |
| گیت source test | `tests/motion.test.tsx:232–271` فهرست ۸ صفحه را چک می‌کند که نام `useMotionPreset` در فایل باشد و برای مدت‌های عددی چند assertion داشته باشد. | **GAP پوشش:** pass این گیت ثابت نمی‌کند تمام `motion.*` داخل صفحه/کامپوننت helper را رعایت می‌کند، delay دستی محدود است، DOM/focus در همهٔ جریان‌ها پایدار است، یا CSS guard دارد. کامپوننت‌های مشترک مستقیماً در فهرست نیستند. |
| Hook مستقیم Framer | درخت runtime در `App.tsx:45,57–65` و `Feedback.tsx:77,81–91` مستقیماً `useReducedMotion()` را می‌خواند، نه helper جاری. در type نصب‌شدهٔ `framer-motion@11.18.2` امضا `boolean | null` است. implementation نصب‌شده `useState(prefersReducedMotion.current)` می‌سازد؛ listener سراسری ref را تغییر می‌دهد ولی برای state فعلی setter/re-render ندارد؛ در نبود `matchMedia` preference را `false` می‌گذارد و init آن مسیر `try/catch` ندارد. | **GAP متنی برای یکپارچگی/live-update و unknown fallback؛ runtime مرورگر مستقلاً آزموده نشده.** در App/Toast شرط `reduced ? ... : motion` مقدار `null` را در شاخهٔ حرکت عادی قرار می‌دهد. پیاده‌سازی این پکیج evidence مستقل محصول نیست. مسیرهای محلی dependency: `node_modules/framer-motion/dist/es/utils/reduced-motion/{use-reduced-motion,index,state}.mjs` و `dist/index.d.ts`. این گزارش آن را pin/تغییر نمی‌دهد. |

## ۳. Crosswalk مصرف‌کنندگان در bundle اصلی Studio

«`CURRENT`» یعنی شرط/utility در source دیده می‌شود؛ به معنی تأیید بصری نیست. `GAP` یعنی مسیر حرکت در source از policy محافظه‌کار جاری عبور نمی‌کند یا برای آن evidence رفتاری نداریم؛ `UNKNOWN` یعنی نتیجهٔ واقعی browser/device/DOM از شواهد حاضر معلوم نیست.

| فایل/خط فعلی | مسیر و رفتار استاتیک | تست/شاهدی که اکنون داریم | دسته‌بندی |
|---|---|---|---|
| `src/App.tsx:45,57–65` | route container از `AnimatePresence mode="wait"` و hook مستقیم Framer استفاده می‌کند؛ در `true` initial/exit را حذف و duration را صفر می‌کند؛ `animate` هنوز target دارد. مقدار `null` به شاخهٔ normal می‌رود. | `tests/a11y.test.tsx:177–182` فقط وجود نام hook در متن App را می‌سنجد؛ fixture برای reduced/live change، route، focus یا exit نیست. | `GAP` برای مسیر hook واحد/live/unknown؛ retention هنگام exit `UNKNOWN`، نه ادعای leak. |
| `src/components/Feedback.tsx:74–108,114–132` | Toast از hook مستقیم Framer استفاده می‌کند؛ reduced transition را صفر و exit/initial motion را حذف می‌کند، اما unknown همانند حالت عادی رفتار می‌کند. `Skeleton` دارای `animate-pulse motion-reduce:animate-none` است. `SkeletonCards:124–132` همان Skeleton را تکرار می‌کند. | `tests/components.test.tsx:31–35` فقط حضور class را چک می‌کند؛ test computed style/media را ارزیابی نمی‌کند. | Toast: `GAP` در یکپارچگی helper/live-update؛ Skeleton: `CURRENT` در source و CSS utility. |
| `src/pages/Shop.tsx:16–18,65,173–180,202,243–255,287` | از helper برای تب/کارت‌ها استفاده می‌کند؛ spring نشانگر تب در reduced duration صفر می‌شود و کارت‌ها preset می‌گیرند. وضعیت loading واقعاً `SkeletonCards` را render می‌کند؛ تصویر hover scale و دکمه active scale جدا از helper هستند. | `tests/shopPage.test.tsx` جریان‌های فروشگاه را می‌سنجد؛ assertion reduced/computed-style برای Skeleton، تصویر یا دکمه پیدا نشد. test مستقل Skeleton فقط class است. | Helper/Skeleton `CURRENT` در source؛ hover/press و render واقعی `UNKNOWN/GAP` برای reduced. |
| `src/pages/CheckIn.tsx:23,30,45–55,89–93` | کارت از helper fade می‌گیرد؛ scan-line تکرارشونده در شاخهٔ reduced اصلاً ساخته نمی‌شود. ولی ردیف‌ها `motionPreset.slide` می‌گیرند و transition را با `{ delay: i * 0.08 }` جایگزین می‌کنند؛ بنابراین delay صفرِ helper حفظ نمی‌شود. | `tests/checkInPage.test.tsx` `matchMedia=false` می‌گذارد و feed/دکمه را می‌سنجد؛ reduced=true یا live toggle ندارد. | scan conditional `CURRENT` در source؛ delay در reduced یک `GAP` است؛ browser/فهرست بلند `UNKNOWN`. |
| `src/pages/Dashboard.tsx:18,58–60` | wrapper صفحه از helper استفاده می‌کند؛ childها مستقل‌اند و wrapper این موضوع را تعمیم نمی‌دهد. | `tests/dashboard.test.tsx` آزمون dashboard/data دارد، نه reduced-motion child props. | wrapper `CURRENT`; فرزندان در ردیف‌های زیر `GAP`. |
| `src/components/KpiCard.tsx:25–30` | opacity/y entrance، `index * 0.08` delay و hover y؛ هیچ helper/reduced شرطی در فایل نیست؛ از `.glass-card-hover` هم استفاده می‌کند. | `tests/components.test.tsx` مقدار/متن را render می‌کند؛ تست motion ندارد. | `GAP` (حرکت و delay مستقیم). |
| `src/components/MemberTable.tsx:71–76` | هر دکمه با x entrance، delay برابر `i * 0.05` و background-color `whileHover` است؛ key=`member_id` ثابت است. | تست reduced/component-level برای این child یافت نشد. | `GAP` برای entrance/delay؛ رفتار focus و لیست بزرگ `UNKNOWN`. |
| `src/components/ScheduleTimeline.tsx:68–73` | ردیف‌ها x entrance و delay=`i * 0.06` دارند؛ source حداکثر شش کلاس render می‌کند، اما reduced guard ندارد. | test مستقیم reduced-motion برای Timeline یافت نشد. | `GAP` برای کاهش حرکت؛ مقدار واقعی delay در browser `UNKNOWN`. |
| `src/pages/Analytics.tsx:16,54,85` | کارت‌ها از `motionPreset.rise` استفاده می‌کنند؛ raw delay دستی در همین قطعه دیده نشد. | گیت ۸ صفحه فقط وجود helper را چک می‌کند؛ render در reduced/live یا screenshot وجود ندارد. | `CURRENT` در قرارداد source، browser behavior `UNKNOWN`. |
| `src/pages/Programs.tsx:34,89–91,145–150` | wrapper و کارت‌ها از helper می‌آیند؛ `stagger(i)` سقف‌دار و reduced=0؛ اما `glass-card-hover` transition CSS مستقلی دارد. | تست source helper و تست‌های feature؛ motion واقعی/keyboard/focus زیر reduced ثابت نشده. | `CURRENT` برای Framer preset؛ CSS hover `UNKNOWN`. |
| `src/pages/Finance.tsx:37,102,106,114–127,161,166–179` | wrapper helper دارد؛ summary، نتیجهٔ کمیسیون و error با initial/animate مستقل opacity/y وارد می‌شوند؛ دکمه‌های مالی hover/active scale دارند. | testهای مالی semantics را می‌سنجند، نه reduced style یا حفظ focus/draft روی toggle. | wrapper `CURRENT`; child motion/scale `GAP`; focus/state behavior `UNKNOWN`. |
| `src/pages/Members.tsx:17,82–88,149–155,201–210` | پنل از helper slide استفاده می‌کند، ولی `exit={{opacity:0,x:-20}}` بدون reduced شرط است؛ bar width فقط در reduced initial=false/duration=0 می‌شود؛ empty state opacity entry/exit مستقل دارد؛ `AnimatePresence mode="wait"`. | unit/component شاهدی برای selection + reduced + exit DOM/focus پیدا نشد. | bar `CURRENT`; exit/empty motion `GAP`; DOM retention/فوکوس `UNKNOWN`. |
| `src/pages/Settings.tsx:30,74,103–107,120–128` | wrapper helper دارد؛ هر row انیمیشن x با delay=`i * 0.04` بدون سقف/شرط، knob با layout spring؛ state toggle سروری است و این inventory منطق آن را تغییر نمی‌دهد. | test موجود behavior تنظیمات را به reduced/focus وصل نمی‌کند. | wrapper `CURRENT`; row/spring `GAP`; تعداد flags/focus در عمل `UNKNOWN`. |
| `src/components/Sidebar.tsx:70–75,86` | نشانگر active با layout spring حرکت می‌کند؛ نقطهٔ «سیستم فعال» کلاس `animate-pulse-soft` بی‌پایان دارد؛ hook/helper ندارد. | `tests/components.test.tsx` و `tests/roleNav.test.tsx` navigation را می‌سنجند، نه motion. | `GAP` برای pulse/layout. |
| `src/components/TopBar.tsx:71–76` | عنوان هر route با opacity + x و duration 0.28 وارد می‌شود؛ شرط reduced ندارد. | test route/a11y شاهد reduced محاسبه‌شده ندارد. | `GAP`. |
| `src/components/UpdateBanner.tsx:10–16,29` | `AnimatePresence` بنر را با y و spring وارد/خارج می‌کند؛ دکمه active scale دارد؛ reduced guard ندارد. | `tests/updateBanner.test.tsx` وجود بنر و دکمه/reload را می‌سنجد، نه motion/media. | `GAP` برای reduced؛ function flow به‌تنهایی motion evidence نیست. |
| `src/styles/index.css:52–78`; `tailwind.config.js:63–80` | `.glass-card-hover` transition-all 300ms؛ `.btn-primary` transition-all 200ms + active scale و در صفحات متعدد/کامپوننت‌ها مصرف می‌شود؛ `.btn-ghost` transition-all رنگ/مرز دارد؛ `.skeleton` `animate-shimmer` بی‌پایان تعریف می‌کند. Tailwind `pulse-soft` و `shimmer` تعریف شده‌اند؛ `scan-line` تعریف شده ولی کلاس آن در `src/` مصرف نشد. | build CSS یک utility برای Skeleton تولید کرده؛ برای transition-all، pulse-soft یا shimmer media override سراسری در stylesheet محصول پیدا نشد. | `.btn-primary`, pulse-soft و transition-all: `GAP`; `.skeleton`/shimmer: تعریف موجود ولی class `.skeleton` در markup فعلی `src/` یافت نشد؛ `scan-line` پیکربندی بلااستفاده در scan. |
| مصرف‌کنندگان class مشترک | `.btn-primary` در `Chat.tsx:158,264`, `Nutrition.tsx:299`, `Members.tsx:176`, `Login.tsx:87,119`, `Programs.tsx:204`, `VolumePanel.tsx:97`, `SegmentalPanel.tsx:175`, `PaymentPanel.tsx:182,197`, `FoodLibrary.tsx:81`, `AutoregPanel.tsx:109`, `AdaptiveNutritionPanel.tsx:191`; `.btn-ghost` در همان سطوح + `RemindersPanel.tsx:70` و `CheckIn.tsx:67`. | جست‌وجوی استاتیک مصرف classها؛ بررسی `prefers-reduced-motion` component-by-component انجام نشده. | `GAP` ناشی از utility مرکزی، نه ادعای رفتار runtime روی همهٔ کنترل‌ها. |
| Transitionهای رنگی | `styles/index.css:74`; `Shop.tsx:168`, `Programs.tsx:106`, `Members.tsx:68`, `Nutrition.tsx:258`, `Chat.tsx:178`, `Settings.tsx:120`, `Sidebar.tsx:65`, `Feedback.tsx:102`, `Finance.tsx:109`, `PaymentPanel.tsx:220`, `FoodLibrary.tsx:108`. | source فقط transition رنگ/مرز/پس‌زمینه نشان می‌دهد؛ این scan آن‌ها را به scale/translate تبدیل نمی‌کند و آزمون visual ندارد. | `LOW-SPATIAL-MOTION/UNKNOWN`: مناسب‌بودن مدت برای کاربر در browser بررسی نشد؛ با gapهای مکانی Framer یکی شمرده نمی‌شود. |

## ۴. CSS خروجی، Skeleton و entrypoint آزمایشگاهی

- `npm run build` روی همین درخت محلی پیش‌تر موفق بود. CSS تولیدشدهٔ `dist/assets/index-BJp792j2.css` شامل قاعدهٔ پایهٔ `.animate-pulse{animation:pulse 2s cubic-bezier(.4,0,.6,1) infinite}` و بعد از آن `@media (prefers-reduced-motion: reduce){.motion-reduce\:animate-none{animation:none}}` است؛ ترتیب و nesting در خروجی بررسی شد.
- `Shop.tsx:202` هنگام loading واقعاً `SkeletonCards` نشان می‌دهد، پس utility افزوده‌شده در مسیر جاری Shop مصرف می‌شود. هیچ browser/JSDOM computed-style assertion در evidence نیست؛ این فقط بررسی cascade در CSS build است.
- کلاس جداگانهٔ `.skeleton` در `styles/index.css:76–78` shimmer بی‌پایان دارد، ولی markup فعلی `.skeleton` را به کار نمی‌برد. آن را با `Skeleton` component یکی ندان؛ اگر class CSS بعداً مصرف شود، reduced guard جدا لازم خواهد داشت.
- `src/visual-concepts/VisualConcepts.tsx` و `visual-concepts.css` نیز motion/useReducedMotion و media query دارند، اما lab جدا هستند: `src/main.tsx` `App` و `styles/index.css` را import می‌کند؛ `visual-concepts.html` ورودی مجزا است. build پیشین `dist/` شامل آن HTML نبود. آن را نه global fix فرض کن نه گیت انتشار PWA.

## ۵. تست‌ها و محدودیت شواهد

| منبع | چه چیزی را می‌سنجد | چه چیزی را نمی‌سنجد |
|---|---|---|
| `tests/motion.test.tsx:103–228` | helper pure، fail-closed pathها، SSR snapshot، live state در fixture، draft/focus و unsubscribe؛ local targeted result ثبت‌شده: ۱۷/۱۷ پاس. | Framer hook مستقیم App/Toast، childهای Dashboard، CSS computed، browser/OS integration. |
| `tests/motion.test.tsx:232–271` | presence متن `useMotionPreset` و محدودیت literal duration برای ۸ صفحه. | اینکه تمام motion descendants/spacing/delay/exit از آن helper پیروی کنند؛ source-grep برابر behavioral acceptance نیست. |
| `tests/components.test.tsx:8–35` | render دادهٔ KpiCard، Sidebar و وجود `motion-reduce:animate-none` روی Skeleton؛ در اجرای targeted قبلی جزئی از ۲۲/۲۲ بود. | media query match واقعی، computed animation یا browser paint. |
| `tests/a11y.test.tsx:177–182` | وجود `useReducedMotion` در source `App.tsx`. | true/false/null، live update، component UI یا screen reader. |
| `tests/checkInPage.test.tsx` | feed و کنترل اسکن با `matchMedia=false`. | reduced=true، تغییر زنده و delay behavior. |
| `tests/updateBanner.test.tsx`, `tests/shopPage.test.tsx` | پیام/کنش بنر و جریان فروشگاه. | motion preference/computed style؛ در shop loading Skeleton صریحاً assert نشده است. |
| `npm test -- --reporter=dot` | اجرای قبلی روی dirty tree: ۵۰ فایل PASS، ۲ SKIP؛ ۳۲۹ PASS، ۱۰ SKIP، ۰ fail. | CI همان SHA، visual layout یا browser/device. JSDOM `getComputedStyle`, React `act(...)` و Recharts بدون layout warnings داشت. |
| browser availability | در این محیط نام‌های `chromium`, `google-chrome`, `firefox` و packageهای موجود Playwright/Puppeteer در Studio یافت نشدند؛ چیزی نصب نشد. | این فهرست جست‌وجو ادعای نبودن مرورگر در همهٔ hostها نیست؛ اجرای browser همین‌جا `NOT_RUN` است. |

## ۶. Disposition snapshot inventory پیش از patch

- **Current facts:** helper/test مستقل نسبت به inventory قدیمی hash متفاوت دارد و نسخهٔ فعلی fallback/live behavior بهتری دارد؛ Skeleton pulse در خروجی CSS واقعاً زیر media query override شده و SkeletonCards در Shop مصرف می‌شود.
- **Confirmed source gaps:** hook مستقیم Framer در App/Toast از helper جدا است؛ چند child/shared component حرکت خام یا delay دستی دارد؛ pulse و utilityهای CSS/Tailwind guard سراسری ندارند. مورد `AnimatePresence` عضو فقط `RISK/UNKNOWN` دربارهٔ retention است، نه leak اثبات‌شده یا مرز امنیت.
- **Status:** `MK-PWA-01-FU-01 = PARTIAL`؛ current-tree static source/hash/test crosswalk ثبت شد، اما independent review و browser/OS/device behavioral evidence انجام نشده است. `MK-PWA-02` و `O3-08` `PARTIAL` می‌مانند؛ `MK-PWA-03/05` و PWA product gates بسته نیستند.
- هیچ patch تازهٔ source در این inventory انجام نشد. تغییر App/Toast، member/finance/setting motion یا CSS سراسری، قرارداد/allowlist/budget/review جدا می‌خواهد؛ این گزارش به‌تنهایی مجوز تغییر آن‌ها نیست.
- تعداد و متن canonical parentها، acceptanceها، dependencyها و `PROPOSED/BLOCKED/NOT_RUN` تغییر نمی‌کند؛ این inventory PWA-13/PWA-47/PWA-52 را PASS نمی‌کند.

## ۷. Manifest اولیهٔ snapshot inventory (پیش از patch)

Hash کامل SHA-256 بایت‌های source/test در snapshot read-only پیش از patch؛ این مقادیر تاریخچه‌ای‌اند و برای فایل‌های اصلاح‌شده با manifest نهایی بخش ۸ جایگزین می‌شوند:

| مسیر | SHA-256 |
|---|---|
| `src/App.tsx` | `4dcdc6749ac6fb7fe2b92bbf47a542a5e6f43693a9f98224f04833d7f1d05007` |
| `src/lib/motion.ts` | `19db976f3f2858521be00060916b0827557e205ac45cf4136115ee078059f246` |
| `src/components/Feedback.tsx` | `0fe5b03d45cd48b520978f7d1485885b8fef2afab1bb4fca4fc0c42314914404` |
| `src/components/KpiCard.tsx` | `7029265e50b414927480d34705b0b3b80cb4c258e28834a1b73b6dd7a2d839d3` |
| `src/components/MemberTable.tsx` | `9dbb89d160747e37da886f8788a9e87f7cd37e6b69db13cdcb832e58d500f597` |
| `src/components/ScheduleTimeline.tsx` | `5c2e175b6e5d6825489a331da032e7f68a54953a3611951c2cd36c2fb616c36e` |
| `src/components/Sidebar.tsx` | `e9c38262467cd2dc10748f8474f85836684297140fe53f143f032c3253031c63` |
| `src/components/TopBar.tsx` | `ed567317b523ce521b2e325dd826fff147dcd0f59161fb9ed67c48607315c187` |
| `src/components/UpdateBanner.tsx` | `24ddeff5fba36fd27efd7ad426161bb7104b6964fe10a69b18b0cdecbc7dee3a` |
| `src/pages/Analytics.tsx` | `74cdc3270316ab835add789485b52b94f34f75335585dba101eb19bc44ffd42b` |
| `src/pages/CheckIn.tsx` | `6fe1e883a959d3fb3c7862c350b1b2fa61f1e19ad5ca3871b5539ee4b64fe29a` |
| `src/pages/Dashboard.tsx` | `96dd035a7ebba4063f479a3a2929c20e3be0bea83a0ab015a6873c4047ae4e65` |
| `src/pages/Finance.tsx` | `73b23afabee755059497c917adeb80f717865b00f3d4aa6c3b75edc73473bd4b` |
| `src/pages/Members.tsx` | `111ac72fdffc9d8e6d443acdfb168bcf8163de3aaba6c3bc79a092df032333a2` |
| `src/pages/Programs.tsx` | `9097b77065b59335141d383035409428e481823d3cec984693c272ca1ea95827` |
| `src/pages/Settings.tsx` | `7f4877bd905dea986ada7fb56b849607e62d7f53af551849ead1df7201ee2535` |
| `src/pages/Shop.tsx` | `7cd3c8b95527da6e9d25cb7175c405fbe89786603b52387a60562ba746424dba` |
| `src/styles/index.css` | `eff3cdc9caa149eaea855a7c105b5c41767b3d160575b2d16d95ba84f82b2cbe` |
| `tailwind.config.js` | `8f7b4aa26a169c4c353e8822d202027d072634b274a112dbb4771b85a64fed03` |
| `src/main.tsx` | `841e2b12a30ed156a10b8fa6d46b4e3394ac62a0a07f72d45078467b0694aa5e` |
| `visual-concepts.html` | `931e749def1c2508e0497a3520a6b6bc1801c526b3056f351e1cf3266496f37b` |
| `src/visual-concepts/main.tsx` | `34254eef85e8e9010aa4f81bc8d4917b89530d9f04c72fd3f67a6b17e2dbcf1e` |
| `src/visual-concepts/VisualConcepts.tsx` | `cc86dcb3f6528b0c6300d6b432de5476d0b7d543d7e4587a164f3642b3a0be43` |
| `src/visual-concepts/visual-concepts.css` | `c6478676d3fc24fbdd12dbab7d4363236b14a9ebfd04032f9069273352c9f365` |
| `tests/motion.test.tsx` | `74a4b247f464c2e9e84876b64fa5bcf107e846014d532762442a4f57c21013d0` |
| `tests/components.test.tsx` | `e21d38a907caa60f307706b9a4e5c78f8adecd8b2950ba8c1200d048ed03bc51` |
| `tests/a11y.test.tsx` | `6cd9217c111b00c1b1ff49cdabaabbf7b4898687e2372840ebac9d39d5840aef` |
| `tests/checkInPage.test.tsx` | `da18738cbab51720bd8d626b701ab77687b164ed4906f9a86fcc80f354485021` |
| `tests/updateBanner.test.tsx` | `b72c25d84803d666a45a4701dbfb6be787dece8a7e0eca1faa02f6ff80c08818` |
| `tests/shopPage.test.tsx` | `aa44ebfbcff69c3541401d7e1ecfe81e892c039b1207e4370e217da5eb4aea05` |
| `src/pages/Chat.tsx` | `07810db93096be134430fae3a5e888c6234bb3e0f2e680e33964f5dfb85ef0ee` |
| `src/pages/Nutrition.tsx` | `95c8bed78c4b28589515cc862d37a864e083ba7b525fae2af11043388ebf7b58` |
| `src/pages/Login.tsx` | `a5d073adbb0e4b47bb4266577abc9aa74a3ad0d8eaaa2c4ac5bcb1c5429c41d5` |
| `src/components/VolumePanel.tsx` | `80c79388a254d1acddd7e3bea730bd0536025e9f17cb59c79e82b04bd51ec28e` |
| `src/components/SegmentalPanel.tsx` | `2ab85a196a4a40048d9954167215964938462cd25fc17757f4955bcaffdc5783` |
| `src/components/PaymentPanel.tsx` | `428ade101b143dd6ea88b716aee383c0714e97f915ae244c3776edeefe26b976` |
| `src/components/FoodLibrary.tsx` | `2bc48f4f7a313eee4e1e224e72f112d8884172dca0671b741261131ad87f1333` |
| `src/components/AutoregPanel.tsx` | `678502d827e0434c509b7de6c534d51cba9fd38093e17569aeea7dba9ba27d6e` |
| `src/components/AdaptiveNutritionPanel.tsx` | `47d434b93034921bb516b101d7c565c3185b37198d2b8f2f408cf9185d5b3a04` |
| `src/components/RemindersPanel.tsx` | `00587b4f0ba06aca9ba1e69d0556802c845367baefe06dabbb1adbcfb5bbbf46` |

**گیت‌های باز بعد از snapshot inventory:** browser/device/OS fixture برای computed style و رفتار بصری، independent review/owner gate، و بررسی جداگانهٔ VisualConcepts lab. اصلاحات محدود پس از inventory و شاهدهای محلی در بخش ۸ آمده‌اند؛ تا evidence واقعی فراهم شود `PARTIAL/UNKNOWN` حفظ شود.

## ۸. اصلاح محدود پس از inventory — reduced-motion follow-up

### دامنه و تغییرهای source

- این follow-up مسیر reduced-motion در runtime اصلی `mp-app/studio/` و تست‌های مرتبط را اصلاح کرد؛ سپس یک patch جدا و محدود برای lab/entrypoint مستقل VisualConcepts اضافه شد. تغییرهای نامرتبط worktree لمس نشدند. `src/lib/motion.ts` بازنویسی نشد؛ helper موجود، `useSyncExternalStore`، fallback محافظه‌کار `reduced=true`، listener زنده و cleanup را تأمین می‌کند.
- `App.tsx` و `Feedback.tsx` دیگر به `useReducedMotion()` مستقیم Framer تکیه نمی‌کنند. App، toast، `TopBar`، `UpdateBanner`، `Sidebar`، `KpiCard`، `MemberTable`، `ScheduleTimeline`، `CheckIn`، `Finance`، `Members`، `Settings` و `Shop` برای حرکت Framer به `useMotionPreset` وصل شدند. در reduced mode exit/layout/shared-layout و hover/pressهای مکانی خاموش یا به fade کوتاه/بدون جابه‌جایی محدود می‌شوند؛ delayهای ردیفی به `stagger(i)` سقف‌دار/صفر منتقل شدند.
- **VisualConcepts lab:** `src/visual-concepts/VisualConcepts.tsx` حالا در صفحه، `LandingPreview` و `FeatureTile` از helper مشترک استفاده می‌کند؛ `useReducedMotion` مستقیم حذف شد. نشانگر `active-direction` فقط در حالت عادی `layoutId` و spring دارد؛ در حالت reduced، `layoutId` حذف و transition به duration صفر می‌رود. ورود/خروج و art previewها از fade کوتاه helper استفاده می‌کنند و hover کارت از preset مشترک می‌آید. CSS مستقل lab هم delayهای animation/transition را صفر و transform حالت hover جهت‌ها را خاموش می‌کند؛ README مصرف helper را مستند می‌کند. این lab همچنان entrypoint جداست: `tsconfig.json` فایل TSX زیر `src/` را type-check می‌کند، اما build استاندارد Vite فقط `dist/index.html` را تولید کرد و HTML lab را bundle نکرد.
- `styles/index.css` یک `@media (prefers-reduced-motion: reduce)` مرکزی دارد: مدت CSS animation/transition و delay را به near-zero می‌رساند، animation را به یک iteration محدود و smooth scrolling را خاموش می‌کند؛ `.btn-primary:active` scale نیز override دارد. برای scaleهای خاص Finance/Shop/UpdateBanner و pulse سایدبار utilityهای `motion-reduce:*` افزوده شد. این rule، motion مبتنی بر JavaScript یا computed style واقعی را به‌تنهایی ثابت نمی‌کند.
- دو نمودار Recharts محصول (`AttendanceChart` و `PeriodReportPanel`) حالا animation سری داده و Tooltip را با preference مشترک خاموش می‌کنند؛ این مسیر از اسکن Framer/CSS اولیه جا مانده بود.

### تست و ساخت محلی

- `tests/checkInPage.test.tsx` اکنون reduced=true را render می‌کند، نشان ثابت اسکن را به‌جای scan متحرک می‌سنجد، تغییر زندهٔ preference را false→true→false آزمون می‌کند و حفظ focus دکمه/state اسکن را در JSDOM می‌سنجد. این browser/OS test نیست.
- `tests/motion.test.tsx` helper/fallback/live listener/draft/focus و source contract را پوشش می‌دهد: ۱۹ مصرف‌کنندهٔ motion/chart، absence از raw `useReducedMotion`، نبود delay خام `i *`، guardهای CSS و تنظیم animation نمودارها. برای lab نیز assertion جداگانه وجود `layoutId` فقط در حالت عادی، duration صفر spring در reduced، استفاده از presetهای ورود/hover و media rule مستقل CSS افزوده شد. این‌ها assertion منبع‌اند، نه computed-style acceptance. `components.test.tsx` presence classهای skeleton/sidebar pulse را می‌سنجد؛ `a11y.test.tsx` وجود helper در App را چک می‌کند.
- targeted پس از patch lab: `npm test -- --reporter=dot tests/motion.test.tsx tests/checkInPage.test.tsx` → **۲ فایل، ۳۴/۳۴ PASS**.
- full Studio suite پس از patch lab: `npm test -- --reporter=dot` → **۵۰ فایل PASS، ۲ SKIP؛ ۳۴۵ PASS، ۱۰ SKIP، صفر fail** (۱۸۶٫۰۹ ثانیه). Warningهای موجود JSDOM `getComputedStyle`, React `act(...)` و Recharts container با width/height صفر دیده شدند؛ skipها و warningها pass نیستند و browser fidelity را نمی‌سنجند.
- `npm run lint` و `npm run build` پس از patch هر دو exit `0`; build استاندارد: Vite `5.4.21`، ۴۰۴۵ module. خروجی `npm run build` فقط `dist/index.html` و assetهای app اصلی را فهرست کرد. برای entrypoint lab یک build ایزولهٔ دیگر با JavaScript API پکیج Vite، همان `vite.config.ts`، ورودی `visual-concepts.html` و `outDir` موقت بیرون مخزن اجرا شد: **exit 0، ۳۳۸۹ module**؛ `visual-concepts.html` و assetها ساخته شدند و temp بعد از ثبت فهرست حذف شد. بررسی ایستای CSS تولیدشده (`visual-concepts-B6s-Jj05.css`, ۳۴٬۵۱۱ بایت) media query، delay صفر animation/transition و hover-transform override را PASS کرد. این‌ها bundle/type-check و رشته‌/CSS inspection هستند، نه اجرای lab در مرورگر یا computed-style واقعی. بررسی استاندارد `dist/assets/index-CRepSoME.css` نیز media rule مرکزی و utilityهای reduced active/group-hover را یافت؛ این فقط fingerprint/CSS bundle inspection است، نه محاسبهٔ computed style.

### وضعیت و مرز ادعا

- اصلاح source/test به معنی پذیرش بصری یا تکمیل reduced-motion نیست. مرورگر واقعی، system preference OS، computed style، screenshot، screen reader، device، focus/route transition در مرورگر و independent review انجام نشد. ابزار browser/E2E در این sandbox موجود نیست؛ VisualConcepts همچنان entrypoint/lab جداگانه است و فقط source/CSS/unit-source coverage آن به‌روز شد.
- `MK-PWA-01-FU-01 = PARTIAL`، `MK-PWA-02 = PARTIAL` و `O3-08 = PARTIAL` باقی می‌مانند؛ browser/device/OS، computed-style و review مستقل بازند. هیچ‌یک از ۵۰ parent، acceptance یا dependency canonical و هیچ release gate تغییر نکرده است. baseline مشترک PWA نیز به‌تنهایی مجوز release نیست.
- بدون stage/commit/push/PR/merge/release/deploy؛ سورس و تست‌ها فقط در worktree محلی‌اند.

### Manifest نهایی SHA-256 فایل‌های تغییریافتهٔ follow-up

مقادیر زیر بایت‌های فعلی فایل‌ها در worktree را ثبت می‌کنند؛ hash manifest اولیهٔ pre-patch در بخش ۷ برای تاریخچه حفظ شده است.

| مسیر | SHA-256 |
|---|---|
| `src/App.tsx` | `873b4fff8457993626c64da25730bc21286819dec6bd4de5c25bfeb2b8bf2de3` |
| `src/components/Feedback.tsx` | `05a94401c44876fc0bd032e08a4c1084a124043788391569f63b08ae6eae4f73` |
| `src/components/Sidebar.tsx` | `d7dce55cee13b79d2d219b56efaa0115eae2fce3a5ec20b5a8b4751c2d57c401` |
| `src/components/TopBar.tsx` | `9e9735f14b2167dc7b003891ae1093d412349885eed7c7c5a43aceec275b2ec4` |
| `src/components/UpdateBanner.tsx` | `957039ed2550b7a2b7a84211c60b21e4ba8255303ac8f182f91a63555fe163b8` |
| `src/components/KpiCard.tsx` | `aa37260b5f922885f3dab67a7cfdff10c62eddec8977cd3ee896180b3c95542c` |
| `src/components/MemberTable.tsx` | `b381b6535c425d8efdd3b0a5f42dee5edc682e0bd423360c8411e7962ea03824` |
| `src/components/ScheduleTimeline.tsx` | `21ca63d97b3c1049dae7c1c3f93594ccee77e7a7ecec4bb37f4a899839a4637e` |
| `src/components/AttendanceChart.tsx` | `14a684bf9e5edf42eefabb13277063839cfb3dc8a14940e528096b67ba3ad84e` |
| `src/components/PeriodReportPanel.tsx` | `a55f207b1777c3077c638a985ab7101db341ab814dba6aa91d9e3f25ecd42ff1` |
| `src/pages/CheckIn.tsx` | `9a12d1389a0820da206885bdd91770eda6ee23617579896ecf3d6d06b6223051` |
| `src/pages/Finance.tsx` | `5c0274d20fcec45191f1def256be18c3b630e551c98d0c96af727bb4432819e4` |
| `src/pages/Members.tsx` | `329525c55f95716c5a1c2027d75a6d68f60e6da529bf37c23f034e4f9bd2633b` |
| `src/pages/Settings.tsx` | `535ee4ba829257c50157d7e44424860da422384f37e0d78ae7b1ad30bcf0a40c` |
| `src/pages/Shop.tsx` | `1c12834104930b77b2263970f8a2e5632efce05f06785b38809f99f3a2bbe9a9` |
| `src/styles/index.css` | `649bcd2547f935bb2adffbc40ddd23d765f8c523bdf8cc316e3f8eb533a25e3b` |
| `tests/a11y.test.tsx` | `1d54b2bdd2b78133495e91bfcd8f41d4306e52a951bf975f6ab0e550dd388311` |
| `tests/checkInPage.test.tsx` | `5a7f3f8d37b1d755f13e922904ea9bb0346ccaa577599100f4121d4855c23179` |
| `tests/components.test.tsx` | `6458e66ef61f9bdeaf671783d44429b273e75dfa203205f9c514bd8d43510359` |
| `tests/motion.test.tsx` | `3153333649368c7943a3a133fc771719827b33e3f5e5ceb1a74b66649d3992da` |
| `src/visual-concepts/README.md` | `6d654f25b20ceb4263a4ba7aa7dcdd6bedd88ec6e348b710c0083642691f426b` |
| `src/visual-concepts/VisualConcepts.tsx` | `e26bf943e62ba85bd727455c17ff1f65fef8832aae8390c10935a4d8dfa7ed6e` |
| `src/visual-concepts/visual-concepts.css` | `b23f25acdc682728dba9adc6df04c94d67be7e9c52214132bdd1eed930a6863d` |

### Fingerprint worktree پس از patch lab

- branch=`arena/5e0f64cf-mp`, `HEAD=d92817f4151ebbafb25425b7b28776a4cc1180dc`, base=`35d4b35184b4148c658b415bd009fc076bf24e00`; `git status --porcelain` در حالت پیش‌فرض: ۵۹ مسیر tracked تغییریافته، ۱۰۱ ورودی untracked، stage صفر.
- Studio tracked diff (`git diff --binary -- mp-app/studio`) SHA-256=`bdedaf8b6ca38dd5a19846017ad2a49ce50f1d4b5c9b0d7874608e1a1aba2aab`.
- ۹ فایل untracked Studio؛ content-manifest SHA-256=`18665cb8b0f84ee570ff3040f89c073397a00245c90d7f705e96f69bb0f8f2fa`, بر مبنای ردیف‌های `sha256sum` مرتب‌شده بر مسیر (`<file-sha256><two spaces><path><newline>`). fingerprintها dirty worktree را مشخص می‌کنند، نه commit/CI یا تأیید محصول.

## ۹. Browser QA مصنوعی — helper و VisualConcepts lab

> افزودهٔ این نوبت به همان worktree dirty؛ تاریخ مرجع Arena `2026-11-23 UTC` است و ساعت دقیق اجرای ابزارها `CHRONOLOGY_UNKNOWN` می‌ماند. این اجرای مرورگر، snapshot مستقل/تمیز یا بازبینی شخص ثالث نیست.

- **شناسه و ورودی:** branch=`arena/5e0f64cf-mp`, `HEAD=d92817f4151ebbafb25425b7b28776a4cc1180dc`; مرورگر با Vite dev server از همان درخت Studio و entrypoint جداگانهٔ `/visual-concepts.html` بالا آمد. صفحه فقط داده و تعامل مصنوعی lab داشت؛ backend، auth واقعی، صفحهٔ route محصول یا PWA نصب‌شده آزموده نشد.
- **ابزار:** `node /tmp/arena-mp-motion-browser-tools/run-motion.mjs`; Node `v22.22.3`, Vite `5.4.21`, Playwright Core `1.65.1`, `@sparticuz/chromium@158.0.0`, مقدار `browser.version()`=`153.0.8010.0`. پکیج‌ها/harness بیرون repository در `/tmp` بودند؛ هیچ dependency/manifest محصولی اضافه نشد. Chromium headless اجرا شد و `prefers-reduced-motion` را Playwright با `emulateMedia` تغییر داد؛ این تنظیم OS یا دستگاه نیست.
- **نتیجه:** **۱۳/۱۳ assertion گروه‌بندی‌شده PASS**. `matchMedia('(prefers-reduced-motion: reduce)')` در مسیر reduced درست بود؛ `getComputedStyle` برای transition/animation duration به سقف `0.05ms` و delayها به `0s` محدود شد. stagger برای index=100 در حالت عادی `0.54s` و در reduced صفر بود. transform مکانی hover کارت در reduced `none` ماند، پس از تغییر زنده به no-preference به `y=-2px` برگشت و با برگشت reduced پاک شد؛ CSS transition عادی `0.16s` بود.
- **ورود/خروج و تعامل:** نمونهٔ replay در reduced بیشینهٔ جابه‌جایی Y برابر `0px` (۲۸ نمونهٔ animation-frame) داشت؛ در حالت عادی `10px` (۳۳ نمونه). انتخاب جهت با `aria-pressed` و تغییر به Studio نمایشی آزموده شد؛ input مقدار synthetic `browser draft stays`، focus و همان DOM node را در هر دو جهت تغییر preference حفظ کرد و selection/screen ماندند. در context جداگانه‌ای که `window.matchMedia` عمداً `undefined` بود، helper fail-closed کرد و hover مکانی فعال نشد. خطای page و درخواست network غیرمحلی دیده نشد.
- **مرز evidence:** این نتایج computed-style و تعامل DOM در Chromium headless را برای entrypoint آزمایشگاهی ثابت می‌کنند؛ screenshot دائمی گرفته/ثبت نشد، keyboard-only traversal و screen reader سنجیده نشدند، سرور production/CI و browser routeهای اصلی محصول پوشش داده نشدند، و OS preference، مرورگر/دستگاه فیزیکی و reviewer مستقل در دسترس نبودند. اسکریپت harness خارج از repo بود و این run تست CI دائمی نیست.
- **وضعیت:** browser evidence خلأ رفتاری را کم می‌کند، اما `MK-PWA-01-FU-01`, `MK-PWA-02` و `O3-08` را از `PARTIAL` به `PASS` نمی‌برد؛ independent review/G9، browser/device/OS target و پذیرش کامل صفحه‌های محصول باز می‌مانند. هیچ parent/status canonical، release gate، یا Go/No-Go تغییر نکرد.
- **عدم تغییر و fingerprint:** source/test تولیدی در این نوبت دست‌نخورده؛ hash helper=`19db976f3f2858521be00060916b0827557e205ac45cf4136115ee078059f246`, lab TSX=`e26bf943e62ba85bd727455c17ff1f65fef8832aae8390c10935a4d8dfa7ed6e`, CSS=`b23f25acdc682728dba9adc6df04c94d67be7e9c52214132bdd1eed930a6863d`; Studio tracked-diff SHA-256 همچنان `bdedaf8b6ca38dd5a19846017ad2a49ce50f1d4b5c9b0d7874608e1a1aba2aab`. index با `git diff --cached --quiet` پاک بود؛ stage/commit/push/PR/merge/release/deploy انجام نشد.

## ۱۰. Browser QA مصنوعی — Studio CheckIn و reduced-motion

> این ادامهٔ آزمایشگاهی روی route اصلی Studio است، نه مرور VisualConcepts lab و نه آزمایش دستگاه/OS. تاریخ مرجع Arena `2026-11-23 UTC`؛ wall-clock دقیق commandها `CHRONOLOGY_UNKNOWN` می‌ماند.

- **اجرا/fixture:** routeهای اصلی Studio با harness موقت `/tmp/arena-mp-motion-browser-tools/run-studio-checkin.mjs`، Vite dev server و auth/API fixture/token کاملاً synthetic آزموده شدند؛ هیچ backend، حساب، token یا دادهٔ واقعی استفاده نشد. Browser `@sparticuz/chromium@158.0.0` / Chromium `153.0.8010.0` با Playwright Core `1.65.1` بود. `prefers-reduced-motion` با browser emulation تغییر داده شد، نه OS.
- **نتیجه:** **۱۰/۱۰ assertion PASS**: tab traversal در Studio menu؛ shell و CheckIn route با fixture بار شدند؛ scan bar در reduced ثابت و در normal متحرک بود؛ تغییر زندهٔ reduced↔normal در هر دو جهت، با حفظ focus، state و identity گره؛ کنترل با Enter؛ fallback fail-closed وقتی `matchMedia` موجود نبود؛ و صفر page errors یا network requests خارجی در اجرای اصلی.
- **تصویر:** [CheckIn reduced-motion synthetic](../../../artifacts/motion-availability-qa-2026-11-23/studio-checkin-reduced.png) با ابعاد ۱۴۴۰×۱۰۰۰ و SHA-256=`03ca06c83a9034eaeb7465da2b201a8c748fc82a56308dfce5fa03fb13e35f4b`. این یک viewport headless با fixture است؛ multi-device، visual sign-off یا OS preference نیست.
- **مرز evidence:** این اجرا مسیر Studio/CheckIn را در مرورگر headless و با API stub می‌سنجد؛ install/service worker/offline/update، backend/auth واقعی، کل مسیرهای عضو/کادر، screen reader، مرورگر/OS فیزیکی، CI و reviewer مستقل را پوشش نمی‌دهد. harness خارج repo است و test دائمی/CI ایجاد نشد.
- **وضعیت/تبعیت:** `MK-PWA-01-FU-01 = PARTIAL`, `MK-PWA-02 = PARTIAL`, `O3-08 = PARTIAL`; شاهد جدید یکی از شکاف‌های browser-emulation را کم می‌کند، اما parent canonical، release gate یا Go/No-Go را تغییر نمی‌دهد. Source/test محصول در این مرحله دست‌نخورده ماند؛ index پاک بود و عملیات stage/commit/push/PR/merge/release/deploy انجام نشد.

## ۱۱. وضعیت تازهٔ workspace برای انتقال

در snapshot تازه پس از مستندات handoff و لینک Architecture Atlas، `git status --porcelain=v1 -uall` نشان داد: **۶۲ مسیر tracked تغییرکرده، ۲۶۳ مسیر untracked، stage صفر**؛ از untrackedها **۷۰ مسیر receipt خصوصی** و ۱۹۳ مسیر دیگر است، شامل ۱۵۸ path زیر `artifacts/`. رسیدها باز، کپی، فهرست‌نویسی یا stage نشدند. بخش بزرگی از `artifacts/` reference/extractionهای قبلی است؛ `git add -A` یا stage کردن یک درخت والد مجاز/ایمن نیست. `git rev-list --left-right --count main...HEAD` هنوز `0 36` بود؛ این مقایسه با `main` محلی است که عقب‌مانده است، نه وضعیت remote/merge. برای وضعیت PR/CI از `gh` و برای status همین worktree از Git استفاده شود.
