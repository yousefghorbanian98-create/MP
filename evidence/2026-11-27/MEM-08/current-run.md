# MEM-08 / PWA-37 — تغذیهٔ عضو (2026-11-27)

```text
MEM-08/PWA-37=PARTIAL/NOT_ACCEPTED
CONTRACT=plan/meal/food-log از سه قرارداد جدا؛ unit ضمنی؛ data_state + target_source صریح
NEW_ENDPOINT=no
UI=MemberNutrition.tsx روی /member/nutrition
TESTS=5 (memberNutrition.test.tsx) + 3 mutation
```

- قرارداد: [`contract-answer.txt`](contract-answer.txt). `PlanOut` در `modules/nutrition/schemas.py:38-51`،
  `list_member_plans` با `ensure_member_scope` در `service.py:60-70`، و `daily_summary` در
  `service.py:169-284` که `data_state` (`logged`/`nothing_logged`) و `target_source`
  (`approved_plan`/`none`) و `reason` را خودش برمی‌گرداند.
- گیت‌ها در تست، نه در UI:
  - `meals: []` ⇒ «برنامهٔ کامل نیست» و `data-plan-complete="no"`.
  - `data_state=nothing_logged` ⇒ هیچ عدد مصرفی نمایش داده نمی‌شود («۰» یعنی ثبت‌نشده).
  - `target_source=none` ⇒ هیچ «درصد رسیدن به هدف»/مقایسه ساخته نمی‌شود.
  - ۴۰۳ ⇒ `role="alert"` و صفر عدد.
- هر عدد واحد (`کیلوکالری`/`گرم`) و هر بخش `منبع:` دارد. هیچ محاسبهٔ تغذیه‌ای و هیچ ادعای
  پزشکی در کلاینت نیست؛ همهٔ اعداد از سرور است.
- mutation: سه شکست ⇒ سه تست قرمز و بازگشت سبز ([`mutation-proof.txt`](mutation-proof.txt)).

## باز (چرا PARTIAL)
ثبت غذای جدید از UI عضو انجام نشده (فقط خواندن)؛ ویرایش/حذف ثبت، هدف‌های ورزشی و
`review` تغذیه‌ای خارج از این برش‌اند؛ اجرای دستگاه/مرورگر و reviewer مستقل نداریم.
