# MEM-12 / PWA-3B — پرداخت دستی کارت‌به‌کارت و ارسال فیش (2026-11-27)

```text
MEM-12/PWA-3B=PARTIAL/NOT_ACCEPTED
CONTRACT=POST /payments/{id}/receipt ⇒ 202 + status=in_review (نه تأیید)
NEW_ENDPOINT=no
UI=MemberPayments.tsx روی /member/payments
TESTS=7 (memberPayments.test.tsx) + 3 mutation + 66 پشتیبان integration/regression
```

- قرارداد: [`contract-answer.txt`](contract-answer.txt). آپلود فقط برای
  `card_to_card` + `pending` (`receipts.py:100-104`)، مالکیت با `ensure_record_scope`
  (`:100`)، سقف ۵ مگابایت (`app/config.py:58`) و سه قالب JPEG/PNG/WebP
  (`receipts.py:31`) که **محتوای فایل** هم سنجیده می‌شود (`:49-82`).
- فهرست از `GET /payments` می‌آید و سرور برای نقش member خودش دامنه را می‌بندد
  (`service.py:414-427`)؛ یک تست ثابت می‌کند کلاینت هیچ `member_id` در query نمی‌فرستد.
- UI: مبلغ همان `amount_rial` سرور با واحد ریال و `منبع:`؛ ورودی فیش فقط برای ردیف
  `pending` کارت‌به‌کارت باز است (`data-upload-enabled`)، بقیه دلیلش را می‌گویند.
- پس از ارسال: `data-receipt-status="in_review"`، `review_id`، مهلت بازبینی، و متن صریح
  «آپلود فیش ≠ تأیید بانک … تا تأیید فرد مجاز اشتراک فعال نمی‌شود». هیچ‌جا «پرداخت شد»
  یا «اشتراک فعال شد» ادعا نمی‌شود.
- خطاها با کد سرور ترجمه می‌شوند: `receipt_too_large`، `unsupported_receipt_type`،
  `invalid_receipt_image`، `receipt_type_mismatch`، `already_processed`،
  `receipt_not_applicable`، `review_expired`؛ کد ناشناخته با کد خام نمایش داده می‌شود.
- کنترل فایل با `Upload` کتابخانه‌ای antd است (قاعدهٔ Q11: کنترل تازه از صفر نوشته
  نمی‌شود؛ ratchet `uiControlBudget.json` با input خام قرمز می‌شد).
- گیت: تست ثبت همهٔ درخواست‌ها و رد کردن مسیرهای `approve|reject|verify|refund|wallet|
  start|callback`؛ هیچ دکمهٔ تأیید/رد در صفحهٔ عضو نیست.
- mutation: ۳ شکست عمدی ⇒ هر بار همان تست قرمز و بازگشت سبز
  ([`mutation-proof.txt`](mutation-proof.txt)).

## BLOCKED (اجباری — پول)
- تأیید فیش با مرجع بانکی مستقل و فعال‌سازی اشتراک = تصمیم فرد مجاز/مالی. مسیر کارکنان
  از قبل هست (`src/pages/Finance.tsx:135` → `ReceiptQueue` با `finance.write`) و این برش
  به آن دست نزده؛ ادعای «چرخهٔ کامل پرداخت آزمایش شد» نداریم.
- حساب بانکی مقصد و مبلغ canonical اشتراک خارج از دامنه است.

## باز (چرا PARTIAL)
بدون اجرای دستگاه/مرورگر با فایل واقعی، بدون بازبین مستقل و بدون آزمون بانکی؛
فیش آپلودشده «مدرک واریز» نیست.
