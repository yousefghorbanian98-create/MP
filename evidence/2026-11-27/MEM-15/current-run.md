# MEM-15 / PWA-3E — جعبهٔ اعلان عضو (2026-11-27)

```text
MEM-15/PWA-3E=PARTIAL/NOT_ACCEPTED
CONTRACT=GET /notifications/member/{id} (id desc، ensure_member_scope) + POST /{id}/read (ایدمپوتنت)
NEW_ENDPOINT=no
UI=MemberInbox.tsx روی /member/inbox
TESTS=6 (memberInbox.test.tsx) + 2 mutation
```

- قرارداد: [`contract-answer.txt`](contract-answer.txt).
- فهرست از سرور، شناسهٔ عضو از `/members/me`؛ شمارش «خوانده‌نشده» از همان فهرست با منبع صریح.
- `channel` هر ردیف نمایش داده می‌شود؛ `inapp` = «درون‌برنامه‌ای» و جملهٔ TODO عیناً هست:
  «وجود یا خواندن یک اعلان اینجا به معنای ارسال push/SMS یا تحویل و مشاهدهٔ آن روی دستگاه نیست.»
- علامت‌گذاری خوانده‌شده: بعد از تأیید سرور **بازخوانی** می‌شود (تست دو خواندن می‌شمارد)؛
  خطای آن فهرست را پاک نمی‌کند و ردیف خوانده‌نشده می‌ماند.
- هیچ `POST /notifications` (ارسال) صدا زده نمی‌شود؛ ۴۰۳ ⇒ `role="alert"` و صفر ردیف.
- mutation: خواندن خوش‌بینانه از کلیک (۱ قرمز) · ترجمهٔ `inapp` به «پیامکارسال شد» (۲ قرمز)
  ([`mutation-proof.txt`](mutation-proof.txt)).

## BLOCKED
- MEM-16 (outbox آفلاین) طبق TODO تا تصویب policy `BLOCKED` است؛ ساخته نشد.
- push/device permission و تحویل واقعی روی دستگاه `NOT_RUN` و خارج از دامنهٔ این برش.

## باز (چرا PARTIAL)
`GET /notifications/reminders/member/{id}` (یادآوری‌های مشتق‌شده، G11) در UI نیامده؛ بدون
دستگاه/بازبین مستقل هم پذیرش کامل نیست.
