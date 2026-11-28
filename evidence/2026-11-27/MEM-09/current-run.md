# MEM-09 / PWA-38 — کلاس و رزرو در مسیر عضو (2026-11-27)

```text
MEM-09/PWA-38=PARTIAL/NOT_ACCEPTED
CONTRACT=capacity/confirmed/waitlisted/seats_left + member_booking_status از سرور
NEW_ENDPOINT=no (GET /classes، POST /classes/book، POST /classes/cancel)
UI=MemberClasses.tsx روی /member/classes
TESTS=7 (memberClasses.test.tsx) + 3 mutation
```

- قرارداد: [`contract-answer.txt`](contract-answer.txt). `service.py:198-211` فیلدهای ظرفیت را
  برمی‌گرداند؛ `service.py:66-120` رزرو با قفل کلاس، خطای `already_booked` و
  `waitlisted` وقتی `confirmed >= capacity`.
- قاعدهٔ پذیرش TODO («دکمهٔ disabled اثبات عدم overbooking نیست») این‌طور رعایت شد:
  بعد از هر رزرو/لغو، فهرست **دوباره از سرور** خوانده می‌شود (تست دو `GET /classes` را
  می‌شمارد) و پیام از `status` پاسخ سرور می‌آید (`confirmed` در برابر `waitlisted`).
- سه حالت رزرو (تأییدشده/لیست انتظار/بدون رزرو) متن و `data-member-booking` جدا دارند؛
  خطای تکراری سرور پنهان نمی‌شود.
- mutation: حذف بازخوانی (۲ تست قرمز)، ثابت‌کردن پیام موفقیت (۱)، پنهان‌کردن خطا (۱)
  ⇒ همه بازگشت سبز ([`mutation-proof.txt`](mutation-proof.txt)).

## باز (چرا PARTIAL)
آزمون race واقعی (دو رزرو هم‌زمان) در این برش از UI اجرا نشده — پوشش backend آن در
`tests/integration/test_classes_finance.py:54` است؛ لغو از لیست انتظار و ارتقای خودکار
فقط از طریق سرور سنجیده شده، نه با دو مرورگر؛ اجرای دستگاه/مرورگر نداریم.
