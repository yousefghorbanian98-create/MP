# فهرست کامل ریپو و سطوح ممیزی

> تولیدشده با `scripts/build_audit_inventory.py` — **دستی ویرایش نکنید.**

این فهرست همهٔ فایل‌های ترک‌شده، همهٔ مسیرهای API (از دکوراتورها)، همهٔ صفحه‌های استودیو با تعداد دکمه/هندلر، و همهٔ workflowها را ثبت می‌کند.
ستون «بازبینی» نشان می‌دهد هر فایل تا کنون خط‌به‌خط بازبینی شده یا نه؛ در این مرحله همه `NOT-REVIEWED` هستند.

## ۱. خلاصهٔ تعداد فایل

- کل فایل‌های ترک‌شده: **1350** (خطوط متنی: 267677)

| ناحیه | تعداد فایل | خطوط متنی |
|---|---|---|
| CI/CD | 6 | 1400 |
| استودیو (React) | 122 | 26329 |
| اسکریپت و ابزار | 19 | 7347 |
| اپ عضو (Flutter) | 114 | 19319 |
| بک‌اند (FastAPI) | 558 | 91507 |
| ریشه و تنظیمات | 12 | 1527 |
| زیرساخت و کانتینر | 15 | 597 |
| سایر mp-app | 4 | 239 |
| شواهد QA | 40 | 1626 |
| مستندات | 319 | 109461 |
| گزارش‌های عامل | 141 | 8325 |

## ۲. عملیات API (از `app.openapi()`، مرجع اصلی)

مسیرها: **141**؛ عملیات (روش×مسیر): **163**.

| روش | مسیر |
|---|---|
| DELETE | `/api/v1/admin/permissions/{grant_id}` |
| DELETE | `/api/v1/admin/users/{user_id}/role` |
| DELETE | `/api/v1/auth/sessions/{session_id}` |
| DELETE | `/api/v1/expenses/{expense_id}` |
| DELETE | `/api/v1/face/enroll/{member_id}` |
| DELETE | `/api/v1/shop/cart/{item_id}` |
| GET | `/api/v1/admin/analytics/churn-risk` |
| GET | `/api/v1/admin/analytics/leaderboards` |
| GET | `/api/v1/admin/attendance` |
| GET | `/api/v1/admin/audit` |
| GET | `/api/v1/admin/checkins` |
| GET | `/api/v1/admin/flags` |
| GET | `/api/v1/admin/flags/{key}` |
| GET | `/api/v1/admin/kpis` |
| GET | `/api/v1/admin/members-summary` |
| GET | `/api/v1/admin/permissions` |
| GET | `/api/v1/admin/permissions/known` |
| GET | `/api/v1/admin/retention` |
| GET | `/api/v1/admin/users` |
| GET | `/api/v1/assessments/jp7/member/{member_id}/trend` |
| GET | `/api/v1/assessments/limb/member/{member_id}/report` |
| GET | `/api/v1/assessments/member/{member_id}` |
| GET | `/api/v1/assessments/{assessment_id}` |
| GET | `/api/v1/auth/sessions` |
| GET | `/api/v1/axis-assessments/member/{member_id}` |
| GET | `/api/v1/axis-assessments/{assessment_id}/matrix` |
| GET | `/api/v1/chat/conversations` |
| GET | `/api/v1/chat/conversations/{conversation_id}/messages` |
| GET | `/api/v1/classes` |
| GET | `/api/v1/expenses` |
| GET | `/api/v1/expenses/{expense_id}/receipt` |
| GET | `/api/v1/face/deep-status` |
| GET | `/api/v1/face/privacy-notice` |
| GET | `/api/v1/face/qr-token` |
| GET | `/api/v1/finance/reports/daily/{run_date}` |
| GET | `/api/v1/finance/reports/period` |
| GET | `/api/v1/finance/reports/schedule` |
| GET | `/api/v1/health/ready` |
| GET | `/api/v1/library/exercises` |
| GET | `/api/v1/library/exercises/{exercise_id}` |
| GET | `/api/v1/members` |
| GET | `/api/v1/members/me` |
| GET | `/api/v1/members/me/checkins` |
| GET | `/api/v1/members/me/face-consent` |
| GET | `/api/v1/members/memberships/plans` |
| GET | `/api/v1/members/memberships/{membership_id}/invoice` |
| GET | `/api/v1/members/{member_id}` |
| GET | `/api/v1/members/{member_id}/memberships` |
| GET | `/api/v1/metrics` |
| GET | `/api/v1/notifications/member/{member_id}` |
| GET | `/api/v1/notifications/reminders/member/{member_id}` |
| GET | `/api/v1/nutrition/food-logs/member/{member_id}/daily` |
| GET | `/api/v1/nutrition/foods` |
| GET | `/api/v1/nutrition/member/{member_id}/adaptive` |
| GET | `/api/v1/nutrition/plans/member/{member_id}` |
| GET | `/api/v1/payments` |
| GET | `/api/v1/payments/coupons` |
| GET | `/api/v1/payments/finance/export.csv` |
| GET | `/api/v1/payments/finance/summary` |
| GET | `/api/v1/payments/invoice/{member_id}` |
| GET | `/api/v1/payments/ledger/{member_id}` |
| GET | `/api/v1/payments/wallet/{member_id}` |
| GET | `/api/v1/payments/wallet/{member_id}/transactions` |
| GET | `/api/v1/payments/{payment_id}/gateway-return` |
| GET | `/api/v1/payments/{payment_id}/receipt` |
| GET | `/api/v1/population/paths` |
| GET | `/api/v1/programs` |
| GET | `/api/v1/programs/member/{member_id}` |
| GET | `/api/v1/programs/member/{member_id}/readiness` |
| GET | `/api/v1/programs/member/{member_id}/volume` |
| GET | `/api/v1/programs/{program_id}` |
| GET | `/api/v1/reports/confidential/{member_id}` |
| GET | `/api/v1/shop/cart` |
| GET | `/api/v1/shop/categories` |
| GET | `/api/v1/shop/change-requests` |
| GET | `/api/v1/shop/gateways` |
| GET | `/api/v1/shop/orders` |
| GET | `/api/v1/shop/orders/{order_id}/receipt` |
| GET | `/api/v1/shop/prices` |
| GET | `/api/v1/shop/products` |
| GET | `/api/v1/shop/products/{product_id}` |
| GET | `/api/v1/shop/status` |
| GET | `/api/v1/updates/manifest` |
| GET | `/health` |
| PATCH | `/api/v1/expenses/{expense_id}` |
| PATCH | `/api/v1/members/{member_id}` |
| PATCH | `/api/v1/shop/cart/{item_id}` |
| PATCH | `/api/v1/shop/orders/{order_id}` |
| PATCH | `/api/v1/shop/products/{product_id}` |
| POST | `/api/v1/admin/permissions` |
| POST | `/api/v1/admin/retention/run` |
| POST | `/api/v1/admin/users/{user_id}/role` |
| POST | `/api/v1/ai/nutrition/generate` |
| POST | `/api/v1/ai/program/generate` |
| POST | `/api/v1/ai/suggest-weight` |
| POST | `/api/v1/assessments` |
| POST | `/api/v1/assessments/jp7` |
| POST | `/api/v1/assessments/limb` |
| POST | `/api/v1/auth/logout` |
| POST | `/api/v1/auth/logout-all` |
| POST | `/api/v1/auth/otp/request` |
| POST | `/api/v1/auth/otp/verify` |
| POST | `/api/v1/auth/phone-change/confirm` |
| POST | `/api/v1/auth/phone-change/request` |
| POST | `/api/v1/auth/phone-change/verify-old` |
| POST | `/api/v1/auth/refresh` |
| POST | `/api/v1/axis-assessments` |
| POST | `/api/v1/axis-assessments/{assessment_id}/review` |
| POST | `/api/v1/chat/conversations` |
| POST | `/api/v1/chat/conversations/{conversation_id}/messages` |
| POST | `/api/v1/chat/conversations/{conversation_id}/read` |
| POST | `/api/v1/classes` |
| POST | `/api/v1/classes/book` |
| POST | `/api/v1/classes/cancel` |
| POST | `/api/v1/expenses` |
| POST | `/api/v1/expenses/{expense_id}/receipt` |
| POST | `/api/v1/face/checkin` |
| POST | `/api/v1/face/checkin-qr` |
| POST | `/api/v1/face/checkins/{checkin_id}/exit` |
| POST | `/api/v1/face/consent` |
| POST | `/api/v1/face/consent/revoke` |
| POST | `/api/v1/face/enroll` |
| POST | `/api/v1/finance/reports/schedule/{job_key}/run` |
| POST | `/api/v1/members` |
| POST | `/api/v1/members/memberships` |
| POST | `/api/v1/members/memberships/from-plan` |
| POST | `/api/v1/notifications` |
| POST | `/api/v1/notifications/{notification_id}/read` |
| POST | `/api/v1/nutrition/food-logs` |
| POST | `/api/v1/nutrition/plans` |
| POST | `/api/v1/nutrition/plans/{plan_id}/approve` |
| POST | `/api/v1/nutrition/weight-logs` |
| POST | `/api/v1/payments` |
| POST | `/api/v1/payments/coupons` |
| POST | `/api/v1/payments/finance/commission` |
| POST | `/api/v1/payments/ledger/{entry_id}/reverse` |
| POST | `/api/v1/payments/wallet/charge` |
| POST | `/api/v1/payments/wallet/pay` |
| POST | `/api/v1/payments/{payment_id}/approve` |
| POST | `/api/v1/payments/{payment_id}/callback` |
| POST | `/api/v1/payments/{payment_id}/fail` |
| POST | `/api/v1/payments/{payment_id}/receipt` |
| POST | `/api/v1/payments/{payment_id}/refund` |
| POST | `/api/v1/payments/{payment_id}/reject` |
| POST | `/api/v1/payments/{payment_id}/start` |
| POST | `/api/v1/payments/{payment_id}/verify` |
| POST | `/api/v1/population/gate-check` |
| POST | `/api/v1/population/intake/next` |
| POST | `/api/v1/programs/from-engine` |
| POST | `/api/v1/programs/set-feedback` |
| POST | `/api/v1/programs/sync/set-feedback` |
| POST | `/api/v1/programs/{program_id}/approve` |
| POST | `/api/v1/programs/{program_id}/reject` |
| POST | `/api/v1/shop/cart` |
| POST | `/api/v1/shop/change-requests` |
| POST | `/api/v1/shop/change-requests/{request_id}/review` |
| POST | `/api/v1/shop/checkout` |
| POST | `/api/v1/shop/gateways` |
| POST | `/api/v1/shop/prices` |
| POST | `/api/v1/shop/products` |
| PUT | `/api/v1/admin/flags` |
| PUT | `/api/v1/members/me` |
| PUT | `/api/v1/shop/gateways/{gateway_id}` |

### ۲-الف. دکوراتورهای `@router.*` (ایستا)

تعداد دکوراتورهای مسیر در فایل‌ها: **97**.

| روش | مسیر کامل | فایل | خط |
|---|---|---|---|
| GET | `/health/ready` | `mp-app/backend/api/v1/monitoring.py` | 88 |
| GET | `/admin/audit` | `mp-app/backend/modules/admin/router.py` | 16 |
| GET | `/admin/flags/{key}` | `mp-app/backend/modules/admin/router.py` | 28 |
| PUT | `/admin/flags` | `mp-app/backend/modules/admin/router.py` | 33 |
| GET | `/admin/analytics/churn-risk` | `mp-app/backend/modules/admin/router.py` | 57 |
| GET | `/admin/kpis` | `mp-app/backend/modules/admin/router.py` | 66 |
| GET | `/admin/attendance` | `mp-app/backend/modules/admin/router.py` | 74 |
| GET | `/admin/checkins` | `mp-app/backend/modules/admin/router.py` | 84 |
| GET | `/admin/members-summary` | `mp-app/backend/modules/admin/router.py` | 94 |
| GET | `/admin/permissions` | `mp-app/backend/modules/admin/router.py` | 118 |
| GET | `/admin/permissions/known` | `mp-app/backend/modules/admin/router.py` | 125 |
| POST | `/admin/permissions` | `mp-app/backend/modules/admin/router.py` | 134 |
| DELETE | `/admin/permissions/{grant_id}` | `mp-app/backend/modules/admin/router.py` | 148 |
| GET | `/admin/users` | `mp-app/backend/modules/admin/router.py` | 155 |
| POST | `/admin/users/{user_id}/role` | `mp-app/backend/modules/admin/router.py` | 164 |
| DELETE | `/admin/users/{user_id}/role` | `mp-app/backend/modules/admin/router.py` | 171 |
| POST | `/assessments` | `mp-app/backend/modules/assessment/router.py` | 22 |
| GET | `/assessments/{assessment_id}` | `mp-app/backend/modules/assessment/router.py` | 32 |
| POST | `/assessments/jp7` | `mp-app/backend/modules/assessment/router.py` | 46 |
| POST | `/assessments/limb` | `mp-app/backend/modules/assessment/router.py` | 73 |
| POST | `/auth/otp/verify` | `mp-app/backend/modules/auth/router.py` | 73 |
| POST | `/auth/refresh` | `mp-app/backend/modules/auth/router.py` | 120 |
| POST | `/auth/logout` | `mp-app/backend/modules/auth/router.py` | 126 |
| GET | `/auth/sessions` | `mp-app/backend/modules/auth/router.py` | 131 |
| DELETE | `/auth/sessions/{session_id}` | `mp-app/backend/modules/auth/router.py` | 145 |
| POST | `/axis-assessments` | `mp-app/backend/modules/axis_assessment/router.py` | 18 |
| GET | `/axis-assessments/member/{member_id}` | `mp-app/backend/modules/axis_assessment/router.py` | 36 |
| POST | `/axis-assessments/{assessment_id}/review` | `mp-app/backend/modules/axis_assessment/router.py` | 41 |
| POST | `/face/consent` | `mp-app/backend/modules/face_id/router.py` | 25 |
| POST | `/face/consent/revoke` | `mp-app/backend/modules/face_id/router.py` | 30 |
| POST | `/face/enroll` | `mp-app/backend/modules/face_id/router.py` | 35 |
| DELETE | `/face/enroll/{member_id}` | `mp-app/backend/modules/face_id/router.py` | 41 |
| POST | `/face/checkin` | `mp-app/backend/modules/face_id/router.py` | 46 |
| GET | `/face/privacy-notice` | `mp-app/backend/modules/face_id/router.py` | 54 |
| GET | `/face/deep-status` | `mp-app/backend/modules/face_id/router.py` | 62 |
| GET | `/face/qr-token` | `mp-app/backend/modules/face_id/router.py` | 70 |
| POST | `/face/checkin-qr` | `mp-app/backend/modules/face_id/router.py` | 83 |
| POST | `/face/checkins/{checkin_id}/exit` | `mp-app/backend/modules/face_id/router.py` | 128 |
| POST | `/members` | `mp-app/backend/modules/membership/router.py` | 26 |
| GET | `/members` | `mp-app/backend/modules/membership/router.py` | 40 |
| GET | `/members/me` | `mp-app/backend/modules/membership/router.py` | 81 |
| GET | `/members/me/checkins` | `mp-app/backend/modules/membership/router.py` | 94 |
| PUT | `/members/me` | `mp-app/backend/modules/membership/router.py` | 108 |
| GET | `/members/memberships/plans` | `mp-app/backend/modules/membership/router.py` | 158 |
| POST | `/members/memberships/from-plan` | `mp-app/backend/modules/membership/router.py` | 165 |
| GET | `/members/memberships/{membership_id}/invoice` | `mp-app/backend/modules/membership/router.py` | 170 |
| GET | `/members/{member_id}` | `mp-app/backend/modules/membership/router.py` | 177 |
| PATCH | `/members/{member_id}` | `mp-app/backend/modules/membership/router.py` | 182 |
| GET | `/chat/conversations` | `mp-app/backend/modules/notification/chat_router.py` | 24 |
| POST | `/chat/conversations` | `mp-app/backend/modules/notification/chat_router.py` | 29 |
| GET | `/chat/conversations/{conversation_id}/messages` | `mp-app/backend/modules/notification/chat_router.py` | 40 |
| POST | `/chat/conversations/{conversation_id}/messages` | `mp-app/backend/modules/notification/chat_router.py` | 45 |
| POST | `/chat/conversations/{conversation_id}/read` | `mp-app/backend/modules/notification/chat_router.py` | 52 |
| POST | `/notifications` | `mp-app/backend/modules/notification/router.py` | 16 |
| GET | `/notifications/member/{member_id}` | `mp-app/backend/modules/notification/router.py` | 21 |
| POST | `/notifications/{notification_id}/read` | `mp-app/backend/modules/notification/router.py` | 31 |
| POST | `/nutrition/plans` | `mp-app/backend/modules/nutrition/router.py` | 24 |
| POST | `/nutrition/plans/{plan_id}/approve` | `mp-app/backend/modules/nutrition/router.py` | 29 |
| POST | `/payments` | `mp-app/backend/modules/payments/router.py` | 41 |
| POST | `/payments/{payment_id}/fail` | `mp-app/backend/modules/payments/router.py` | 165 |
| GET | `/payments` | `mp-app/backend/modules/payments/router.py` | 179 |
| POST | `/payments/wallet/pay` | `mp-app/backend/modules/payments/router.py` | 206 |
| GET | `/payments/ledger/{member_id}` | `mp-app/backend/modules/payments/router.py` | 224 |
| GET | `/payments/{payment_id}/receipt` | `mp-app/backend/modules/payments/router.py` | 254 |
| GET | `/payments/finance/summary` | `mp-app/backend/modules/payments/router.py` | 292 |
| POST | `/payments/finance/commission` | `mp-app/backend/modules/payments/router.py` | 309 |
| GET | `/population/paths` | `mp-app/backend/modules/population/router.py` | 26 |
| POST | `/population/gate-check` | `mp-app/backend/modules/population/router.py` | 31 |
| POST | `/population/intake/next` | `mp-app/backend/modules/population/router.py` | 36 |
| GET | `/admin/retention` | `mp-app/backend/modules/privacy/router.py` | 28 |
| POST | `/admin/retention/run` | `mp-app/backend/modules/privacy/router.py` | 34 |
| GET | `/programs` | `mp-app/backend/modules/programs/router.py` | 23 |
| GET | `/programs/{program_id}` | `mp-app/backend/modules/programs/router.py` | 51 |
| POST | `/programs/set-feedback` | `mp-app/backend/modules/programs/router.py` | 99 |
| POST | `/programs/sync/set-feedback` | `mp-app/backend/modules/programs/router.py` | 134 |
| GET | `/shop/status` | `mp-app/backend/modules/shop/router.py` | 119 |
| GET | `/shop/categories` | `mp-app/backend/modules/shop/router.py` | 125 |
| GET | `/shop/products` | `mp-app/backend/modules/shop/router.py` | 134 |
| GET | `/shop/products/{product_id}` | `mp-app/backend/modules/shop/router.py` | 146 |
| POST | `/shop/products` | `mp-app/backend/modules/shop/router.py` | 151 |
| PATCH | `/shop/products/{product_id}` | `mp-app/backend/modules/shop/router.py` | 157 |
| GET | `/shop/cart` | `mp-app/backend/modules/shop/router.py` | 166 |
| POST | `/shop/cart` | `mp-app/backend/modules/shop/router.py` | 171 |
| PATCH | `/shop/cart/{item_id}` | `mp-app/backend/modules/shop/router.py` | 188 |
| DELETE | `/shop/cart/{item_id}` | `mp-app/backend/modules/shop/router.py` | 197 |
| POST | `/shop/checkout` | `mp-app/backend/modules/shop/router.py` | 204 |
| GET | `/shop/orders` | `mp-app/backend/modules/shop/router.py` | 218 |
| GET | `/shop/orders/{order_id}/receipt` | `mp-app/backend/modules/shop/router.py` | 223 |
| PATCH | `/shop/orders/{order_id}` | `mp-app/backend/modules/shop/router.py` | 235 |
| GET | `/shop/gateways` | `mp-app/backend/modules/shop/router.py` | 241 |
| POST | `/shop/gateways` | `mp-app/backend/modules/shop/router.py` | 246 |
| PUT | `/shop/gateways/{gateway_id}` | `mp-app/backend/modules/shop/router.py` | 251 |
| GET | `/shop/prices` | `mp-app/backend/modules/shop/router.py` | 259 |
| POST | `/shop/prices` | `mp-app/backend/modules/shop/router.py` | 268 |
| GET | `/shop/change-requests` | `mp-app/backend/modules/shop/router.py` | 274 |
| POST | `/shop/change-requests` | `mp-app/backend/modules/shop/router.py` | 283 |
| GET | `/updates/manifest` | `mp-app/backend/modules/updates/router.py` | 12 |

## ۳. صفحه‌ها و دکمه‌های استودیو

فایل‌های TSX در `src/`: **44**؛ دکمهٔ `<button>`: **67**؛ `onClick`: **75**؛ `await import()` پویا: **0**.

کامپوننت `<Button>` (antd): **17**. شمارش `onClick` شامل هر دو است.

| فایل | `<button>` | `<Button>` | `onClick` | `await import()` | خطوط |
|---|---|---|---|---|---|
| `mp-app/studio/src/App.tsx` | 0 | 0 | 0 | 0 | 91 |
| `mp-app/studio/src/auth/AuthContext.tsx` | 0 | 0 | 0 | 0 | 105 |
| `mp-app/studio/src/components/AdaptiveNutritionPanel.tsx` | 1 | 0 | 1 | 0 | 205 |
| `mp-app/studio/src/components/AdminPermissions.tsx` | 0 | 3 | 2 | 0 | 261 |
| `mp-app/studio/src/components/AttendanceChart.tsx` | 0 | 0 | 0 | 0 | 71 |
| `mp-app/studio/src/components/AutoregPanel.tsx` | 1 | 0 | 1 | 0 | 153 |
| `mp-app/studio/src/components/CouponPanel.tsx` | 0 | 1 | 1 | 0 | 167 |
| `mp-app/studio/src/components/DeviceSessions.tsx` | 0 | 2 | 1 | 0 | 129 |
| `mp-app/studio/src/components/ExerciseLibrary.tsx` | 3 | 0 | 3 | 0 | 156 |
| `mp-app/studio/src/components/Feedback.tsx` | 1 | 0 | 1 | 0 | 171 |
| `mp-app/studio/src/components/FoodLibrary.tsx` | 2 | 0 | 2 | 0 | 162 |
| `mp-app/studio/src/components/Jp7TrendPanel.tsx` | 0 | 0 | 0 | 0 | 187 |
| `mp-app/studio/src/components/KpiCard.tsx` | 0 | 0 | 0 | 0 | 50 |
| `mp-app/studio/src/components/LedgerPanel.tsx` | 0 | 2 | 2 | 0 | 209 |
| `mp-app/studio/src/components/MemberTable.tsx` | 1 | 0 | 2 | 0 | 111 |
| `mp-app/studio/src/components/PaymentPanel.tsx` | 7 | 0 | 7 | 0 | 270 |
| `mp-app/studio/src/components/PeriodReportPanel.tsx` | 0 | 0 | 0 | 0 | 119 |
| `mp-app/studio/src/components/PhoneChangeDialog.tsx` | 3 | 0 | 2 | 0 | 191 |
| `mp-app/studio/src/components/ReadinessPanel.tsx` | 0 | 0 | 0 | 0 | 164 |
| `mp-app/studio/src/components/ReceiptQueue.tsx` | 0 | 3 | 2 | 0 | 169 |
| `mp-app/studio/src/components/RemindersPanel.tsx` | 1 | 0 | 1 | 0 | 142 |
| `mp-app/studio/src/components/RoleManager.tsx` | 1 | 0 | 1 | 0 | 113 |
| `mp-app/studio/src/components/SafetyBadge.tsx` | 0 | 0 | 0 | 0 | 54 |
| `mp-app/studio/src/components/ScheduleTimeline.tsx` | 0 | 0 | 0 | 0 | 90 |
| `mp-app/studio/src/components/SegmentalPanel.tsx` | 1 | 0 | 1 | 0 | 238 |
| `mp-app/studio/src/components/Sidebar.tsx` | 2 | 0 | 2 | 0 | 102 |
| `mp-app/studio/src/components/TopBar.tsx` | 2 | 0 | 1 | 0 | 129 |
| `mp-app/studio/src/components/UpdateBanner.tsx` | 1 | 0 | 1 | 0 | 39 |
| `mp-app/studio/src/components/VolumePanel.tsx` | 1 | 0 | 1 | 0 | 137 |
| `mp-app/studio/src/components/ui/JalaliDateField.tsx` | 0 | 0 | 0 | 0 | 67 |
| `mp-app/studio/src/main.tsx` | 0 | 0 | 0 | 0 | 59 |
| `mp-app/studio/src/pages/Analytics.tsx` | 0 | 0 | 0 | 0 | 117 |
| `mp-app/studio/src/pages/Assessment.tsx` | 0 | 0 | 0 | 0 | 31 |
| `mp-app/studio/src/pages/Chat.tsx` | 5 | 0 | 5 | 0 | 274 |
| `mp-app/studio/src/pages/CheckIn.tsx` | 1 | 0 | 1 | 0 | 149 |
| `mp-app/studio/src/pages/Dashboard.tsx` | 0 | 0 | 0 | 0 | 139 |
| `mp-app/studio/src/pages/Expenses.tsx` | 0 | 6 | 5 | 0 | 412 |
| `mp-app/studio/src/pages/Finance.tsx` | 3 | 0 | 3 | 0 | 182 |
| `mp-app/studio/src/pages/Login.tsx` | 3 | 0 | 3 | 0 | 145 |
| `mp-app/studio/src/pages/Members.tsx` | 3 | 0 | 3 | 0 | 216 |
| `mp-app/studio/src/pages/Nutrition.tsx` | 3 | 0 | 3 | 0 | 323 |
| `mp-app/studio/src/pages/Programs.tsx` | 4 | 0 | 4 | 0 | 243 |
| `mp-app/studio/src/pages/Settings.tsx` | 1 | 0 | 1 | 0 | 172 |
| `mp-app/studio/src/pages/Shop.tsx` | 16 | 0 | 12 | 0 | 830 |

## ۴. Workflowهای CI

| فایل | jobs | `uses:` بدون SHA |
|---|---|---|
| `.github/workflows/ci.yml` | secret-scan, docs, backend, studio, client-flutter, live-contract, e2e-api, client-pinned | 0 |
| `.github/workflows/client-format-fix.yml` | gitleaks-fingerprints, format-qr, format-client | 0 |
| `.github/workflows/container.yml` | build-push | 0 |
| `.github/workflows/deploy.yml` | preflight, build-and-push, deploy, rollback | 0 |
| `.github/workflows/gitleaks-fingerprints.yml` | gitleaks-fingerprints | 0 |
| `.github/workflows/web.yml` | web | 0 |

## ۵. فهرست کامل فایل‌ها

| ناحیه | مسیر | خطوط | اندازه (بایت) | بازبینی |
|---|---|---|---|---|
| CI/CD | `.github/workflows/ci.yml` | 597 | 32003 | NOT-REVIEWED |
| CI/CD | `.github/workflows/client-format-fix.yml` | 446 | 23828 | NOT-REVIEWED |
| CI/CD | `.github/workflows/container.yml` | 58 | 2168 | NOT-REVIEWED |
| CI/CD | `.github/workflows/deploy.yml` | 150 | 6001 | NOT-REVIEWED |
| CI/CD | `.github/workflows/gitleaks-fingerprints.yml` | 64 | 2953 | NOT-REVIEWED |
| CI/CD | `.github/workflows/web.yml` | 85 | 2799 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/Dockerfile` | 11 | 412 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/README.md` | 3 | 130 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/electron/main.cjs` | 31 | 810 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/electron/preload.cjs` | 6 | 225 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/eslint.config.mjs` | 47 | 1820 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/index.html` | 20 | 927 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/nginx.conf` | 26 | 808 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/package-lock.json` | 8535 | 297511 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/package.json` | 51 | 1397 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/postcss.config.js` | 6 | 81 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/public/icon-192.png` | — | 2771 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/public/icon-512.png` | — | 7938 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/public/manifest.webmanifest` | — | 692 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/public/sw.js` | 55 | 1800 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/App.tsx` | 90 | 3229 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/auth/AuthContext.tsx` | 104 | 3361 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/components/AdaptiveNutritionPanel.tsx` | 204 | 8126 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/components/AdminPermissions.tsx` | 260 | 9874 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/components/AttendanceChart.tsx` | 70 | 2215 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/components/AutoregPanel.tsx` | 152 | 5407 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/components/CouponPanel.tsx` | 166 | 5454 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/components/DeviceSessions.tsx` | 128 | 5279 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/components/ExerciseLibrary.tsx` | 155 | 6274 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/components/Feedback.tsx` | 170 | 6156 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/components/FoodLibrary.tsx` | 161 | 6645 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/components/Jp7TrendPanel.tsx` | 186 | 7813 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/components/KpiCard.tsx` | 49 | 1657 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/components/LedgerPanel.tsx` | 208 | 7749 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/components/MemberTable.tsx` | 110 | 4908 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/components/PaymentPanel.tsx` | 269 | 10048 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/components/PeriodReportPanel.tsx` | 118 | 4788 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/components/PhoneChangeDialog.tsx` | 190 | 7420 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/components/ReadinessPanel.tsx` | 163 | 6839 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/components/ReceiptQueue.tsx` | 168 | 5986 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/components/RemindersPanel.tsx` | 141 | 5186 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/components/RoleManager.tsx` | 112 | 4102 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/components/SafetyBadge.tsx` | 53 | 1924 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/components/ScheduleTimeline.tsx` | 89 | 3685 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/components/SegmentalPanel.tsx` | 237 | 8240 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/components/Sidebar.tsx` | 101 | 4691 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/components/TopBar.tsx` | 128 | 5748 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/components/UpdateBanner.tsx` | 38 | 1660 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/components/VolumePanel.tsx` | 136 | 6081 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/components/ui/JalaliDateField.tsx` | 66 | 2923 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/lib/adminApi.ts` | 221 | 7838 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/lib/api.ts` | 1616 | 46484 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/lib/money.ts` | 43 | 1802 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/lib/motion.ts` | 126 | 5195 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/lib/roleNav.ts` | 133 | 6548 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/lib/session.ts` | 341 | 12162 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/lib/update.ts` | 72 | 2170 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/lib/useApi.ts` | 75 | 2694 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/main.tsx` | 58 | 2422 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/pages/Analytics.tsx` | 116 | 5949 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/pages/Assessment.tsx` | 30 | 1063 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/pages/Chat.tsx` | 273 | 10142 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/pages/CheckIn.tsx` | 148 | 7447 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/pages/Dashboard.tsx` | 138 | 5259 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/pages/Expenses.tsx` | 411 | 15115 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/pages/Finance.tsx` | 181 | 8186 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/pages/Login.tsx` | 144 | 5839 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/pages/Members.tsx` | 215 | 9433 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/pages/Nutrition.tsx` | 322 | 12759 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/pages/Programs.tsx` | 242 | 9910 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/pages/Settings.tsx` | 171 | 7125 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/pages/Shop.tsx` | 829 | 35794 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/stores/appStore.ts` | 45 | 1493 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/styles/index.css` | 124 | 3680 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/src/vite-env.d.ts` | 4 | 193 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tailwind.config.js` | 67 | 1884 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/a11y.test.tsx` | 183 | 7679 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/adaptivePanel.test.tsx` | 185 | 7321 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/adminApi.test.ts` | 61 | 2733 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/adminPermissions.test.tsx` | 206 | 8545 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/api.test.ts` | 129 | 4443 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/apiCoverage.test.ts` | 750 | 35670 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/appStore.test.ts` | 33 | 1166 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/authFlow.test.tsx` | 205 | 8806 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/autoregPanel.test.tsx` | 103 | 3805 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/chatPage.test.tsx` | 206 | 8017 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/components.test.tsx` | 29 | 1242 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/couponPanel.test.tsx` | 79 | 2909 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/dashboard.test.tsx` | 76 | 2885 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/design-tokens.test.ts` | 63 | 2307 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/deviceSessions.test.tsx` | 127 | 4908 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/exerciseLibrary.test.tsx` | 146 | 6021 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/expenseReceipt.test.tsx` | 129 | 5136 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/expensesPage.test.tsx` | 233 | 9328 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/financePage.test.tsx` | 192 | 7308 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/foodLibrary.test.tsx` | 129 | 4546 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/jalaliDate.test.tsx` | 41 | 2072 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/jp7Trend.test.tsx` | 175 | 6408 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/ledgerPanel.test.tsx` | 198 | 7769 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/liveContract.test.ts` | 201 | 7684 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/motion.test.tsx` | 112 | 5483 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/nutritionNoMemberSentinel.test.tsx` | 29 | 1151 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/nutritionPage.test.tsx` | 235 | 8993 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/paymentPanel.test.tsx` | 312 | 15077 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/periodReportPanel.test.tsx` | 95 | 3268 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/phoneChange.test.tsx` | 104 | 4301 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/programsPage.test.tsx` | 87 | 3819 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/pwa.test.ts` | 80 | 3558 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/readinessPanel.test.tsx` | 138 | 5503 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/receiptQueue.test.tsx` | 143 | 5526 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/remindersPanel.test.tsx` | 147 | 5889 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/roleNav.test.tsx` | 124 | 5180 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/safetyBadge.test.tsx` | 85 | 3030 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/segmentalPanel.test.tsx` | 227 | 8513 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/session.test.ts` | 384 | 16149 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/settingsRole.test.tsx` | 68 | 2468 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/shopPage.test.tsx` | 264 | 11202 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/topbarTitles.test.tsx` | 45 | 1706 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/uiControlBudget.json` | 39 | 700 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/uiLibrary.test.ts` | 150 | 6711 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/update.test.ts` | 16 | 632 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/updateBanner.test.tsx` | 91 | 3039 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/vitest.setup.ts` | 20 | 756 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/volumePanel.test.tsx` | 148 | 4799 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tests/wp15Money.test.ts` | 52 | 2269 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/tsconfig.json` | 20 | 510 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/vite.config.ts` | 56 | 2320 | NOT-REVIEWED |
| استودیو (React) | `mp-app/studio/vitest.config.ts` | 21 | 841 | NOT-REVIEWED |
| اسکریپت و ابزار | `scripts/build_audit_inventory.py` | 305 | 13434 | NOT-REVIEWED |
| اسکریپت و ابزار | `scripts/docs_gate.py` | 212 | 9320 | NOT-REVIEWED |
| اسکریپت و ابزار | `scripts/interaction_map.py` | 405 | 18725 | NOT-REVIEWED |
| اسکریپت و ابزار | `scripts/repo_hygiene_gate.py` | 104 | 4544 | NOT-REVIEWED |
| اسکریپت و ابزار | `scripts/repowise_handoff.py` | 357 | 20974 | NOT-REVIEWED |
| اسکریپت و ابزار | `scripts/test_retired_signing_scan.py` | 123 | 5777 | NOT-REVIEWED |
| اسکریپت و ابزار | `tools/mermaid-check/check.mjs` | 76 | 2544 | NOT-REVIEWED |
| اسکریپت و ابزار | `tools/mermaid-check/package-lock.json` | 2021 | 73085 | NOT-REVIEWED |
| اسکریپت و ابزار | `tools/mermaid-check/package.json` | 14 | 325 | NOT-REVIEWED |
| اسکریپت و ابزار | `tools/rea-skill/reverse-engineer-anything/LICENSE-REA` | 21 | 1064 | NOT-REVIEWED |
| اسکریپت و ابزار | `tools/rea-skill/reverse-engineer-anything/SKILL.md` | 608 | 43592 | NOT-REVIEWED |
| اسکریپت و ابزار | `tools/rea-skill/reverse-engineer-anything/references/android-applications.md` | 63 | 4092 | NOT-REVIEWED |
| اسکریپت و ابزار | `tools/rea-skill/reverse-engineer-anything/references/connection-and-recovery.md` | 254 | 19499 | NOT-REVIEWED |
| اسکریپت و ابزار | `tools/rea-skill/reverse-engineer-anything/references/desktop-build.md` | 860 | 51806 | NOT-REVIEWED |
| اسکریپت و ابزار | `tools/rea-skill/reverse-engineer-anything/references/environments.md` | 399 | 22010 | NOT-REVIEWED |
| اسکریپت و ابزار | `tools/rea-skill/reverse-engineer-anything/references/evidence-workflows.md` | 176 | 11340 | NOT-REVIEWED |
| اسکریپت و ابزار | `tools/rea-skill/reverse-engineer-anything/references/javascript-applications.md` | 266 | 15437 | NOT-REVIEWED |
| اسکریپت و ابزار | `tools/rea-skill/reverse-engineer-anything/references/native-and-artifacts.md` | 943 | 60788 | NOT-REVIEWED |
| اسکریپت و ابزار | `tools/rea-skill/reverse-engineer-anything/references/runtime-observation.md` | 140 | 12296 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/README.md` | 3 | 145 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/analysis_options.yaml` | 6 | 128 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/android/.gitignore` | 14 | 253 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/android/app/build.gradle.kts` | 60 | 2212 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/android/app/src/debug/AndroidManifest.xml` | 7 | 378 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/android/app/src/main/AndroidManifest.xml` | 65 | 3688 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/android/app/src/main/kotlin/ir/muscleparadise/mp_client/MainActivity.kt` | 119 | 4814 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/android/app/src/main/kotlin/ir/muscleparadise/mp_client/OfflineFeedbackDatabase.kt` | 313 | 12724 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/android/app/src/main/res/drawable-hdpi/ic_launcher_foreground.png` | — | 13488 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/android/app/src/main/res/drawable-mdpi/ic_launcher_foreground.png` | — | 6421 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/android/app/src/main/res/drawable-v21/launch_background.xml` | 12 | 438 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/android/app/src/main/res/drawable-xhdpi/ic_launcher_foreground.png` | — | 18595 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/android/app/src/main/res/drawable-xxhdpi/ic_launcher_foreground.png` | — | 34012 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/android/app/src/main/res/drawable-xxxhdpi/ic_launcher_foreground.png` | — | 51626 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/android/app/src/main/res/drawable/launch_background.xml` | 12 | 434 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/android/app/src/main/res/mipmap-anydpi-v26/ic_launcher.xml` | 9 | 335 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/android/app/src/main/res/mipmap-hdpi/ic_launcher.png` | — | 544 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/android/app/src/main/res/mipmap-mdpi/ic_launcher.png` | — | 442 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/android/app/src/main/res/mipmap-xhdpi/ic_launcher.png` | — | 721 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/android/app/src/main/res/mipmap-xxhdpi/ic_launcher.png` | — | 1031 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/android/app/src/main/res/mipmap-xxxhdpi/ic_launcher.png` | — | 1443 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/android/app/src/main/res/values-night/styles.xml` | 18 | 975 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/android/app/src/main/res/values/colors.xml` | 4 | 120 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/android/app/src/main/res/values/styles.xml` | 18 | 988 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/android/app/src/main/res/xml/network_security_config.xml` | 26 | 1649 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/android/app/src/profile/AndroidManifest.xml` | 7 | 378 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/android/build.gradle.kts` | 24 | 537 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/android/gradle.properties` | 6 | 300 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/android/gradle/wrapper/gradle-wrapper.properties` | 5 | 202 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/android/settings.gradle.kts` | 26 | 771 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/assets/fonts/OFL-Vazirmatn.txt` | 93 | 4390 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/assets/fonts/Vazirmatn-Bold.ttf` | — | 123036 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/assets/fonts/Vazirmatn-Regular.ttf` | — | 122752 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/assets/logo/app_icon.png` | — | 249050 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/ci_apk.sh` | 25 | 669 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/lib/core/api_client.dart` | 212 | 8749 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/lib/core/app_state.dart` | 456 | 19887 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/lib/core/haptics.dart` | 67 | 3275 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/lib/core/membership.dart` | 177 | 5774 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/lib/core/motion.dart` | 33 | 1935 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/lib/core/offline_feedback_outbox.dart` | 692 | 22115 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/lib/core/persian_format.dart` | 38 | 2122 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/lib/core/router.dart` | 123 | 4166 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/lib/core/session.dart` | 254 | 10359 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/lib/core/theme.dart` | 39 | 1241 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/lib/core/updater/update_service.dart` | 126 | 4014 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/lib/features/assessment14/assessment14_page.dart` | 229 | 8135 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/lib/features/assessment14/assessment14_providers.dart` | 65 | 2856 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/lib/features/auth/otp_page.dart` | 143 | 4407 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/lib/features/bodycomp/bodycomp_page.dart` | 536 | 17925 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/lib/features/chat/member_chat_data.dart` | 195 | 6290 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/lib/features/chat/member_chat_page.dart` | 580 | 19901 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/lib/features/checkin/checkin_page.dart` | 402 | 17212 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/lib/features/checkin/member_checkin_history.dart` | 292 | 10202 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/lib/features/classes/classes_page.dart` | 268 | 9718 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/lib/features/feedback/feedback_providers.dart` | 115 | 4213 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/lib/features/feedback/offline_feedback_queue_card.dart` | 206 | 7626 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/lib/features/feedback/set_feedback_sheet.dart` | 348 | 14036 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/lib/features/home/home_page.dart` | 548 | 17615 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/lib/features/intake/intake_page.dart` | 411 | 13192 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/lib/features/intake/program_result.dart` | 172 | 5596 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/lib/features/notifications/notifications_page.dart` | 252 | 9404 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/lib/features/nutrition/adaptive_nutrition_card.dart` | 486 | 17201 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/lib/features/nutrition/nutrition_page.dart` | 608 | 21409 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/lib/features/profile/phone_change_dialog.dart` | 173 | 6498 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/lib/features/profile/profile_page.dart` | 502 | 17939 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/lib/features/progress/progress_page.dart` | 119 | 4073 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/lib/features/shell/app_shell.dart` | 166 | 5636 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/lib/features/shop/my_orders_sheet.dart` | 214 | 7471 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/lib/features/shop/order_receipt_sheet.dart` | 440 | 16501 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/lib/features/shop/shop_page.dart` | 574 | 20993 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/lib/features/today/readiness_card.dart` | 271 | 10142 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/lib/features/today/today_controller.dart` | 36 | 1146 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/lib/features/today/today_page.dart` | 286 | 10919 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/lib/features/today/volume_card.dart` | 321 | 11343 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/lib/features/wallet/wallet_ledger.dart` | 208 | 6956 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/lib/features/wallet/wallet_page.dart` | 374 | 14131 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/lib/main.dart` | 50 | 1685 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/lib/shared/widgets/glass_card.dart` | 38 | 932 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/pubspec.yaml` | 47 | 1265 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/test/adaptive_nutrition_test.dart` | 203 | 7540 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/test/api_client_test.dart` | 210 | 6894 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/test/assessment14_page_test.dart` | 141 | 4571 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/test/bodycomp_real_data_test.dart` | 213 | 8021 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/test/classes_cancel_test.dart` | 160 | 5542 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/test/face_consent_gate_test.dart` | 156 | 5821 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/test/haptics_recorder.dart` | 24 | 972 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/test/home_banner_test.dart` | 160 | 5420 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/test/home_page_test.dart` | 107 | 3683 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/test/logout_button_test.dart` | 114 | 3817 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/test/logout_test.dart` | 98 | 3931 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/test/member_chat_page_test.dart` | 418 | 15243 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/test/member_checkin_history_test.dart` | 238 | 7641 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/test/membership_test.dart` | 119 | 4445 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/test/motion_haptics_test.dart` | 187 | 7643 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/test/notifications_page_test.dart` | 150 | 5342 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/test/nutrition_food_log_test.dart` | 241 | 8382 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/test/offline_feedback_outbox_test.dart` | 585 | 16825 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/test/phone_change_dialog_test.dart` | 223 | 7581 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/test/qr_biometric_gate_test.dart` | 63 | 2441 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/test/readiness_card_test.dart` | 160 | 5868 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/test/session_refresh_test.dart` | 167 | 5868 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/test/set_feedback_sheet_test.dart` | 153 | 6116 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/test/shop_orders_receipt_test.dart` | 339 | 12593 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/test/shop_page_test.dart` | 184 | 6516 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/test/today_controller_test.dart` | 41 | 1538 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/test/today_page_test.dart` | 93 | 2832 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/test/volume_card_test.dart` | 161 | 5558 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/test/wallet_history_test.dart` | 276 | 9321 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/tools/apk_audit.py` | 179 | 8344 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/tools/apk_deep_audit.py` | 315 | 13526 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/tools/ci_test_failures.py` | 234 | 8877 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/tools/dart_gate.py` | 290 | 12498 | NOT-REVIEWED |
| اپ عضو (Flutter) | `mp-app/client/tools/manifest_gate.py` | 153 | 5486 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/.env.example` | 46 | 1933 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/Dockerfile` | 31 | 1762 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/README.md` | 3 | 121 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/alembic.ini` | 149 | 5014 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/api/__init__.py` | 0 | 0 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/api/routes.json` | 4219 | 74480 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/api/v1/__init__.py` | 0 | 0 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/api/v1/api.py` | 57 | 2795 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/api/v1/monitoring.py` | 138 | 5275 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/app/__init__.py` | 0 | 0 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/app/clock.py` | 23 | 956 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/app/config.py` | 309 | 15183 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/app/deps.py` | 142 | 5833 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/app/errors.py` | 102 | 3916 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/app/id_floor.py` | 34 | 1709 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/app/id_guard.py` | 64 | 3134 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/app/ids.py` | 36 | 1760 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/app/jalali.py` | 94 | 2646 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/app/logging.py` | 145 | 4727 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/app/main.py` | 195 | 8385 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/app/metrics.py` | 140 | 5359 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/app/money.py` | 15 | 522 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/app/pool_metrics.py` | 69 | 3003 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/app/security/grants.py` | 117 | 4844 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/app/security/headers.py` | 37 | 1452 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/app/security/hierarchy.py` | 61 | 3211 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/app/security/jwt.py` | 103 | 3443 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/app/security/ownership.py` | 36 | 1514 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/app/security/proxy.py` | 65 | 2859 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/app/security/route_policy.py` | 141 | 7660 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/app/sms.py` | 145 | 5573 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/app/unhandled.py` | 119 | 6204 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/cache/__init__.py` | 0 | 0 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/cache/keys.py` | 21 | 661 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/cache/store.py` | 123 | 4137 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/coverage-subprocess.rc` | — | 525 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/data/external/free_exercise_db/SOURCE.md` | 13 | 845 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/data/external/free_exercise_db/exercises.json` | 22694 | 1005327 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/data/food/iranian_foods.js` | 347 | 38344 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/__init__.py` | 0 | 0 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/base.py` | 173 | 7234 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/migrations/README` | 1 | 38 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/migrations/env.py` | 53 | 1482 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/migrations/script.py.mako` | — | 704 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/migrations/versions/0691adce99d0_m51_c1_chat.py` | 110 | 4648 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/migrations/versions/39f0cd2d8531_initial_schema.py` | 769 | 35485 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/migrations/versions/445c5b70864b_m56_c1_safety_flags.py` | 32 | 885 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/migrations/versions/632164e8c647_qf06_expense_receipts.py` | 46 | 1341 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/migrations/versions/67f8b00508eb_q6_c1_gateway_authority.py` | 41 | 1318 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/migrations/versions/74fd2b754c43_m57_c2_client_id.py` | 36 | 1078 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/migrations/versions/8a1f2c3d4e5b_m58_drop_orphan_indexes.py` | 54 | 1899 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/migrations/versions/97e2ddab2431_m49_c3_body_weight_logs.py` | 75 | 2845 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/migrations/versions/98e17b2e5f08_qf10_refunded_at.py` | 27 | 726 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/migrations/versions/a1b2c3d4e5f6_m23_jp_quality_and_locked_equation.py` | 38 | 1252 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/migrations/versions/a5b6c7d8e9f0_qf05_ledger.py` | 77 | 2425 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/migrations/versions/a7b8c9d0e1f2_m35_norm_tables.py` | 42 | 1804 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/migrations/versions/a7c3d9e1f2b4_g2_coupons.py` | 63 | 2403 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/migrations/versions/b0770716f820_m49_c1_food_logs.py` | 72 | 3168 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/migrations/versions/b19c28d37e46_m111_refund_reference.py` | 21 | 479 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/migrations/versions/b2c3d4e5f6a1_m27_classes_finance.py` | 66 | 2407 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/migrations/versions/b6c7d8e9f0a1_qf06_expenses.py` | 87 | 3083 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/migrations/versions/b7c8d9e0f1a2_m36_axis_assessment.py` | 78 | 3179 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/migrations/versions/b7c9d1e2f3a4_m59_shop.py` | 254 | 10650 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/migrations/versions/c1d2e3f4a5b6_qf03_admin_permissions.py` | 65 | 2019 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/migrations/versions/c3d4e5f6a1b2_m33_exercise_catalog.py` | 57 | 2671 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/migrations/versions/c3f01ab129e2_m47_c1_align_indexes_and_nullability_.py` | 182 | 7635 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/migrations/versions/c5d6e7f8a9b0_m65_qr_replay_guard.py` | 26 | 673 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/migrations/versions/c7d8e9f0a1b2_qf23_report_runs.py` | 46 | 1750 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/migrations/versions/c8d9e0f1a2b3_m36_norm_direction.py` | 25 | 642 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/migrations/versions/d2e3f4a5b6c7_qf09_card_to_card.py` | 99 | 3930 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/migrations/versions/d4e5f6a1b2c3_m33_axis_schema.py` | 29 | 977 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/migrations/versions/d8e9f0a1b2c3_qf27_worker_heartbeats.py` | 38 | 1141 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/migrations/versions/d9e0f1a2b3c4_m82_phone_change_challenges.py` | 64 | 2506 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/migrations/versions/e0f1a2b3c4d5_m38_set_feedback.py` | 49 | 1622 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/migrations/versions/e3f4a5b6c7d8_qf20_outbox.py` | 83 | 3007 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/migrations/versions/e5f6a1b2c3d4_m33_review_columns.py` | 31 | 968 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/migrations/versions/f1a2b3c4d5e6_m42_checkout.py` | 21 | 503 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/migrations/versions/f3eaefb13ae2_m54_c1_limb.py` | 69 | 2763 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/migrations/versions/f4a5b6c7d8e9_qf21_inbox.py` | 40 | 1133 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/migrations/versions/f603fe744993_m57_c1_sync_fields.py` | 36 | 1063 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/migrations/versions/f6a1b2c3d4e5_m34_progressions.py` | 48 | 1848 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/migrations/versions/f9b0c1d2e3f4_merge_heads_unique_gateway_authority.py` | 86 | 2862 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/models/__init__.py` | 118 | 2885 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/models/admin.py` | 72 | 2936 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/models/ai.py` | 30 | 1164 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/models/assessment.py` | 171 | 8938 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/models/auth.py` | 124 | 5837 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/models/chat.py` | 64 | 2783 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/models/classes.py` | 42 | 1920 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/models/content.py` | 116 | 7001 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/models/face_id.py` | 67 | 3032 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/models/finance.py` | 114 | 5519 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/models/membership.py` | 55 | 2472 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/models/notification.py` | 31 | 1282 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/models/nutrition.py` | 111 | 5282 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/models/outbox.py` | 80 | 3619 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/models/payments.py` | 200 | 10213 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/models/programs.py` | 117 | 5958 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/models/segment.py` | 53 | 2741 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/models/shop.py` | 213 | 11534 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/db/models/worker.py` | 25 | 1033 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/devtools/__init__.py` | 0 | 0 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/devtools/sandbox_bank.py` | 303 | 13987 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/engine/adaptive_nutrition.py` | 388 | 17691 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/engine/autoreg.py` | 59 | 2647 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/engine/axis_map.py` | 56 | 2548 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/engine/axis_prescription.py` | 189 | 8671 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/engine/axis_rules.py` | 222 | 10060 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/engine/catalog_sync.py` | 77 | 2710 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/engine/churn_risk.py` | 117 | 4556 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/engine/feedback_apply.py` | 166 | 6934 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/engine/gender_plans.py` | 80 | 3958 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/engine/nutrition.py` | 89 | 3035 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/engine/readiness.py` | 289 | 12848 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/engine/reminders.py` | 158 | 6358 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/engine/safety.py` | 169 | 8016 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/engine/scoring.py` | 153 | 6917 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/engine/segmental.py` | 208 | 8662 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/engine/set_feedback.py` | 105 | 5133 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/engine/sync_lww.py` | 147 | 6395 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/engine/volume.py` | 244 | 10944 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/engine/workout.py` | 274 | 9303 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/eval/__init__.py` | 7 | 442 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/eval/gold.py` | 39 | 2085 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/eval/harness.py` | 147 | 5879 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/eval/llm_column.py` | 176 | 6762 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/eval/prescription_eval.py` | 106 | 4892 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/eval/run_eval.py` | 86 | 3721 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/eval/scenarios.py` | 66 | 2549 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/eval/scoring_eval.py` | 116 | 4809 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/jobs/__init__.py` | 0 | 0 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/jobs/outbox_relay.py` | 70 | 2405 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/jobs/scheduler.py` | 150 | 5630 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/admin/analytics.py` | 481 | 18494 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/admin/kpis.py` | 60 | 2090 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/admin/permissions.py` | 128 | 4482 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/admin/roles.py` | 92 | 4172 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/admin/router.py` | 175 | 6054 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/admin/schemas.py` | 55 | 1196 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/admin/service.py` | 92 | 2659 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/ai/router.py` | 35 | 940 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/ai_engine/__init__.py` | 0 | 0 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/ai_engine/router.py` | 55 | 1989 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/ai_engine/schemas.py` | 26 | 928 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/ai_engine/service.py` | 85 | 3437 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/assessment/__init__.py` | 0 | 0 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/assessment/equations.py` | 54 | 2820 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/assessment/repository.py` | 59 | 1848 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/assessment/router.py` | 91 | 2918 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/assessment/schemas.py` | 86 | 2678 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/assessment/service.py` | 429 | 16773 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/auth/__init__.py` | 0 | 0 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/auth/router.py` | 156 | 5646 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/auth/schemas.py` | 93 | 2484 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/auth/service.py` | 426 | 17309 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/axis_assessment/__init__.py` | 1 | 122 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/axis_assessment/router.py` | 50 | 1818 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/axis_assessment/schemas.py` | 61 | 1241 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/axis_assessment/service.py` | 279 | 10267 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/classes/router.py` | 84 | 2772 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/classes/service.py` | 152 | 5158 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/content/__init__.py` | 0 | 0 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/exercises/__init__.py` | 0 | 0 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/exercises/router.py` | 128 | 4662 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/expenses/__init__.py` | 1 | 52 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/expenses/receipts.py` | 76 | 2731 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/expenses/router.py` | 114 | 3910 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/expenses/schemas.py` | 72 | 1693 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/expenses/service.py` | 195 | 6440 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/face_id/__init__.py` | 0 | 0 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/face_id/deep.py` | 94 | 4655 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/face_id/privacy.py` | 42 | 2148 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/face_id/router.py` | 153 | 5861 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/face_id/schemas.py` | 70 | 1583 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/face_id/service.py` | 262 | 8645 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/membership/__init__.py` | 0 | 0 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/membership/repository.py` | 70 | 2144 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/membership/router.py` | 221 | 7931 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/membership/schemas.py` | 63 | 1626 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/membership/service.py` | 266 | 9496 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/notification/__init__.py` | 0 | 0 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/notification/chat_router.py` | 54 | 2063 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/notification/chat_service.py` | 188 | 6975 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/notification/router.py` | 44 | 1549 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/notification/schemas.py` | 29 | 633 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/notification/service.py` | 171 | 5554 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/nutrition/__init__.py` | 0 | 0 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/nutrition/router.py` | 101 | 3643 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/nutrition/schemas.py` | 106 | 2243 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/nutrition/service.py` | 454 | 16290 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/outbox/__init__.py` | 1 | 37 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/outbox/health.py` | 129 | 4625 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/outbox/inbox.py` | 67 | 2260 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/outbox/service.py` | 157 | 5249 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/payments/__init__.py` | 0 | 0 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/payments/finance.py` | 107 | 3823 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/payments/gateway.py` | 278 | 12543 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/payments/invoice.py` | 152 | 6184 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/payments/ledger.py` | 206 | 7449 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/payments/manual_transfer_policy.py` | 117 | 4480 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/payments/receipts.py` | 318 | 11498 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/payments/repository.py` | 48 | 1391 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/payments/router.py` | 370 | 14809 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/payments/schemas.py` | 151 | 4128 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/payments/service.py` | 593 | 25842 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/population/__init__.py` | 0 | 0 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/population/gates.py` | 66 | 3142 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/population/intake.py` | 116 | 5258 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/population/router.py` | 38 | 1228 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/privacy/__init__.py` | 1 | 51 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/privacy/retention.py` | 164 | 5919 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/privacy/router.py` | 37 | 1359 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/programs/__init__.py` | 0 | 0 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/programs/router.py` | 141 | 5369 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/programs/schemas.py` | 106 | 3629 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/programs/service.py` | 620 | 23956 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/reporting/__init__.py` | 0 | 0 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/reporting/axes.py` | 85 | 4661 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/reporting/router.py` | 38 | 1463 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/reporting/service.py` | 263 | 12048 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/reports/__init__.py` | 1 | 64 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/reports/period.py` | 135 | 5392 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/reports/router.py` | 79 | 2643 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/reports/schedule.py` | 200 | 7539 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/shop/router.py` | 295 | 12307 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/shop/service.py` | 800 | 30388 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/updates/registry.json` | 65 | 1690 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/updates/router.py` | 17 | 550 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/modules/updates/service.py` | 137 | 5311 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/pyproject.toml` | 138 | 7597 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/requirements.txt` | 86 | 1686 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/scripts/__init__.py` | 0 | 0 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/scripts/attach_exercise_media.py` | 108 | 3910 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/scripts/backup.py` | 283 | 12621 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/scripts/build_exercise_gifs.py` | 144 | 6824 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/scripts/build_progressions.py` | 248 | 9530 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/scripts/coverage_gate.py` | 133 | 5439 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/scripts/coverage_run.sh` | 27 | 1052 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/scripts/dast.py` | 249 | 10405 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/scripts/deploy_gate.py` | 240 | 9903 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/scripts/export_routes.py` | 177 | 7861 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/scripts/import_exercise_catalog.py` | 155 | 5381 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/scripts/import_food_catalog.py` | 206 | 8809 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/scripts/locust_m39c3.py` | 43 | 1254 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/scripts/route_guard_gate.py` | 136 | 6851 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/scripts/seed_criteria.py` | 113 | 4247 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/scripts/seed_norms.py` | 283 | 10114 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/scripts/seed_s3c_m39.py` | 49 | 1613 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/scripts/seed_shop.py` | 200 | 6962 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/scripts/tag_axis_coverage.py` | 682 | 23402 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/scripts/uvicorn_proxy_flags.sh` | 11 | 643 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/security/__init__.py` | 0 | 0 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/security/crypto.py` | 65 | 3044 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/security/rbac.py` | 311 | 16466 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/1.gif` | — | 340590 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/10.gif` | — | 296855 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/10_0.jpg` | — | 9764 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/10_1.jpg` | — | 9536 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/11.gif` | — | 328370 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/11_0.jpg` | — | 13294 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/11_1.jpg` | — | 14417 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/12.gif` | — | 283990 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/12_0.jpg` | — | 14573 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/12_1.jpg` | — | 14499 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/13.gif` | — | 406167 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/13_0.jpg` | — | 17085 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/13_1.jpg` | — | 19014 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/14.gif` | — | 367200 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/14_0.jpg` | — | 14497 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/14_1.jpg` | — | 15831 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/15.gif` | — | 361824 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/15_0.jpg` | — | 14448 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/15_1.jpg` | — | 13969 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/16.gif` | — | 301165 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/16_0.jpg` | — | 12972 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/16_1.jpg` | — | 12648 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/17.gif` | — | 326358 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/17_0.jpg` | — | 14252 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/17_1.jpg` | — | 14516 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/1_0.jpg` | — | 16497 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/1_1.jpg` | — | 16601 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/2.gif` | — | 298529 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/2_0.jpg` | — | 16606 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/2_1.jpg` | — | 16411 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/3.gif` | — | 329197 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/3_0.jpg` | — | 15542 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/3_1.jpg` | — | 15567 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/4.gif` | — | 328264 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/4_0.jpg` | — | 16470 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/4_1.jpg` | — | 16267 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/5.gif` | — | 317654 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/5_0.jpg` | — | 15307 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/5_1.jpg` | — | 15706 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/6.gif` | — | 318420 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/6_0.jpg` | — | 10362 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/6_1.jpg` | — | 9973 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/7.gif` | — | 364415 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/7_0.jpg` | — | 17200 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/7_1.jpg` | — | 17222 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/8.gif` | — | 286445 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/8_0.jpg` | — | 12460 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/8_1.jpg` | — | 12591 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/9.gif` | — | 347915 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/9_0.jpg` | — | 15558 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/static/exercises/9_1.jpg` | — | 15735 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/__init__.py` | 0 | 0 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/conftest.py` | 71 | 1983 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/e2e/__init__.py` | 0 | 0 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/evaluation/test_eval_harness.py` | 44 | 1588 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/evaluation/test_prescription_eval.py` | 12 | 436 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/evaluation/test_scoring_eval.py` | 18 | 575 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/__init__.py` | 0 | 0 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/_actors.py` | 30 | 1303 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/_metrics.py` | 4 | 199 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/conftest.py` | 71 | 2481 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_admin_analytics.py` | 248 | 9396 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_admin_pass.py` | 104 | 3487 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_ai_engine.py` | 148 | 4984 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_ai_kpis.py` | 70 | 1917 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_api_contract.py` | 343 | 11728 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_attach_exercise_media.py` | 120 | 4025 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_axis_assessment_api.py` | 291 | 10112 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_backup_drill.py` | 57 | 2211 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_battle.py` | 247 | 8507 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_ci_artifacts.py` | 195 | 7584 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_classes_finance.py` | 127 | 4212 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_coverage_gate.py` | 99 | 3259 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_deploy_gate_branches.py` | 292 | 10992 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_e2e_adaptive_loop.py` | 369 | 14188 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_e2e_dataflow.py` | 254 | 9949 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_face_privacy.py` | 89 | 3060 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_g2_coupons.py` | 168 | 6780 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_g9_library.py` | 200 | 8122 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_gender_plans_api.py` | 142 | 5227 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_import_food_catalog.py` | 203 | 6648 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_infra.py` | 54 | 2017 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_m45_admin_attendance.py` | 239 | 9614 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_m45_checkin_feed.py` | 107 | 3756 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_m45_programs_list.py` | 109 | 3635 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_m46_db_pool.py` | 62 | 2627 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_m46_engine_catalog_fk.py` | 130 | 4391 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_m46_flags_list.py` | 91 | 3073 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_m46_security_matrix.py` | 154 | 5642 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_m46_whoami.py` | 70 | 2262 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_m47_migration_drift.py` | 69 | 2755 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_m48_feedback_applied.py` | 470 | 15683 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_m48_volume_api.py` | 222 | 7751 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_m49_adaptive_nutrition.py` | 285 | 9640 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_m49_food_logging.py` | 561 | 18238 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_m50_jp7_trend.py` | 222 | 8027 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_m51_chat.py` | 276 | 10184 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_m54_segmental.py` | 212 | 7268 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_m55_reminders.py` | 215 | 7010 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_m56_safety_gate.py` | 120 | 3913 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_m57_sync.py` | 323 | 10955 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_m59_shop.py` | 868 | 33491 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_m61_face_member_gate.py` | 139 | 5939 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_m65_qr_security.py` | 157 | 5367 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_m67_studio_auth.py` | 88 | 3578 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_m74_class_cancel.py` | 178 | 6127 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_m75_notifications.py` | 131 | 4521 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_m78_adaptive_nutrition_client.py` | 114 | 3757 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_m80_member_checkin_history.py` | 162 | 6137 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_m82_phone_change.py` | 397 | 14095 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_m83_wallet_ledger.py` | 131 | 5288 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_m84_class_booking_name.py` | 147 | 5462 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_m97_migrations_and_backup.py` | 270 | 12448 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_migrations.py` | 48 | 1530 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_monitoring.py` | 156 | 5778 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_ownership.py` | 258 | 9375 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_payments_deep.py` | 162 | 6549 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_phase2_shop_display.py` | 179 | 6608 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_phase3_no_online_gateway.py` | 155 | 5762 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_phase4_identity_session.py` | 136 | 5857 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_phase4b_device_sessions.py` | 129 | 5201 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_phase5_admin_permissions.py` | 244 | 10210 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_phase6_card_to_card.py` | 306 | 13079 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_phase6b_ledger.py` | 244 | 10194 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_phase6c_expenses.py` | 226 | 9185 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_phase7_member_scope_sweep.py` | 102 | 4518 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_phase8_inbox.py` | 70 | 2769 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_phase8_network.py` | 80 | 3466 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_phase8_outbox.py` | 185 | 7338 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_phase8_privacy.py` | 174 | 6580 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_phase8_release_sweep.py` | 178 | 7904 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_phase8_reports.py` | 146 | 6714 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_phase8_worker.py` | 145 | 5601 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_pilot_dry_run.py` | 175 | 6363 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_q6_gateway.py` | 365 | 13641 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_qf00_ownership_gaps.py` | 161 | 5493 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_qf06_expense_receipt.py` | 157 | 6267 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_qf10_period_report.py` | 151 | 5824 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_rea_fixes.py` | 80 | 3015 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_reporting.py` | 120 | 4020 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_routes_access_matrix.py` | 127 | 5956 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_routes_artifact.py` | 54 | 2657 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_routes_effective_guards.py` | 105 | 5335 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_sandbox_bank.py` | 558 | 23268 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_security.py` | 139 | 5100 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_sms.py` | 111 | 3661 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_unhandled_errors.py` | 225 | 9789 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_updates.py` | 60 | 2094 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_wp03_axis_single_guard.py` | 58 | 2033 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_wp13_metrics_auth.py` | 76 | 2700 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_wp14_logout_all.py` | 85 | 3721 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_wp25_scrape_errors_ready.py` | 15 | 561 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_wp31_id_floor.py` | 82 | 3394 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_wp32_error_envelope.py` | 28 | 1069 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_wp33_gateway_return_status.py` | 43 | 1791 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_wp34_member_profile_required.py` | 24 | 1032 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/integration/test_wp35_contract_guards.py` | 121 | 4831 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/load/locustfile.py` | 65 | 2282 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/load/locustfile_full.py` | 208 | 7169 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/regression/__init__.py` | 0 | 0 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/regression/fixtures/wp41_config_golden.json` | 11402 | 435365 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/regression/test_apk_audit.py` | 95 | 3464 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/regression/test_apk_deep_audit.py` | 159 | 6797 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/regression/test_b2_wp23_wp43_wp44.py` | 54 | 2290 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/regression/test_branch_id.py` | 39 | 1351 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/regression/test_ci_test_failures.py` | 169 | 7069 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/regression/test_dart_gate.py` | 135 | 4982 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/regression/test_deploy_gate.py` | 22 | 631 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/regression/test_manifest_gate.py` | 95 | 3652 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/regression/test_manual_transfer_policy.py` | 184 | 5888 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/regression/test_no_duplicate_guard.py` | 50 | 1716 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/regression/test_production_ops.py` | 198 | 7678 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/regression/test_qr_format_workflow.py` | 120 | 5023 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/regression/test_rbac.py` | 68 | 3451 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/regression/test_release_signing_policy.py` | 18 | 656 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/regression/test_role_nav_parity.py` | 76 | 4180 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/regression/test_route_guard_gate.py` | 72 | 2983 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/regression/test_wp06_deprecations_and_counts.py` | 78 | 2577 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/regression/test_wp11_xff_trust.py` | 157 | 5609 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/regression/test_wp12_env_failsafe.py` | 132 | 5023 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/regression/test_wp15_rial_strict.py` | 79 | 3107 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/regression/test_wp21_logging_queue.py` | 99 | 3411 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/regression/test_wp22_pool_observability.py` | 108 | 4059 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/regression/test_wp24_rbac_decision_cache.py` | 161 | 5916 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/regression/test_wp25_dast_skip_counter.py` | 39 | 1083 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/regression/test_wp25_silent_failures.py` | 108 | 4088 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/regression/test_wp26_sms_logging.py` | 100 | 4141 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/regression/test_wp32_detail_preserved.py` | 35 | 1439 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/regression/test_wp36_shop_today.py` | 57 | 2408 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/regression/test_wp41_config_characterization.py` | 124 | 4193 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/regression/test_wp45_f22_migration_sql.py` | 58 | 2430 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/regression/test_wp45_session_pattern.py` | 49 | 1889 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/unit/__init__.py` | 0 | 0 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/unit/test_adaptive_nutrition.py` | 271 | 10351 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/unit/test_autoreg.py` | 36 | 1311 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/unit/test_axis_assessment_models.py` | 82 | 2817 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/unit/test_axis_prescription.py` | 103 | 4174 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/unit/test_axis_rules.py` | 77 | 2898 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/unit/test_axis_schema.py` | 52 | 1712 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/unit/test_axis_tagging.py` | 123 | 3635 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/unit/test_backup.py` | 84 | 2791 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/unit/test_cache.py` | 104 | 3466 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/unit/test_catalog_import.py` | 58 | 1908 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/unit/test_churn_risk.py` | 62 | 2043 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/unit/test_crypto.py` | 71 | 2163 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/unit/test_deep_model_lock.py` | 124 | 4037 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/unit/test_engine.py` | 77 | 3387 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/unit/test_equation_lock.py` | 59 | 1731 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/unit/test_food_catalog_import.py` | 129 | 5654 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/unit/test_gender_plans.py` | 58 | 2183 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/unit/test_jalali_backup.py` | 44 | 1528 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/unit/test_jobs.py` | 87 | 2923 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/unit/test_llm_column.py` | 136 | 5113 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/unit/test_load_attribution.py` | 58 | 2542 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/unit/test_models.py` | 171 | 4823 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/unit/test_norms.py` | 45 | 1720 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/unit/test_population_gates.py` | 51 | 2165 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/unit/test_progressions.py` | 79 | 3096 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/unit/test_rbac_policies.py` | 7 | 465 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/unit/test_readiness.py` | 196 | 6702 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/unit/test_reminders.py` | 147 | 5716 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/unit/test_repositories.py` | 96 | 3330 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/unit/test_safety.py` | 160 | 6779 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/unit/test_scoring.py` | 86 | 3703 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/unit/test_segmental.py` | 170 | 6848 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/unit/test_set_feedback.py` | 97 | 3271 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/unit/test_sync_lww.py` | 159 | 6935 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/tests/unit/test_volume_landmarks.py` | 118 | 4034 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/01d4502c089320cdeefb204b05284d9a.png` | — | 102 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/0ebd6ec29641c4c742d9525852ff8871.png` | — | 102 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/0fedcedf3a6e9dfb1e485a2ecb44d0cd.png` | — | 82 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/124ed067eb239824313ef8fdd49d6f1a.png` | — | 82 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/1a523781da546fbdb43e421c35cb691f.png` | — | 102 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/1b585b7bd7ce1c98ad7d373cfd3e9bd3.png` | — | 82 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/1e9cc012695703f718dc70c00cfd77b9.png` | — | 102 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/206f5d55aa9340fc59dcbfcd0bcb8575.png` | — | 82 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/207e772f939c082295a55be1f92100b3.png` | — | 82 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/272a758beec97d407c7a08d81635592f.png` | — | 82 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/2866b82591a03c76e16b6736da50f833.png` | — | 102 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/2a62c4346ff0417f99c93fd9ed4cd397.png` | — | 102 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/2b0a55e91eb333db40c67a42c3ad533b.png` | — | 102 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/2b76c1fc3d2c5a20d587f03b291a8732.png` | — | 82 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/2e0c7bbcce73422a09df8e98d2cd4248.png` | — | 82 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/370cb62eb492d1bcdbbe4e29c2601388.png` | — | 82 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/3c9193e87b4aba152b9826eae1ff1154.png` | — | 102 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/4516e715a03748837b8495ed090b4f34.png` | — | 102 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/551a0a77b4f56d73ccb6e87adaf52bda.png` | — | 102 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/58bcc655f3cb97b47e161829c4a2529c.png` | — | 102 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/5a5dcf0cb1dc6affdb87cd97c2e2841e.png` | — | 82 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/61dc5b260571c7d77acb49424cab6637.png` | — | 102 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/63a04a231c4d671ed4deb2e481607c81.png` | — | 82 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/641fa72eb6307c892a20f3b5d12c12fa.png` | — | 82 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/6af7525bf20ad3443acc7afbc3ed53c9.png` | — | 102 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/6b62a369eb6fa365d3034ee8fb741a80.png` | — | 102 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/6df0a3ea0f41ad855fcf9f2915138a17.png` | — | 82 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/6e42097a659338ba0faa22c771142916.png` | — | 82 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/72a3588f92be7706dc66c960c1121ee3.png` | — | 102 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/7307c11ea611bee04d439346640906cb.png` | — | 102 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/760cc961c54a730ca5a03b50c1f537c0.png` | — | 82 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/76960d24881b7cf1d4cafe3b01631bc6.png` | — | 82 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/7acc53ad116e525063f6c7d732011498.png` | — | 102 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/7cd9bc01f47a248d05e13c9936b3930b.png` | — | 102 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/8282be7ea869822c2bf3d8e9bfb2551e.png` | — | 102 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/83d8d84cef09cb0b911e8b65b9c41000.png` | — | 102 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/8587bde3f96a81aecc03d12ed605cd30.png` | — | 82 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/8a1c876331f869677bc3a70c913a0ea9.png` | — | 82 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/8e0cf99ed3afbadcbf1834d8e6cb57dd.png` | — | 102 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/934d789bc44bd6c42fc1886b74941e82.png` | — | 102 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/94be846b428fff7c1bf593cb865d8f3d.png` | — | 82 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/9c111bc18ad2a7963fb0ce6a0d7341ab.png` | — | 102 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/9f912c1b12526c5afaba379bfefc5c7f.png` | — | 102 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/a6802a62ad208d0abddcc92db9134fec.png` | — | 102 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/a733927d4f56c74141d7ba9e3a70d97a.png` | — | 82 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/ab1d7e1b97961c048b3fb35f62d42306.png` | — | 102 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/ac96f9f2970387d4c33c96c32996f72b.png` | — | 102 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/adeab87720e3eaa889fee585188a6108.png` | — | 102 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/b0181c2f22e1f04891cf94354ef7669f.png` | — | 102 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/b12b4cfddeaa5d32a89c0afa31c5f44f.png` | — | 102 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/b4a97a81bbab2c0f54738f85f0b6d366.png` | — | 102 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/b58acf54d6256ff12fea99f944b631ef.png` | — | 102 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/b7e0fcc362fe0d6deaef4df8564f6b2e.png` | — | 102 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/b809ee3459a8136cd41ce3622d8a1fa6.png` | — | 102 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/b80ad29069b29cd29c1fce47dc1e3991.png` | — | 102 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/bb4712baa828dd5aa251541b0e45911a.png` | — | 82 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/bc8a82762e911f2bc21c076b0a27c2fd.png` | — | 102 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/bec0e76264e464bfc592b40601bdc7f2.png` | — | 102 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/c21cb53324c97d8419030cced8738725.png` | — | 82 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/c312355e1e79f3d310e289e438826437.png` | — | 102 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/c3aa58363f4d401a1db548552f8fa93d.png` | — | 82 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/c83014abce9c63eccca1d1b12af38ea4.png` | — | 82 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/cc9101852cf21bff67c43639773959cf.png` | — | 82 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/cd0661ad3c3c065e3b51b5dd357ceb67.png` | — | 82 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/d0207cf204eabdbc37b5db88f7e40b91.png` | — | 82 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/d58c34fea4cc8d4cf6c4cbcdbfbda9a6.png` | — | 82 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/dd9e820d6ccce60787388741db9dc8cf.png` | — | 102 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/df66d8168f79a19f811ae29e8f5c73ce.png` | — | 82 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/df9f2b908bf4ff172e2cb9ded9c2632a.png` | — | 82 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/e67a576a1cf73d85ba09357f13679f2e.png` | — | 102 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/eb8f712c5dcb3092d6a4064dd186b25b.png` | — | 102 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/f1477222ed8cd174a66cf690b8e32923.png` | — | 102 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/f504cbfb82fc6ca294f3de1ce1e2d858.png` | — | 82 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/f88050bf9b93642c06937882e426c55b.png` | — | 82 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/var/receipts/ff2a6b016df49fe82b669f42f625aaf2.png` | — | 82 | NOT-REVIEWED |
| بک‌اند (FastAPI) | `mp-app/backend/verify-addendum-gates.sh` | 120 | 6916 | NOT-REVIEWED |
| ریشه و تنظیمات | `.dockerignore` | 37 | 571 | NOT-REVIEWED |
| ریشه و تنظیمات | `.gitignore` | 81 | 1552 | NOT-REVIEWED |
| ریشه و تنظیمات | `.gitleaksignore` | 505 | 60102 | NOT-REVIEWED |
| ریشه و تنظیمات | `.repowise/decisions.yaml` | 66 | 3042 | NOT-REVIEWED |
| ریشه و تنظیمات | `.semgrep/mp-harness-rules.yml` | 186 | 7163 | NOT-REVIEWED |
| ریشه و تنظیمات | `.semgrep/project-rules.yml` | 131 | 4943 | NOT-REVIEWED |
| ریشه و تنظیمات | `.semgrep/tests/mp-ts-float-money.ts` | 19 | 625 | NOT-REVIEWED |
| ریشه و تنظیمات | `AGENTS.md` | 55 | 9199 | NOT-REVIEWED |
| ریشه و تنظیمات | `LICENSE` | 36 | 1637 | NOT-REVIEWED |
| ریشه و تنظیمات | `NOTICE-THIRD-PARTY.md` | 80 | 6770 | NOT-REVIEWED |
| ریشه و تنظیمات | `README.md` | 331 | 25176 | NOT-REVIEWED |
| ریشه و تنظیمات | `mp.db` | — | 884736 | NOT-REVIEWED |
| زیرساخت و کانتینر | `.devcontainer/Dockerfile` | 37 | 1674 | NOT-REVIEWED |
| زیرساخت و کانتینر | `.devcontainer/README.md` | 35 | 2553 | NOT-REVIEWED |
| زیرساخت و کانتینر | `.devcontainer/devcontainer.json` | 31 | 771 | NOT-REVIEWED |
| زیرساخت و کانتینر | `.devcontainer/post-create.sh` | 26 | 892 | NOT-REVIEWED |
| زیرساخت و کانتینر | `.devcontainer/provision-android-sdk.sh` | 97 | 4946 | NOT-REVIEWED |
| زیرساخت و کانتینر | `mp-app/infra/Caddyfile` | 47 | 1270 | NOT-REVIEWED |
| زیرساخت و کانتینر | `mp-app/infra/Dockerfile.backend` | — | 1176 | NOT-REVIEWED |
| زیرساخت و کانتینر | `mp-app/infra/ansible/inventory.ini` | 3 | 120 | NOT-REVIEWED |
| زیرساخت و کانتینر | `mp-app/infra/ansible/playbook.yml` | 46 | 1183 | NOT-REVIEWED |
| زیرساخت و کانتینر | `mp-app/infra/docker-compose.yml` | 160 | 5242 | NOT-REVIEWED |
| زیرساخت و کانتینر | `mp-app/infra/monitoring/alerts.yml` | 35 | 1202 | NOT-REVIEWED |
| زیرساخت و کانتینر | `mp-app/infra/monitoring/prometheus.yml` | 17 | 562 | NOT-REVIEWED |
| زیرساخت و کانتینر | `mp-app/infra/scripts/compress-media.sh` | 21 | 745 | NOT-REVIEWED |
| زیرساخت و کانتینر | `mp-app/infra/scripts/healthcheck.sh` | 18 | 812 | NOT-REVIEWED |
| زیرساخت و کانتینر | `mp-app/infra/scripts/rollback.sh` | 24 | 1019 | NOT-REVIEWED |
| سایر mp-app | `mp-app/deploy/docker-compose.yml` | 126 | 4116 | NOT-REVIEWED |
| سایر mp-app | `mp-app/shared/design-tokens.json` | 37 | 1004 | NOT-REVIEWED |
| سایر mp-app | `mp-app/shared/motion-spec.md` | 39 | 2412 | NOT-REVIEWED |
| سایر mp-app | `mp-app/tests/load/k6-gate.js` | 37 | 1348 | NOT-REVIEWED |
| شواهد QA | `evidence/m60/README.md` | 49 | 4770 | NOT-REVIEWED |
| شواهد QA | `evidence/m60/STATUS.md` | 51 | 4376 | NOT-REVIEWED |
| شواهد QA | `evidence/m60/aot-arm64.json` | 1 | 1090 | NOT-REVIEWED |
| شواهد QA | `evidence/m60/apk-audit.json` | 103 | 3088 | NOT-REVIEWED |
| شواهد QA | `evidence/m60/apk-deep-audit.json` | 89 | 2549 | NOT-REVIEWED |
| شواهد QA | `evidence/m60/dast.json` | 7 | 115 | NOT-REVIEWED |
| شواهد QA | `evidence/m60/flutter-arm64-v8a.json` | 1 | 2790 | NOT-REVIEWED |
| شواهد QA | `evidence/m60/flutter-armeabi-v7a.json` | 1 | 2803 | NOT-REVIEWED |
| شواهد QA | `evidence/m60/flutter-x86_64.json` | 1 | 2769 | NOT-REVIEWED |
| شواهد QA | `evidence/m60/live-proof.md` | 108 | 6140 | NOT-REVIEWED |
| شواهد QA | `evidence/m60/pkg-arm64.json` | 1 | 686 | NOT-REVIEWED |
| شواهد QA | `evidence/m60/res-arm64-v8a.json` | 1 | 6506 | NOT-REVIEWED |
| شواهد QA | `evidence/m60/res-arm64.json` | 1 | 679 | NOT-REVIEWED |
| شواهد QA | `evidence/m60/res-armeabi-v7a.json` | 1 | 6514 | NOT-REVIEWED |
| شواهد QA | `evidence/m60/res-x86_64.json` | 1 | 6494 | NOT-REVIEWED |
| شواهد QA | `qa-report/FINAL-REPORT.md` | 61 | 7584 | NOT-REVIEWED |
| شواهد QA | `qa-report/buttons.json` | 810 | 16530 | NOT-REVIEWED |
| شواهد QA | `qa-report/diagrams/payment-state-machine.html` | 83 | 4604 | NOT-REVIEWED |
| شواهد QA | `qa-report/graphs/load-latency-200users.png` | — | 40168 | NOT-REVIEWED |
| شواهد QA | `qa-report/load/locust_exceptions.csv` | — | 31 | NOT-REVIEWED |
| شواهد QA | `qa-report/load/locust_failures.csv` | — | 52 | NOT-REVIEWED |
| شواهد QA | `qa-report/load/locust_stats.csv` | — | 1477 | NOT-REVIEWED |
| شواهد QA | `qa-report/load/locust_stats_history.csv` | — | 10608 | NOT-REVIEWED |
| شواهد QA | `qa-report/screenshots/analytics.png` | — | 163797 | NOT-REVIEWED |
| شواهد QA | `qa-report/screenshots/assessment.png` | — | 109651 | NOT-REVIEWED |
| شواهد QA | `qa-report/screenshots/chat.png` | — | 124426 | NOT-REVIEWED |
| شواهد QA | `qa-report/screenshots/checkin.png` | — | 213065 | NOT-REVIEWED |
| شواهد QA | `qa-report/screenshots/dashboard.png` | — | 157729 | NOT-REVIEWED |
| شواهد QA | `qa-report/screenshots/expenses.png` | — | 144721 | NOT-REVIEWED |
| شواهد QA | `qa-report/screenshots/finance.png` | — | 165669 | NOT-REVIEWED |
| شواهد QA | `qa-report/screenshots/members.png` | — | 132409 | NOT-REVIEWED |
| شواهد QA | `qa-report/screenshots/nutrition.png` | — | 113152 | NOT-REVIEWED |
| شواهد QA | `qa-report/screenshots/programs.png` | — | 171959 | NOT-REVIEWED |
| شواهد QA | `qa-report/screenshots/shop.png` | — | 147735 | NOT-REVIEWED |
| شواهد QA | `qa-report/smoke-result.json` | 84 | 1385 | NOT-REVIEWED |
| شواهد QA | `qa-report/tools/browser/buttons.mjs` | 45 | 3163 | NOT-REVIEWED |
| شواهد QA | `qa-report/tools/browser/login.mjs` | 9 | 658 | NOT-REVIEWED |
| شواهد QA | `qa-report/tools/browser/smoke.mjs` | 36 | 2667 | NOT-REVIEWED |
| شواهد QA | `qa-report/tools/locustfile.py` | 54 | 1730 | NOT-REVIEWED |
| شواهد QA | `qa-report/tools/seed_live.py` | 28 | 1129 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/16_LAYER_PRODUCTION_PLAN.md` | 479 | 45441 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/ABILITY-14-FEASIBILITY-2026-11-14.md` | 95 | 10983 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/ACCESS-AUDIT-2026-11-15.md` | 112 | 8543 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/AGENT-TOOLING-REVIEWS.md` | 213 | 19013 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/ANDROID-OFFLINE-PLAN.md` | 71 | 7892 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/ARCHITECTURE-LAYERS-AND-STAGES.md` | 193 | 9705 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/AUDIT-2026-11-15.md` | 61 | 5098 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/BRANCH-CONSOLIDATION-2026-11-20.md` | 79 | 6139 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/BRAND-IDENTITY-BRIEF-2026-11-16.md` | 98 | 14790 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/BUILD-QUEUE.md` | 204 | 26536 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/BUILDER-START-AND-REPOWISE.md` | 64 | 11463 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/CHANGELOG.md` | 255 | 24464 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/COMPETITIVE-BENCHMARK-2026-11-14.md` | 169 | 22811 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/COMPETITIVE-UX-AUDIT-2026-11-16.md` | 197 | 16562 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/DATA-RETENTION.md` | 45 | 3725 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/DEPLOYMENT.md` | 91 | 10376 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/FACEID-PRIVACY-TEXT.md` | 19 | 1921 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/FINN_LOOP.md` | 380 | 40958 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/HANDOFF-ANALYSIS-2026-11-14.md` | 250 | 30702 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/HANDOFF-PROJECT-2026-11-18.md` | 139 | 31560 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/LOAD-TEST-2026-11-15.md` | 173 | 10902 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/LOOP-PLAN-M100-M106.md` | 65 | 15299 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/LOOP-PLAN-M22-M31.md` | 126 | 16395 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/LOOP-PLAN-M33-M40.md` | 99 | 11353 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/LOOP-PLAN-M63-M99.md` | 128 | 40879 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/M46-REPORT-2026-11-15.md` | 225 | 10939 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/MASTER-PLAN-M59.md` | 175 | 11369 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/MASTER_MAP.md` | 277 | 28237 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/OPS-RUNBOOK.md` | 132 | 12425 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/OSS-DEEP-RESEARCH-2026-11-18.md` | 130 | 28934 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/OSS-REUSE-RESEARCH-2026-11-16.md` | 124 | 34704 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/OUTPUT-AUDIT-2026-11-14.md` | 47 | 5160 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/OWNER-DECISIONS.md` | 219 | 19824 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/PILOT-PROTOCOL-M40.md` | 39 | 2824 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/PLAN-CLOUD-PRODUCTION.md` | 122 | 28540 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/PLAN-FINN-ECC-MICROLOOPS-QA.md` | 176 | 53468 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/PLAN-FINN-REA-ECC-CLOUD.md` | 79 | 19700 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/PLAN-MANUAL-TRANSFER.md` | 83 | 13304 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/PLAN-OSS-VALUE-MICROLOOPS-2026-11-18.md` | 37 | 10811 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/PRD.md` | 174 | 15822 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/PROPOSAL-SUBAGENTS-AND-CHECKPOINTS.md` | 85 | 17775 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/REA-OPERATIONS.md` | 237 | 12949 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/REA-REVIEW-2026-11-15.md` | 58 | 5100 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/READY-TO-BUILD-2026-11-15.md` | 247 | 15598 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/READY-TO-RESUME-2026-11-15.md` | 163 | 10249 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/RELEASE-CHECKLIST.md` | 62 | 5629 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/REPORT-ECC-QA-TRIAL-2026-11-18.md` | 37 | 7620 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/REPORT-ECC-SUBAGENT-SMOKE.md` | 23 | 5630 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/REPORT-FREE-ECC-ALTERNATIVES-2026-11-18.md` | 76 | 14018 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/REPORT-M113-N8N-MESSENGERS.md` | 46 | 13556 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/REPORT-OLD-ANDROID-KEY-REVIEW-2026-11-18.md` | 36 | 8925 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/REPORT-OSS-VALUE-DEEP-DIVE-2026-11-18.md` | 57 | 16030 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/REPORT-PR-3-REVIEW-2026-11-18.md` | 63 | 9566 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/REPORT-PRELOOP-READINESS-2026-11-18.md` | 23 | 7354 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/REPORT-QF-00-BASELINE-2026-11-19.md` | 190 | 37749 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/REPORT-REA-CODE-OSS-RESEARCH-2026-11-18.md` | 95 | 25022 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/REPORT-REA-ECC-SUBAGENTS.md` | 62 | 16030 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/ROADMAP-NEXT-2026-11-19.md` | 249 | 34005 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/SECURITY-AUDIT-2026-11-15.md` | 54 | 2920 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/SECURITY-REVIEW-2026-11-15.md` | 79 | 5279 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/SESSION_HANDOFF.md` | 283 | 64856 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/TODO-2026-11-16.md` | 557 | 96281 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/TODO-CLOUD-FINANCE-ACCESS.md` | 153 | 32699 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/TOOLING-RUNBOOK.md` | 71 | 6579 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/UI-CONTROLS-Q11.md` | 107 | 10091 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/adr/001-modular-monolith.md` | 25 | 1978 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/adr/002-sqlite-with-postgres-migration.md` | 26 | 1840 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/adr/003-rules-engine-over-llm.md` | 24 | 2197 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/adr/004-yunet-sface-face-recognition.md` | 24 | 1746 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/adr/005-n8n-boundary.md` | 43 | 5633 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/adr/README.md` | 22 | 2385 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/adr/TEMPLATE.md` | 42 | 1959 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/architecture/README.md` | 59 | 5934 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/architecture/c4.md` | 84 | 4444 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/architecture/cloud-finance-access.md` | 91 | 6803 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/architecture/interaction-baseline.json` | 11 | 229 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/architecture/interaction-map-2026-11-19.md` | 291 | 18627 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/architecture/interaction-map.json` | 2261 | 52640 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/architecture/module-map.md` | 25 | 2995 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/architecture/modules/shop.md` | 90 | 7764 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/architecture/oss-value-flows.md` | 40 | 3259 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/architecture/pr-review-flows-2026-11-18.md` | 55 | 5590 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/architecture/repowise-model-2026-11-19.dsl` | 583 | 22449 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/architecture/repowise-pr-review-2026-11-18.dsl` | 513 | 22577 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/architecture/repowise-pr-review-scope-2026-11-18.txt` | 576 | 26241 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/architecture/repowise-transfer-2026-11-18.dsl` | 511 | 22209 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/architecture/repowise-transfer-scope-2026-11-18.txt` | 564 | 25727 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/architecture/system-atlas.md` | 73 | 6836 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/assets/knowledge-atlas.svg` | 77 | 5239 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/assets/readme-hero.svg` | 66 | 4533 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/assets/system-architecture.svg` | 148 | 13022 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/BASELINE.md` | 200 | 34258 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/CHECKLIST.md` | 149 | 20514 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/DECISIONS.md` | 439 | 68492 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/EXECUTION-LOG.md` | 674 | 101569 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/FINN-AUDIT-LOOP.md` | 88 | 13193 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/INVENTORY.md` | 1715 | 164030 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/MICRO-LOOPS.md` | 83 | 6853 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/backend-coverage.xml` | 12153 | 430390 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/bandit.json` | 3064 | 84377 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/contract-invalid-authed.json` | 12111 | 477649 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/contract-invalid-findings.json` | 13 | 227 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/contract-matrix-raw.json` | 32264 | 845117 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/contract-rbac-findings.json` | 3692 | 73721 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/detect-secrets.err` | — | 0 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/detect-secrets.json` | 1463 | 53157 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/live-security-raw.json` | 654 | 17024 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/live-security-verdicts.json` | 93 | 4620 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/lizard-warnings.txt` | 55 | 6316 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/openapi-live.json` | 1 | 171735 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/otp-ratelimit-verdicts.json` | 1 | 2 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/radon-cc.txt` | 83 | 2578 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/radon-mi.txt` | 224 | 7654 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/ruff-blocking.rc` | — | 2 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/ruff-blocking.txt` | 1 | 19 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/ruff-format.rc` | — | 2 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/ruff-format.txt` | 1 | 28 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/ruff-recommended-stats.txt` | 44 | 1800 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/ruff-recommended.rc` | — | 2 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/ruff-recommended.txt` | 382 | 38125 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/ruff-tree-config.rc` | — | 2 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/ruff-tree-config.txt` | 340 | 34092 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/semgrep-project.json` | 1 | 12405 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/summary.json` | 22 | 418 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/T02-alembic-heads.txt` | 2 | 30 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/T03-orm-vs-db.txt` | 3 | 56 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/T04-tsc.log` | — | 0 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/T04.rc` | — | 18 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/T05-vitest.log` | — | 132149 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/T14-semgrep-backend-BASE-662ff88.json` | 1 | 28488 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/T14-semgrep-backend-full.json` | 1 | 13391 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/T14-semgrep-backend.json` | 1 | 8233 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/T15-semgrep-studio-BASE-662ff88.json` | 1 | 9172 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/T15-semgrep-studio.json` | 1 | 4793 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/T16-semgrep-client-BASE-662ff88.json` | 1 | 5395 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/T16-semgrep-client.json` | 1 | 4225 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/T17-eslint.json` | 1 | 14272 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/T17-eslint.log` | — | 0 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/T18-madge.log` | — | 91 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/T19-jscpd.log` | — | 3723 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/T19-jscpd/jscpd-report.json` | 133 | 3758 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/T20-knip-v5.err` | — | 0 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/T20-knip-v5.json` | 1 | 5528 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/T20-knip.err` | — | 1382 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/T20-knip.json` | 0 | 0 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/T21-mutmut-manual.json` | 461 | 10067 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/T23-pathid-scan-base.json` | 444 | 7185 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/T23-pathid-scan.json` | 444 | 7185 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/T30-smoke-recheck.txt` | 4 | 469 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/T30-smoke.txt` | 14 | 573 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/T37-otp-bruteforce.json` | 13 | 419 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/T38-xff-dockerfile.txt` | 4 | 248 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/T39-env-docker.txt` | 7 | 249 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/T40-load-plain-dev.log` | — | 1878 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/T46-load-instr.log` | — | 1022 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/T48-shop-S1.txt` | 3 | 337 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/T48-shop-S3.txt` | 3 | 383 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/bench_logging.log` | — | 973 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/contract_invalid.log` | — | 856 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/contract_matrix.log` | — | 608 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/contract_seed.log` | — | 1556 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/invalid_authed.log` | — | 2582 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/live-security-raw.json` | 577 | 14141 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/live-security-verdicts.json` | 72 | 3723 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/live_security.log` | — | 4018 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/load-backend-instr.json` | 61 | 1165 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/load-plain-dev.json` | 113 | 2193 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/logging-cost.json` | 85 | 1934 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/otp-ratelimit-verdicts.json` | 1 | 2 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/otp_bruteforce.log` | — | 88 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/otp_limits_all.log` | — | 1950 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/pool-events.jsonl` | — | 8145 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/rbac-systemerror-repro.json` | 22 | 525 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/repro_rbac.log` | — | 663 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/scan_ui_wiring.log` | — | 1358 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/scripts/T37_bruteforce.py` | 20 | 1162 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/scripts/mut_loop.py` | 23 | 1746 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/scripts/pathid_scan.py` | 26 | 1704 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/scripts/run-t-rows-2.sh` | 15 | 752 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/t-rows/scripts/run-t-rows.sh` | 20 | 993 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/vulture.txt` | 1 | 74 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/wp02/kit-probe/contract-rbac-findings-after.json` | 3608 | 72160 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/wp02/kit-probe/kit-all-after.log` | — | 2052 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/wp02/kit-probe/kit-all-before-change.log` | — | 2040 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/wp02/matrix-cells-clean.json` | 1 | 518446 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/wp02/matrix-eval-after.json` | 15 | 300 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/wp02/routes-HEAD-before.json` | 2958 | 53972 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/wp02/scripts/matrix-eval-run.log` | — | 301 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/wp02/scripts/matrix-runner-run2.log` | — | 86 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/wp02/scripts/wp02_eval.py` | 52 | 2647 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/wp02/scripts/wp02_matrix.py` | 72 | 3820 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/wp04/README.txt` | 9 | 876 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/wp04/coverage-by-dir.json` | 68 | 996 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/wp04/full-run.log` | — | 3797 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/wp24/out-after-miss2.txt` | 18 | 511 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/wp24/out-after2.txt` | 18 | 511 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/wp24/out-before.txt` | 22 | 620 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/wp31-load-ratios.json` | 45 | 1177 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/wp31/probe-invalid-authed-after.log` | — | 698 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/wp31/probe-invalid-authed-before-822e483.log` | — | 2581 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/wp31/summary.json` | 55 | 1581 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/wp32/probe-after-8926fcd+fix.log` | — | 2577 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/wp32/probe-before-0afd240.log` | — | 2579 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/after/wp32/summary.json` | 54 | 1820 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/bandit.json` | 3064 | 84377 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/before/bandit.json` | 3162 | 88436 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/before/detect-secrets.err` | — | 0 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/before/detect-secrets.json` | 1447 | 52573 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/before/lizard-warnings.txt` | 55 | 6316 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/before/radon-cc.txt` | 83 | 2578 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/before/radon-mi.txt` | 222 | 7620 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/before/ruff-blocking.rc` | — | 2 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/before/ruff-blocking.txt` | 1 | 19 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/before/ruff-format.rc` | — | 2 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/before/ruff-format.txt` | 1 | 28 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/before/ruff-recommended-stats.txt` | 54 | 2153 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/before/ruff-recommended.rc` | — | 2 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/before/ruff-recommended.txt` | 432 | 42414 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/before/ruff-tree-config.rc` | — | 2 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/before/ruff-tree-config.txt` | 1 | 19 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/before/semgrep-project.json` | 1 | 12345 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/before/summary.json` | 22 | 418 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/before/vulture.txt` | 1 | 74 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/detect-secrets.err` | — | 0 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/detect-secrets.json` | 1479 | 53680 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/lizard-warnings.txt` | 55 | 6316 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/pip-audit.json` | 1 | 5206 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/radon-cc.txt` | 83 | 2578 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/radon-mi.txt` | 224 | 7654 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/requirements-freeze.txt` | 91 | 1746 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/evidence/vulture.txt` | 1 | 74 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/findings.json` | 521 | 15410 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/measure-baseline.sh` | 79 | 5235 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/probes/probe_invalid_authed.repo-copy.py` | 213 | 11482 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/ruff-recommended.toml` | 70 | 4973 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/audit/status.json` | 94 | 10045 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/brand/concepts/M101-CONCEPTS.md` | 75 | 7809 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/brand/concepts/m101-a-geometric-mp.png` | — | 85273 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/brand/concepts/m101-a-geometric-mp.svg` | 87 | 6179 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/brand/concepts/m101-b-wordmark-led.png` | — | 88038 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/brand/concepts/m101-b-wordmark-led.svg` | 88 | 6352 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/brand/concepts/m101-c-progress-loop.png` | — | 89760 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/brand/concepts/m101-c-progress-loop.svg` | 90 | 6476 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/brand/concepts/m101-three-options-comparison.png` | — | 110809 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/brand/concepts/m101-three-options-comparison.svg` | 104 | 6917 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/brand/selected-c/M103-C-PACKAGE.md` | 54 | 7832 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/brand/selected-c/m103-c-progress-loop-refinement.png` | — | 98769 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/brand/selected-c/m103-c-progress-loop-refinement.svg` | 77 | 5798 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/brand/selected-c/m103-mark-size-check.png` | — | 27217 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/brand/selected-c/mp-progress-background.png` | — | 3925 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/brand/selected-c/mp-progress-background.svg` | 5 | 339 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/brand/selected-c/mp-progress-foreground.png` | — | 11539 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/brand/selected-c/mp-progress-foreground.svg` | 9 | 713 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/brand/selected-c/mp-progress-icon-preview.png` | — | 11891 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/brand/selected-c/mp-progress-icon-preview.svg` | 10 | 798 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/brand/selected-c/mp-progress-lockup-dark-vazirmatn-candidate.png` | — | 19725 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/brand/selected-c/mp-progress-lockup-dark-vazirmatn-candidate.svg` | 12 | 1143 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/brand/selected-c/mp-progress-lockup-dark.png` | — | 19725 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/brand/selected-c/mp-progress-lockup-dark.svg` | 12 | 1039 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/brand/selected-c/mp-progress-lockup-light.png` | — | 18771 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/brand/selected-c/mp-progress-lockup-light.svg` | 12 | 1003 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/brand/selected-c/mp-progress-lockup-mono-dark.png` | — | 17385 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/brand/selected-c/mp-progress-lockup-mono-dark.svg` | 11 | 956 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/brand/selected-c/mp-progress-lockup-mono-light.png` | — | 17707 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/brand/selected-c/mp-progress-lockup-mono-light.svg` | 11 | 945 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/brand/selected-c/mp-progress-mark-16px.png` | — | 445 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/brand/selected-c/mp-progress-mark-16px.svg` | 8 | 647 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/brand/selected-c/mp-progress-mark-mono-dark.png` | — | 28694 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/brand/selected-c/mp-progress-mark-mono-dark.svg` | 8 | 602 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/brand/selected-c/mp-progress-mark-mono.png` | — | 21051 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/brand/selected-c/mp-progress-mark-mono.svg` | 8 | 544 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/brand/selected-c/mp-progress-mark.png` | — | 21206 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/brand/selected-c/mp-progress-mark.svg` | 9 | 680 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/delivery-reports/2026-11-14-final.md` | 30 | 2745 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/delivery-reports/2026-11-14-global.md` | 57 | 7868 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/design/ADMIN-ARCHITECTURE.md` | 40 | 4470 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/design/DECISIONS.md` | 54 | 4949 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/design/DESIGN.md` | 68 | 5896 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/design/design-system.md` | 42 | 2459 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/design/web-interface-guidelines.checklist.md` | 94 | 5904 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/evals/phase6-money-scenarios.md` | 38 | 3909 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/finn/check-rea-skill.sh` | 28 | 1141 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/finn/install-ecc.sh` | 5 | 246 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/finn/install-toolchain.sh` | 172 | 8604 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/finn/test-check-rea-skill.sh` | 26 | 1240 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/guides/flutter-codespace.md` | 79 | 4096 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/handoff/fitness-handoff-2026-11-11.zip` | — | 97258 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/runbooks/codespaces-execution.md` | 257 | 21949 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/runbooks/incident.md` | 22 | 2672 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/runbooks/provisioning.md` | 50 | 5740 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/runbooks/rollback.md` | 31 | 2858 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/security/biometric-policy.md` | 30 | 1932 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/security/owasp-checklist.md` | 21 | 2071 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/testing/performance-budget.md` | 18 | 1110 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/testing/test-reports.md` | 34 | 2234 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/ui-previews/01-studio-dashboard.png` | — | 1334538 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/ui-previews/02-client-today-workout.png` | — | 1479109 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/ui-previews/03-kiosk-face-gate.png` | — | 1685735 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/ui-previews/04-payment-receipt.png` | — | 1731496 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/ui-previews/05-member-profile.png` | — | 628461 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/ui-previews/06-coach-report.png` | — | 1189456 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/ui-previews/07-client-home-grid.png` | — | 2119140 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/ui-previews/08-client-bodycomp-results.png` | — | 550098 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/user-stories/coach.md` | 32 | 4035 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/user-stories/manager.md` | 31 | 2919 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/user-stories/member.md` | 48 | 5804 | NOT-REVIEWED |
| مستندات | `docs/MuscleParadise/user-stories/reception.md` | 20 | 2017 | NOT-REVIEWED |
| مستندات | `docs/README.md` | 106 | 10628 | NOT-REVIEWED |
| مستندات | `docs/architecture/diagram-design/01-architecture.html` | 68 | 6789 | NOT-REVIEWED |
| مستندات | `docs/architecture/diagram-design/02-payments-lifecycle.html` | 51 | 5112 | NOT-REVIEWED |
| مستندات | `docs/architecture/diagram-design/03-ci-release.html` | 61 | 5774 | NOT-REVIEWED |
| مستندات | `docs/architecture/diagram-design/png/01-architecture.png` | — | 146270 | NOT-REVIEWED |
| مستندات | `docs/architecture/diagram-design/png/02-payments-lifecycle.png` | — | 86723 | NOT-REVIEWED |
| مستندات | `docs/architecture/diagram-design/png/03-ci-release.png` | — | 133208 | NOT-REVIEWED |
| مستندات | `docs/architecture/repowise/PROJECT-HANDOFF.md` | 458 | 35000 | NOT-REVIEWED |
| مستندات | `docs/architecture/repowise/README.md` | 29 | 2388 | NOT-REVIEWED |
| مستندات | `docs/architecture/repowise/architecture.dsl` | 288 | 11578 | NOT-REVIEWED |
| مستندات | `docs/architecture/repowise/findings-2026-11-20.md` | 21 | 1945 | NOT-REVIEWED |
| مستندات | `docs/architecture/repowise/findings-main-e5c8891.md` | 39 | 3562 | NOT-REVIEWED |
| گزارش‌های عامل | `.finn/state/DECISIONS.md` | 355 | 61808 | NOT-REVIEWED |
| گزارش‌های عامل | `.finn/state/LEDGER.md` | 195 | 40160 | NOT-REVIEWED |
| گزارش‌های عامل | `.finn/state/REGRESSIONS.md` | 118 | 26695 | NOT-REVIEWED |
| گزارش‌های عامل | `.finn/state/STATE.md` | 286 | 45724 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/FINAL_REPORT.md` | 132 | 10670 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/fixtures/ecc-qa-smoke/README.md` | 15 | 1318 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/fixtures/ecc-qa-smoke/contract.json` | 45 | 911 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/fixtures/ecc-qa-smoke/safe_fixture.py` | 7 | 358 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/fixtures/ecc-qa-smoke/trial_tests.py` | 13 | 945 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/fixtures/ecc-qa-smoke/unsafe_policy.py` | 3 | 209 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/2026-11-16-toolchain-install.md` | 72 | 7379 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/M02-code-review.md` | 14 | 846 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/M03-code-review.md` | 16 | 1001 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/M04-code-review.md` | 17 | 1183 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/M05-code-review.md` | 22 | 1369 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/M06-code-review.md` | 25 | 1922 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/M07-code-review.md` | 17 | 1069 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/M08-code-review.md` | 15 | 1250 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/M08-security-review.md` | 17 | 1319 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/M09-security-review.md` | 18 | 1547 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/M10-code-review.md` | 14 | 828 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/M11-code-review.md` | 14 | 806 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/M12-code-review.md` | 14 | 876 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/M13-code-review.md` | 14 | 934 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/M14-code-review.md` | 14 | 927 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/M15-code-review.md` | 14 | 834 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/M16-code-review.md` | 15 | 850 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/M18-code-review.md` | 16 | 1576 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/M19-code-review.md` | 15 | 1171 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/M20-code-review.md` | 15 | 1010 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/M21-code-review.md` | 19 | 701 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/apk-ci/RUN.txt` | 1 | 38 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/apk-ci/step-analyze.txt` | 131 | 30626 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/apk-ci/step-build.txt` | 173 | 11643 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/apk-ci/step-icons.txt` | 12 | 644 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/apk-ci/step-pubget.txt` | 101 | 2940 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/apk-ci/step-test.txt` | 35 | 4019 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/audit/2026-11-14-dataflow-audit.md` | 22 | 1975 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/backend-ci/RUN.txt` | 1 | 28 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/backend-ci/backend-bandit.txt` | 6 | 460 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/backend-ci/backend-lint.txt` | 2 | 47 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/backend-ci/backend-pipaudit.txt` | 4 | 224 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/backend-ci/backend-test.txt` | 52 | 4411 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/ci-follow-up-441922-441942.md` | 110 | 9161 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/ci-run-44176044057.md` | 25 | 2102 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/client-ci/RUN.txt` | 1 | 35 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/client-ci/client-analyze.txt` | 151 | 35175 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/client-ci/client-test.txt` | 422 | 28236 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/codespaces-user-handoff.md` | 51 | 8142 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/ecc-native-setup.md` | 10 | 2552 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/eval/2026-11-14-EVAL-SUMMARY.md` | 45 | 3130 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/eval/2026-11-14-after-fixes.json` | 16 | 383 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/eval/2026-11-14-after-fixes.md` | 16 | 857 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/eval/2026-11-14-after-wrist-fix.json` | 16 | 382 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/eval/2026-11-14-after-wrist-fix.md` | 16 | 832 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/eval/2026-11-14-baseline.json` | 27 | 1435 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/eval/2026-11-14-baseline.md` | 31 | 1924 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/eval/2026-11-14-m35c3-scoring-eval.json` | 28 | 467 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/eval/2026-11-14-m38c3-prescription-eval.json` | 22 | 351 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/eval/2026-11-15-llm-column.json` | 10 | 423 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/eval/2026-11-15-llm-column.md` | 46 | 2227 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/evidence/M33c1-free-exercise-db.rule-evidence.json` | 29 | 1343 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/evidence/M33c3-axis-tagging.rule-evidence.json` | 223 | 6332 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/evidence/M34c1-progression-ladders.rule-evidence.json` | 305 | 7563 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/evidence/M34c2-four-state-decision.rule-evidence.json` | 20 | 1049 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/evidence/M34c3-load-attribution.rule-evidence.json` | 14 | 749 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/evidence/M35c1-norm-tables.rule-evidence.json` | 38 | 1690 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/evidence/M35c2-scoring-engine.rule-evidence.json` | 17 | 942 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/evidence/M36c2-axis-assessment-api.rule-evidence.json` | 20 | 1121 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/evidence/M36c3-review-audit.rule-evidence.json` | 20 | 1106 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/evidence/M39c3-set-feedback.perf.json` | 26 | 1044 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/evidence/M40-pilot-dryrun.rule-evidence.json` | 18 | 1168 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/evidence/M44-churn-risk.rule-evidence.json` | 21 | 1502 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/flutter-sdk-provisioning.md` | 71 | 12333 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/load/M22-smoke-report.md` | 28 | 1897 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/load/M22-smoke_exceptions.csv` | — | 31 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/load/M22-smoke_failures.csv` | — | 198 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/load/M22-smoke_stats.csv` | — | 983 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/load/M22-smoke_stats_history.csv` | — | 3494 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/load/M30-smoke-report.md` | 5 | 420 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/load/M36c2-smoke_exceptions.csv` | — | 31 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/load/M36c2-smoke_failures.csv` | — | 504 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/load/M36c2-smoke_stats.csv` | — | 1349 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/load/M36c2-smoke_stats_history.csv` | — | 1870 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/m104-startup-measurement.md` | 40 | 4312 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/m106-brand-identity-review.md` | 50 | 5553 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/m107-codespaces-rails.md` | 45 | 5077 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/m108-ci-pinned-gates.md` | 58 | 9151 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/m109-dart-format.md` | 143 | 13377 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/m110-sandbox-bank.md` | 88 | 8041 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/m112-release-signing-hardening.md` | 53 | 3157 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/m64-workflow-audit.md` | 29 | 3734 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/m65-qr-security.md` | 27 | 3132 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/m67-studio-auth.md` | 38 | 7351 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/m70-settings-role-gate.md` | 27 | 3504 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/m71-api-coverage.md` | 35 | 4237 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/m72-membership-display.md` | 39 | 5342 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/m73-food-logging.md` | 51 | 7053 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/m74-class-cancel.md` | 45 | 5183 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/m75-notifications.md` | 41 | 4341 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/m76-readiness.md` | 30 | 3414 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/m77-weekly-volume.md` | 26 | 2752 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/m78-adaptive-nutrition-client.md` | 39 | 4986 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/m79-jp7-crosswalk.md` | 30 | 3630 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/m80-member-checkin-history.md` | 30 | 3575 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/m81-member-chat.md` | 43 | 6243 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/m82-phone-change.md` | 51 | 6676 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/m83-wallet-ledger.md` | 44 | 5414 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/m84-class-booking-name.md` | 27 | 4178 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/m85-screening-scope.md` | 18 | 1576 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/m86-offline-contract.md` | 23 | 2543 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/m87-android-feedback-outbox.md` | 53 | 9089 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/m90-member-receipt.md` | 64 | 10549 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/m97-migration-drift.md` | 71 | 10502 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/m98-haptics-motion.md` | 84 | 13828 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/m99-closeout-report.md` | 141 | 16373 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/rea/2026-11-15-REA-AUDIT-VERIFY.md` | 77 | 5676 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/rea/2026-11-15-REA-GAP-CLOSURE.md` | 85 | 5486 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/rea/2026-11-15-apk-inventory-summary.json` | 129 | 4837 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/rea/2026-11-15-apk-release-exposure.json` | 1 | 10588 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/rea/2026-11-15-studio-after-m45.json` | 84 | 3479 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/rea/2026-11-15-studio-js-analysis.json` | 315 | 10034 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/rea/REA-AUDIT.md` | 40 | 4647 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/rea/analyze.json` | 1 | 3544 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/rea/cloud-finance-hesabdar-reference-summary.json` | 178 | 4052 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/rea/cloud-finance-openbooks-reference-summary.json` | 178 | 4059 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/rea/ecc-isolated-smoke-metadata.json` | 31 | 1233 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/rea/ecc-task-only-smoke-metadata.json` | 26 | 1105 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/rea/extract-artifact.json` | 1 | 117933 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/rea/free-ecc-alternatives-smoke-metadata.json` | 108 | 2857 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/rea/identify-flutter-build.json` | 1 | 2846 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/rea/inspect-android-package.json` | 1 | 686 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/rea/inspect-artifact.json` | 1 | 413366 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/rea/inspect-dart-aot.json` | 1 | 1118 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/rea/m113-review.md` | 37 | 7242 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/rea/oss-deep-casbin-adapter.json` | 223 | 5035 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/rea/oss-deep-ledgerline.json` | 197 | 4459 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/rea/oss-deep-persiantools.json` | 273 | 6149 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/rea/oss-deep-pgdispatch.json` | 278 | 6478 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/rea/oss-deep-uploadshield.json` | 205 | 4601 | NOT-REVIEWED |
| گزارش‌های عامل | `finn/reports/rea/project-ecc-orchestration-summary.json` | 267 | 12773 | NOT-REVIEWED |
