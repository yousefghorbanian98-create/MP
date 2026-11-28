STAFF-02 (PWA-41) — اعضا و پروفایل: برشِ اجراشده در ROUND 2/9
=============================================================

وضعیت: **PARTIAL** — جست‌وجو/فهرست از سرور + منفی‌های دسترسی اجرا شد؛
detail/edit کامل، pagination در UI و حالت stale همان‌طور باز مانده‌اند
(تیک TODO زده نشد؛ `TODO_DONE` بدون تغییر).

## شکافی که پیدا شد (و چرا «کار» بود، نه بازنویسی)

`MemberTable` داده را از `GET /api/v1/admin/members-summary` می‌گرفت و
جست‌وجوی نام/تلفن را **در مرورگر** روی همان ردیف‌ها فیلتر می‌کرد.
با بیشتر از `limit` (پیش‌فرض ۲۰۰) عضو:

- عضوی که در صفحهٔ اول نبود هرگز «پیدا» نمی‌شد (فیلتر روی دادهٔ ناقص)؛
- برچسب «N عضو» عدد صفحه را نشان می‌داد، نه نتیجهٔ جست‌وجو.

=> نقض قانون «هر عدد منبع سرور دارد» + جست‌وجوی گم‌شونده برای کارکنان.

## تغییر (۵ فایل، بدون endpoint تازه)

| فایل | تغییر |
|---|---|
| `mp-app/backend/modules/admin/analytics.py` | `members_summary(db, *, limit, q)` — فیلتر `q` روی نام/تلفن در SQL با `ilike` و escape صریح `%`/`_` |
| `mp-app/backend/modules/admin/router.py` | پارامتر `q` با `max_length=80` روی `GET /admin/members-summary` |
| `mp-app/studio/src/lib/api.ts` | `fetchMembersSummary(token, signal, q)` — با `q` مسیر `?q=`، بدون آن همان مسیر خالی |
| `mp-app/studio/src/components/MemberTable.tsx` | `q` به سرور می‌رود (`deps=[q]`)؛ فقط تفکیک جنسیت روی ردیف‌های برگشته می‌ماند |
| `mp-app/studio/tests/staffMemberSearch.test.tsx` | ۳ تست: `q` encoded به سرور · ردیف نمایش‌داده‌شده همان پاسخ سرور است (بدون فیلتر مرورگر) · نتیجهٔ خالی حالت خالی صریح |

`mp-app/backend/tests/integration/test_staff_members_search.py` — ۷ تست:
جست‌وجوی نام · جست‌وجوی تلفن · `%`/`_` wildcard نیست · بی‌نتیجه = خالی (نه همه) ·
`q` خالی = بدون فیلتر · `q` بلندتر از ۸۰ = ۴۲۲ · نقش member روی این مسیر = ۴۰۳.

## اثبات جهش

`evidence/2026-11-27/STAFF-02/mutation-proof.txt` (بک‌اند):
- baseline `7 passed`؛ **M3** نادیده‌گرفتن `q` ⇒ `3 failed`
  (`test_search_by_name_is_server_side`, `test_wildcards_are_not_honoured`,
  `test_unknown_query_returns_empty_not_everything`)؛
- **M4** حذف escape در الگوی LIKE ⇒ `1 failed` (`test_wildcards_are_not_honoured`)؛
- بازگردانی: `modules/admin/analytics.py: OK` (sha256 یکی).

`evidence/2026-11-27/STAFF-02/frontend-mutation-proof.txt` (Studio):
- baseline `3 passed`؛ **M7** حذف `q` از فراخوانی ⇒ `1 failed`
  (`متن جست‌وجو را به‌صورت q سمت سرور می‌فرستد`)؛ بازگردانی `MemberTable.tsx: OK`.

## شواهد دسترسی (TestClient، خروجی خام)

با یک گروه سه‌نفره (staff + دو عضو) و توکن member «الف»:

```
member A -> /api/v1/members/:other   403 {"error":{"code":"forbidden","message":"دسترسی فقط به دادهٔ خودتان مجاز است"}}
member A -> /api/v1/members/:self    200 {"id":1,"user_id":2,...}
member A -> /api/v1/members          403 {"error":{...}}
manager  -> member 1                 200
manager  -> member 2                 200
```

## باز (ادعا نمی‌شود)

- detail/edit کامل با permission server در UI (فرم ویرایش/ذخیره با بازخوانی) — انجام نشده.
- pagination در UI (`limit/offset` فقط در API هست؛ جدول صفحه‌بندی ندارد).
- حالت stale/نمونه‌داده/sentinel برای فهرست اعضا در UI.
- «شعبهٔ دیگر»: دادهٔ تست تک‌شعبه است (`branch_id=1` در همهٔ ردیف‌ها)؛ منفیِ
  بین‌شعبه‌ای بدون دادهٔ دو شعبه قابل اثبات نیست — ثبت به‌عنوان بدهی، نه ادعا.
- جست‌وجو بی‌debounce است: هر تغییر متن یک درخواست می‌فرستد (درخواست قبلی با
  AbortSignal لغو می‌شود). به‌عنوان بدهی UX ثبت می‌شود.
