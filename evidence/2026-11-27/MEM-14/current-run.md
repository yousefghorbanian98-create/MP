# MEM-14 / PWA-3D — چت عضو (2026-11-27)

```text
MEM-14/PWA-3D=PARTIAL/NOT_ACCEPTED
CONTRACT=5 مسیر REST در chat_router.py:24-53 · ownership در chat_service.py:26-44
NEW_ENDPOINT=no
UI=MemberChat.tsx روی /member/chat
TESTS=6 (memberChat.test.tsx) + 3 mutation
```

- قرارداد: [`contract-answer.txt`](contract-answer.txt). `GAP:` سرور idempotency برای ارسال
  پیام ندارد؛ UI ادعای آن نمی‌کند.
- فهرست گفتگوها بدون `member_id` در query؛ دامنه سمت سرور بسته است (تست روی query خالی assert دارد).
- انتخاب گفتگو: `GET …/messages` → `POST …/read` → **بازخوانی**؛ متن «سرور N پیام را
  خوانده‌شده ثبت کرد» از پاسخ سرور می‌آید، نه از کلیک.
- ارسال: بعد از `POST` **بازخوانی** می‌شود؛ تستی که سرور پیام را ذخیره نمی‌کند ثابت می‌کند
  پیام تازه در UI سبز نمی‌شود (بدون افزودن خوش‌بینانه).
- `status=closed` ⇒ ورودی و دکمه غیرفعال با دلیل سرور؛ `unread_count` و `rule_version` از سرور.
- صفحه صریح می‌گوید realtime/WebSocket ندارد و پیام تازه فقط با بازخوانی می‌آید.
- ۴۰۳ ⇒ `role="alert"`، صفر گفتگو، صفر پیام.
- mutation: افزودن خوش‌بینانه (۱ قرمز) · خوانده‌شدن بدون سرور (۲ قرمز) · حذف گارد گفتگوی بسته
  (۱ قرمز) ([`mutation-proof.txt`](mutation-proof.txt)).

## BLOCKED
- ارسال/دریافت realtime و تحویل روی دستگاه: `DEVICE_REQUIRED` و خارج از دامنه (بخش ② سند).

## باز (چرا PARTIAL)
بدون بازبین مستقل و بدون اجرای مرورگر؛ idempotency ارسال سمت سرور وجود ندارد (GAP ثبت شد).
