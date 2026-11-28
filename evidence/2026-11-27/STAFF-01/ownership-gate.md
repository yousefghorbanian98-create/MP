STAFF-01(ب) — گیتِ مالکیت/نقش روی ماتریس SEC-01 (ROUND 2/9، فاز B)
====================================================================

دامنه: فقط بند (ب) — گیت اجراییِ نقش/مالکیت. بند (الف) (کامل‌بودن route/render/test)
در دور قبل بسته شد و در `evidence/2026-11-27/STAFF-01/{current-run.md,mutation-proof.txt}`
ثبت است؛ فایل قبلی دست‌نخورده مانده و اثبات جهش این دور در فایل جداگانه
`ownership-mutation-proof.txt` است.

پاسخ به پرسش پیش‌نیاز (SEC-01 قابل تبدیل است؟)
-----------------------------------------------
`YES` — با شمارش: ماتریس SEC-01 و `api/routes.json` یک منبع دارند
(`scripts/export_routes.py::access_matrix`)، هر دو ۱۶۳ operation (۹۷۸ ردیف متنی =
۱۶۳ operation با تفکیک نقش/متد)، و سه تست موجود همین ماتریس را اجرایی نگه می‌دارند.
جزئیات: `evidence/2026-11-27/SEC-01/convertibility.txt`. ماتریس دومی ساخته نشد.

آنچه تازه شد (یک فایل تست، بدون endpoint تازه)
----------------------------------------------
`mp-app/backend/tests/integration/test_staff_ownership_gate.py` — ۲۷ تست:

| تست | چه چیزی را می‌سنجد |
|---|---|
| `test_selection_is_not_empty` | فهرست staff از artifact خالی نشود (≥ ۲۰) — گیتِ بی‌صدا خالی نمی‌شود |
| `test_live_selection_matches_artifact` | مجموعهٔ staff-only GET در اپ زنده == artifact |
| `test_every_token_only_operation_has_a_role` | هر operation با `anonymous=never` دست‌کم یک نقش مجاز دارد |
| `test_machine_token_exemptions_are_exactly_the_documented_set` | استثنای بدون‌نقش بسته است (فقط `GET /api/v1/metrics` با دلیل) |
| `test_member_gets_403_on_staff_route[...]` × ۲۳ | برای هر مسیر staff-only GET، توکن `member` **واقعاً** ۴۰۳ می‌گیرد |

طراحی که جهش را می‌گیرد: فهرست مسیرها از `api/routes.json` خوانده می‌شود، نه از
policy زنده؛ اگر کسی قاعده‌ای را به نفع member باز کند، فهرست کوچک نمی‌شود بلکه
همان مسیر ۲۰۰ می‌گیرد و تست قرمز می‌شود. اگر مسیر staff تازه‌ای بدون قاعدهٔ نقش
اضافه شود، اپ زنده با artifact نمی‌خواند و `test_live_selection_matches_artifact`
قرمز می‌شود (اثبات: M2).

اثبات جهش (خلاصه؛ خروجی خام در `ownership-mutation-proof.txt`)
-------------------------------------------------------------
- baseline: `27 passed`.
- M1 — افزودن `("member", "/api/v1/admin/kpis", "GET")` به `POLICIES`:
  `2 failed` (`test_live_selection_matches_artifact` + `test_member_gets_403_on_staff_route[api-v1-admin-kpis]`),
  و اثبات خام: `GET /api/v1/admin/kpis as member -> 200 {"members_total":0,...}`.
  بازگردانی: `security/rbac.py: OK` (sha256 قبل/بعد یکی).
- M2 — افزودن مسیر `GET /api/v1/admin/ownership-gate-probe` به
  `modules/admin/router.py` بدون ردیف policy: `1 failed`
  (`test_live_selection_matches_artifact`). بازگردانی: `modules/admin/router.py: OK`.

محدودیت (ادعا نمی‌شود)
----------------------
این گیت **مالکیت سطری** (member فقط ردیف خودش) را اثبات نمی‌کند؛ آن کنترل در
service است. سه رفتار مشاهده‌شده در همین دور با TestClient (نه به‌عنوان اثبات کامل):
member روی member دیگر ۴۰۳ · member روی خودش ۲۰۰ · member روی فهرست staff ۴۰۳ —
ثبت در `evidence/2026-11-27/STAFF-02/current-run.md`.

گیت‌های همراه که با این تغییر اجرا و پاس شدند
--------------------------------------------
`test_routes_artifact.py` · `test_routes_access_matrix.py` · `test_routes_effective_guards.py`
· `test_gate_codes.py` (بعد از بازتولید interaction map) — ۶۱ تست مرتبط پاس.
