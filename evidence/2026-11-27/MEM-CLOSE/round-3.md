# MEM-CLOSE — دور ۳ (فاز B): STAFF-02 (detail/edit) · STAFF-04 (کلاس/حضور) · ۵ دروازهٔ تازه

> snapshot در HEAD همین commit. «PARTIAL» یعنی ساخته و با تست و mutation اثبات‌شده،
> ولی بدون بازبین مستقل/اجرای مرورگر پذیرفته نشده. جدول‌های دور ۱ و ۲ دست‌نخورده‌اند.

| # | عنوان | تست‌ها | mutations | وضعیت | یادداشت |
|---|---|---|---|---|---|
| STAFF-02 | اعضا: detail/edit + سقف صفحه + کهنگی | ۶ (`staffMemberDetail.test.tsx`) | 2 (M10, M11) | PARTIAL (بسته‌تر) | `STAFF-02/round-3.md` · `GAP: offset` · `OWNER_DECISION: بین‌شعبه‌ای` |
| STAFF-04 | کلاس/حضور کارکنان | ۴ (`staffClasses.test.tsx`) | 1 (M9) | PARTIAL | `STAFF-04/current-run.md` · `GAP: roster` · `GAP: تأیید مربی` |
| STAFF-01(ب) | sweep نوشتن‌ها (POST) | ۶۱ در همان گیت | 1 (M8) | DONE (این بند) | STAFF_GATED 23 → 57 |

## اعداد (از دستورهای ③/④)

- `STAFF_GATED=57` — ۲۳ GET + ۳۴ POST مسیر staff-only، هر کدام با تست ۴۰۳ واقعی.
- `STAFF_PAGES=12` — محاسبه از خودِ `staffRouteMap.test.ts`: `PAGE_IDS=13` منهای
  `withoutDedicatedTest=["analytics"]` = ۱۲ (۱۲ → ۱۲ با احتساب صفحهٔ تازهٔ `classes`
  که تست گرفت و `members` که از baseline بیرون آمد).
  ⚠️ عدد «۵» در دستور دور ۳ از این فایل بازتولید نمی‌شود؛ تعریف فایل‌محور بالا
  گزارش می‌شود و اختلاف پنهان نمی‌شود.
- `TODO_DONE=7` (بدون تیک تازه) · `OPEN_TESTIDS=0` · `MEMBER_ROUTES=11` · `MEMBER_SCREENS=11`
- `NEW_GATES=5` (G1..G5 در `ROUND-3/gates.txt`)

## بدهی‌ها (نه ادعا)

- `CHAT_NO_OPTIMISTIC` و `PAYMENT_NO_APPROVE` ساخته نشدند (دور ۴).
- صفحه‌بندی واقعی (offset) و roster نام‌دار و تأیید حضور توسط مربی: endpoint ندارند.
- فیلدهای بیشتر ویرایش (`full_name`/`gender`/`birth_date`) در UI نیست.
