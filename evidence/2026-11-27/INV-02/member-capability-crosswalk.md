# INV-02 — crosswalk عضو (v2)

> **وضعیت:** `PARTIAL / NOT_ACCEPTED`. این نسخه سه false-negative نسخهٔ اول را
> رفع می‌کند (تمپلیت `${base}`, alias نقش‌ها, مسیرهای پویا) — طبق یافته‌های
> `review.md` خودِ اجرای قبلی. هیچ ردیفی CURRENT نمی‌شود.

- SHA: `90f0896de4089f8c581bbccbda76b941ce13731c` · branch: `arena/3c08bfbd-mp` · tracked-dirty: `False` · untracked: `0`
- `backend/api/routes.json` → `sha256_b64:fwMz37kqW7VlFLfgA8x4Nw_H6Pq-OpqLU0LMqrmoTPg`
- `backend/security/rbac.py` → `sha256_b64:qHQPdbM-hk4aOZD0134vp4HwwhBcEz2YkqQc5j_fnSw`
- `studio/src/lib/roleNav.ts` → `sha256_b64:ZQ_3Q0OvbiUBD2oHurTeR30v_vzulL45I6IA7QXVMiA`
- `studio/src/lib/api.ts` → `sha256_b64:u7PafkCfgDhLFBkj5cizbsnmUb7HNaRdYJXCbiECcKY`
- `studio/src/lib/adminApi.ts` → `sha256_b64:YSy9HomngwFUX2fIgmRRmnxJLRSO9Ed5BQ9QzBMn8s4`
- `studio/src/lib/navigation.ts` → `sha256_b64:qU1pePZ45tLOOfLiQwAgWSHqQ8ke3ZLMOBM7fGAvDSA`
- call-site: `{'template-base': 29, 'helper': 68, 'literal': 0}` · پویا: **0**
- شمارش: `GAP=3` · `PARTIAL_REVIEW=14`

| وضعیت | معنا |
|---|---|
| `PARTIAL_REVIEW` | route/نقش + call-site + اشارهٔ تستی؛ مجوز اثبات نشده |
| `GAP` | call-site یا تست همان مسیر نیست |
| `DYNAMIC_UNCOVERED` | فقط call پویا؛ اسکنر استاتیک نمی‌تواند نگاشت کند — بررسی دستی |
| `BLOCKED` | مسیر/نقشهٔ دامنه وجود ندارد |
| `CURRENT` | **هرگز در این نسخه صادر نمی‌شود** |

| # | کلید | فایل | route | نقش‌ها (alias حل‌شده) | API مصرف‌شده/کل | call-site | پویای پوشش‌داده‌نشده | اشارهٔ تستی | وضعیت |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `assessment14` | 2 فایل | — | — | 2 / 7 | `api.ts` | — | `apiCoverage.test.ts`<br>`test_api_contract.py`<br>`test_battle.py`<br>`test_e2e_adaptive_loop.py` | **PARTIAL_REVIEW** |
| 2 | `auth` | 1 فایل | — | — | 8 / 10 | `api.ts`<br>`session.ts` | — | `a11y.test.tsx`<br>`apiCoverage.test.ts`<br>`authFlow.test.tsx`<br>`deviceSessions.test.tsx` | **PARTIAL_REVIEW** |
| 3 | `bodycomp` | 1 فایل | — | — | 2 / 8 | `api.ts` | — | `apiCoverage.test.ts`<br>`test_api_contract.py`<br>`test_battle.py`<br>`test_e2e_adaptive_loop.py` | **PARTIAL_REVIEW** |
| 4 | `chat` | 2 فایل | — | super_admin, admin, manager, coach, reception, member | 1 / 3 | `api.ts` | — | `a11y.test.tsx`<br>`test_e2e_adaptive_loop.py`<br>`test_m51_chat.py` | **PARTIAL_REVIEW** |
| 5 | `checkin` | 2 فایل | — | super_admin, admin, manager, coach, reception, member | 2 / 12 | `api.ts` | — | `a11y.test.tsx`<br>`locustfile_full.py`<br>`memberCheckin.test.tsx`<br>`test_m45_checkin_feed.py` | **PARTIAL_REVIEW** |
| 6 | `classes` | 1 فایل | — | — | 3 / 3 | `ScheduleTimeline.tsx`<br>`api.ts` | — | `a11y.test.tsx`<br>`apiCoverage.test.ts`<br>`authFlow.test.tsx`<br>`memberClasses.test.tsx` | **PARTIAL_REVIEW** |
| 7 | `feedback` | 3 فایل | — | — | 3 / 10 | `api.ts` | — | `apiCoverage.test.ts`<br>`locustfile_full.py`<br>`setFeedback.test.tsx`<br>`test_axis_assessment_api.py` | **PARTIAL_REVIEW** |
| 8 | `home` | 1 فایل | — | — | 1 / 11 | `AuthContext.tsx`<br>`api.ts` | — | `a11y.test.tsx`<br>`api.test.ts`<br>`authFlow.test.tsx`<br>`liveContractMember.test.ts` | **PARTIAL_REVIEW** |
| 9 | `intake` | 2 فایل | — | — | 0 / 3 | — | — | — | **GAP** |
|  |  |  |  |  |  |  |  |  | ↳ هیچ call-site استاتیکی برای مسیرهای این دامنه نیست |
| 10 | `notifications` | 1 فایل | — | — | 0 / 4 | — | — | — | **GAP** |
|  |  |  |  |  |  |  |  |  | ↳ هیچ call-site استاتیکی برای مسیرهای این دامنه نیست |
| 11 | `nutrition` | 2 فایل | — | super_admin, admin, manager, coach, member | 3 / 8 | `api.ts` | — | `test_e2e_adaptive_loop.py`<br>`test_m49_adaptive_nutrition.py`<br>`test_m49_food_logging.py`<br>`test_m78_adaptive_nutrition_client.py` | **PARTIAL_REVIEW** |
| 12 | `profile` | 2 فایل | — | — | 4 / 10 | `AuthContext.tsx`<br>`api.ts`<br>`session.ts` | — | `a11y.test.tsx`<br>`api.test.ts`<br>`authFlow.test.tsx`<br>`liveContractMember.test.ts` | **PARTIAL_REVIEW** |
| 13 | `progress` | 1 فایل | — | — | 2 / 7 | `api.ts` | — | `apiCoverage.test.ts`<br>`test_api_contract.py`<br>`test_battle.py`<br>`test_e2e_adaptive_loop.py` | **PARTIAL_REVIEW** |
| 14 | `shell` | 1 فایل | — | — | 8 / 10 | `api.ts`<br>`session.ts` | — | `a11y.test.tsx`<br>`apiCoverage.test.ts`<br>`authFlow.test.tsx`<br>`deviceSessions.test.tsx` | **PARTIAL_REVIEW** |
| 15 | `shop` | 3 فایل | — | super_admin, admin, manager, coach, reception, member | 8 / 15 | `api.ts` | — | `apiCoverage.test.ts`<br>`memberShop.test.tsx`<br>`test_m59_shop.py`<br>`test_phase2_shop_display.py` | **PARTIAL_REVIEW** |
| 16 | `today` | 4 فایل | — | — | 0 / 4 | — | — | — | **GAP** |
|  |  |  |  |  |  |  |  |  | ↳ هیچ call-site استاتیکی برای مسیرهای این دامنه نیست |
| 17 | `wallet` | 2 فایل | — | — | 4 / 25 | `api.ts` | — | `locustfile_full.py`<br>`memberPayments.test.tsx`<br>`paymentPanel.test.tsx`<br>`receiptQueue.test.tsx` | **PARTIAL_REVIEW** |

## چه چیزی این نسخه هنوز اثبات نمی‌کند

- مجوز سمت سرور؛ `routes.json`/`rbac.py` شاهد قرارداد است، نه اجرا.
- مالکیت: تست منفی (عضو A → دادهٔ عضو B) در همین اجرا اجرا نشده.
- تمایز «مصرف‌کنندهٔ صفحهٔ عضو» از «پنل کارکنان»: فایل مشترک است (`api.ts`,
  `adminApi.ts`)؛ تفکیک کامپوننتی نیاز به مرور دستی دارد.
- مرورگر/دستگاه/نصب‌پذیری و reviewer مستقل.

## بازتولید

```bash
python3 scripts/crosswalk_v2.py --repo . --kind member --out evidence/<DATE>/INV-02
```
