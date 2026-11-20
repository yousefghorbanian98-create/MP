# سناریوهای زندهٔ فاز ۶ — پول کارت‌به‌کارت (۲۰۲۶-۱۱-۱۹)

> هر سناریو یک تست اجراشده است، نه یک ادعا. ستون «شاهد» نام تست در
> `mp-app/backend/tests/integration/test_phase6_card_to_card.py` است.
> اجرای کامل: `cd mp-app/backend && pytest -q tests/integration/test_phase6_card_to_card.py`
> → **۱۲ قبول / ۰ رد** (اندازه‌گیری‌شده در همین تاریخ).

| # | سناریو | انتظار | شاهد |
|---|---|---|---|
| ۱ | عضو برای پرداخت خودش فیش PNG می‌فرستد | ۲۰۲، `review_id`، وضعیت `in_review` | `test_member_uploads_receipt_and_payment_enters_review` |
| ۲ | عضو دیگر برای همان پرداخت فیش می‌فرستد | ۴۰۳/۴۰۴ و پرداخت `pending` می‌ماند | `test_another_member_cannot_upload_for_someone_elses_payment` |
| ۳ | کارمند با مجوز مالی فیش عضو را آپلود می‌کند | ۴۰۳ `member_only` | `test_staff_still_cannot_upload_a_members_receipt` |
| ۴ | فایل غیرتصویری / PNG خراب / بزرگ‌تر از سقف | ۴۲۲ `unsupported_receipt_type` · ۴۲۲ `invalid_receipt_image` · ۴۱۳ `receipt_too_large` | `test_receipt_type_and_size_are_enforced` |
| ۵ | پرداخت نقدی فیش می‌گیرد | ۴۰۰ `receipt_not_applicable` | `test_cash_payment_has_no_receipt_path` |
| ۶ | تأیید با `finance.write` | ۲۰۰ `paid` + رسید `approved` + اعلان + audit | `test_staff_approval_is_atomic_and_notifies_the_member` |
| ۷ | تأیید همراه پلن | اشتراک در همان تراکنش ساخته می‌شود | `test_approval_can_activate_membership_in_the_same_transaction` |
| ۸ | سازندهٔ پرداخت خودش تأیید می‌کند | ۴۰۳ `self_approval_forbidden`، پرداخت `in_review` می‌ماند | `test_creator_cannot_approve_their_own_payment` |
| ۹ | تأیید دوباره | ۴۰۰ `already_processed`، `reference_id` تغییر نمی‌کند | `test_double_approval_changes_nothing_economically` |
| ۱۰ | رد فیش با دلیل | پرداخت `failed` + رسید `rejected` + دلیل ذخیره | `test_rejection_marks_payment_failed_with_reason` |
| ۱۱ | تأیید پس از رد | ۴۰۰ `not_in_review` | همان تست، بخش دوم |
| ۱۲ | `idempotency_key` تکراری | همان پرداخت، فقط یک ردیف در DB | `test_idempotency_key_prevents_duplicate_payments` |
| ۱۳ | تأیید رسید منقضی | ۴۰۰ `review_expired` | `test_expired_review_cannot_be_approved` |

## چرا «زنده» است و چه چیزی زنده نیست

- زنده: مسیر کامل HTTP (توکن واقعی، multipart واقعی، SQLite/DB واقعی، فایل روی دیسک).
- زنده: قواعد مجوز سرور (`finance.write`، مالکیت پرداخت، منع تأیید خود).
- **نه زنده و `BLOCKED`:** انتقال واقعی پول بین حساب بانکی عضو و باشگاه، و تأیید
  بانکی کارت‌به‌کارت. این‌ها بدون دسترسی بانکی/شاهد انسانی قابل آزمون نیستند و
  در گزارش‌ها هم `BLOCKED` می‌مانند.
- **نه زنده:** آپلود از اپ Flutter (toolchain محلی نصب نیست) — مسیر HTTP آن با
  `curl`/TestClient آزموده شده، ولی کلاینت Dart اجرا نشده است.

## گیت‌های مرتبط

- `tests/apiCoverage.test.ts` — هر مسیر تازه مصرف‌کننده یا استثنای مستند دارد.
- `scripts/route_guard_gate.py` — هر مسیر guard دارد (۳ عملیات تازهٔ فاز ۶ هم).
- `tests/integration/test_m47_migration_drift.py` — مهاجرت‌های فاز ۶ بدون drift و برگشت‌پذیر.
