# MEM-13 / PWA-3C — فروشگاه (فقط نمایش) (2026-11-27)

```text
MEM-13/PWA-3C=PARTIAL/NOT_ACCEPTED
CONTRACT=خواندن status/products مجاز؛ هر نوشتن با assert_online_purchase_open() fail-closed
NEW_ENDPOINT=no
UI=MemberShop.tsx روی /member/shop
TESTS=5 (memberShop.test.tsx) + 2 mutation + 8 پشتیبان integration
```

- قرارداد: [`contract-answer.txt`](contract-answer.txt). `modules/shop/router.py:119-149`
  خواندن، `:168-216` نوشتن‌ها که اول `service.assert_online_purchase_open()` را صدا
  می‌زند؛ `tests/integration/test_phase2_shop_display.py:166` نشان می‌دهد checkout
  بسته ⇒ **409**.
- UI هیچ مسیر `/shop/cart`، `/shop/cart/items` یا `/shop/checkout` را صدا نمی‌زند؛
  تست این را با ثبت همهٔ درخواست‌ها gate می‌کند.
- قیمت با واحد «ریال» و `منبع:` سرور؛ `data-shop-open` وضعیت فروشگاه را از سرور نشان
  می‌دهد (اگر بسته است، نوشتن ممنوع و گفته می‌شود).
- موجودی صفر ⇒ «ناموجود» (نه «۰ عدد») با `data-stock-qty="0"`.
- اگر پاسخ محصول تصویر ندارد، تصویر ساخته نمی‌شود و همین صریح گفته می‌شود.
- mutation: افزودن `POST /shop/cart` و نمایش «۰ عدد» به‌جای «ناموجود» ⇒ هر بار یک تست
  قرمز، بازگشت سبز ([`mutation-proof.txt`](mutation-proof.txt)).

## BLOCKED (اجباری — پول)
- خرید/سبد/پرداخت عمداً ساخته نبود؛ سیاست قیمت‌گذاری و فروش آنلاین = مالک/مالی.

## باز (چرا PARTIAL)
سبد خرید، سفارش و پرداخت خارج از دامنه؛ اجرای دستگاه/مرورگر `NOT_RUN`.
