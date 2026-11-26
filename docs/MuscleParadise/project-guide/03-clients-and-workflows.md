# ۳. کلاینت‌ها، PWA و سفرهای کاربر

[بازگشت به راهنما](README.md) · [نقشهٔ پروژه](01-project-map.md) · [دفتر سفرهای UI→API](../architecture/session-decisions-2026-11-23/WIRING-LEDGER.md)

## ۳.۱ MP Client — اپ عضو با Flutter

ریشهٔ کلاینت [`mp-app/client/`](../../../mp-app/client/) است. `pubspec.yaml` به Flutter/Dart SDK در بازهٔ `>=3.3.0 <4.0.0`، Riverpod برای state، `go_router`، `http`, `shared_preferences`, `qr_flutter`, `local_auth`, `image_picker` و `flutter_animate` وابسته است. وجود dependency به‌تنهایی ثابت نمی‌کند هر capability در تمام buildها فعال است. فارسی/RTL و Vazirmatn در `main.dart` و theme به‌کار می‌روند.

### راه‌اندازی نشست و درخواست API

- `main.dart` یک `ProviderContainer` می‌سازد و پیش از UI، `authProvider.notifier.restore()` را اجرا می‌کند؛ مسیر اولیه `/home` یا `/otp` بر اساس نتیجه انتخاب می‌شود.
- `core/session.dart`، `AuthController` و providerهای Riverpod را تعریف می‌کند؛ `ApiClient` از همان نقطه تزریق می‌شود.
- توکن access و refresh با کلیدهای `mp_token` و `mp_refresh` در `SharedPreferences` ذخیره می‌شوند؛ این source به‌تنهایی رمزگذاری storage توسط Keystore یا مقاومت در برابر دستگاه compromiseشده را اثبات نمی‌کند.
- `ApiClient` با `--dart-define=MP_API=...` پیکربندی می‌شود؛ default برای Android Emulator برابر `http://10.0.2.2:8000/api/v1` است. HTTP روی localhost/RFC1918 مجاز است؛ میزبان عمومی باید HTTPS باشد.
- همهٔ پاسخ‌ها می‌توانند JSON object یا array باشند؛ پاسخ‌های غیر 2xx به `ApiException` و پیام خطای server تبدیل می‌شوند.
- روی 401، کلاینت یک refresh مشترک برای درخواست‌های هم‌زمان انجام می‌دهد و درخواست را حداکثر یک بار تکرار می‌کند؛ refresh endpoint خودش از interceptor مستثناست. اگر نشست برنگردد، وضعیت محلی خالی می‌شود. 403 موجب refresh بی‌فایده نمی‌شود.
- `logout()` تلاش می‌کند ابتدا session سرور را لغو کند، اما حتی در خطای شبکه local session را پاک می‌کند؛ خروج محلی را با تأیید ابطال سمت سرور یکی ندانید.

### ناوبری و صفحات

`core/router.dart` مسیرهای زیر را تعریف می‌کند:

| route | صفحه/کار |
|---|---|
| `/otp` | ورود OTP. |
| `/intake` | فرم اطلاعات اولیه و گرفتن مسیر/پیشنهاد برنامه. |
| `/home` | `AppShell` عضو. |
| `/today` | جلسهٔ امروز، تمرین و بازخورد. |
| `/progress` | روند/پیشرفت. |
| `/profile` | پروفایل و اشتراک. |
| `/bodycomp` | ارزیابی ترکیب بدن/سنجش. |
| `/nutrition` | plan و ثبت‌های تغذیه. |
| `/checkin` | QR/حضور و رضایت‌های مربوط. |
| `/classes` | کلاس و رزرو. |
| `/wallet` | کیف‌پول/پرداخت‌های عضو. |
| `/shop` | کاتالوگ فروشگاه و آثار تاریخی سبد. |
| `/chat` | گفت‌وگوی عضو. |
| `/notifications` | صندوق اعلان داخلی. |

`AppShell` در source **پنج** مقصد پایین‌صفحه دارد: خانه، برنامه (`TodayPage`)، توانایی‌ها، پیشرفت، پروفایل. comment فایل به‌اشتباه «شل ۴ تبی» می‌گوید؛ تعداد واقعی `static _tabs` و آیتم‌های navigation پنج است. صفحات `/progress` و `/profile` نیز wrapper برای push مستقیم دارند.

فهرست `lib/features/` را می‌توان از روی پوشه‌ها دید؛ route table معیار دقیق مسیر است. نام route یا وجود page، پیاده‌شدن end-to-end یا auth gate یکسان برای همهٔ routeها را ثابت نمی‌کند.

### State و داده

`core/app_state.dart` providerهایی برای دادهٔ واقعیِ دریافت‌شده از API می‌سازد، از جمله برنامه، کیف‌پول، پرداخت‌های عضو، اشتراک، فروشگاه، کلاس، تغذیه، اعلان، readiness و volume. بیشتر درخواست‌ها از `apiClientProvider` و شناسهٔ عضو نشست عبور می‌کنند؛ مالکیت نهایی باید در server نیز بررسی شود. نمونهٔ لیست یا fallback empty در UI را با دادهٔ سرور یا آزمون کامل یکی نگیرید.

یک مرز مهم `TodayPage` است:

- دریافت برنامه از `myProgramsProvider` و تمرین‌های روز به API متصل است.
- دایره/تیک «این حرکت را انجام دادم» در `today_controller.dart` فقط یک `Set<int>` در Riverpod نگه می‌دارد و با lifecycle آن state از بین می‌رود؛ این تیک به‌تنهایی به API/DB ذخیره نمی‌شود.
- فرم «بازخورد ست» در `SetFeedbackSheet` مسیر مجزای POST و نتیجهٔ پیشنهاد/دلیل دارد. ذخیرهٔ feedback را با تیک محلی تمرین یکی نکنید.

### Outbox آفلاین محدود Android

این قابلیت، offline mode عمومی اپ نیست.

- `core/offline_feedback_outbox.dart` به‌صورت default خاموش است: build flag `MP_ANDROID_OFFLINE_FEEDBACK_ENABLED` باید صریح true شود؛ runtime فقط Android و نه Web را می‌پذیرد.
- Kotlin `MainActivity` با MethodChannel به `OfflineFeedbackDatabase` (SQLite app-private) وصل می‌شود. جدول `sync_queue` مالک را به `owner_member_id` می‌بندد، شناسهٔ یکتای device/client دارد و stateهای pending/retry/conflict/failed/synced را نگه می‌دارد.
- فقط یک payload ساختاریافتهٔ feedback ست در صف قرار می‌گیرد: شناسهٔ برنامه/حرکت، وزن، تکرار هدف/انجام‌شده، RIR و زمان. `soreness`, notes و فیلدهای ناشناخته عمداً حذف می‌شوند؛ credential/token یا متن raw خطا در payload sync نیست.
- ثبت آفلاین فقط وقتی شبکهٔ Android در دسترس تشخیص داده نشود انجام می‌شود. اگر نتیجهٔ درخواست آنلاین نامعلوم/timeout باشد، خودکار به صف آفلاین تبدیل نمی‌شود تا write تکراری ایجاد نشود.
- همگام‌سازی با همان عضو و access token به `/programs/sync/set-feedback`، حداکثر ۱۰۰ ردیف در batch، پاسخ per-item معتبر و owner match لازم دارد. نتیجهٔ stale/clock-skew/invalid به conflict می‌رود و بی‌سروصدا پاک یا موفق اعلام نمی‌شود.
- retry خودکار تا پنج تلاش با فاصلهٔ افزایشی و سقف شش ساعت؛ موارد exhausted برای retry دستی می‌مانند. کاربر می‌تواند صف همان حساب را آگاهانه حذف کند؛ logout وقتی صف unresolved دارد انتخاب نگه‌داری/حذف می‌خواهد.
- متن «ذخیره شد روی دستگاه» تأیید سرور نیست. local database و این flow نیازمند بررسی retention/رمزگذاری دستگاه و آزمون روی مدل Android هدف هستند؛ این مستندسازی تأیید device QA یا encryption محلی نمی‌دهد.

کدهای route، controller و native در `lib/core/offline_feedback_outbox.dart`, `lib/features/feedback/feedback_providers.dart`, `lib/features/feedback/offline_feedback_queue_card.dart`, `android/.../MainActivity.kt` و `android/.../OfflineFeedbackDatabase.kt` هستند. محدودیت Android و flag را در CI/build و تست همان commit دوباره بررسی کنید.

## ۳.۲ MP Studio — پنل کارکنان React

ریشه [`mp-app/studio/`](../../../mp-app/studio/) از React 18، TypeScript، Vite، Zustand، Ant Design، Tailwind، Framer Motion و Recharts استفاده می‌کند. package scripts:

- `npm run dev`: Vite development server.
- `npm run lint`: ESLint.
- `npm test`: Vitest run.
- `npm run build`: `tsc -b` سپس Vite production bundle.
- `npm run preview`: پیش‌نمایش build.
- `npm run electron`: پوستهٔ Electron موجود.

### App، ورود و navigation

`src/App.tsx` دوازده صفحهٔ feature را map می‌کند: Dashboard, Members, Programs, Nutrition, Assessment, Chat, CheckIn, Finance, Expenses, Analytics, Settings, Shop. `Login` سیزدهمین سطح interaction است، نه صفحه‌ای در map اصلی.

`AuthProvider` ابتدا وضعیت `checking` دارد؛ token موجود را با `/members/me` بررسی می‌کند؛ سپس صفحهٔ مجاز یا Login را نمایش می‌دهد. ورود staff با OTP است. `STUDIO_ROLES` شامل `super_admin`, `admin`, `manager`, `coach`, `reception` می‌شود و `member` را نمی‌پذیرد. بنابراین UI فعلی Studio از همین login مسیر ورود عضو مشترک PWA نمی‌سازد؛ این یکی از گپ‌های پیاده‌سازی نسبت به ADR-007 است.

صفحهٔ انتخابی و فیلترها در `stores/appStore.ts` با Zustand نگه‌داری می‌شوند. `roleNav.ts` نقش JWT را صرف navigation/UX به‌کار می‌گیرد؛ API باید مستقل RBAC/scope را اعمال کند. بعضی `PAGE_RULES` برای `member` هم صفحه را مجاز می‌شمارند، اما gate ورود فعلی عضو را نمی‌پذیرد؛ این metadata UI را proof عضویت مشترک ندانید.

### Studio API و نشست

- `lib/api.ts` آدرس نسبی `API_BASE = "/api/v1"` را استفاده می‌کند؛ در browser درخواست به همان origin است.
- `lib/session.ts` access/refresh token را در browser `localStorage` با همان نام‌های `mp_token` و `mp_refresh` نگه می‌دارد.
- `sessionFetch` bearer token را اضافه می‌کند، روی یک 401 refresh مشترک و یک retry انجام می‌دهد، 403 را جدا از 401 نگه می‌دارد و logout local را حتی در خطای شبکه انجام می‌دهد.
- کد session صریح می‌گوید این **HttpOnly-cookie boundary نیست** و نباید XSS-proof توصیف شود. این‌ها credentialهای browser storage هستند؛ CSP/XSS/HTTPS/security review را از این helper نتیجه نگیرید.
- `getJson`/`getBlob` پیام فارسی سرور را می‌خوانند؛ 401 re-auth و 403 permission failure رفتار جدا دارند.
- state اصلی داده باید از API بیاید؛ Zustand برای انتخاب صفحه/فیلتر است، نه پایگاه دادهٔ دامنه.

### Layout فارسی و توسعه

`src/main.tsx` `ConfigProvider direction="rtl"`, locale `fa_IR`, theme مشترک و `StyleProvider layer` را نصب می‌کند. `designTokens` با `mp-app/shared/design-tokens.json` همگام است. `vite.config.ts` host را روی `0.0.0.0` باز می‌کند، host allowlist را می‌پذیرد و `/api` و `/health` را به `MP_API_TARGET` (پیش‌فرض `http://127.0.0.1:8000`) proxy می‌کند. برای preview Arena، مسیر browser باید relative بماند؛ `127.0.0.1` در تنظیم proxy فقط ارتباط server-side Vite به API محلی sandbox است، نه کد browser.

## ۳.۳ PWA موجود، رفتار cache و شکاف انتشار

فایل‌های مستقیم:

- `studio/public/manifest.webmanifest`: فارسی/RTL، `start_url: /`, `scope: /`, `display: standalone` و icons 192/512 به‌علاوهٔ maskable 512. نام فعلی آن `MP Studio` و شرحش «پنل مربی و مدیر» است.
- `studio/src/main.tsx`: بعد از `load`، `/sw.js` را ثبت می‌کند؛ guard محدودکنندهٔ `import.meta.env.PROD` ندارد، پس dev نیز ثبت می‌کند.
- `studio/public/sw.js`: نسخهٔ cache `mp-studio-v1`، `skipWaiting` و `clients.claim` دارد؛ هنگام activation کلیدهای cache دیگر را پاک می‌کند.
- درخواست `/api/` از service worker بدون `respondWith` عبور می‌کند؛ API response را این SW cache نمی‌کند.
- `/assets/` هش‌دار Vite cache-first است؛ در miss به network می‌رود و response را ذخیره می‌کند.
- سایر درخواست‌ها (از جمله HTML و درخواست manifest در پیاده‌سازی فعلی) ابتدا network می‌گیرند و در خطا `caches.match` را fallback می‌کنند. comment فایل رفتار manifest را «شبکه» توصیف می‌کند، ولی کد branch اختصاصی manifest ندارد؛ سیاست دقیق را از شرط‌های اجرا بخوانید، نه comment تنها.
- `pwa.test.ts` manifest/icons/link، عدم cache API، fallback HTML و ثبت service worker را با بررسی منبع/فایل می‌سنجد. این تست browser installation, offline UX واقعی, update prompt, OS/device یا member parity نیست.

### اثر تصمیم پذیرفته‌شده

ADR-007، PWA مشترک React عضو/کادر را **baseline کلاینت اصلی انتشار اول** انتخاب می‌کند، با حفظ Flutter/Android. ولی کد مشاهده‌شدهٔ Studio دوازده صفحهٔ کارکنان و login کارکنان دارد، manifest هم Studio است و login `member` را رد می‌کند. این واقعیت را از تصمیم محصول جدا نگه دارید:

| مورد | وضعیت |
|---|---|
| React Studio فعلی + manifest + service worker | در source موجود؛ تعدادی تست منبع وجود دارد. |
| baseline انتشار اول مشترک PWA | تصمیم مالک در ADR-007 پذیرفته است. |
| مسیر عضو در PWA و تجربهٔ مشترک عضو/کادر | تکمیل/پذیرش آن از فایل‌های بالا ثابت نمی‌شود؛ کار باز است. |
| Flutter/Android | حفظ می‌شود؛ native client مسیر اصلی تصمیم‌شدهٔ release نیست. |
| نصب/آفلاین/آپدیت/device QA | `UNKNOWN/NOT_RUN` در سطح end-to-end؛ آزمون متن منبع جای آزمون مرورگر/گوشی نیست. |
| انتشار واقعی | ADR-007 صریحاً فعلاً `NO-GO` می‌گوید تا جریان‌های اصلی و گیت‌ها پذیرفته شوند. |

## ۳.۴ سفرهای محصول از نگاه UI تا API

این جدول خلاصهٔ [Wiring ledger](../architecture/session-decisions-2026-11-23/WIRING-LEDGER.md) است؛ «وجود مسیر» را با پذیرش کامل یکی نمی‌کند.

| سفر | Client/Studio | سرور/مدل | وضعیت یا مرز |
|---|---|---|---|
| OTP و نشست | Flutter `/otp`; Studio Login | `auth/otp/request`, `verify`, refresh/logout, sessions; `User`, `OtpCode`, `RefreshToken` | dev SMS به provider واقعی ارسال نمی‌کند؛ Studio فقط staff role را قبول می‌کند؛ شبکه/SMS delivery اثبات‌نشده. |
| پروفایل و اشتراک | Client `/profile`; Studio Members | `/members/me`, members/memberships; `Member`, `Membership` | clientها API دارند؛ scope عضو در server لازم است؛ device/E2E در این کار اجرا نشده. |
| Intake و gate | Flutter `/intake` | `/population/gate-check`, `/ai/program/generate`; population → engine → programs | TestClient body JSON در گزارش قبلی 200 شده؛ این نشست آن را تکرار نکرد. سن/محدودیت و نمایش draft باید در source/test بررسی شوند. |
| تأیید برنامه | عضو برنامه می‌گیرد؛ Studio Programs صف بازبینی دارد | `/programs`, `/programs/member/{id}`, approve/reject, readiness/volume | code path وجود دارد؛ safety blocked/needs_review هنوز ممکن است draft بسازد/نمایش دهد؛ approved-only کامل اثبات نشده. |
| جلسهٔ امروز | Flutter Today | `GET /programs/member/{id}` و set-feedback endpoints | تیک completion محلی/زودگذر؛ feedback جدا ذخیره می‌شود؛ Android outbox فقط برای feedback محدود است. |
| ارزیابی/پیشرفت | Client `/bodycomp`, `/progress`; Studio Assessment | `/assessments/*`, `/axis-assessments/*`, `/programs/.../readiness` | route/model هست؛ هیچ claim پزشکی یا مستقل از تکمیل assessment E2E از وجود UI نتیجه نمی‌شود. |
| تغذیه و ثبت | Client `/nutrition`; Studio Nutrition | `/ai/nutrition/generate`, `/nutrition/plans`, food/weight logs; `NutritionPlan`, `FoodLog`, `BodyWeightLog` | هدف ماکرو/کالری با وعدهٔ برنامه‌ریزی‌شده یا ثبت غذا فرق دارد؛ خروجی generator در گزارش فعلی می‌تواند `meals: []` باشد. |
| کلاس | Flutter `/classes`; Studio (بسته به page) | `/classes`, `/classes/book`, `/classes/cancel`; `GymClass`, `ClassBooking` | آزمون‌های regression محدود گزارش شده‌اند؛ race همزمان و دستگاه واقعی ثابت نشده‌اند. |
| حضور QR | Flutter `/checkin`; پذیرش Studio | `/face/qr-token`, `/face/checkin-qr`, `/face/checkin`, exit; `CheckIn` | QR برای redemption یک‌بارمصرف؛ `method=face` در گزارش آزمون 409؛ camera/kiosk/fizical QA انجام نشده. |
| پرداخت/رسید | Flutter Wallet; Studio Finance/PaymentPanel | `/payments`, receipt upload/review, wallet/ledger, refund | پرداخت release کارت‌به‌کارت/تطبیق انسانی؛ آزمون sandbox به بانک live تبدیل نمی‌شود؛ فیش تصویر خصوصی است. |
| Shop | Client `/shop`; Studio Shop | `/shop/products`, prices, cart, checkout, orders | کاتالوگ قابل‌مشاهده؛ online purchase عضو طبق تصمیم خاموش/fail-closed؛ مسیرهای legacy API وجود دارند. |
| چت و اعلان | Client Chat/Notifications; Studio Chat | `/chat/conversations*`, `/notifications*` | صندوق داخلی API دارد؛ push/background notification یا delivery guarantee ثابت نیست. |
| عملیات روزانه | Studio Dashboard, Analytics, CheckIn, Expenses | `/admin/*`, `/finance/*`, `/expenses*`, readiness/metrics | page/API وجود دارند؛ مجوز مالی effective، completeness و عملیات واقعی هرکدام گیت جدا دارند. |

برای route دقیق، schema، guard و method از [کاتالوگ](../architecture/session-decisions-2026-11-23/API-ROUTE-CATALOG.md) استفاده کنید؛ برای mapping صفحه→endpoint→test به artifact نقشه نگاه کنید و source واقعی را باز کنید. `tests: []` در interaction artifact به‌تنهایی اثبات نبودن هر test دیگری نیست.

## ۳.۵ دسترس‌پذیری، RTL، motion و جزئیات رفتاری

- Flutter `Directionality.rtl`, locale فارسی و Vazirmatn دارد؛ Studio از Ant Design RTL/locale فارسی و توکن‌های مشترک استفاده می‌کند.
- کلاینت از `MpMotion.dur(context, ...)` و Studio `useMotionPreset` برای احترام به reduced motion در سطوح بررسی‌شده استفاده می‌کنند. این موضوع را به تمام انیمیشن/صفحه و screen reader تعمیم ندهید.
- UI پیام pending، خطا، retry و empty state در برخی صفحات دارد؛ یکپارچگی این قواعد در همهٔ صفحات هنوز inventory/test می‌خواهد.
- نمودارهای UX هدف، proposal/طرح‌اند مگر state صریح پذیرش دارند؛ root README، ADRها و current PWA docs در زمان این مستندسازی هم‌نسخه نبودند. اختلاف‌ها در [بخش وضعیت/واژه‌نامه](05-security-status-glossary.md) ثبت شده است.

## ۳.۶ مطالعهٔ فایل‌به‌فایل یک feature

برای فهم یک قابلیت، به ترتیب زیر بخوانید؛ ترتیب از entry point تا رفتار می‌رود:

1. `mp-app/client/lib/features/<feature>/` یا `mp-app/studio/src/pages/<Page>.tsx` برای UI/state.
2. `core/app_state.dart`/Riverpod یا `studio/src/lib/api.ts` برای request payload/response.
3. `core/api_client.dart` یا `studio/src/lib/session.ts` برای transport/auth/retry.
4. `api/routes.json` و router FastAPI برای method/path/schema/guard.
5. service، scope helper و security policy برای business rule/مالکیت.
6. `db/models/<domain>.py` و Alembic version برای پایگاه داده.
7. `tests/unit`, `tests/integration`, `client/test`, `studio/tests` برای شاهد؛ فقط اجرای واقعی همین تست/CI و همان source revision را گزارش کنید.
8. اسناد تصمیم/فهرست کار را بخوانید تا کد تاریخی را با هدف محصول اشتباه نگیرید.
