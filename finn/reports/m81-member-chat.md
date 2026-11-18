# M81 — گفتگوی عضو روی API موجود

- تاریخ: 2026-11-17
- شاخه: `arena/4f336f66-mp` (active؛ HEAD پایه `d64e3b0`، بدون commit/push)
- نتیجه: **UNKNOWN تا اجرای واقعی Flutter widget/analyze/full Client gates**. کد و تست‌ها اضافه شده‌اند؛ `PASS` ادعا نمی‌شود.

## پیاده‌سازی Client

- صفحهٔ `MemberChatPage` به route `/chat` و گرید خانه با عنوان «گفتگو با مربی» وصل شد.
- provider از `GET /chat/conversations` بدون `member_id` می‌خواند و پاسخ هر گفتگو را با `memberId` نشست تطبیق می‌دهد؛ پاسخ عضو دیگر را به‌جای نمایش به خطای صریح تبدیل می‌کند.
- thread از `GET /chat/conversations/{id}/messages` خوانده می‌شود؛ شناسهٔ گفتگو، نقش فرستنده، زمان‌ها، بدنه و unread count اعتبارسنجی می‌شوند. پیام‌ها بر اساس `sender_role` نمایش داده می‌شوند.
- `POST /chat/conversations/{id}/read` فقط با action صریح «علامت‌گذاری» فراخوانی می‌شود؛ پس از موفقیت، thread دوباره از API خوانده می‌شود.
- ارسال به `POST /chat/conversations/{id}/messages` فقط برای متن غیرخالی و گفتگوی باز فعال است؛ متن trim و محدودیت ۲۰۰۰ نویسه اعمال می‌شود. اگر API خطا دهد متن در composer می‌ماند؛ پس از موفقیت thread و فهرست گفتگوها تازه می‌شوند.
- loading، empty، API error/retry، thread خالی، گفتگو بسته، notice/error action، refresh و route خانه پوشش داده شده‌اند. تست‌ها برای مسیرهای list/messages/send/read، مالکیت پاسخ، و حفظ draft نوشته شده‌اند.
- هیچ package، API یا backend موازی ایجاد نشد و فایل backend تغییر نکرد.

## تصمیم مرزی دربارهٔ آغاز گفتگوی تازه

- M81 Client فقط گفتگوهای موجود را می‌خواند و در آن‌ها پیام می‌دهد؛ از اپ عضو `POST /chat/conversations` فراخوانی نمی‌شود.
- مدل `Member` شناسهٔ مربی تخصیص‌یافته ندارد و API موجود برای member مسیر انتخاب/resolve مربی ارائه نمی‌کند. `open_conversation` اگر `coach_id` نیاید آن را از `user.id` caller می‌گیرد؛ برای عضو، این می‌تواند خود عضو را به‌عنوان طرف coach ثبت کند. ارسال حدسی `coach_id` یا ساخت چنین گفتگویی امن/درست نیست.
- empty state به‌صراحت می‌گوید از مربی بخواهید گفتگو را از سامانهٔ باشگاه آغاز کند. افزودن آغاز گفتگو از Client به قرارداد server-side معتبرِ تعیین مربی نیاز دارد؛ scope این loop آن را جعل نمی‌کند.

## بازبینی گیت مصرف API (اصلاح رگرسیون کشف‌شده)

- اجرای نخست `apiCoverage.test.ts` شکست واقعی گیت را روی مسیر قبلی `/api/v1/classes/book` نشان داد: tokenizer فقط `api.get(...)` با alias محلی را می‌شناخت و callهای واقعی Flutter به شکل `ref.read(apiClientProvider).post(...)` را نمی‌شمرد.
- برای آن‌که گیت مسیرهای واقعی Client را اندازه بگیرد، tokenizer دارت در `mp-app/studio/tests/apiCoverage.test.ts` به‌صورت محدود برای زنجیره‌های Riverpod `read/watch(apiClientProvider).<method>` گسترش یافت و regression probe اضافه شد. exceptionهای قدیمیِ classes/cancel و notifications list/read که اکنون مصرف واقعی دارند به evidence مسیر تبدیل شدند؛ routeها یا استثناهای جعلی اضافه نشدند.
- اجرای مجدد gate سبز شد. این تغییر را به‌عنوان اصلاح گیت عمومی ثبت می‌کنم، نه تغییر feature در Studio.

## شواهد اجرایی

- Backend قرارداد جاری، بدون تغییر کد: از `mp-app/backend`، `pytest -q tests/integration/test_m51_chat.py` → **13 passed**, 2 deprecation warnings. برای این اجرای متمرکز، وابستگی‌های dev در venv موقت `/tmp/mp-m81-backend-venv` نصب شد؛ repository/manifest backend تغییر نکرد.
- Dart syntax/static gate: `PYTHONPATH=/tmp/mp-m81-static python3 tools/dart_gate.py --include-tests` از `mp-app/client` → **58 فایل Dart، 0 یافته**. Parserهای Tree-sitter موقتاً در `/tmp/mp-m81-static` نصب شدند؛ این gate جایگزین analyzer یا Flutter runtime نیست.
- M71 API coverage targeted: `npm test -- --run tests/apiCoverage.test.ts` → **4 passed**.
- Studio regression suite: `npm test` → **32 فایل pass / 1 فایل با 9 skip موجود؛ 217 passed / 9 skipped**.
- Studio build/typecheck: `npm run build` → `tsc -b` و Vite build موفق؛ فقط هشدار شناخته‌شدهٔ dynamic/static import در `api.ts`.
- `git diff --check` → موفق.
- `npm ci` پیام **4 advisory** داد (3 moderate، 1 high)؛ audit fix یا تغییر dependency انجام نشد.

## گیت‌های اجرا‌نشده و وضعیت نهایی

- `flutter test test/member_chat_page_test.dart`, `flutter test test/home_page_test.dart`, `flutter analyze --no-fatal-infos`, کل `flutter test`، `flutter pub get` و APK build اجرا نشدند: executable Flutter/Dart، Java/JDK و Android SDK در این sandbox حاضر نیستند. تست‌ها skip نشده‌اند؛ runtime gate **اجرا‌نشده** است.
- در نتیجه M81: **`UNKNOWN`**. این loop blocker بیرونی ندارد و M82 را متوقف نمی‌کند؛ M78–M80 نیز تا Flutter gates مستقل `UNKNOWN` می‌مانند.
- هیچ push، CI/workflow، release، deploy/rollback، production DB یا دادهٔ واقعی استفاده نشد.
