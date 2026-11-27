# نقشهٔ سطح تعامل (فاز ۱ نقشه)

این صفحه از منابع واقعی ساخته می‌شود و با دست نوشته نشده است:

- `mp-app/studio/src/lib/api.ts` و `mp-app/studio/src/lib/adminApi.ts`
- `mp-app/client/lib/**` (فراخوانی `api.get|post|put|delete`)
- `mp-app/backend/api/routes.json`
- `mp-app/studio/tests/*.test.*` و `mp-app/client/test/**`

بازتولید و گیت:

```bash
python3 scripts/interaction_map.py
python3 scripts/interaction_map.py --check
```

| سنجه | مقدار |
|---|---|
| مسیر قرارداد API | 163 |
| صفحهٔ استودیو | 14 |
| ویژگی کلاینت | 18 |
| endpoint یکتای استفاده‌شده | 94 |
| سطح بی‌تست | 6 |

## گپ‌های قرارداد

- هیچ: هر endpointی که کلاینت صدا می‌زند در قرارداد هست.

## سطح‌های بی‌تست

- client-feature:auth
- client-feature:core
- client-feature:intake
- client-feature:progress
- studio-page:Analytics
- studio-page:Members

## استودیو

### Analytics

دکمه 0 · ورودی 0 · عدد 0 · انتخاب 0 · دیالوگ 0

| متد | مسیر | guard | نقش‌ها | در قرارداد |
|---|---|---|---|---|
| GET | `/api/v1/admin/analytics/churn-risk` | permission | manager, admin, super_admin | بله |
| GET | `/api/v1/admin/analytics/leaderboards` | permission | manager, admin, super_admin | بله |

تست: **ندارد**

### Assessment

دکمه 2 · ورودی 0 · عدد 0 · انتخاب 0 · دیالوگ 0

| متد | مسیر | guard | نقش‌ها | در قرارداد |
|---|---|---|---|---|
| GET | `/api/v1/assessments/jp7/member/*/trend` | permission | member, coach, manager, admin, super_admin | بله |
| POST | `/api/v1/assessments/limb` | permission | member, coach, manager, admin, super_admin | بله |
| GET | `/api/v1/assessments/limb/member/*/report` | permission | member, coach, manager, admin, super_admin | بله |
| GET | `/api/v1/notifications/reminders/member/*` | permission | member, coach, reception, manager, admin, super_admin | بله |

تست: `mp-app/studio/tests/jp7Trend.test.tsx`

### Chat

دکمه 5 · ورودی 0 · عدد 0 · انتخاب 0 · دیالوگ 0

| متد | مسیر | guard | نقش‌ها | در قرارداد |
|---|---|---|---|---|
| GET | `/api/v1/chat/conversations` | permission | member, coach, manager, admin, super_admin | بله |
| POST | `/api/v1/chat/conversations` | permission | member, coach, manager, admin, super_admin | بله |
| GET | `/api/v1/chat/conversations/*/messages` | permission | member, coach, manager, admin, super_admin | بله |
| POST | `/api/v1/chat/conversations/*/messages` | permission | member, coach, manager, admin, super_admin | بله |
| POST | `/api/v1/chat/conversations/*/read` | permission | member, coach, manager, admin, super_admin | بله |

تست: `mp-app/studio/tests/chatPage.test.tsx`

### CheckIn

دکمه 1 · ورودی 0 · عدد 0 · انتخاب 0 · دیالوگ 0

| متد | مسیر | guard | نقش‌ها | در قرارداد |
|---|---|---|---|---|
| GET | `/api/v1/admin/checkins` | permission | coach, reception, manager, admin, super_admin | بله |

تست: `mp-app/studio/tests/checkInPage.test.tsx`

### Dashboard

دکمه 1 · ورودی 0 · عدد 0 · انتخاب 0 · دیالوگ 0

| متد | مسیر | guard | نقش‌ها | در قرارداد |
|---|---|---|---|---|
| GET | `/api/v1/admin/attendance` | permission | coach, reception, manager, admin, super_admin | بله |
| GET | `/api/v1/admin/kpis` | permission | manager, admin, super_admin | بله |
| GET | `/api/v1/admin/members-summary` | permission | coach, reception, manager, admin, super_admin | بله |

تست: `mp-app/studio/tests/dashboard.test.tsx`

### Expenses

دکمه 0 · ورودی 4 · عدد 2 · انتخاب 1 · دیالوگ 2

| متد | مسیر | guard | نقش‌ها | در قرارداد |
|---|---|---|---|---|
| GET | `/api/v1/expenses` | grant:finance.read, permission | manager, admin, super_admin | بله |
| POST | `/api/v1/expenses` | grant:finance.write, permission | manager, admin, super_admin | بله |
| GET | `/api/v1/expenses/*/receipt` | grant:finance.read, permission | manager, admin, super_admin | بله |
| POST | `/api/v1/expenses/*/receipt` | grant:finance.write, permission | manager, admin, super_admin | بله |

تست: `mp-app/studio/tests/expenseReceipt.test.tsx`، `mp-app/studio/tests/expensesPage.test.tsx`

### Finance

دکمه 10 · ورودی 6 · عدد 1 · انتخاب 2 · دیالوگ 2

| متد | مسیر | guard | نقش‌ها | در قرارداد |
|---|---|---|---|---|
| GET | `/api/v1/finance/reports/period` | grant:finance.read, permission | manager, admin, super_admin | بله |
| GET | `/api/v1/payments` | permission | member, reception, manager, admin, super_admin | بله |
| POST | `/api/v1/payments` | permission | member, reception, manager, admin, super_admin | بله |
| POST | `/api/v1/payments/*/approve` | grant:finance.write, permission | reception, manager, admin, super_admin | بله |
| POST | `/api/v1/payments/*/fail` | permission | reception, manager, admin, super_admin | بله |
| GET | `/api/v1/payments/*/receipt` | permission | member, reception, manager, admin, super_admin | بله |
| POST | `/api/v1/payments/*/refund` | grant:finance.write, permission, roles | manager, admin, super_admin | بله |
| POST | `/api/v1/payments/*/reject` | grant:finance.write, permission | reception, manager, admin, super_admin | بله |
| POST | `/api/v1/payments/*/verify` | grant:finance.write, permission | reception, manager, admin, super_admin | بله |
| GET | `/api/v1/payments/coupons` | grant:finance.write, permission | member, reception, manager, admin, super_admin | بله |
| POST | `/api/v1/payments/coupons` | grant:finance.write, permission | reception, manager, admin, super_admin | بله |
| POST | `/api/v1/payments/finance/commission` | permission | manager, admin, super_admin | بله |
| GET | `/api/v1/payments/finance/summary` | permission | manager, admin, super_admin | بله |
| GET | `/api/v1/payments/ledger/*` | permission | member, reception, manager, admin, super_admin | بله |

تست: `mp-app/studio/tests/financePage.test.tsx`

### Login

دکمه 3 · ورودی 0 · عدد 0 · انتخاب 0 · دیالوگ 0

بدون فراخوانی API در این صفحه و کامپوننت‌هایش.

تست: `mp-app/studio/tests/login.test.tsx`

### MemberAccount

دکمه 7 · ورودی 0 · عدد 0 · انتخاب 0 · دیالوگ 2

| متد | مسیر | guard | نقش‌ها | در قرارداد |
|---|---|---|---|---|
| GET | `/api/v1/members/*/memberships` | permission | member, coach, reception, manager, admin, super_admin | بله |
| GET | `/api/v1/members/me` | permission | member, coach, reception, manager, admin, super_admin | بله |

تست: `mp-app/studio/tests/memberAccountPage.test.tsx`

### Members

دکمه 4 · ورودی 0 · عدد 0 · انتخاب 0 · دیالوگ 0

| متد | مسیر | guard | نقش‌ها | در قرارداد |
|---|---|---|---|---|
| GET | `/api/v1/admin/members-summary` | permission | coach, reception, manager, admin, super_admin | بله |
| POST | `/api/v1/ai/program/generate` | permission | member, coach, manager, admin, super_admin | بله |
| GET | `/api/v1/axis-assessments/*/matrix` | permission | member, coach, manager, admin, super_admin | بله |
| GET | `/api/v1/axis-assessments/member/*` | permission | member, coach, manager, admin, super_admin | بله |

تست: **ندارد**

### Nutrition

دکمه 6 · ورودی 0 · عدد 0 · انتخاب 1 · دیالوگ 0

| متد | مسیر | guard | نقش‌ها | در قرارداد |
|---|---|---|---|---|
| POST | `/api/v1/nutrition/food-logs` | permission | member, coach, manager, admin, super_admin | بله |
| GET | `/api/v1/nutrition/food-logs/member/*/daily` | permission | member, coach, manager, admin, super_admin | بله |
| GET | `/api/v1/nutrition/foods` | permission | member, coach, manager, admin, super_admin | بله |
| GET | `/api/v1/nutrition/member/*/adaptive` | permission | member, coach, manager, admin, super_admin | بله |
| POST | `/api/v1/nutrition/weight-logs` | permission | member, coach, manager, admin, super_admin | بله |

تست: `mp-app/studio/tests/nutritionNoMemberSentinel.test.tsx`، `mp-app/studio/tests/nutritionPage.test.tsx`

### Programs

دکمه 9 · ورودی 0 · عدد 0 · انتخاب 0 · دیالوگ 0

| متد | مسیر | guard | نقش‌ها | در قرارداد |
|---|---|---|---|---|
| POST | `/api/v1/ai/suggest-weight` | permission | member, coach, manager, admin, super_admin | بله |
| GET | `/api/v1/library/exercises` | permission | member, coach, manager, admin, super_admin | بله |
| GET | `/api/v1/programs` | permission | coach, reception, manager, admin, super_admin | بله |
| POST | `/api/v1/programs/*/approve` | permission | coach, manager, admin, super_admin | بله |
| POST | `/api/v1/programs/*/reject` | permission | coach, manager, admin, super_admin | بله |
| GET | `/api/v1/programs/member/*/readiness` | permission | member, coach, manager, admin, super_admin | بله |
| GET | `/api/v1/programs/member/*/volume` | permission | member, coach, manager, admin, super_admin | بله |

تست: `mp-app/studio/tests/programsPage.test.tsx`

### Settings

دکمه 2 · ورودی 0 · عدد 0 · انتخاب 4 · دیالوگ 0

| متد | مسیر | guard | نقش‌ها | در قرارداد |
|---|---|---|---|---|
| GET | `/api/v1/admin/audit` | permission | manager, admin, super_admin | بله |
| GET | `/api/v1/admin/flags` | permission | manager, admin, super_admin | بله |
| PUT | `/api/v1/admin/flags` | permission | manager, admin, super_admin | بله |
| GET | `/api/v1/admin/permissions` | permission | super_admin | بله |
| POST | `/api/v1/admin/permissions` | permission | super_admin | بله |
| DELETE | `/api/v1/admin/permissions/*` | permission | super_admin | بله |
| GET | `/api/v1/admin/permissions/known` | permission | super_admin | بله |
| GET | `/api/v1/admin/users` | permission | super_admin | بله |
| DELETE | `/api/v1/admin/users/*/role` | permission | super_admin | بله |
| POST | `/api/v1/admin/users/*/role` | permission | super_admin | بله |
| GET | `/api/v1/auth/sessions` | authenticated | member, coach, reception, manager, admin, super_admin | بله |

تست: `mp-app/studio/tests/settingsRole.test.tsx`

### Shop

دکمه 17 · ورودی 9 · عدد 5 · انتخاب 5 · دیالوگ 2

بدون فراخوانی API در این صفحه و کامپوننت‌هایش.

تست: `mp-app/studio/tests/shopPage.test.tsx`

## کلاینت

| ویژگی | endpoint | guard | نقش‌ها | در قرارداد | تست |
|---|---|---|---|---|---|
| assessment14 | `GET /api/v1/axis-assessments/*/matrix` | permission | member, coach, manager, admin, super_admin | بله | 1 فایل |
| assessment14 | `GET /api/v1/axis-assessments/member/*` | permission | member, coach, manager, admin, super_admin | بله | 1 فایل |
| assessment14 | `POST /api/v1/axis-assessments` | permission | coach, manager, admin, super_admin | بله | 1 فایل |
| auth | `POST /api/v1/auth/otp/request` | — | member, coach, reception, manager, admin, super_admin | بله | **ندارد** |
| bodycomp | `GET /api/v1/assessments/jp7/member/*/trend` | permission | member, coach, manager, admin, super_admin | بله | 1 فایل |
| chat | `GET /api/v1/chat/conversations` | permission | member, coach, manager, admin, super_admin | بله | 1 فایل |
| chat | `GET /api/v1/chat/conversations/*/messages` | permission | member, coach, manager, admin, super_admin | بله | 1 فایل |
| chat | `POST /api/v1/chat/conversations/*/messages` | permission | member, coach, manager, admin, super_admin | بله | 1 فایل |
| chat | `POST /api/v1/chat/conversations/*/read` | permission | member, coach, manager, admin, super_admin | بله | 1 فایل |
| checkin | `GET /api/v1/face/privacy-notice` | permission | member, coach, reception, manager, admin, super_admin | بله | 3 فایل |
| checkin | `GET /api/v1/face/qr-token` | permission | member, coach, manager, admin, super_admin | بله | 3 فایل |
| checkin | `GET /api/v1/members/me/checkins` | permission | member, coach, reception, manager, admin, super_admin | بله | 3 فایل |
| checkin | `GET /api/v1/members/me/face-consent` | permission | member, coach, reception, manager, admin, super_admin | بله | 3 فایل |
| checkin | `POST /api/v1/face/consent` | permission | member, coach, reception, manager, admin, super_admin | بله | 3 فایل |
| classes | — | — | — | — | دارد |
| feedback | `POST /api/v1/programs/set-feedback` | permission | member, coach, manager, admin, super_admin | بله | 2 فایل |
| home | — | — | — | — | دارد |
| intake | `GET /api/v1/members/me` | permission | member, coach, reception, manager, admin, super_admin | بله | **ندارد** |
| intake | `POST /api/v1/ai/nutrition/generate` | permission | member, coach, manager, admin, super_admin | بله | **ندارد** |
| intake | `POST /api/v1/ai/program/generate` | permission | member, coach, manager, admin, super_admin | بله | **ندارد** |
| intake | `POST /api/v1/population/gate-check` | permission | member, coach, reception, manager, admin, super_admin | بله | **ندارد** |
| intake | `PUT /api/v1/members/me` | permission | member, coach, reception, manager, admin, super_admin | بله | **ندارد** |
| notifications | — | — | — | — | دارد |
| nutrition | — | — | — | — | دارد |
| profile | `GET /api/v1/members/me` | permission | member, coach, reception, manager, admin, super_admin | بله | 2 فایل |
| profile | `POST /api/v1/auth/phone-change/confirm` | authenticated | member, coach, reception, manager, admin, super_admin | بله | 2 فایل |
| profile | `POST /api/v1/auth/phone-change/request` | authenticated | member, coach, reception, manager, admin, super_admin | بله | 2 فایل |
| profile | `POST /api/v1/auth/phone-change/verify-old` | authenticated | member, coach, reception, manager, admin, super_admin | بله | 2 فایل |
| profile | `PUT /api/v1/members/me` | permission | member, coach, reception, manager, admin, super_admin | بله | 2 فایل |
| progress | `GET /api/v1/assessments/member/*` | permission | member, coach, manager, admin, super_admin | بله | **ندارد** |
| shell | — | — | — | — | **ندارد** |
| shop | `DELETE /api/v1/shop/cart/*` | permission | member, reception, manager, admin, super_admin | بله | 2 فایل |
| shop | `POST /api/v1/shop/cart` | permission | member, reception, manager, admin, super_admin | بله | 2 فایل |
| shop | `POST /api/v1/shop/checkout` | permission | member, reception, manager, admin, super_admin | بله | 2 فایل |
| today | — | — | — | — | دارد |
| wallet | `GET /api/v1/payments/wallet/*/transactions` | permission | member, reception, manager, admin, super_admin | بله | 1 فایل |
| core | `GET /api/v1/classes` | permission | member, coach, reception, manager, admin, super_admin | بله | **ندارد** |
| core | `GET /api/v1/members/*/memberships` | permission | member, coach, reception, manager, admin, super_admin | بله | **ندارد** |
| core | `GET /api/v1/members/me` | permission | member, coach, reception, manager, admin, super_admin | بله | **ندارد** |
| core | `GET /api/v1/nutrition/food-logs/member/*/daily` | permission | member, coach, manager, admin, super_admin | بله | **ندارد** |
| core | `GET /api/v1/nutrition/foods` | permission | member, coach, manager, admin, super_admin | بله | **ندارد** |
| core | `GET /api/v1/nutrition/plans/member/*` | permission | member, coach, manager, admin, super_admin | بله | **ندارد** |
| core | `GET /api/v1/payments` | permission | member, reception, manager, admin, super_admin | بله | **ندارد** |
| core | `GET /api/v1/payments/wallet/*` | permission | member, reception, manager, admin, super_admin | بله | **ندارد** |
| core | `GET /api/v1/programs/member/*` | permission | member, coach, manager, admin, super_admin | بله | **ندارد** |
| core | `GET /api/v1/shop/cart` | permission | member, coach, reception, manager, admin, super_admin | بله | **ندارد** |
| core | `GET /api/v1/shop/categories` | permission | member, coach, reception, manager, admin, super_admin | بله | **ندارد** |
| core | `GET /api/v1/shop/gateways` | permission | member, coach, reception, manager, admin, super_admin | بله | **ندارد** |
| core | `GET /api/v1/shop/orders` | permission | member, coach, reception, manager, admin, super_admin | بله | **ندارد** |
| core | `GET /api/v1/shop/orders/*/receipt` | permission | member, coach, reception, manager, admin, super_admin | بله | **ندارد** |
| core | `GET /api/v1/shop/products` | permission | member, coach, reception, manager, admin, super_admin | بله | **ندارد** |
| core | `POST /api/v1/auth/logout` | — | member, coach, reception, manager, admin, super_admin | بله | **ندارد** |
| core | `POST /api/v1/auth/otp/verify` | — | member, coach, reception, manager, admin, super_admin | بله | **ندارد** |
| core | `POST /api/v1/auth/refresh` | — | member, coach, reception, manager, admin, super_admin | بله | **ندارد** |
| core | `POST /api/v1/programs/sync/set-feedback` | permission | member, coach, manager, admin, super_admin | بله | **ندارد** |

## پوشش نقش‌ها

| نقش | تعداد endpoint | نمونهٔ سطح‌ها |
|---|---|---|
| admin | 104 | Analytics، Assessment، Chat، CheckIn، Dashboard، Expenses |
| coach | 74 | Assessment، Chat، CheckIn، Dashboard، MemberAccount، Members |
| manager | 104 | Analytics، Assessment، Chat، CheckIn، Dashboard، Expenses |
| member | 77 | Assessment، Chat، Finance، MemberAccount، Members، Nutrition |
| reception | 50 | Assessment، CheckIn، Dashboard، Finance، MemberAccount، Members |
| super_admin | 111 | Analytics، Assessment، Chat، CheckIn، Dashboard، Expenses |

## محدودیت صریح

- نقش‌ها از `routes.json` می‌آید، نه از خواندن UI؛ پس «چه کسی دکمه را می‌بیند» هنوز دستی مرور می‌شود.
- جدول DB از این نقشه بیرون است: مسیر ← جدول نیاز به ردیابی مدل دارد و ادعای خودکار نمی‌کنیم.
- کامپوننت‌ها فقط یک سطح از صفحه‌ها باز می‌شوند؛ کامپوننت تودرتوی عمیق‌تر ممکن است دیده نشود.
