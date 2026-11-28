# MEM-11 / PWA-3A — کیف پول عضو (2026-11-27)

```text
MEM-11/PWA-3A=PARTIAL/NOT_ACCEPTED
CONTRACT=GET /payments/ledger/{member_id} ⇒ balance_rial + reconcile + entries(id desc, 200, بدون offset)
NEW_ENDPOINT=no
UI=MemberWallet.tsx روی /member/wallet
TESTS=5 (memberWallet.test.tsx) + 2 mutation + پشتیبان test_m83_wallet_ledger.py
```

- قرارداد: [`contract-answer.txt`](contract-answer.txt). `modules/payments/ledger.py:86-95`
  (`id desc`، `limit=200`، **بدون offset**)، `:97` موجودی، `:108-125` تطبیق،
  `:189-203` سریال‌سازی. تایپ کلاینت `lib/api.ts:225-254`.
- موجودی **از `balance_rial` سرور** خوانده می‌شود و با `data-balance-rial` صریح نمایش
  داده می‌شود؛ هیچ جمع کلاینتی وجود ندارد (تست gate دارد).
- `reconcile.matches === false` ⇒ هشدار قرمز با «واحد ریال» و هر دو عدد + منبع؛ پنهان
  نمی‌شود.
- هر ردیف: `data-entry-kind` ∈ charge|pay|refund|reversal با برچسب فارسی،
  `data-reversed`، منبع (`payment #…`). «معکوس‌شده» از `reversed_by_entry_id` می‌آید.
- UI صریح می‌گوید سرور صفحه‌بندی ندارد ⇒ صفحه دکوراتیو ساخته نشد.
- mutation: جمع کلاینتی و `matches=false` پنهان ⇒ هر بار یک تست قرمز، بازگشت سبز
  ([`mutation-proof.txt`](mutation-proof.txt)).

## BLOCKED (اجباری — پول)
- هیچ عملیات مالی (شارژ، پرداخت، بازگشت وجه) در این برش ساخته نشد؛ حتی دکمهٔ غیرفعال
  هم ساخته نشد. تصمیم دربارهٔ درگاه/مبلغ/سیاست بازگشت وجه = مالک/مالی
  (`modules/payments/router.py` منطقهٔ نوشتن دست‌نخورده).

## باز (چرا PARTIAL)
تاریخچه بیش از ۲۰۰ ردیف بدون صفحه‌بندی سرور قابل مشاهده نیست (محدودیت قرارداد، نه UI)؛
عملیات مالی و رسیدها خارج از دامنه‌اند.
