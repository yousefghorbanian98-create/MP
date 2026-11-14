# گزارش بازبینی کد M16 — پرداخت/درگاه (code-reviewer)

**بازبین:** ایجنت code-reviewer | **تاریخ:** 2026-11-14 (بازبینی پس‌انداخت — backfill)

## دامنه
`modules/payments/gateway.py` (Protocol/Mock/Zarinpal + HMAC)، `invoice.py` (رسید/فاکتور)، `wallet_pay` اتمیک، `tests/integration/test_payments_deep.py`.

## یافته‌ها
- ✅ تست double-spend: دومین پرداخت رد و موجودی دقیق می‌ماند
- ✅ توکن HMAC: جعل مبلغ/شناسه توکن را باطل می‌کند (G8-مالی)
- ✅ رسید/فاکتور قطعی و قابل‌استناد
- ⚠️ قرارداد علامت کیف‌پول (مثبت + kind) یکدست شد — در D-008 ثبت شد

## حکم
**صفر Blocker** — ۱۴۱ تست سبز / ۸۹٪.
