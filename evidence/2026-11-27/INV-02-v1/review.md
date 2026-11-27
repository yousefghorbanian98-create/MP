# INV-02 — بازبینی منبعی crosswalk عضو

> **وضعیت:** `PARTIAL / NOT_ACCEPTED`. این فایل تفسیر دستیِ محدودِ خروجی ایستا است؛ نه اصلاح خروجی خام، نه آزمون محصول، نه اثبات نقش/مالکیت و نه پذیرش PWA-01.

## منشأ و بازتولیدپذیری

- هدف اسکریپت: commit جداشدهٔ `352781043ad2ba202d8b3b459df1ce7e3d914ef7` (`origin/main` هنگام تولید). worktree در زمان جمع‌آوری داده tracked-clean بود؛ JSON خام `tracked-dirty=false` و `untracked=3` را ثبت می‌کند. این سه مورد ابزارهای بازتولید بودند، نه تغییر محصول؛ پوشهٔ خروجی پس از ثبت metadata ساخته شد.
- ابزارها از `yousefghorbanian98-create/Chat2DB`، ref=`arena/c1fb460b-chat2db`، مسیر `docs/mp-inv-redo/` آمده‌اند. SHA-256 بایت‌های ابزار اجراشده: `inv02_member_crosswalk.py`=`6d9305ad60e0c0e1eaaf3eb864cfa0ea42aec2c9fc937082e5ddce0df40c7cf2`; `inv03_staff_crosswalk.py`=`d70ab9c8c3e2046ba3418ed50efc7bb4d6615e6602413878ffb5e9b9b79731b2`; `run-inv-redo.sh`=`5c05932a07e3ddb197953b7b1c77d614fff1da19074524966b300f6c4378faa2`. ابزارهای دریافت‌شده در worktree اصلی هنوز untracked هستند؛ منبع و hash را برای جلوگیری از اتکا به فایل محلی ثبت می‌کنیم.
- پوشهٔ `2026-11-27` برچسب/مسیر مرجع evidence است، نه فیلد زمان اجرای script. خود generator `started_at` ندارد؛ mtime خام‌های INV-02 در filesystem برابر `2026-11-27T11:21:00.042396Z` است و فقط زمان نوشتن فایل را نشان می‌دهد، نه زمان دقیق شروع/پایان فرمان.
- hash فایل‌های منبع در JSON خام با فایل‌های متناظر checkout حاضر تطبیق داده شد. هیچ product test، build، browser/device، CI یا تست مجوزی در این بازبینی اجرا نشد.

## خروجی خام — بدون ویرایش

- [Markdown تولیدشده](member-capability-crosswalk.md) · SHA-256: `b659f6ba01b463af25b5ed38c5995cbc0688b735d50d0af885301266f12c6c6a`
- [JSON تولیدشده](member-capability-crosswalk.STALE.json) · SHA-256: `8ec8f4d046fde7122c45a6889f09817e32c16d330c1932b884b3701e8b6ed5f0`
- همان اجرای خام: ۱۷ feature directory از Flutter، ۱۴۱ مسیر یکتای API طبق loader اسکریپت، ۴۷ مسیر call-site شناخته‌شده توسط الگوهای اسکریپت؛ `PARTIAL_REVIEW=13` و `GAP=4`. این‌ها شمارش اسکریپت‌اند؛ ۴۷ را کل call-siteهای ممکن یا تست-reference را اجرای تست تلقی نکنید.

## مقایسهٔ GAPها با source همان SHA

| ردیف خام | شاهد source و محدودیت crosswalk | تفسیر محدود پس از بازبینی |
|---|---|---|
| `checkin` — `GAP` | Flutter [checkin_page.dart](../../../mp-app/client/lib/features/checkin/checkin_page.dart) می‌گیرد `GET /face/qr-token` و از مسیرهای face-consent نیز استفاده می‌کند؛ [member_checkin_history.dart](../../../mp-app/client/lib/features/checkin/member_checkin_history.dart) از `GET /members/me/checkins` می‌خواند. نقشهٔ دستی `FEATURE_TO_API` در script مسیر `/members/me/checkins` را زیر این feature قرار نداده است. در React، `/member` در [App.tsx](../../../mp-app/studio/src/App.tsx) به `MemberRoutePending` ختم می‌شود؛ صفحهٔ کارکنان `CheckIn` جایگزین جریان عضو نیست. | نبود سطح عضو در PWA برای حضور/سوابق، در بررسی ایستای route تأیید می‌شود؛ اما دامنهٔ API خام کامل نیست. `MEM-10`، QR با اعتبارسنجی سمت سرور را می‌خواهد. مسیرهای رضایت/ثبت/تشخیص چهره را به PWA منتقل نکنید؛ نام `/face/checkin-qr` به‌تنهایی رفتار آن را ثابت نمی‌کند. Flutter برای نمایش QR، `LocalAuthentication` محلی هم دارد؛ این مشاهده، الزام محصولی تازه یا مجوزی برای افزودن آن به React نیست. جزئیات چرخهٔ QR همچنان نیازمند تست/سیاست واقعی است. |
| `intake` — `GAP` | Flutter [intake_page.dart](../../../mp-app/client/lib/features/intake/intake_page.dart) از `/population/gate-check` استفاده می‌کند و سپس `/members/me`، `/ai/program/generate` و `/ai/nutrition/generate` را هم در جریان دارد. نقشهٔ دستی feature فقط مسیرهای `population/*` و یک prefix ارزیابی را می‌شمارد؛ پس کل سفر intake را پوشش نمی‌دهد. در Studio هیچ سطح عضو قابل استفاده‌ای در route `/member` حاضر نیست. | نبود مسیر/سطح intake عضو در React در همین source بررسی‌شده تأیید می‌شود، ولی فهرست APIهای raw، کل سفر را مدل نمی‌کند. `MEM-06` safety gate لازم دارد؛ `unknown/blocked/needs_review` و تصمیم تخصصی را حدس نزنید یا از Flutter به‌عنوان policy مصوب کپی نکنید. |
| `notifications` — `GAP` | صفرِ خام، false-negative کامل برای همهٔ مصرف‌ها نیست: [api.ts](../../../mp-app/studio/src/lib/api.ts) تابع `fetchReminders` را با template مسیر `/notifications/reminders/member/${memberId}` می‌سازد؛ [RemindersPanel.tsx](../../../mp-app/studio/src/components/RemindersPanel.tsx) آن را برای عضو انتخاب‌شده از staff صدا می‌زند و این پنل در Assessment آمده است. اما این inbox عضو نیست. در Studio call-site برای `/notifications/member/{member_id}` و `/{notification_id}/read` پیدا نشد؛ خود route عضو نیز placeholder است. | اسکریپت به‌علت مسیر template/dynamic بخشی از مصرف را از دست داده؛ reminder کادر را با inbox عضو یکی نگیرید. GAP سطح inbox عضو طبق `MEM-15` باقی است. Inbox هم به‌تنهایی ارسال/تحویل push یا SMS را ثابت نمی‌کند. |
| `today` — `GAP` | اسکریپت به‌خاطر `${...}` در path، مصرف‌های واقعی را نمی‌شمارد: `fetchMemberVolume` و `fetchReadiness` از برنامه‌های کادر، و `fetchAdaptiveReport` از پنل تغذیهٔ کادر استفاده می‌شوند؛ محل‌ها در [api.ts](../../../mp-app/studio/src/lib/api.ts)، [Programs.tsx](../../../mp-app/studio/src/pages/Programs.tsx) و [Nutrition.tsx](../../../mp-app/studio/src/pages/Nutrition.tsx) است. این‌ها دادهٔ عضو انتخاب‌شده در صفحات کادرند، نه صفحهٔ «امروزِ خود عضو». | ادعای خام «هیچ call-site در Studio وجود ندارد» نادرست است؛ اما حضور این endpointها در staff UI، جای route/member home را نمی‌گیرد. با `/member` placeholder، سطح امروزِ عضو همچنان GAP ایستای PWA است؛ نسخهٔ امروز، readiness یا توصیهٔ تازه از این اسکن استنتاج نمی‌شود. |

## محدودیت‌های مهم و نتیجه

1. `CONSUMER_PATTERNS` در generator literalهای محدودی مثل `${API_BASE}/...` را می‌گیرد و `$`/بخش‌های template را از مسیر حذف می‌کند؛ wrapperهایی با base/path متغیر و template literalها ممکن است از شمارش جا بمانند. نقشهٔ `FEATURE_TO_API` نیز دستی است و هم‌پوشانی featureها/صفحه‌های کادر را حل نمی‌کند.
2. «اشارهٔ تستی» فقط ذکر متنی مسیر در فایل تست است، نه اجرای آن. `routes.json` و roleهای manifest نیز اثبات server enforcement یا ownership نیستند.
3. status/count خام عمداً در فایل‌های generated تغییر داده نشده‌اند؛ یافته‌های بالا تفسیر بازبین‌اند و محصول را نمی‌پذیرند.

`INV-02` حداکثر `PARTIAL / NOT_ACCEPTED` می‌ماند؛ checkbox آن باز و `PWA-01=PROPOSED/NOT_RUN` است. هیچ status پذیرش یا release ارتقا نیافته؛ release همچنان `NO-GO` است. گام مستقل بعدی طبق صف، `SEC-01` است؛ ماتریس نقش/ownership و تست منفی سمت سرور باید جداگانه انجام شود.

> **نام‌گذاری STALE (۲۰۲۶-۱۱-۲۷):** این دو artifact با generator نسخهٔ v1 و روی
> commit دیگری ساخته شده‌اند و digestهایشان با HEAD نمی‌خواند؛ طبق قاعدهٔ STATE،
> نامشان `STALE` گرفت و از گیت `scripts/verify_crosswalk_digests.py` خارج شدند.
> محتوا byte-for-byte دست‌نخورده است؛ نسخهٔ جاری `INV-0X/` است.
