# M70 — گیت نقش Settings و RoleManager

**تاریخ:** 2026-11-16 UTC
**شاخه:** `arena/4f336f66-mp` · **پایه:** `d64e3b008d1c6c20c65c5ebfa4816277d4d23ce0`
**وضعیت:** `PASS` برای گیت تجربهٔ کاربری super_admin-only در Studio؛ مجوز نهایی همچنان در backend است.

## یافته و اصلاح

- `Settings` برای `admin` و `super_admin` مجاز است؛ این صفحه عمداً برای admin بسته نشد.
- `RoleManager` فهرست کاربران را از `GET /admin/users` می‌خواند، اما این route فقط برای `super_admin` مجاز است. پیش از اصلاح، صفحهٔ Settings برای admin هم کامپوننت مدیریت نقش را نمایش می‌داد و درخواست‌هایی می‌فرستاد که به 403 می‌رسیدند.
- `RoleManager` اکنون فقط وقتی نقش توکن access برابر `super_admin` باشد render و بارگذاری می‌شود؛ در نتیجه admin نه دکمه/فرم مدیریت نقش می‌بیند و نه درخواست `admin/users` یا `admin/audit` تولید می‌شود. نمایش نقش در مرورگر فقط UX است؛ backend همچنان مرجع مجوز است.
- `roleNav.ts` خواندن access token را از `getAccessToken()` می‌گیرد، نه با کلید `mp_token` تکراری. role payload برای منوی/صفحهٔ UI است، نه گیت امنیتی API.

## شواهد اجرایی جاری

- Studio هدفمند: `npm test -- tests/session.test.ts tests/settingsRole.test.tsx tests/roleNav.test.tsx tests/shopPage.test.tsx --reporter=dot` → **36 passed / 0 failed** در چهار فایل، شامل دو تست جدید Settings و تست‌های نقش/Shop.
- Studio کاملِ جاری: `npm test -- --reporter=dot` → **217 passed / 9 skipped**, 32 فایل pass و یک فایل skipشده (33 فایل کل). تست‌های skipشده همان 9 مورد ازپیش‌موجود در فایل contract هستند.
- Studio `npm run build` موفق شد (`tsc -b` و Vite). Vite همچنان هشدار موجود دربارهٔ import پویا/ایستای `api.ts` می‌دهد؛ خطای build نیست. در چند تست قدیمی Shop/Nutrition/Readiness، هشدار React `act(...)` دیده شد؛ تست‌ها موفق‌اند.
- Backend: `./.venv/bin/pytest -q tests/integration/test_m46_security_matrix.py -k test_super_admin_only_routes` → **1 passed, 20 deselected**. این regression روی `/api/v1/admin/users` anonymous را 401، member/admin را 403 و `super_admin` را 200 می‌سنجد.
- `settingsRole.test.tsx` منفی و مثبت را با API mock بررسی می‌کند: admin صفحهٔ Settings را نگه می‌دارد ولی RoleManager/API آن را ندارد؛ super_admin کامپوننت و درخواست‌هایش را دارد.

## حدود

- تست مرورگر/Studio و backend محلی است؛ CI، production و E2E دستگاه اجرا نشد.
- منوی نقش client-side قابل جعل است؛ 403 backend همچنان الزام امنیتی است و این تغییر جایگزین آن نیست.
- `npm run lint` در این manifest به ESLint اشاره می‌کند ولی ESLint/config نصب/تعریف نشده؛ به‌جایش TypeScript build و تست‌ها اجرا شدند.
- M68 و M69 همچنان مستقل و مسدودند؛ M66/D10 Flutter همچنان `UNKNOWN` است.
