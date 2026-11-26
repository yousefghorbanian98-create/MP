# ۲. Backend، API و داده

[بازگشت به راهنما](README.md) · [نقشهٔ معماری](01-project-map.md) · [کاتالوگ API (۱۶۳ operation)](../architecture/session-decisions-2026-11-23/API-ROUTE-CATALOG.md)

## ۲.۱ مشخصات فنی و نقطهٔ ورود

Backend در [`mp-app/backend/`](../../../mp-app/backend/) یک **modular monolith** است: Python 3.11+، FastAPI، SQLAlchemy 2.x، Pydantic 2، Alembic و SQLite به‌عنوان URL پیش‌فرض. وابستگی‌های اصلی در `pyproject.toml` و نسخه‌های تثبیت‌شدهٔ CI در `requirements.txt` (فایل constraints) هستند.

فایل‌های جهت‌یاب:

| مسیر | مسئولیت |
|---|---|
| `app/main.py` | `create_app()`, lifespan, middleware, exception handlerها و نصب routeها. |
| `app/config.py` | `Settings` با پیشوند `MP_`, خواندن `.env`/environment و اعتبارسنجی production. |
| `app/deps.py` | `DbSession`, کاربر جاری، session/JWT و guardهای مشترک. |
| `api/v1/api.py` | جمع‌کردن routeهای دامنه زیر پیشوند نسخه‌دار `/api/v1`. |
| `modules/<domain>/router.py` | تبدیل HTTP و schema به فراخوانی سرویس دامنه. |
| `modules/<domain>/service.py` | قواعد کاربردی/تراکنشی آن دامنه. |
| `db/base.py` | `Base`, mixinهای زمان/branch، engine و سازندهٔ session. |
| `db/models/` | مدل‌ها و جدول‌های SQLAlchemy. |
| `db/migrations/env.py`, `versions/` | تنظیم Alembic و تغییرات نسخه‌دار schema. |
| `security/` | Casbin، grant، ownership و ابزارهای رمزنگاری/auth. |
| `jobs/`, `cache/` | scheduler، relay و کش؛ نحوهٔ روشن‌شدن runtime جدا بررسی می‌شود. |
| `tests/` | تست‌های unit، integration، regression، E2E، load و evaluation. |

### ترتیب ساخت و آغاز برنامه

1. `app.main` در import-time `_assert_explicit_environment()` را اجرا می‌کند. مقدار پیش‌فرض class برابر `development` است، اما production/dev باید صریح از environment یا `.env` آمده باشد؛ بدون تعیین آن، اپ به‌طور ضمنی با development بالا نمی‌آید، مگر پرچم تست `MP_ALLOW_IMPLICIT_DEV=true` فعال باشد.
2. `create_app()` پیکربندی logging را تنظیم می‌کند و FastAPI را می‌سازد.
3. در `lifespan`, مقدار مؤثر config log می‌شود. فقط اگر `environment == development` باشد `init_db()`/`create_all` فراخوانی می‌شود. اجرای migration production خودکار نیست.
4. CORS از `MP_CORS_ORIGINS` allowlist می‌گیرد؛ middleware هدر امنیتی، `X-Request-ID`, metric درخواست و handlerهای خطا نصب می‌شوند.
5. Routerهای دامنه زیر `/api/v1` و liveness route در `/health` ثبت می‌شوند؛ OpenAPI/Swagger از FastAPI ساخته می‌شود.

نکتهٔ راه‌اندازی مهم: README ریشه فرمان Uvicorn را بدون `MP_ENVIRONMENT` نشان می‌دهد، در حالی که source فعلی آن را صریح لازم دارد. از quickstart اصلاح‌شدهٔ [راهنمای توسعه](04-development-testing-operations.md) استفاده کنید.

## ۲.۲ لایهٔ API و کاتالوگ

`api/v1/api.py` Routerهای auth، اعضا/اشتراک، کلاس، کتابخانهٔ حرکت، پرداخت، هزینه، گزارش، حریم، ارزیابی، برنامه، population، تغذیه، حضور/چهره، اعلان، گفت‌وگو، admin، shop، AI و update را جمع می‌کند. `api/v1/monitoring.py` routeهای سلامت/متریک را می‌دهد؛ return مرورگر پرداخت نیز از Router جداگانه در API aggregate وارد می‌شود.

### عملیات برحسب حوزه — snapshot قرارداد

فایل ماشینی `mp-app/backend/api/routes.json` در snapshot این مستندسازی **۱۶۳ رکورد method+path در ۱۴۱ الگوی path** داشت. عدد از قرارداد صادرشده می‌آید، نه اجرای همهٔ عملیات.

| حوزه در کاتالوگ | تعداد operation | نمونهٔ مسئولیت |
|---|---:|---|
| هویت، پروفایل و عضویت | 23 | OTP/session، اعضا، profile، membership و invoice. |
| Intake، برنامه و کتابخانه | 15 | gate-check، ایجاد برنامه و کتابخانهٔ exercise. |
| ارزیابی و سنجش | 10 | assessment، JP7، محور/اندازه‌گیری limb و گزارش روند. |
| کلاس، QR و حضور | 12 | رزرو/لغو کلاس، consent، token و check-in/exit. |
| تغذیه، غذا و وزن | 9 | plan، جست‌وجوی غذا، food/weight log و گزارش. |
| مالی، پرداخت، هزینه و Shop | 52 | receipt، wallet/ledger، coupon، expense/report و کاتالوگ/سفارش فروشگاه. |
| چت، اعلان، مدیریت و عملیات | 42 | chat، admin، feature flags، readiness، metrics، notification و reports. |

هر route را در کاتالوگ با متد، guard، role metadata و scope ببینید. `guards/roles` در JSON exporter اطلاعات inventory هستند؛ برای مجوز مؤثر باید کدهای `security/rbac.py`, `app/deps.py`, grantهای route و ownership helperهای service به‌همراه تست همان مسیر خوانده شوند. کاتالوگ، نبودن UI یا تست را قطعی ثابت نمی‌کند.

برای بازتولید inventory، از ریشهٔ repo:

```bash
python3 mp-app/backend/scripts/export_routes.py
# سپس بررسی شود چه فایل‌هایی تولید/تغییر کرده‌اند؛ خروجی را بی‌بررسی commit نکنید.
python3 scripts/interaction_map.py --check
```

دستور exporter را در source خودش بررسی کنید؛ گیت interaction map تطبیق artifact و contract را می‌سنجد، نه runtime.

## ۲.۳ درخواست احرازشده و مرزهای دسترسی

مسیر معمول:

```text
HTTP request
  → middleware / correlation ID / rate limit / validation
  → route dependencies
  → get_db() → SQLAlchemy Session
  → Authorization: Bearer <access token>
  → decode JWT → active user → auth_version → sid/RefreshToken check (اگر موجود)
  → Casbin role + method + path
  → route-specific guard / time-limited grant
  → record ownership / branch scope / service-level state rule
  → commit / response
```

جزئیات قابل مشاهده:

- `get_db()` یک session باز می‌کند و در پایان می‌بندد.
- `get_current_user()` access JWT را decode می‌کند، کاربر active را می‌خواهد و `auth_version` را تطبیق می‌دهد. توکن‌های جدید دارای `sid` به ردیف refresh-session hashed، ابطال و انقضایش وابسته‌اند؛ مسیرهای legacy بدون `sid` تا پایان عمر کوتاهشان حالت stateless قدیمی دارند.
- `require_permission()` مسیر/متد و نقش را با Casbin می‌سنجد. نقش‌های کد: `member`, `coach`, `reception`, `manager`, `admin`, `super_admin`. سیاست‌های `DENIES` می‌توانند allow عمومی را محدود کنند؛ از وراثت نقش نتیجهٔ دسترسی یک endpoint را حدس نزنید.
- `PathId` سقف شناسهٔ ایمن JSON را اعمال می‌کند؛ app-level id guard هم برای مسیرها نصب است. ورودی نامعتبر معمولاً 422 است، ولی پیام/خطای نهایی را handler و تست تعیین می‌کنند.
- **RBAC ≠ مالکیت ردیف:** اعضا نباید با تغییر `member_id` به دادهٔ دیگری دسترسی بگیرند. توابعی مانند `ensure_member_scope`/`ensure_record_scope` و کنترل در service مرز ABAC/مالکیت را پیاده می‌کنند.
- **RBAC ≠ grant خاص:** grantهای زمان‌دار (برای حوزه‌های حساس مانند مالی) محدودیت بیشتری می‌گذارند؛ به `app/security/grants.py` و routeهای مربوط رجوع کنید.
- UI یا توکن‌خوان سمت React فقط navigation/UX را پنهان/نمایش می‌دهد؛ API باید خودش مجوز بگیرد.

قالب خطا از app handlers می‌آید؛ Client و Studio پاسخ‌های JSON ساختاریافته و قالب legacy FastAPI را برای انتقال پیام مدیریت می‌کنند. وضعیت‌هایی که لازم است در UI متفاوت بمانند: 401 نشست، 403 مجوز، 409 تعارض/حالت ممنوع، 422 ورودی نامعتبر، 429 محدودیت نرخ، 5xx خطای سرور/شبکه. نگاشت کامل تجربه بین همهٔ صفحه‌ها هنوز باید آزموده شود.

## ۲.۴ نقشهٔ router و ماژول‌های دامنه

این جدول هدف فایل‌ها را خلاصه می‌کند؛ ماژول‌های خارج از `router.py` یا provider خارجی لزوماً در هر deployment فعال نیستند.

| مسیر ماژول | حوزه | مدل/مسئولیت شاخص |
|---|---|---|
| `modules/auth/` | OTP، session، تغییر تلفن، احراز | User, OtpCode, RefreshToken, phone-change challenge. |
| `modules/membership/` | عضو، profile، اشتراک | Member, Membership. |
| `modules/payments/` | روش/وضعیت پرداخت، فیش، کیف‌پول، ledger، gateway adapter | Payment, PaymentReceipt, WalletTransaction, LedgerEntry, Coupon. |
| `modules/expenses/`, `reporting/`, `reports/` | هزینه‌ها، گزارش دوره‌ای و محرمانه | Expense, ExpenseRevision, ExpenseReceipt, ReportRun و دادهٔ تجمیعی. |
| `modules/shop/` | دسته/محصول/قیمت/سبد/سفارش و feature flag | Product, Variant, CartItem, Order, PriceBook و config gateway. |
| `modules/assessment/`, `axis_assessment/` | ارزیابی و آزمون | Assessment, scoreهای دامنه/محور، JP7، field/l limb data و norms. |
| `modules/programs/` | برنامه، هفته، حرکت و feedback | WorkoutProgram, ProgramWeek, ProgramExercise, SetFeedback. |
| `modules/population/` | gate/مسیر جمعیت و safety gate | ورودی و قواعد eligibility/gate. |
| `modules/ai/`, `modules/ai_engine/` | endpointهای تولید/پیشنهاد و موتور/adapter | RuleRun و منطق قواعد؛ مدل بیرونی به معنی فعال یا مجاز نیست. |
| `modules/exercises/` | کاتالوگ حرکات و query | Exercise/catalog data و source registry. |
| `modules/nutrition/` | برنامهٔ تغذیه، meal، غذا/وزن log | NutritionPlan, MealItem, FoodLog, BodyWeightLog. |
| `modules/classes/` | برنامهٔ کلاس و رزرو | GymClass, ClassBooking. |
| `modules/face_id/` | consent، enrollment، QR و check-in | BiometricConsent, FaceTemplate, CheckIn. |
| `modules/notification/` | صندوق اعلان و چت | Notification, Conversation, Message؛ `chat_router.py` جداست. |
| `modules/admin/` | مدیریت، flag و audit | AuditLog, FeatureFlag, Campaign, Offer, AdminPermission. |
| `modules/privacy/` | پیش‌نمایش/اجرای retention | سیاست retention allowlist شده. |
| `modules/updates/` | manifest/نسخهٔ به‌روزرسانی | اطلاعات update، نه deploy اپ. |
| `modules/outbox/` | صف رویداد، inbox، dead letter و سلامت صف | OutboxEvent, InboxMessage, OutboxDeadLetter, WorkerHeartbeat. |
| `api/v1/monitoring.py` | readiness و metrics | سلامت API و instrument؛ نه وضعیت DNS/TLS یا مرورگر. |

Routerهای inventory در `api/v1/api.py` نصب می‌شوند؛ برای صفحه یا operation مشخص، route را با `routes.json` پیدا کنید، سپس schema/service/model/test همان دامنه را باز کنید. نام پوشهٔ «ai» به‌تنهایی تضمین LLM یا inference شبکه‌ای نیست.

## ۲.۵ مدل داده و مهاجرت‌ها

### فهرست جدول‌ها بر اساس فایل model

این فهرست از declarationهای `__tablename__` در checkout استخراج شده است. معنای دقیق column، nullable، index، FK و constraint را فقط از فایل مدل و migration متناظر بخوانید؛ نام جدول به‌تنهایی قرارداد API نیست.

| فایل مدل | جدول‌های تعریف‌شده | کاربرد اصلی |
|---|---|---|
| `admin.py` | `audit_logs`, `feature_flags`, `campaigns`, `offers` | ردپای رویدادهای حساس و تنظیم/محتوای مدیریتی. |
| `ai.py` | `rule_runs` | ثبت اجرا/نتیجهٔ قواعد. |
| `assessment.py` | `assessments`, `domain_scores`, `jackson_pollock_measurements`, `norm_entries`, `axis_assessments`, `axis_scores`, `field_test_results` | ارزیابی، امتیاز و norm. |
| `auth.py` | `users`, `otp_codes`, `phone_change_challenges`, `refresh_tokens`, `admin_permissions` | هویت، OTP، session و مجوزهای شخصی زمان‌دار. |
| `chat.py` | `conversations`, `messages` | گفت‌وگوی عضو و کارکنان. |
| `classes.py` | `gym_classes`, `class_bookings` | سانس، ظرفیت، رزرو/waitlist. |
| `content.py` | `exercises`, `catalog_sources`, `catalog_exercises`, `progression_ladders`, `progression_steps`, `food_items` | کتابخانهٔ حرکت/غذا و progression/catalog sources. |
| `face_id.py` | `face_templates`, `biometric_consents`, `checkins` | consent، embedding/template و رویداد حضور. |
| `finance.py` | `expenses`, `expense_revisions`, `report_runs`, `expense_receipts` | هزینه، تاریخچهٔ اصلاح و اجرای گزارش. |
| `membership.py` | `members`, `memberships` | پروفایل عضو و وضعیت/بازهٔ اشتراک. |
| `notification.py` | `notifications` | صندوق داخلی. |
| `nutrition.py` | `nutrition_plans`, `meal_items`, `food_logs`, `body_weight_logs` | هدف/برنامه و ثبت واقعی غذا/وزن. |
| `outbox.py` | `outbox_events`, `outbox_dead_letters`, `inbox_messages` | تحویل event، retry و inbox/idempotency. |
| `payments.py` | `payments`, `payment_receipts`, `wallet_transactions`, `ledger_entries`, `coupons` | پرداخت، فیش، wallet/ledger و تخفیف. |
| `programs.py` | `workout_programs`, `program_weeks`, `program_exercises`, `set_feedbacks` | برنامه و بازخورد ست. |
| `segment.py` | `limb_measurements` | سنجش اندام/بخش بدن. |
| `shop.py` | `product_categories`, `products`, `product_variants`, `cart_items`, `orders`, `order_items`, `payment_gateway_configs`, `change_requests`, `price_book` | کاتالوگ و آثار تاریخی/مشروط سبد و سفارش. |
| `worker.py` | `worker_heartbeats` | freshness/heartbeat پردازش‌گر. |

### کلیدهای مدل‌خوانی

- زمان‌های ایجاد/به‌روزرسانی اغلب از `TimestampMixin` می‌آیند؛ timezone و serialization را در schema بررسی کنید.
- فیلد `branch_id` از `BranchMixin` برای جداسازی آینده/محلی در برخی مدل‌هاست؛ این را با tenant authorization تکمیل‌شده اشتباه نگیرید.
- پاداش/سود مالی به «یک ستون balance» فروکاستنی نیست: Payment، receipt، wallet transaction، append-only ledger، reversal و expense ممکن است معنا/تاریخ متفاوت داشته باشند.
- `NutritionPlan` و `MealItem` با ثبت غذای خورده‌شده (`FoodLog`) جدا هستند؛ generator فعلی طبق گزارش تحلیل می‌تواند هدف ماکرو/کالری با `meals: []` بسازد.
- `CheckIn.qr_jti_hash` فقط digest شناسهٔ تصادفی QR را نگه می‌دارد و unique constraint برای بستن race همزمان دارد؛ bearer token خام نباید در DB ثبت شود.
- مسیر ذخیرهٔ فایل رسید خصوصی است و فایل‌ها ممکن است خارج از DB باشند. این راهنما هیچ محتوا یا نام/مقدار شخصی از پوشهٔ receipt نقل نمی‌کند.

### Alembic

در snapshot بررسی‌شده ۳۸ revision Python در `db/migrations/versions/` وجود داشت؛ گراف استاتیک `revision/down_revision` یک root (`39f0cd2d8531`, initial schema) و یک head (`a7c3d9e1f2b4`) نشان می‌داد و یک migration merge هم دارد. این محاسبه روی فایل‌هاست، نه اتصال به DB زنده. تغییرهای قابل‌مشاهده در نام‌ها/شرح‌ها شامل schema اولیه، assessment، class/finance، کاتالوگ و progression، sync/QR، wallet/ledger، پرداخت کارت‌به‌کارت، expense/receipt، outbox/inbox، report run، heartbeat و coupon است.

فرمان‌های معمول از `mp-app/backend/`:

```bash
python -m alembic history
python -m alembic heads
python -m alembic current
python -m alembic check

# فقط روی DB محلی/scratch پس از بررسی URL:
python -m alembic upgrade head
```

`db/migrations/env.py` URL را از `settings.database_url` می‌گیرد و metadata مدل‌ها را وارد می‌کند. Dev lifespan از `create_all` استفاده می‌کند؛ آن فرمان migration history/upgrade تولیدی را جایگزین نمی‌کند. پیش از migration دادهٔ واقعی، backup، clone امن، duplicate/constraint audit، سازگاری dialect، rollback plan و scratch migration لازم‌اند. این مستندسازی روی دیتابیس تولیدی هیچ migration اجرا نکرده است.

برای دادهٔ پشتیبان، `scripts/backup.py` عملیات `backup`, `verify`, `restore` دارد. `verify` برای بررسی manifest/hash و سلامت SQLite طراحی شده و در مسیر اصلی فایل را restore نمی‌کند؛ `restore` باید به مسیر scratch و همراه `--extras-to` محدود شود تا archive قدیمی source/asset اصلی را بازنویسی نکند. دستورها و هشدارهای دقیق در [Ops runbook](../OPS-RUNBOOK.md) هستند.

## ۲.۶ خلاصهٔ قواعد دامنه و جریان‌های اصلی

> تمام موارد زیر description مسیرهای کد/گزارش‌اند؛ وضعیت test-reported و مسیرهای پیکربندی‌شده با اجرای عملی بانک/دستگاه فرق دارند. مرجع سناریوها [Wiring ledger](../architecture/session-decisions-2026-11-23/WIRING-LEDGER.md) است.

| جریان | API/service/data | مرز و گپ |
|---|---|---|
| OTP/login | `modules/auth/router.py` → auth service → OtpCode/User/RefreshToken؛ SMS adapter در `app/sms.py` | `dev` SMS کد واقعی نمی‌فرستد؛ provider و secrets واقعی باید صریح انتخاب و شبکه/تحویل جدا آزموده شوند. Token refresh/logout/version روی server-side است. |
| تغییر شماره | چند گام OTP برای شمارهٔ قبلی/جدید و challenge کوتاه‌عمر | دو طرف باید کنترل شوند؛ routeها از پاسخ status handler و test پیروی کنند. |
| Member/membership | `modules/membership/` → Member/Membership | عضو عادی فقط رکوردهای خودش؛ فعال‌شدن اشتراک را با ساخت payment/بارگذاری فیش یکی نکنید. |
| برنامهٔ تمرین | `population` gate → `ai_engine`/`engine/workout.py` → `programs`/Exercise | قواعد قطعی اعداد را می‌سازند؛ حالت `blocked` یا `needs_review` هنوز می‌تواند draft ایجاد/نمایش دهد طبق گپ گزارش‌شده؛ approved-only به‌عنوان تضمین کامل ادعا نشود. |
| بازخورد ست | `POST /programs/set-feedback` یا مسیر sync → SetFeedback | پیشنهاد auto-reg از داده/قاعده؛ تیک «انجام شد» در Today یک state محلی جداست، نه همان ذخیرهٔ بازخورد. |
| کلاس | `classes/service.py` → GymClass/ClassBooking | ظرفیت، waitlist و cancel/rebook rules در سرویس؛ race محیط همزمانی/device از یک تست SQLite نتیجه‌گیری نمی‌شود. |
| حضور | `face_id` consent/enroll/checkin/QR | QR کوتاه‌عمر امضا می‌شود و یک‌بارمصرف است؛ `method=face` fail-closed گزارش شده، اما آزمون دستگاه/پذیرش واقعی نشده. |
| تغذیه | `nutrition` plan/food/weight logs | target/plan، meal item و food log داده‌های متمایزند؛ target را وعدهٔ کامل/تشخیص تغذیه‌ای حرفه‌ای معرفی نکنید. |
| کارت‌به‌کارت | payment + receipt upload/review + manual approval | تصمیم انتشار، تطبیق انسانی با منبع بانکی مستقل است؛ تصویر فیش به‌تنهایی منبع حقیقت پرداخت نیست. |
| Wallet/ledger/refund | wallet API و ledger row؛ reversal append-only؛ refund gateway/record | test sandbox یا approval API به معنی حرکت پول بانکی نیست. concurrency financial و accounting policy جدا گیت دارند. |
| Shop | محصول/قیمت/موجودی، cart/order routeها و flag | policy انتشار فروشگاه عضو را نمایش‌محور می‌خواهد؛ online purchase خاموش/فیلتر می‌شود. داده‌های legacy به‌تنهایی مسیر مجاز محصول نیستند. |
| هزینه/گزارش | Expense + revision/receipt + ReportRun و finance reports | دادهٔ ناقص، از جمله refund بی‌تاریخ، می‌تواند `complete=false` و سود نامعلوم بدهد؛ صفر را به جای unknown نگذارید. |
| Chat/notification | Conversation/Message/Notification + outbox/inbox | inbox داخل سامانه از push واقعی جداست؛ push provider/SLA و worker deployment اثبات نشده‌اند. |

## ۲.۷ Jobs، outbox، cache و health

### Scheduler و relay

`jobs/scheduler.py` jobهای تمدید/انقضای اشتراک، یادآوری‌ها و گزارش مالی دوره‌ای را تعریف می‌کند. `build_scheduler()` وجود دارد، اما بررسی `app/main.py` نشان داد lifespan فعلی آن را start نمی‌کند. بنابراین تعریف job/تست تابع مساوی scheduler فعال در deployment نیست.

`jobs/outbox_relay.py` رویدادها را با retry/backoff و dead-letter relay می‌کند؛ `modules/outbox/service.py` مرز event/inbox را پیاده می‌کند. نمونهٔ handler موجود صرفاً log می‌کند، و source این checkout به‌تنهایی اتصال push/SMS واقعی را ثابت نمی‌کند. worker باید جداگانه راه‌اندازی، heartbeat، queue/retry/idempotency و alert آن عملیاتی شود. `MP_REQUIRE_WORKER=true` می‌تواند readiness را به heartbeat تازه گره بزند؛ مقدار جاری default false است.

### Cache

`cache/store.py` interface `CacheBackend`, `InMemoryCache` و `ValkeyCache` دارد. Valkey/Redis availability هنگام راه‌اندازی probe می‌شود؛ خطای command در مسیر read/write/invalidation به fallback process-local می‌رود. این fallback یک دیتابیس مشترک نیست و نباید برای state حساس یا rate limit مشترک بین workerها منبع حقیقت فرض شود. readiness جدا storage محدودسازی auth را بررسی می‌کند.

### سلامت و metrics

- `/health`: liveness ساده؛ `status=ok` یعنی کد route پاسخ می‌دهد، نه آماده‌بودن dependencyها.
- `/api/v1/health/ready`: DB، rate-limit storage، اشباع connection pool و check-in SLO را می‌سنجد؛ اگر `MP_REQUIRE_WORKER` فعال باشد heartbeat worker هم لازم است. پاسخ readiness ناموفق HTTP 503 می‌شود.
- `/api/v1/metrics`: نیازمند `Authorization: Bearer <MP_METRICS_TOKEN>`؛ token unset endpoint را بسته می‌کند. خطای refresh metrics ثبت می‌شود و شمارنده در metrics/readiness بازتاب دارد.
- Prometheus/Exporter/Compose در مخزن وجود دارند؛ Alertmanager/receiver، DNS/TLS، scraping بیرونی و دریافت هشدار باید در محیط هدف جدا آزموده شوند.

## ۲.۸ خطاهای رایج خواندن Backend

1. Router شلوغ نیست؟ باز هم business rule را از `service.py` و schema/validator جدا بخوانید.
2. `roles` در `routes.json` دیدید؟ effective permission را از Casbin + guardها + ownership دنبال کنید.
3. endpoint پیدا شد؟ client مصرف‌کننده، integration test و device/browser مسیر را هم پیدا کنید.
4. ORM model پیدا شد؟ وجود جدول روی دیتابیس target را از Alembic/`current` بررسی کنید؛ `create_all` migration نیست.
5. `scheduler`/`outbox relay` وجود دارد؟ process manager/Compose command/startup و heartbeat را بررسی کنید.
6. provider class پیدا شد؟ config، production validator، network reachability، provider credentials و evidence واقعی لازم است.
7. receipt route پیدا شد؟ فایل خصوصی را فقط با auth/scope بررسی کنید؛ این task عمداً `var/receipts` را نخوانده و نباید آن را در سند/آزمون/اسکرین‌شات کپی کرد.
