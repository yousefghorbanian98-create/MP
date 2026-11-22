# PROJECT-HANDOFF — راهنمای جامع برنامه برای نشست‌های AI

> تولیدشده از کد با `scripts/repowise_handoff.py` · commit مرجع: `c06e353`
> بازتولید: `python3 scripts/repowise_handoff.py` · بررسی رانش: `python3 scripts/repowise_handoff.py --check`
> این فایل از خود کد ساخته شده؛ برای جزئیات پیاده‌سازی، فایل منبع را بخوانید. قبل از ادعا درباره‌ی رفتار، آن را در کد یا تست تأیید کنید.

## ۰. این فایل را چگونه بخوانیم
۱. بخش‌های ۱ تا ۳ معماری و اندازه‌ها را می‌دهند.
۲. بخش ۴ و ۵ قرارداد API و مدل داده را می‌دهند؛ هر مسیر نگهبان و نقش خودش را دارد.
۳. بخش ۶ جریان‌های اصلی (OTP، پرداخت، کوپن، رسید، کیف‌پول) را توضیح می‌دهد.
۴. بخش ۷ تا ۱۰ پیکربندی، مجوزها، Studio، اپ عضو و CI را می‌دهند.
۵. بخش ۱۱ آخرین نتایج اندازه‌گیری‌شده و موانع را می‌دهد. بخش ۱۲ جدول «کجا را تغییر دهم» است.

## ۱. اجزا و اندازه
| بخش | مسیر | اندازه | تست |
|---|---|---|---|
| اپ عضو (Flutter) | `mp-app/client` | 44 فایل Dart در lib | 29 فایل تست |
| Studio (React + TS) | `mp-app/studio` | 53 فایل در src | 46 فایل تست |
| API (FastAPI) | `mp-app/backend` | 95 فایل Python در modules | 144 فایل تست |

## ۲. ماژول‌های بک‌اند
نگاشت مسیر به ماژول تقریبی است: پیشوند مسیر (مثلاً `assessments`) گاهی با نام پوشه (`assessment`) فرق دارد. برای نگاشت دقیق، روتر هر ماژول را بخوانید.

| ماژول (`modules/`) | فایل‌های Python | مسیرهای API با پیشوند هم‌نام | عملیات |
|---|---|---|---|
| `admin` | 7 | 16 | 19 |
| `ai` | 1 | 3 | 3 |
| `ai_engine` | 4 | 0 | 0 |
| `assessment` | 6 | 0 | 0 |
| `auth` | 4 | 10 | 10 |
| `axis_assessment` | 4 | 0 | 0 |
| `classes` | 2 | 3 | 4 |
| `content` | 1 | 0 | 0 |
| `exercises` | 2 | 0 | 0 |
| `expenses` | 5 | 3 | 6 |
| `face_id` | 6 | 0 | 0 |
| `membership` | 5 | 0 | 0 |
| `notification` | 6 | 0 | 0 |
| `nutrition` | 4 | 8 | 8 |
| `outbox` | 4 | 0 | 0 |
| `payments` | 11 | 21 | 24 |
| `population` | 4 | 3 | 3 |
| `privacy` | 3 | 0 | 0 |
| `programs` | 4 | 10 | 10 |
| `reporting` | 4 | 0 | 0 |
| `reports` | 4 | 1 | 1 |
| `shop` | 2 | 15 | 22 |
| `updates` | 2 | 1 | 1 |

پیشوندهای API بدون پوشهٔ هم‌نام در `modules/` (در `api/` یا `app/` تعریف شده‌اند): `assessments` (7 عملیات)، `axis-assessments` (4 عملیات)، `chat` (5 عملیات)، `face` (10 عملیات)، `finance` (4 عملیات)، `health` (1 عملیات)، `library` (2 عملیات)، `members` (13 عملیات)، `metrics` (1 عملیات)، `notifications` (4 عملیات)، `root` (1 عملیات)

## ۳. مسیرهای API (قرارداد)
141 مسیر و 163 عملیات. منبع: `mp-app/backend/api/routes.json` (تولیدشده از کد).

| متد | مسیر | نگهبان (guard) | نقش‌های مجاز |
|---|---|---|---|
| GET | `/api/v1/admin/analytics/churn-risk` | permission | manager, admin, super_admin |
| GET | `/api/v1/admin/analytics/leaderboards` | permission | manager, admin, super_admin |
| GET | `/api/v1/admin/attendance` | permission | coach, reception, manager, admin, super_admin |
| GET | `/api/v1/admin/audit` | permission | manager, admin, super_admin |
| GET | `/api/v1/admin/checkins` | permission | coach, reception, manager, admin, super_admin |
| GET | `/api/v1/admin/flags` | permission | manager, admin, super_admin |
| PUT | `/api/v1/admin/flags` | permission | manager, admin, super_admin |
| GET | `/api/v1/admin/flags/{key}` | permission | manager, admin, super_admin |
| GET | `/api/v1/admin/kpis` | permission | manager, admin, super_admin |
| GET | `/api/v1/admin/members-summary` | permission | coach, reception, manager, admin, super_admin |
| GET | `/api/v1/admin/permissions` | permission | super_admin |
| POST | `/api/v1/admin/permissions` | permission | super_admin |
| GET | `/api/v1/admin/permissions/known` | permission | super_admin |
| DELETE | `/api/v1/admin/permissions/{grant_id}` | permission | super_admin |
| GET | `/api/v1/admin/retention` | permission | manager, admin, super_admin |
| POST | `/api/v1/admin/retention/run` | permission | manager, admin, super_admin |
| GET | `/api/v1/admin/users` | permission | manager, admin, super_admin |
| DELETE | `/api/v1/admin/users/{user_id}/role` | permission | manager, admin, super_admin |
| POST | `/api/v1/admin/users/{user_id}/role` | permission | manager, admin, super_admin |
| POST | `/api/v1/ai/nutrition/generate` | permission | member, coach, manager, admin, super_admin |
| POST | `/api/v1/ai/program/generate` | permission | member, coach, manager, admin, super_admin |
| POST | `/api/v1/ai/suggest-weight` | permission | member, coach, manager, admin, super_admin |
| POST | `/api/v1/assessments` | permission | coach, manager, admin, super_admin |
| POST | `/api/v1/assessments/jp7` | permission | coach, manager, admin, super_admin |
| GET | `/api/v1/assessments/jp7/member/{member_id}/trend` | permission | member, coach, manager, admin, super_admin |
| POST | `/api/v1/assessments/limb` | permission | member, coach, manager, admin, super_admin |
| GET | `/api/v1/assessments/limb/member/{member_id}/report` | permission | member, coach, manager, admin, super_admin |
| GET | `/api/v1/assessments/member/{member_id}` | permission | member, coach, manager, admin, super_admin |
| GET | `/api/v1/assessments/{assessment_id}` | permission | member, coach, manager, admin, super_admin |
| POST | `/api/v1/auth/logout` | — | — |
| POST | `/api/v1/auth/logout-all` | authenticated | member, manager, admin, super_admin |
| POST | `/api/v1/auth/otp/request` | — | — |
| POST | `/api/v1/auth/otp/verify` | — | — |
| POST | `/api/v1/auth/phone-change/confirm` | authenticated | manager, admin, super_admin |
| POST | `/api/v1/auth/phone-change/request` | authenticated | manager, admin, super_admin |
| POST | `/api/v1/auth/phone-change/verify-old` | authenticated | manager, admin, super_admin |
| POST | `/api/v1/auth/refresh` | — | — |
| GET | `/api/v1/auth/sessions` | authenticated | member, manager, admin, super_admin |
| DELETE | `/api/v1/auth/sessions/{session_id}` | authenticated | member, manager, admin, super_admin |
| POST | `/api/v1/axis-assessments` | permission | coach, manager, admin, super_admin |
| GET | `/api/v1/axis-assessments/member/{member_id}` | permission | member, coach, manager, admin, super_admin |
| GET | `/api/v1/axis-assessments/{assessment_id}/matrix` | permission | member, coach, manager, admin, super_admin |
| POST | `/api/v1/axis-assessments/{assessment_id}/review` | permission, permission | manager, admin, super_admin |
| GET | `/api/v1/chat/conversations` | permission | member, coach, manager, admin, super_admin |
| POST | `/api/v1/chat/conversations` | permission | member, coach, manager, admin, super_admin |
| GET | `/api/v1/chat/conversations/{conversation_id}/messages` | permission | member, coach, manager, admin, super_admin |
| POST | `/api/v1/chat/conversations/{conversation_id}/messages` | permission | member, coach, manager, admin, super_admin |
| POST | `/api/v1/chat/conversations/{conversation_id}/read` | permission | member, coach, manager, admin, super_admin |
| GET | `/api/v1/classes` | permission | member, coach, reception, manager, admin, super_admin |
| POST | `/api/v1/classes` | permission | coach, manager, admin, super_admin |
| POST | `/api/v1/classes/book` | permission | member, coach, manager, admin, super_admin |
| POST | `/api/v1/classes/cancel` | permission | member, coach, manager, admin, super_admin |
| GET | `/api/v1/expenses` | grant:finance.read, permission | manager, admin, super_admin |
| POST | `/api/v1/expenses` | grant:finance.write, permission | manager, admin, super_admin |
| DELETE | `/api/v1/expenses/{expense_id}` | grant:finance.write, permission | manager, admin, super_admin |
| PATCH | `/api/v1/expenses/{expense_id}` | grant:finance.write, permission | manager, admin, super_admin |
| GET | `/api/v1/expenses/{expense_id}/receipt` | grant:finance.read, permission | manager, admin, super_admin |
| POST | `/api/v1/expenses/{expense_id}/receipt` | grant:finance.write, permission | manager, admin, super_admin |
| POST | `/api/v1/face/checkin` | permission | member, coach, reception, manager, admin, super_admin |
| POST | `/api/v1/face/checkin-qr` | permission | member, coach, reception, manager, admin, super_admin |
| POST | `/api/v1/face/checkins/{checkin_id}/exit` | permission | member, coach, manager, admin, super_admin |
| POST | `/api/v1/face/consent` | permission | member, coach, reception, manager, admin, super_admin |
| POST | `/api/v1/face/consent/revoke` | permission | member, coach, reception, manager, admin, super_admin |
| GET | `/api/v1/face/deep-status` | permission | member, coach, reception, manager, admin, super_admin |
| POST | `/api/v1/face/enroll` | permission | member, coach, manager, admin, super_admin |
| DELETE | `/api/v1/face/enroll/{member_id}` | permission | member, coach, manager, admin, super_admin |
| GET | `/api/v1/face/privacy-notice` | permission | member, coach, reception, manager, admin, super_admin |
| GET | `/api/v1/face/qr-token` | permission | member, coach, manager, admin, super_admin |
| GET | `/api/v1/finance/reports/daily/{run_date}` | grant:finance.read, permission | manager, admin, super_admin |
| GET | `/api/v1/finance/reports/period` | grant:finance.read, permission | manager, admin, super_admin |
| GET | `/api/v1/finance/reports/schedule` | grant:finance.read, permission | manager, admin, super_admin |
| POST | `/api/v1/finance/reports/schedule/{job_key}/run` | grant:finance.write, permission | manager, admin, super_admin |
| GET | `/api/v1/health/ready` | — | — |
| GET | `/api/v1/library/exercises` | permission | member, coach, manager, admin, super_admin |
| GET | `/api/v1/library/exercises/{exercise_id}` | permission | member, coach, manager, admin, super_admin |
| GET | `/api/v1/members` | permission | coach, reception, manager, admin, super_admin |
| POST | `/api/v1/members` | permission | coach, reception, manager, admin, super_admin |
| GET | `/api/v1/members/me` | permission | member, coach, reception, manager, admin, super_admin |
| PUT | `/api/v1/members/me` | permission | member, coach, reception, manager, admin, super_admin |
| GET | `/api/v1/members/me/checkins` | permission | member, coach, reception, manager, admin, super_admin |
| GET | `/api/v1/members/me/face-consent` | permission | member, coach, reception, manager, admin, super_admin |
| POST | `/api/v1/members/memberships` | permission | coach, reception, manager, admin, super_admin |
| POST | `/api/v1/members/memberships/from-plan` | permission | coach, reception, manager, admin, super_admin |
| GET | `/api/v1/members/memberships/plans` | permission | member, coach, reception, manager, admin, super_admin |
| GET | `/api/v1/members/memberships/{membership_id}/invoice` | permission | member, coach, reception, manager, admin, super_admin |
| GET | `/api/v1/members/{member_id}` | permission | member, coach, reception, manager, admin, super_admin |
| PATCH | `/api/v1/members/{member_id}` | permission | coach, reception, manager, admin, super_admin |
| GET | `/api/v1/members/{member_id}/memberships` | permission | member, coach, reception, manager, admin, super_admin |
| GET | `/api/v1/metrics` | — | — |
| POST | `/api/v1/notifications` | permission | manager, admin, super_admin |
| GET | `/api/v1/notifications/member/{member_id}` | permission | member, coach, reception, manager, admin, super_admin |
| GET | `/api/v1/notifications/reminders/member/{member_id}` | permission | member, coach, reception, manager, admin, super_admin |
| POST | `/api/v1/notifications/{notification_id}/read` | permission | member, coach, reception, manager, admin, super_admin |
| POST | `/api/v1/nutrition/food-logs` | permission | member, coach, manager, admin, super_admin |
| GET | `/api/v1/nutrition/food-logs/member/{member_id}/daily` | permission | member, coach, manager, admin, super_admin |
| GET | `/api/v1/nutrition/foods` | permission | member, coach, manager, admin, super_admin |
| GET | `/api/v1/nutrition/member/{member_id}/adaptive` | permission | member, coach, manager, admin, super_admin |
| POST | `/api/v1/nutrition/plans` | permission | coach, manager, admin, super_admin |
| GET | `/api/v1/nutrition/plans/member/{member_id}` | permission | member, coach, manager, admin, super_admin |
| POST | `/api/v1/nutrition/plans/{plan_id}/approve` | permission | coach, manager, admin, super_admin |
| POST | `/api/v1/nutrition/weight-logs` | permission | member, coach, manager, admin, super_admin |
| GET | `/api/v1/payments` | permission | member, reception, manager, admin, super_admin |
| POST | `/api/v1/payments` | permission | member, reception, manager, admin, super_admin |
| GET | `/api/v1/payments/coupons` | grant:finance.write, permission | member, reception, manager, admin, super_admin |
| POST | `/api/v1/payments/coupons` | grant:finance.write, permission | reception, manager, admin, super_admin |
| POST | `/api/v1/payments/finance/commission` | permission | manager, admin, super_admin |
| GET | `/api/v1/payments/finance/export.csv` | permission | manager, admin, super_admin |
| GET | `/api/v1/payments/finance/summary` | permission | manager, admin, super_admin |
| GET | `/api/v1/payments/invoice/{member_id}` | permission | member, reception, manager, admin, super_admin |
| POST | `/api/v1/payments/ledger/{entry_id}/reverse` | grant:finance.write, permission | reception, manager, admin, super_admin |
| GET | `/api/v1/payments/ledger/{member_id}` | permission | member, reception, manager, admin, super_admin |
| POST | `/api/v1/payments/wallet/charge` | grant:finance.write, permission | reception, manager, admin, super_admin |
| POST | `/api/v1/payments/wallet/pay` | permission | member, reception, manager, admin, super_admin |
| GET | `/api/v1/payments/wallet/{member_id}` | permission | member, reception, manager, admin, super_admin |
| GET | `/api/v1/payments/wallet/{member_id}/transactions` | permission | member, reception, manager, admin, super_admin |
| POST | `/api/v1/payments/{payment_id}/approve` | grant:finance.write, permission | reception, manager, admin, super_admin |
| POST | `/api/v1/payments/{payment_id}/callback` | permission | member, reception, manager, admin, super_admin |
| POST | `/api/v1/payments/{payment_id}/fail` | permission | reception, manager, admin, super_admin |
| GET | `/api/v1/payments/{payment_id}/gateway-return` | — | — |
| GET | `/api/v1/payments/{payment_id}/receipt` | permission | member, reception, manager, admin, super_admin |
| POST | `/api/v1/payments/{payment_id}/receipt` | permission | member, reception, manager, admin, super_admin |
| POST | `/api/v1/payments/{payment_id}/refund` | permission | reception, manager, admin, super_admin |
| POST | `/api/v1/payments/{payment_id}/reject` | grant:finance.write, permission | reception, manager, admin, super_admin |
| POST | `/api/v1/payments/{payment_id}/start` | permission | member, reception, manager, admin, super_admin |
| POST | `/api/v1/payments/{payment_id}/verify` | grant:finance.write, permission | reception, manager, admin, super_admin |
| POST | `/api/v1/population/gate-check` | permission | member, coach, reception, manager, admin, super_admin |
| POST | `/api/v1/population/intake/next` | permission | member, coach, reception, manager, admin, super_admin |
| GET | `/api/v1/population/paths` | permission | member, coach, reception, manager, admin, super_admin |
| GET | `/api/v1/programs` | permission | coach, reception, manager, admin, super_admin |
| POST | `/api/v1/programs/from-engine` | permission | coach, manager, admin, super_admin |
| GET | `/api/v1/programs/member/{member_id}` | permission | member, coach, manager, admin, super_admin |
| GET | `/api/v1/programs/member/{member_id}/readiness` | permission | member, coach, manager, admin, super_admin |
| GET | `/api/v1/programs/member/{member_id}/volume` | permission | member, coach, manager, admin, super_admin |
| POST | `/api/v1/programs/set-feedback` | permission | member, coach, manager, admin, super_admin |
| POST | `/api/v1/programs/sync/set-feedback` | permission | member, coach, manager, admin, super_admin |
| GET | `/api/v1/programs/{program_id}` | permission | member, coach, manager, admin, super_admin |
| POST | `/api/v1/programs/{program_id}/approve` | permission | coach, manager, admin, super_admin |
| POST | `/api/v1/programs/{program_id}/reject` | permission | coach, manager, admin, super_admin |
| GET | `/api/v1/reports/confidential/{member_id}` | grant:reports.confidential, permission | coach, admin, super_admin |
| GET | `/api/v1/shop/cart` | permission | member, coach, reception, manager, admin, super_admin |
| POST | `/api/v1/shop/cart` | permission | member, reception, manager, admin, super_admin |
| DELETE | `/api/v1/shop/cart/{item_id}` | permission | member, reception, manager, admin, super_admin |
| PATCH | `/api/v1/shop/cart/{item_id}` | permission | member, reception, manager, admin, super_admin |
| GET | `/api/v1/shop/categories` | permission | member, coach, reception, manager, admin, super_admin |
| GET | `/api/v1/shop/change-requests` | permission | member, coach, reception, manager, admin, super_admin |
| POST | `/api/v1/shop/change-requests` | permission | reception, manager, admin, super_admin |
| POST | `/api/v1/shop/change-requests/{request_id}/review` | permission | reception, manager, admin, super_admin |
| POST | `/api/v1/shop/checkout` | permission | member, reception, manager, admin, super_admin |
| GET | `/api/v1/shop/gateways` | permission | member, coach, reception, manager, admin, super_admin |
| POST | `/api/v1/shop/gateways` | permission | reception, manager, admin, super_admin |
| PUT | `/api/v1/shop/gateways/{gateway_id}` | permission | reception, manager, admin, super_admin |
| GET | `/api/v1/shop/orders` | permission | member, coach, reception, manager, admin, super_admin |
| PATCH | `/api/v1/shop/orders/{order_id}` | permission | reception, manager, admin, super_admin |
| GET | `/api/v1/shop/orders/{order_id}/receipt` | permission | member, coach, reception, manager, admin, super_admin |
| GET | `/api/v1/shop/prices` | permission | member, coach, reception, manager, admin, super_admin |
| POST | `/api/v1/shop/prices` | permission | reception, manager, admin, super_admin |
| GET | `/api/v1/shop/products` | permission | member, coach, reception, manager, admin, super_admin |
| POST | `/api/v1/shop/products` | permission | reception, manager, admin, super_admin |
| GET | `/api/v1/shop/products/{product_id}` | permission | member, coach, reception, manager, admin, super_admin |
| PATCH | `/api/v1/shop/products/{product_id}` | permission | reception, manager, admin, super_admin |
| GET | `/api/v1/shop/status` | permission | member, coach, reception, manager, admin, super_admin |
| GET | `/api/v1/updates/manifest` | — | — |
| GET | `/health` | — | — |

## ۴. جریان‌های اصلی
### ۱. ورود با OTP
1. `POST /api/v1/auth/otp/request` با شماره؛ کد ۶ رقمی با TTL پیش‌فرض ۱۲۰ ثانیه ساخته می‌شود (`otp_ttl_seconds`). در محیط `development` کد در پاسخ `dev_code` برمی‌گردد.
2. `POST /api/v1/auth/otp/verify` با شماره و کد؛ کاربر در صورت نبود ساخته می‌شود (نقش عضو) و جفت توکن برمی‌گردد.
3. `POST /api/v1/auth/refresh` توکن را می‌چرخاند؛ `logout` و `logout-all` نشست‌ها را می‌بندند.
4. تغییر شماره سه مرحله دارد: `phone-change/request` → `verify-old` → `confirm`.
نرخ محدودیت: `otp_rate_limit` = `10/minute`، `otp_burst_limit` = `3/second`؛ حداکثر تلاش `otp_max_attempts` = ۵.

### ۲. پرداخت، کیف‌پول و کوپن
- کوپن در `modules/payments/service.py` (`_apply_coupon`) روی سرور و روی مبلغ واقعی محاسبه می‌شود. نوع: درصدی (۱ تا ۱۰۰) یا مبلغ ثابت ریال؛ هر دو با انقضا و سقف استفاده.
- حداقل مبلغ پس از تخفیف ۱٬۰۰۰ ریال است. کد تکراری پاسخ ۴۰۹ می‌دهد. کوپن با کلید idempotency یک‌بار مصرف می‌شود.
- حالت‌های پرداخت: `pending` → `paid` | `failed` | `in_review`؛ `in_review` → `paid` | `failed`؛ `paid` → `refunded`. نمودار: `docs/architecture/diagram-design/png/02-payments-lifecycle.png`.
- رسید کارت‌به‌کارت: `receipts.py` وضعیت رسید را `in_review` می‌کند؛ تأیید ادمین `approved` و رد `rejected` می‌سازد.
- کیف‌پول: موجودی = مجموع credit − مجموع debit (`_wallet_balance_expr`). دسترسی عضو فقط به کیف‌پول خودش است (`ensure_member_scope` با `Member.id`، نه `User.id`).
- درگاه: `payment_gateway` = `manual` (پیش‌فرض) | `mock` | `sandbox`.

### ۳. دامنه‌ها و نقش‌ها
- نقش‌ها: `member`، `coach`، `manager`، `reception`، `admin`، `super_admin`.
- مجوزهای جزئی (`grants`) فقط برای کارهایی که پول یا گزارش حساس را جابه‌جا می‌کنند لازم‌اند؛ فهرست در بخش مجوزها.
- گارد `require_permission()` روی روتر `/programs` است؛ عضو به آن دسترسی ندارد (۴۰۳ درست است).

### ۴. اورلود و عملکرد (اندازه‌گیری‌شده، محلی)
۲۰۰ کاربر همزمان، SQLite و یک worker: حدود ۱۸۰ درخواست بر ثانیه، p95 ≈ ۲۱۰ms، p99 ≈ ۳۳۰ms، ۰ خطا در دو اجرای سالم. یک بار استخر اتصال پر شد و ریشه‌یابی نشده است (`qa-report/FINAL-REPORT.md`).

## ۵. مدل داده
64 جدول ORM. منبع: `mp-app/backend/db/models/*.py`.

| جدول | کلاس | فایل |
|---|---|---|
| `admin_permissions` | AdminPermission | `auth.py` |
| `assessments` | Assessment14Domain | `assessment.py` |
| `audit_logs` | AuditLog | `admin.py` |
| `axis_assessments` | AxisAssessment | `assessment.py` |
| `axis_scores` | AxisScore | `assessment.py` |
| `biometric_consents` | BiometricConsent | `face_id.py` |
| `body_weight_logs` | BodyWeightLog | `nutrition.py` |
| `campaigns` | Campaign | `admin.py` |
| `cart_items` | CartItem | `shop.py` |
| `catalog_exercises` | CatalogExercise | `content.py` |
| `catalog_sources` | CatalogSource | `content.py` |
| `change_requests` | ChangeRequest | `shop.py` |
| `checkins` | CheckIn | `face_id.py` |
| `class_bookings` | ClassBooking | `classes.py` |
| `conversations` | Conversation | `chat.py` |
| `coupons` | Coupon | `payments.py` |
| `domain_scores` | DomainScore | `assessment.py` |
| `exercises` | Exercise | `content.py` |
| `expense_receipts` | ExpenseReceipt | `finance.py` |
| `expense_revisions` | ExpenseRevision | `finance.py` |
| `expenses` | Expense | `finance.py` |
| `face_templates` | FaceTemplate | `face_id.py` |
| `feature_flags` | FeatureFlag | `admin.py` |
| `field_test_results` | FieldTestResult | `assessment.py` |
| `food_items` | FoodItem | `content.py` |
| `food_logs` | FoodLog | `nutrition.py` |
| `gym_classes` | GymClass | `classes.py` |
| `inbox_messages` | InboxMessage | `outbox.py` |
| `jackson_pollock_measurements` | JacksonPollockMeasurement | `assessment.py` |
| `ledger_entries` | LedgerEntry | `payments.py` |
| `limb_measurements` | LimbMeasurement | `segment.py` |
| `meal_items` | MealItem | `nutrition.py` |
| `members` | Member | `membership.py` |
| `memberships` | Membership | `membership.py` |
| `messages` | Message | `chat.py` |
| `norm_entries` | NormEntry | `assessment.py` |
| `notifications` | Notification | `notification.py` |
| `nutrition_plans` | NutritionPlan | `nutrition.py` |
| `offers` | Offer | `admin.py` |
| `order_items` | OrderItem | `shop.py` |
| `orders` | Order | `shop.py` |
| `otp_codes` | OtpCode | `auth.py` |
| `outbox_dead_letters` | OutboxDeadLetter | `outbox.py` |
| `outbox_events` | OutboxEvent | `outbox.py` |
| `payment_gateway_configs` | PaymentGatewayConfig | `shop.py` |
| `payment_receipts` | PaymentReceipt | `payments.py` |
| `payments` | Payment | `payments.py` |
| `phone_change_challenges` | PhoneChangeChallenge | `auth.py` |
| `price_book` | PriceBook | `shop.py` |
| `product_categories` | ProductCategory | `shop.py` |
| `product_variants` | ProductVariant | `shop.py` |
| `products` | Product | `shop.py` |
| `program_exercises` | ProgramExercise | `programs.py` |
| `program_weeks` | ProgramWeek | `programs.py` |
| `progression_ladders` | ProgressionLadder | `content.py` |
| `progression_steps` | ProgressionStep | `content.py` |
| `refresh_tokens` | RefreshToken | `auth.py` |
| `report_runs` | ReportRun | `finance.py` |
| `rule_runs` | RuleRun | `ai.py` |
| `set_feedbacks` | SetFeedback | `programs.py` |
| `users` | User | `auth.py` |
| `wallet_transactions` | WalletTransaction | `payments.py` |
| `worker_heartbeats` | WorkerHeartbeat | `worker.py` |
| `workout_programs` | WorkoutProgram | `programs.py` |

### مهاجرت‌ها
38 مهاجرت Alembic. سرِ فعلی (head): `a7c3d9e1f2b4_g2_coupons.py`.
اعمال: `cd mp-app/backend && alembic upgrade head`.

## ۶. پیکربندی (متغیرهای محیط)
متغیرهای محیط با پیشوند `MP_` (مثلاً `MP_DATABASE_URL`). مقدار پیش‌فرض کد:

| کلید | پیش‌فرض |
|---|---|
| `MP_APP_NAME` | `"Muscle Paradise"` |
| `MP_ENVIRONMENT` | `"development"` |
| `MP_DATABASE_URL` | `"sqlite:///./mp.db"` |
| `MP_SECRET_KEY` | `DEFAULT_DEV_SECRET` |
| `MP_PUBLIC_BASE_URL` | `"http://127.0.0.1:8000"` |
| `MP_PAYMENT_GATEWAY` | `"manual"` |
| `MP_PAYMENT_SANDBOX` | `True` |
| `MP_SANDBOX_BANK_URL` | `"http://127.0.0.1:8088"` |
| `MP_SANDBOX_BANK_MERCHANT_ID` | `"SANDBOX-MERCHANT"` |
| `MP_BIOMETRIC_KEY` | `""` |
| `MP_ACCESS_TOKEN_MINUTES` | `30` |
| `MP_REFRESH_TOKEN_DAYS` | `14` |
| `MP_OTP_TTL_SECONDS` | `120` |
| `MP_SMS_PROVIDER` | `"dev"` |
| `MP_SMS_API_URL` | `""` |
| `MP_SMS_API_KEY` | `""` |
| `MP_SMS_USERNAME` | `""` |
| `MP_SMS_PASSWORD` | `""` |
| `MP_SMS_ORIGINATOR` | `""` |
| `MP_OTP_MAX_ATTEMPTS` | `5` |
| `MP_OTP_RATE_LIMIT` | `"10/minute"` |
| `MP_OTP_BURST_LIMIT` | `"3/second"` |
| `MP_LOGIN_RATE_LIMIT` | `"10/minute"` |
| `MP_RECEIPTS_DIR` | `"var/receipts"` |
| `MP_RECEIPT_MAX_BYTES` | `5 * 1024 * 1024` |
| `MP_RECEIPT_REVIEW_TTL_HOURS` | `48` |
| `MP_SHOP_WRITE_RATE_LIMIT` | `"30/minute"` |
| `MP_SHOP_CHECKOUT_RATE_LIMIT` | `"10/minute"` |
| `MP_SHOP_ONLINE_PURCHASE_ENABLED` | `False` |
| `MP_SHOP_TIMEZONE` | `"Asia/Tehran"` |
| `MP_TRUSTED_PROXIES` | `""` |
| `MP_REQUIRE_WORKER` | `False` |
| `MP_SHOP_OPEN_HOUR` | `7` |
| `MP_SHOP_CLOSE_HOUR` | `23` |
| `MP_SHOP_CLOSED_WEEKDAYS` | `""` |
| `MP_VALKEY_URL` | `"redis://localhost:6379/0"` |
| `MP_CORS_ORIGINS` | `(` |
| `MP_BACKEND_DIR` | `Path(__file__).resolve().parent.parent` |

## ۷. مجوزها
مجوزهای شناخته‌شده (کلید ناشناخته هرگز مجاز نیست). منبع: `app/security/grants.py`.

| مجوز | کاربرد |
|---|---|

## ۸. Studio (پنل مربی و مدیر)
| شناسهٔ صفحه | عنوان در منو | کامپوننت |
|---|---|---|
| `dashboard` | داشبورد | `Dashboard` |
| `members` | اعضا | `Members` |
| `programs` | برنامه‌ها | `Programs` |
| `nutrition` | تغذیه | `Nutrition` |
| `assessment` | ارزیابی | `Assessment` |
| `chat` | چت | `Chat` |
| `checkin` | حضور | `CheckIn` |
| `finance` | مالی | `Finance` |
| `expenses` | هزینه‌ها | `Expenses` |
| `analytics` | تحلیل‌ها | `Analytics` |
| `settings` | تنظیمات | `Settings` |
| `shop` | فروشگاه | `Shop` |

دسترسی هر صفحه بر اساس نقش در `src/lib/roleNav.ts` (تابع `canSeePage`) تعیین می‌شود. عنوان هر صفحه در `src/components/TopBar.tsx` است؛ تست `tests/topbarTitles.test.tsx` پوشش آن را نگه می‌دارد.

## ۹. اپ عضو (Flutter)
پوشه‌های ویژگی در `mp-app/client/lib/features/`: `assessment14`، `auth`، `bodycomp`، `chat`، `checkin`، `classes`، `feedback`، `home`، `intake`، `notifications`، `nutrition`، `profile`، `progress`، `shell`، `shop`، `today`، `wallet`.

نقطهٔ ورود: `lib/main.dart`. وضعیت بیلد: وب در CI (`web.yml`) ساخته می‌شود؛ APK امضاشده **BLOCKED** است تا اسرار `MP_ANDROID_*` تنظیم شوند.

## ۱۰. CI و انتشار
| فایل | نام | رویداد(ها) | jobs |
|---|---|---|---|
| ~~`apk.yml`~~ | mp-apk | (حذف‌شده با AD‑21، ۲۰۲۶‑۱۱‑۲۲) | — |
| `ci.yml` | mp-ci | pull_request, push | secret-scan, docs, backend, studio, client-flutter, live-contract, e2e-api, client-pinned |
| `client-format-fix.yml` | client-format-fix (M109) | push, workflow_dispatch | gitleaks-fingerprints, format-qr, format-client |
| `container.yml` | mp-container | push, workflow_dispatch | build-push |
| `deploy.yml` | mp-deploy | workflow_dispatch | preflight, build-and-push, deploy, rollback |
| `gitleaks-fingerprints.yml` | Gitleaks fingerprint audit | workflow_dispatch | gitleaks-fingerprints |
| `web.yml` | mp-web | workflow_dispatch | web |

گیت‌های `ci.yml`: `secret-scan`، `docs`، `backend` (pytest با `--cov-fail-under=70`)، `studio` (vitest، tsc، build)، `client-flutter`، `live-contract`، `e2e-api`، `client-pinned`.

## ۱۱. آخرین اعتبارسنجی و موانع
آخرین اجرای اندازه‌گیری‌شده روی `main` (مرجع: `qa-report/FINAL-REPORT.md`):

| بخش | نتیجه | نکته |
|---|---|---|
| backend pytest | ۱٬۰۹۵ پاس، ۲ skip، پوشش ۹۴٫۲۸٪ | اندازه‌گیری شده |
| studio vitest | ۲۸۲ پاس، ۹ skip | اندازه‌گیری شده |
| studio tsc / build | بدون خطا | اندازه‌گیری شده |
| مرورگر (۱۱ صفحه) | بدون خطای کنسول، ۴xx/۵xx یا استثنا | اسکرین‌شات‌ها در `docs/MuscleParadise/screenshots/` |
| دکمه‌ها | ۴۵ کلیک، ۰ خطا | دکمه‌های مالی و مخرب کلیک نشدند (با تست‌های یکپارچه پوشش داده شده‌اند) |
| interaction map | ۳۱ سطح، ۱۶۳ مسیر، رانش صفر | گیت `scripts/interaction_map.py --check` |
| مستندات | ۱۸ سند، ۲۷۶ لینک محلی | گیت `scripts/docs_gate.py` |

### موانع واقعی (BLOCKED)
- APK امضاشده: اسرار `MP_ANDROID_*` و متغیر `MP_ANDROID_CERT_SHA256` تنظیم نشده‌اند.
- اجرای Flutter در sandbox: `pub.dev` و `storage.googleapis.com` مسدودند؛ فقط در Codespace یا CI.
- دستگاه واقعی، پرداخت بانکی، push/SMS، Valkey، PostgreSQL، Prometheus: در دسترس نیستند.
- انیمیشن: فریم‌ریت روی دستگاه اندازه‌گیری نشده است.
- همزمانی کوپن روی PostgreSQL: تست نشده (فقط SQLite).

## ۱۲. کجا را تغییر دهم؟
| می‌خواهید تغییر دهید… | از اینجا شروع کنید |
|---|---|
| قرارداد API یا مسیر جدید | `mp-app/backend/api/routes.json` (تولیدشده) و روتر ماژول در `modules/<name>/router.py` |
| منطق پرداخت یا کوپن | `mp-app/backend/modules/payments/service.py`، `receipts.py`، `schemas.py` |
| مهاجرت دیتابیس | `mp-app/backend/db/migrations/versions/` (سرِ فعلی در بخش مهاجرت‌ها) |
| مدل داده | `mp-app/backend/db/models/*.py` |
| مجوز یا نقش | `mp-app/backend/app/security/grants.py`، `ownership.py`، `deps.py` |
| صفحهٔ Studio | `mp-app/studio/src/pages/` + ثبت در `App.tsx` + منو در `Sidebar.tsx` + عنوان در `TopBar.tsx` |
| دسترسی صفحه به نقش | `mp-app/studio/src/lib/roleNav.ts` |
| صفحهٔ اپ عضو | `mp-app/client/lib/features/<name>/` |
| گیت‌های CI | `.github/workflows/*.yml` (هرگز گیت را شُل نکنید؛ تست یا کد را اصلاح کنید) |
| متغیر محیط | `mp-app/backend/app/config.py` (پیشوند `MP_`) |
| بذر داده برای QA محلی | `qa-report/tools/seed_live.py` |
| بار و تست مرورگر | `qa-report/tools/locustfile.py`، `qa-report/tools/browser/` |


## ۱۳. کاستی‌ها و ادعاهای قدیمی
- **README** پیش‌تر ۱۲۱ مسیر و ۱۳۷ عملیات ذکر می‌کرد؛ عدد درست ۱۴۱ مسیر و ۱۶۳ عملیات است (منبع: `routes.json`).
- **README** پیش‌تر فقط بعضی workflowها را نام می‌برد؛ جدول بالا همهٔ فایل‌های `.github/workflows` را دارد.
- **`web.yml`** فقط `workflow_dispatch` دارد؛ `apk.yml` با AD‑21 حذف شد.
- **کیوسک / چک‌این** مسیر ناقص است و اتصال انتها‌به‌انتها کامل نشده است.
- **PostgreSQL، Valkey، pgBackRest، Prometheus** در نقشه‌اند و در این مخزن به‌صورت کامل اجرا و تأیید نشده‌اند.
- **تغذیه:** درخواست `nutrition/food-logs/member/-1/daily` با شناسهٔ placeholder `-1` ارسال می‌شود؛ باید بررسی شود.
- **بنر به‌روزرسانی** روی محتوای صفحه می‌افتد؛ ایموجی فوتر در فونت نمایش داده نمی‌شود.
- **استخر اتصال SQLite:** یک بار پر شد و ریشه‌یابی نشده است.
- **مستندات قدیمی** (`docs/MuscleParadise/`، گزارش‌های `finn/`) ممکن است به فایل‌های حذف‌شده اشاره کنند؛ `doc-drift` ۲۵ مورد از این دست یافته است.


## ۱۴. دیاگرام‌ها
- معماری: `docs/architecture/diagram-design/png/01-architecture.png`
- پرداخت، کوپن و رسید: `docs/architecture/diagram-design/png/02-payments-lifecycle.png`
- CI و انتشار: `docs/architecture/diagram-design/png/03-ci-release.png`
- منابع سازندهٔ دیاگرام‌ها: `docs/architecture/diagram-design/*.html` (HTML مستقل)
