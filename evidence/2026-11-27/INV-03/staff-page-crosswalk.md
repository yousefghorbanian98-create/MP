# INV-03 — crosswalk صفحات کارکنان (v2)

> **وضعیت:** `PARTIAL / NOT_ACCEPTED`. این نسخه سه false-negative نسخهٔ اول را
> رفع می‌کند (تمپلیت `${base}`, alias نقش‌ها, مسیرهای پویا) — طبق یافته‌های
> `review.md` خودِ اجرای قبلی. هیچ ردیفی CURRENT نمی‌شود.

- SHA: `7399142fd10f5efcf2fefc3e65359f2f868dd9b0` · branch: `arena/3c08bfbd-mp` · tracked-dirty: `False` · untracked: `0`
- `backend/api/routes.json` → `sha256:7f0333dfb92a5bb56514b7e003cc78370fc7e8fabe3a9a8b5342ccaab9a84cf8`
- `backend/security/rbac.py` → `sha256:a8740f75b33e864e1a3990f4d77e2fa781f0c2105c133d9892a41ce63fdf9d2c`
- `studio/src/lib/roleNav.ts` → `sha256:650ff74343af6e25010f6a07bab4de477d2ffefcee94be3923a200ed05d53220`
- `studio/src/lib/api.ts` → `sha256:77e368e3743431bef553a82cd06e8f8414ad833ea99b161b794a8548ea1021eb`
- `studio/src/lib/adminApi.ts` → `sha256:612cbd1e89a78301545f67c88264519a7c492d148ef44779050f50cc1327f2ce`
- `studio/src/lib/navigation.ts` → `sha256:6f9b434207f6fdbfb6701355e323ceaac2f3d10d2d2e505a820ae32752f206b6`
- call-site: `{'template-base': 28, 'helper': 59, 'literal': 0}` · پویا: **0**
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
| 3 | `programs` | 1 فایل | `/staff/programs` | super_admin, admin, manager, coach, member | 2 / 10 | `api.ts` | — | `apiCoverage.test.ts`<br>`locustfile_full.py`<br>`test_axis_assessment_api.py`<br>`test_battle.py` | **PARTIAL_REVIEW** |
| 4 | `nutrition` | 1 فایل | `/staff/nutrition` | super_admin, admin, manager, coach, member | 3 / 9 | `api.ts` | — | `test_e2e_adaptive_loop.py`<br>`test_m49_adaptive_nutrition.py`<br>`test_m49_food_logging.py`<br>`test_m78_adaptive_nutrition_client.py` | **PARTIAL_REVIEW** |
| 5 | `assessment` | 1 فایل | `/staff/assessment` | super_admin, admin, manager, coach, member | 3 / 8 | `api.ts` | — | `apiCoverage.test.ts`<br>`test_ai_kpis.py`<br>`test_api_contract.py`<br>`test_battle.py` | **PARTIAL_REVIEW** |
| 6 | `chat` | 1 فایل | `/staff/chat` | super_admin, admin, manager, coach, reception, member | 1 / 3 | `api.ts` | — | `a11y.test.tsx`<br>`test_e2e_adaptive_loop.py`<br>`test_m51_chat.py` | **PARTIAL_REVIEW** |
| 7 | `checkin` | 1 فایل | `/staff/checkin` | super_admin, admin, manager, coach, reception, member | 1 / 11 | `api.ts` | — | `a11y.test.tsx`<br>`locustfile_full.py`<br>`test_m45_checkin_feed.py`<br>`test_m46_security_matrix.py` | **PARTIAL_REVIEW** |
| 8 | `finance` | 1 فایل | `/staff/finance` | super_admin, admin, manager | 4 / 21 | `api.ts` | — | `locustfile_full.py`<br>`paymentPanel.test.tsx`<br>`receiptQueue.test.tsx`<br>`test_api_contract.py` | **PARTIAL_REVIEW** |
| 9 | `expenses` | 1 فایل | `/staff/expenses` | super_admin, admin, manager | 1 / 3 | `api.ts` | — | `test_phase6c_expenses.py`<br>`test_phase8_release_sweep.py`<br>`test_qf06_expense_receipt.py`<br>`test_routes_effective_guards.py` | **PARTIAL_REVIEW** |
| 10 | `analytics` | 1 فایل | `/staff/analytics` | super_admin, admin, manager, coach | 2 / 4 | `adminApi.ts` | — | `a11y.test.tsx`<br>`locustfile_full.py`<br>`test_admin_analytics.py` | **PARTIAL_REVIEW** |
| 11 | `settings` | 1 فایل | `/staff/settings` | super_admin, admin | 13 / 17 | `adminApi.ts`<br>`api.ts`<br>`update.ts` | — | `a11y.test.tsx`<br>`adminPermissions.test.tsx`<br>`api.test.ts`<br>`authFlow.test.tsx` | **PARTIAL_REVIEW** |
| 12 | `shop` | 1 فایل | `/staff/shop` | super_admin, admin, manager, coach, reception, member | 8 / 15 | `api.ts` | — | `apiCoverage.test.ts`<br>`test_m59_shop.py`<br>`test_phase2_shop_display.py`<br>`test_phase3_no_online_gateway.py` | **PARTIAL_REVIEW** |

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
