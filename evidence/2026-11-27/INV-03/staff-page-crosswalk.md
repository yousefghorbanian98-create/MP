# INV-03 — crosswalk صفحات کارکنان (v2)

> **وضعیت:** `PARTIAL / NOT_ACCEPTED`. این نسخه سه false-negative نسخهٔ اول را
> رفع می‌کند (تمپلیت `${base}`, alias نقش‌ها, مسیرهای پویا) — طبق یافته‌های
> `review.md` خودِ اجرای قبلی. هیچ ردیفی CURRENT نمی‌شود.

- SHA: `485d9625aebc95212b19ba5674679fa3042f3664` · branch: `arena/3c08bfbd-mp` · tracked-dirty: `False` · untracked: `0`
- `backend/api/routes.json` → `sha256_b64:fwMz37kqW7VlFLfgA8x4Nw_H6Pq-OpqLU0LMqrmoTPg`
- `backend/security/rbac.py` → `sha256_b64:qHQPdbM-hk4aOZD0134vp4HwwhBcEz2YkqQc5j_fnSw`
- `studio/src/lib/roleNav.ts` → `sha256_b64:ZQ_3Q0OvbiUBD2oHurTeR30v_vzulL45I6IA7QXVMiA`
- `studio/src/lib/api.ts` → `sha256_b64:9SGYAkelFLPOe5b8cy7f5zsIErOwivvBMoafb3YagJM`
- `studio/src/lib/adminApi.ts` → `sha256_b64:YSy9HomngwFUX2fIgmRRmnxJLRSO9Ed5BQ9QzBMn8s4`
- `studio/src/lib/navigation.ts` → `sha256_b64:sz8wEjTEfIIxJmtt5DR6wfVGSMqCSpKqNKtdhjyLbgY`
- call-site: `{'template-base': 29, 'helper': 70, 'literal': 0}` · پویا: **0**
- شمارش: `PARTIAL_REVIEW=12`

| وضعیت | معنا |
|---|---|
| `PARTIAL_REVIEW` | route/نقش + call-site + اشارهٔ تستی؛ مجوز اثبات نشده |
| `GAP` | call-site یا تست همان مسیر نیست |
| `DYNAMIC_UNCOVERED` | فقط call پویا؛ اسکنر استاتیک نمی‌تواند نگاشت کند — بررسی دستی |
| `BLOCKED` | مسیر/نقشهٔ دامنه وجود ندارد |
| `CURRENT` | **هرگز در این نسخه صادر نمی‌شود** |

| # | کلید | فایل | route | نقش‌ها (alias حل‌شده) | API مصرف‌شده/کل | call-site | پویای پوشش‌داده‌نشده | اشارهٔ تستی | وضعیت |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `dashboard` | 1 فایل | `/staff/dashboard` | super_admin, admin, manager, coach, reception, member | 3 / 4 | `api.ts` | — | `a11y.test.tsx`<br>`api.test.ts`<br>`authFlow.test.tsx`<br>`liveContract.test.ts` | **PARTIAL_REVIEW** |
| 2 | `members` | 1 فایل | `/staff/members` | super_admin, admin, manager, coach, reception | 4 / 11 | `AuthContext.tsx`<br>`api.ts` | — | `a11y.test.tsx`<br>`api.test.ts`<br>`apiCoverage.test.ts`<br>`authFlow.test.tsx` | **PARTIAL_REVIEW** |
| 3 | `programs` | 1 فایل | `/staff/programs` | super_admin, admin, manager, coach, member | 3 / 10 | `api.ts` | — | `apiCoverage.test.ts`<br>`locustfile_full.py`<br>`setFeedback.test.tsx`<br>`test_axis_assessment_api.py` | **PARTIAL_REVIEW** |
| 4 | `nutrition` | 1 فایل | `/staff/nutrition` | super_admin, admin, manager, coach, member | 3 / 9 | `api.ts` | — | `test_e2e_adaptive_loop.py`<br>`test_m49_adaptive_nutrition.py`<br>`test_m49_food_logging.py`<br>`test_m78_adaptive_nutrition_client.py` | **PARTIAL_REVIEW** |
| 5 | `assessment` | 1 فایل | `/staff/assessment` | super_admin, admin, manager, coach, member | 3 / 8 | `api.ts` | — | `apiCoverage.test.ts`<br>`test_ai_kpis.py`<br>`test_api_contract.py`<br>`test_battle.py` | **PARTIAL_REVIEW** |
| 6 | `chat` | 1 فایل | `/staff/chat` | super_admin, admin, manager, coach, reception, member | 1 / 3 | `api.ts` | — | `a11y.test.tsx`<br>`test_e2e_adaptive_loop.py`<br>`test_m51_chat.py` | **PARTIAL_REVIEW** |
| 7 | `checkin` | 1 فایل | `/staff/checkin` | super_admin, admin, manager, coach, reception, member | 2 / 11 | `api.ts` | — | `a11y.test.tsx`<br>`locustfile_full.py`<br>`memberCheckin.test.tsx`<br>`test_m45_checkin_feed.py` | **PARTIAL_REVIEW** |
| 8 | `finance` | 1 فایل | `/staff/finance` | super_admin, admin, manager | 4 / 21 | `api.ts` | — | `locustfile_full.py`<br>`memberPayments.test.tsx`<br>`paymentPanel.test.tsx`<br>`receiptQueue.test.tsx` | **PARTIAL_REVIEW** |
| 9 | `expenses` | 1 فایل | `/staff/expenses` | super_admin, admin, manager | 1 / 3 | `api.ts` | — | `test_phase6c_expenses.py`<br>`test_phase8_release_sweep.py`<br>`test_qf06_expense_receipt.py`<br>`test_routes_effective_guards.py` | **PARTIAL_REVIEW** |
| 10 | `analytics` | 1 فایل | `/staff/analytics` | super_admin, admin, manager, coach | 2 / 4 | `adminApi.ts` | — | `a11y.test.tsx`<br>`locustfile_full.py`<br>`test_admin_analytics.py` | **PARTIAL_REVIEW** |
| 11 | `settings` | 1 فایل | `/staff/settings` | super_admin, admin | 13 / 17 | `adminApi.ts`<br>`api.ts`<br>`update.ts` | — | `a11y.test.tsx`<br>`adminPermissions.test.tsx`<br>`api.test.ts`<br>`authFlow.test.tsx` | **PARTIAL_REVIEW** |
| 12 | `shop` | 1 فایل | `/staff/shop` | super_admin, admin, manager, coach, reception, member | 8 / 15 | `api.ts` | — | `apiCoverage.test.ts`<br>`memberShop.test.tsx`<br>`test_m59_shop.py`<br>`test_phase2_shop_display.py` | **PARTIAL_REVIEW** |

## چه چیزی این نسخه هنوز اثبات نمی‌کند

- مجوز سمت سرور؛ `routes.json`/`rbac.py` شاهد قرارداد است، نه اجرا.
- مالکیت: تست منفی (عضو A → دادهٔ عضو B) در همین اجرا اجرا نشده.
- تمایز «مصرف‌کنندهٔ صفحهٔ عضو» از «پنل کارکنان»: فایل مشترک است (`api.ts`,
  `adminApi.ts`)؛ تفکیک کامپوننتی نیاز به مرور دستی دارد.
- مرورگر/دستگاه/نصب‌پذیری و reviewer مستقل.

## بازتولید

```bash
python3 scripts/crosswalk_v2.py --repo . --kind staff --out evidence/<DATE>/INV-03
```
