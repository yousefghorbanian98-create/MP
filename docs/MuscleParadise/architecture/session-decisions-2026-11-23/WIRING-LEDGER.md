# دفتر wiring و سفرهای محصول — snapshot 2026-11-23

> سند همراه [نقشهٔ یکپارچه](../system-integrated-flow-v1-2026-11-23.md) است. «مسیر کد» با «رفتار همه‌جانبهٔ آزموده‌شده» یکی نیست. برچسب `CODE` یعنی source قابل ردیابی؛ `TEST-REPORTED` یعنی همان سناریو در [گزارش تحلیل](../analysis-2026-11-23.md) آمده ولی در این نشست دوباره اجرا نشده؛ `DESIGN` یعنی قرارداد/طرح UI؛ `GAP` یعنی رفتار ناقص/مسدود؛ `OPEN` یعنی runtime/device/production هنوز اثبات نشده است.

## ۱. سطح‌های UI و مسیرهای کلاینت

### Flutter عضو

[`AppShell`](../../../../mp-app/client/lib/features/shell/app_shell.dart) شامل ۵ تب است: `HomePage`, `TodayPage`, `Assessment14Page`, `ProgressPage`, `ProfilePage`. [`router.dart`](../../../../mp-app/client/lib/core/router.dart) این مسیرها را تعریف می‌کند:

| route | صفحه/جریان | محدودیت قابل‌مشاهده |
|---|---|---|
| `/otp` | OTP | OTP request/verify API؛ provider ارسال واقعی وابسته به تنظیم. |
| `/intake` | اطلاعات اولیه و ساخت پیشنهاد برنامه | gate-check و generate API؛ خروجی blocked هنوز ممکن است draft شود و نمایش داده شود. |
| `/home` | AppShell | تب‌ها در shell هستند؛ branch جاری تست دستگاه Flutter ندارد. |
| `/today`, `/progress`, `/profile` | بخش‌های shell یا push مستقیم | صفحهٔ امروز ممکن است برنامه را از API بخواند، اما تیک انجام تمرینِ مسیر مرورشده فقط state محلی است. |
| `/bodycomp`, `/nutrition` | ارزیابی ترکیب بدن / تغذیه | اندازه‌گیری/target و FoodLog مفهوم‌های مستقل‌اند. |
| `/checkin`, `/classes` | رضایت/QR / کلاس و رزرو | QR server flow و کلاس API؛ face recognition زنده فرض نشود. |
| `/wallet`, `/shop` | دفتر/پرداخت و کاتالوگ | پرداخت دستی؛ checkout فروشگاه عضو خاموش است. |
| `/chat`, `/notifications` | گفت‌وگو و inbox | صندوق داخلی را با push delivery یکی نگیرید. |

صفحهٔ احراز هویت و بخش‌های push مستقیم، همگی یک shell واحد نیستند. نمودار آن‌ها را به featureهای قابل‌فهم گروه کرده است؛ فهرست مسیرهای دقیق در `router.dart` است.

### Studio کارکنان

[`App.tsx`](../../../../mp-app/studio/src/App.tsx) ۱۲ صفحهٔ feature (Dashboard, Members, Programs, Nutrition, Assessment, Chat, CheckIn, Finance, Expenses, Analytics, Settings, Shop) را با صفحهٔ Login/گیت نشست ترکیب می‌کند؛ بنابراین inventory interaction، ۱۳ سطح Studio را می‌شمارد. وقتی auth وضعیت `checking` است loading نشان داده می‌شود؛ وقتی `unauthenticated` است Login نمایش داده می‌شود؛ پس از ورود، sidebar/topbar و صفحهٔ انتخابی نمایش می‌یابند.

[`roleNav.ts`](../../../../mp-app/studio/src/lib/roleNav.ts) نقش را از token صرفاً برای UX می‌خواند و `canSeePage`/`PAGE_RULES` را اجرا می‌کند. توضیح همان فایل می‌گوید هر API باید دوباره server-side مجوز بگیرد؛ UI hide/disable به‌تنهایی مرز امنیت نیست. Studio از `sessionFetch`/helperهای مشترک درخواست می‌سازد. توکن‌ها/کنترل‌های Option 03 در [سند UI/UX](../frontend-ui-ux-flow-option-03-lab-v1-2026-11-23.md) و نقشه‌های [عضو](../frontend-ui-ux-member-option-03-v1-2026-11-23.dot)، [Studio](../frontend-ui-ux-studio-option-03-v1-2026-11-23.dot) و [control wiring](../frontend-ui-ux-control-wiring-option-03-v1-2026-11-23.dot) شرح داده شده‌اند.

### Interaction inventory

[`interaction-map.json`](../interaction-map.json) برای snapshot خوانده‌شده ۳۱ سطح دارد: ۱۳ سطح Studio + ۱۸ گروه feature در Flutter؛ قرارداد ۱۶۳ operation است. `python scripts/interaction_map.py --check` در این نشست **PASS** داد: ۳۱ سطح، ۱۶۳ مسیر قرارداد، رانش صفر. فهرست فعلی endpointدار با `tests: []` در artifact:

- Studio `Members`؛
- Flutter `auth`, `intake`, `progress`, `core`.

این یعنی generator تست صفحه‌ای/ویژگی را در این سطح match نکرده؛ **اثبات قطعی فقدان هر آزمون دیگر نیست**. پنج مورد بالا برای بازبینی انسانی باقی می‌مانند.

## ۲. چرخهٔ درخواست مشترک

```text
نقش/کاربر
  → صفحه / intent
  → form validation + loading/pending + جلوگیری از double-submit
  → Flutter API client یا Studio sessionFetch
  → FastAPI /api/v1 + request id + rate/validation/error middleware
  → OTP/access session و اعتبار توکن
  → route guard / role / grant / record ownership & scope
       ├─ رد: 401/403؛ بدون ورود به سرویس دامنه
       └─ اجازه: router → service/domain rules → SQL / فایل خصوصی / provider اختیاری
  → پاسخ HTTP
  → refresh/invalidate و پیام مناسب؛ حفظ ورودی/تعارض/Retry
```

**شواهد wiring:** FastAPI app در [`app/main.py`](../../../../mp-app/backend/app/main.py) Router تجمیعی [`api/v1/api.py`](../../../../mp-app/backend/api/v1/api.py) را زیر `/api/v1` نصب می‌کند. CORS allowlist، `X-Request-ID`, metrics، validation/error handlers و ID floor در source وجود دارند. [`app/deps.py`](../../../../mp-app/backend/app/deps.py) Bearer access token، active user، auth version و در sessionهای جدید `sid` را بررسی می‌کند؛ `require_permission` مسیر/متد را با Casbin می‌سنجد. serviceها همچنان باید record ownership/scope را بررسی کنند. این architecture trace به معنی ممیزی همهٔ routeها نیست.

**قرارداد تجربهٔ پاسخ:** Option 03 حالت pending، پیام inline/toast، جلوگیری از submit تکراری، حفظ ورودی، و رفتار قابل‌فهم برای 401/403/422/409/429 را به‌عنوان الگوی تعامل می‌دهد. این باید صفحه‌به‌صفحه inventory/test شود؛ نباید ادعا کرد که هر route/feature همین mapping را کامل اجرا می‌کند. برای timeout نوشتن، امن‌ترین UI «موفقیت» نیست؛ ابتدا نتیجهٔ قبلی باید reconcile شود.

## ۳. سفرهای دامنه و ردگیری لایه‌ها

| سفر | رابط/intent | قرارداد/API و handler | سرویس/داده | شواهد و گپ‌های صریح |
|---|---|---|---|---|
| OTP و نشست | Flutter `/otp`; Studio Login/AuthProvider | `/auth/otp/request`, `/auth/otp/verify`, `/auth/refresh`, `/auth/logout`, `/auth/sessions*`; session restore از `/members/me` در Studio | `OtpCode`, `User`, `RefreshToken`, `PhoneChangeChallenge`, `Member` | کد و قرارداد قابل‌ردیابی؛ تنظیم فعلی SMS `dev` است. provider واقعی به secret/config و تست شبکه نیاز دارد؛ تحویل SMS production در این کار اثبات نشد. |
| پروفایل و اشتراک | `/profile`, Studio Members/عضویت | `/members/me`, `/members/*`, `/members/memberships*` | `User`, `Member`, `Membership` | route→model قابل ردیابی است؛ access مؤثر وابسته به role و record ownership؛ device/E2E اجرا نشده. |
| Intake و gate | Flutter `/intake`: دریافت هدف/سطح/روزها/محدودیت و پاسخ gate | `POST /population/gate-check` با JSON `{"path":"adult"}`؛ سپس `POST /ai/program/generate` | `population` → `ai_engine` → `engine/workout` → `programs`; `WorkoutProgram` و جزئیات هفته/حرکت | `analysis-2026-11-23.md` آزمون TestClient body را **۲۰۰** گزارش می‌کند؛ این نشست آن را تکرار نکرد. سند قدیمی query/422 دربارهٔ قرارداد قبلی است. classifying سن/جمعیت server-side و Flutter device/E2E همچنان open است. |
| برنامه و safety | عضو درخواست تولید می‌دهد؛ Studio Programs صف/بازبینی/approve/reject می‌کند؛ عضو برنامه می‌گیرد | `/ai/program/generate`, `/programs`, `/programs/member/{member_id}`, readiness/volume و set-feedback endpoints | generator قطعی و `WorkoutProgram`/`ProgramWeek`/`ProgramExercise`; موتور از کاتالوگ حرکت استفاده می‌کند | گزارش آزمون واقعی قید `knee_injury` را `blocked` می‌بیند؛ شناسهٔ ناشناس `needs_review` می‌شود. **گپ:** blocked/needs_review هنوز می‌تواند رکورد draft بسازد و از Intake نمایش داده شود؛ نمایش عضو به شرط approved fail-closed نشده است. API خروجی `exercise_id` می‌دهد و نام حرکت/خوانایی کامل نیز گپ گزارش شده. |
| ثبت انجام تمرین | صفحه Today؛ کاربر set را تیک می‌زند و feedback جدا می‌دهد | feedback مسیر `/programs/set-feedback` یا sync path را دارد؛ دامنهٔ offline در routeهای گزارش‌شده باید محدود بررسی شود | state محلی و SetFeedback سمت سرور | در مسیر مرورشده تیک completion فقط Riverpod/local Set ندارد API/DB؛ با feedback persisted یکی نیست. وجود endpoint sync به‌تنهایی queue فعال/تحویل تضمین‌شده نیست. |
| رزرو کلاس | Client لیست/رزرو/لغو را نشان می‌دهد | `GET /classes`, `POST /classes/book`, `POST /classes/cancel` | `GymClass`, `ClassBooking`; ظرفیت → confirmed یا waitlisted؛ cancel/rebook ترتیب FIFO را به‌روزرسانی می‌کند | تحلیل، regression rebook و جلوگیری از overbooking ناشی از cancel فرد waitlisted را روی TestClient/SQLite گزارش می‌کند. race همزمان و device E2E اثبات نشده. |
| حضور QR | عضو CheckIn رضایت/QR را می‌گیرد؛ پذیرش اسکن می‌کند | عضو `GET /face/qr-token`; پذیرش `POST /face/checkin-qr`; `POST /face/checkin` با `method=face` | `BiometricConsent`, `FaceTemplate`, `CheckIn` | گزارش تحلیل، token/check-in QR مسیر جاری را نشان می‌دهد و face با ۴۰۹ fail-closed است، صفر check-in برای method=face. آزمون اسکنر/Android/پذیرش فیزیکی و امنیت بازپخش در دستگاه انجام نشده. قفل محلی تأیید حضور server را جایگزین نمی‌کند. |
| ارزیابی/پیشرفت | `/bodycomp`, `/progress`, Assessment و JP7 در Studio | `/assessments/*`, `/axis-assessments/*`, `/ai/suggest-weight`, یادآوری‌ها | اندازه‌گیری‌های خام، Axis/FieldTest/JP7 | کد/مدل‌ها ردیابی شده؛ گزارش انسانی/تست موردی به معنی اعتبار پزشکی نیست. هیچ عدد فردی یا تصویر بدن در این سند نقل نشده. |
| تولید تغذیه | Flutter Nutrition/Studio Nutrition | `POST /ai/nutrition/generate`, `/nutrition/plans*` | `NutritionPlan`, `MealItem` | گزارش تحلیل: generator target کالری/ماکرو ذخیره می‌کند و `meals: []` است؛ هدف nutrition را «برنامهٔ وعدهٔ کامل» معرفی نکنید. |
| خوراک/وزن ثبت‌شده | عضو FoodLog/weight ثبت می‌کند؛ UI روز را می‌خواند | `/nutrition/food-logs`, `/nutrition/weight-logs`, `/nutrition/food-logs/member/{id}/daily`, `/nutrition/foods` | `FoodLog`, `BodyWeightLog` | این دفترِ واقعیت با `NutritionPlan/MealItem` جداست؛ مالکیت member scope باید سروری کنترل شود. وجود route به‌تنهایی coverage نیست. |
| کارت‌به‌کارت و فیش | عضو پرداخت/تمدید و بارگذاری فیش؛ Studio صف بررسی مالی | `/payments`, `/payments/{id}/receipt`, approve/reject؛ مسیرهای callback/verify gateway جدا | `Payment`, `PaymentReceipt`, `Membership`, `AuditLog` | تصمیم محصول: پرداخت دستی و بازبینی انسانی منبع بانکی. `manual/mock/sandbox` به‌تنهایی live gateway نیست. ثبت فیش نباید success واریز را نشان دهد. Integration/settlement واقعی در این کار آزموده نشد. |
| کیف‌پول و checkout آزمایشی | Client Shop/Wallet؛ checkout فقط با flag آزمایشی روشن | `/payments/wallet/pay`, `/shop/cart*`, `/shop/checkout` | Payment, WalletTransaction, LedgerEntry, Product/Cart/Order | گزارش تحلیل، آزمون‌های رگرسیون با SQLite موقت برای عدم اثر side-effect در کمبود balance و یک Payment موفق را ثبت کرده؛ ریسک concurrency در آن آزمون ثابت نشده. این flow برای مجوز خرید عضو یا روشن‌کردن فروشگاه production نیست. |
| Refund | Studio Finance/PaymentPanel | `POST /payments/{payment_id}/refund` | RBAC + `finance.write`; AuditLog actor و وضعیت refund | گزارش تحلیل: reception رد، manager بدون grant رد، manager مجاز + sandbox refund و audit actor؛ تکرار already_refunded. این شاهد API آزمایشی است، نه بازپرداخت بانکی زنده. Studio فعلی confirmation ساده دارد و دلیل/چک‌لیست حسابداری کامل نیست. |
| فروشگاه نمایشی | عضو Shop فقط کاتالوگ؛ کارکنان مدیریت کاتالوگ | `/shop/products`, cart, checkout, orders و gateway routeها | Product/Variant/Cart/Order و config flag | `shop_online_purchase_enabled=False` در config جاری؛ writeهای checkout در پیش‌فرض fail-closed. قیمت/موجودی/خرید حضوری طبق سیاست مالک؛ تصویر محصول از عکس پیشرفت عضو جداست. مسیرهای تاریخی cart/order در schema باقی‌اند. |
| هزینه/گزارش سود | Studio Expenses/Finance/PeriodReport | `/expenses*`, `/finance/reports/*`, payment finance routes | `Expense`, `ExpenseRevision`, `ReportRun`, payment/ledger | report دوره‌ای اگر refund بدون تاریخ یا داده ناقص باشد `complete=false`; profit UI مقدار/میلهٔ سود را حذف و نامعلوم می‌کند طبق گزارش Option 03. تعریف حسابداریِ profit/مالیات و report رسمی باز است. |
| چت/اعلان | Flutter/Studio inbox، chat, read | `/chat/conversations*`, `/notifications*` | Conversation, Message, Notification, OutboxEvent, InboxMessage | route/model قابل ردیابی؛ push خارجی، تحویل background و اجرای outbox worker در deployment این کار اثبات نشده‌اند. Inbox داخلی را منبع push receipt تلقی نکنید. |
| Dashboard/check-in ops | Studio dashboard، attendance/check-in | `/admin/analytics/*`, `/admin/attendance`, `/admin/checkins`, `/health`, `/metrics` | سرویس admin/reporting/metrics | KPI/feed از API و انتخاب عضو به صفحه Members در Option 03 متصل شده؛ چهرهٔ تصویری CheckIn فقط visual/demo است و نباید SLO یا biometric live جلوه داده شود. |

## ۴. مرز داده و عملیات

| مرز | رفتار قابل مشاهده | وضعیت/محدودیت |
|---|---|---|
| DB | SQLAlchemy؛ default URL در `app/config.py`، SQLite محلی | PostgreSQL هدف احتمالی/مشروط است؛ تغییر driver یا قرارداد hosting بدون migration، race/locking، backup و rollback آزموده‌شده انجام‌شده فرض نشود. |
| فایل فیش | مسیر تنظیمی `receipts_dir` پیش‌فرض `var/receipts`; endpoint حفاظت‌شده؛ web static mount جداست | در این کار محتوای پوشه باز نشده و در مستندات/تصویر درج نشده. فایل خصوصی باید با auth/scope و retention مناسب تحویل شود. |
| Valkey/cache | config URL و بعضی fallbackها موجود است | قابل‌دسترس‌بودن Valkey و production failover/load اثبات نشده. |
| Background jobs | `jobs/scheduler.py`، scheduler builder و finance schedule موجود؛ تست jobها هست | `main.py` در lifespan دیده‌شده scheduler را start نمی‌کند. وجود builder/تست تابع به معنی worker زمان‌بندی‌شدهٔ فعال نیست؛ startup/deploy/heartbeat/idempotency باید جدا بررسی شود. |
| SMS | config `sms_provider=dev` | ارسال واقعی SMS وابسته به config و secret، محدودیت egress و دسترس‌پذیری است. |
| AI/Ollama | engine/adapterهای optional | route/API AI به معنی اتصال بیرونی/کیفیت مدل یا authority safety نیست؛ runtime config باید جدا ممیزی شود. |
| health/proxy/metrics | route/code/config/Compose وجود دارد | public DNS/TLS، production profile، restore، monitoring alert و تمرین recovery اثبات نشده. |

## ۵. وضعیت UI/UX Option 03 که در نقشه اعمال شده

این بندها زبان طراحی/کیفیت تعامل و سیم‌کشی را توصیف می‌کنند؛ «موافق‌بودن با همین گزینه به‌عنوان تصمیم رسمی محصول» هنوز نیازمند تأیید مالک است.

- Studio توکن‌های رنگ/فاصله/حالت focus را به Tailwind/Ant Design وصل کرده؛ reduced-motion در `App.tsx` به `useReducedMotion` وابسته است.
- Flutter shell از `MpMotion.dur(context, …)` استفاده می‌کند تا کاهش حرکت سیستم رعایت شود.
- یک intent باید به owner/state مشخص، validation، حالت pending و پاسخ مرتبط وصل باشد؛ دکمهٔ نمایشی یا منوی role مجوز API نیست.
- Dashboard → Member selection، payment review، expenses/period reports، Programs review و CheckIn/Shop control maps در اسناد Option 03 موجودند؛ هر مسیر/کنترل باید به endpoint و نتیجهٔ قابل مشاهده برسد.
- سود گزارش ناقص به‌صورت صفر، score جعلی یا chart پر نشود؛ زبان UI باید unknown/loading/empty/offline/error/conflict را جدا کند.
- جزئیات صفحه‌ای/کنترل‌ها را در نمودارهای UI/UX پیوست ببینید؛ نمودار master برای خوانایی همهٔ componentهای nested را نمایش نمی‌دهد.

## ۶. سطح شواهد و کارهای اثبات‌نشده

| سطح | نمونه در این بسته | چه چیزی را ثابت می‌کند؟ | چه چیزی را ثابت نمی‌کند؟ |
|---|---|---|---|
| کدخوانی | `router.dart`, `App.tsx`, `routes.json`, service/model | مسیرها/وابستگی‌های قابل مشاهده در snapshot | اجرای موفق API، کامل‌بودن wiring، درست‌بودن همهٔ مجوزها |
| inventory/gate | `interaction_map.py --check` PASS | artifact با route contract جاری رانش ندارد | تست تمام endpointها/controls، line-by-line DB trace یا E2E |
| تست خودکار گزارش‌شده | TestClient/regression در `analysis-2026-11-23.md` | سناریوی دقیق در DB آزمایشی/runner آزمون‌شده | شبکه، بانک، Android، browser/device، production concurrency |
| طرح/مستند UX | Option 03، نمودارهای target و athlete cycle | تصمیم‌های طراحی و proposal را قابل بحث می‌کند | اجرا/تأیید کسب‌وکار یا نتیجهٔ safety |
| runtime عملیاتی | در این task اجرا نشده | — | deploy, migration, TLS, backup/restore, alerts, SMS, push, scheduler, OCR, live gateway |

### شناسه‌های regression گزارش‌شده (بدون ادعای اجرای مجدد در این نشست)

- body JSON `POST /population/gate-check` → 200 برای `adult` در TestClient؛ contract قدیمی query→422 stale است.
- تولید برنامه با `knee_injury` → `blocked` و `safe_to_generate=false` در پاسخ؛ بااین‌حال draft هنوز می‌تواند نمایش داده شود.
- لغو waitlisted نباید confirmed را بیش از ظرفیت کند؛ rebook همان reservation رکورد تازه‌مرتب‌شده می‌شود.
- `method=face` → 409 و بدون check-in؛ QR در مسیر جداست.
- کیف‌پول/checkout ناکافی side-effect پایدار ندارد در سناریوی تست؛ concurrent overspend هنوز از آن تست نتیجه‌گیری نمی‌شود.
- refund grant/actor/audit/replay و store/cart behavior در TestClient/SQLite آزمایشی گزارش شده‌اند؛ هیچ‌کدام بانک یا production را ثابت نمی‌کنند.

## ۷. بازتولید/هم‌راستاسازی

- route catalog را با `mp-app/backend/api/routes.json` مقایسه کن؛ شمارش snapshot اکنون **۱۶۳ operation/۱۴۱ path template** است.
- interaction gate: `python scripts/interaction_map.py --check`؛ خروجی فقط سطح UI → contract را پوشش می‌دهد.
- render master: دستور در [system-integrated-flow README](../system-integrated-flow-v1-2026-11-23.md).
- اگر کد/تصمیم عوض شد، پیش از تغییر label وضعیت، ابتدا شاهد source/test جاری را ثبت کن؛ سپس DOT، این ledger، route catalog و پس از تأیید رسمی index را با هم به‌روز کن.
