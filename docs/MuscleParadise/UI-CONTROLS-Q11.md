# کنترل‌های رابط کاربری — انتخاب کتابخانه (گیت Q11)

> وضعیت: **تصمیم گرفته شد و اعمال شد** (۲۰۲۶-۱۱-۱۹). این سند پاسخ «چه چیزی انتخاب شد و چرا» است؛
> فهرست کامل گزینه‌های بررسی‌شده، موارد ردشده و کارهای باقی‌مانده همین‌جاست.

## ۱. قاعده

هیچ کنترل تعاملی (toggle، switch، checkbox، radio، select، dialog، date picker، آپلود فایل،
جدول با مرتب‌سازی) از صفر نوشته نمی‌شود. هر کنترل از یک کتابخانهٔ متن‌باز با مجوز OSI می‌آید.

شرط‌های پذیرش هر کتابخانه:

1. مجوز OSI و بدون «نسخهٔ پولی/کلید لایسنس».
2. بدون تلمتری و بدون درخواست شبکهٔ پنهان.
3. راست‌به‌چپ درست، نه با `transform` دستی.
4. تاریخ جلالی واقعی برای کاربر ایرانی.
5. سازگار با React 18 و Tailwind v3 موجود (بدون بازنویسی پوسته).

گیت اجرایی: `mp-app/studio/tests/uiLibrary.test.ts` — پنج تست، شامل «بودجهٔ ratchet» که
نمی‌گذارد تعداد کنترل دست‌ساز در هیچ فایلی بالا برود.

## ۲. انتخاب‌شده‌ها (نصب‌شده، با نسخهٔ قفل‌شده)

| کتابخانه | نسخه | مجوز | تلمتری | RTL | برای چه کاری |
|---|---|---|---|---|---|
| antd | 5.29.3 | MIT | ندارد | `ConfigProvider direction="rtl"` + locale رسمی `fa_IR` | Select، Modal، Switch، Checkbox، Radio، Table (مرتب‌سازی/فیلتر/صفحه‌بندی)، Upload.Dragger (رسید)، Tooltip، Steps، Slider، Form، DatePicker میلادی |
| @ant-design/cssinjs | 1.24.0 | MIT | ندارد | — | `StyleProvider layer` تا preflight تیلویند استایل antd را نشکند (دستور رسمی antd برای Tailwind v3) |
| @ant-design/icons | 5.6.1 | MIT | ندارد | — | آیکون‌های آماده؛ جای کاراکترهای `✓`/`!`/`i` که نام دسترس‌پذیر نداشتند |
| react-multi-date-picker | 4.5.2 | MIT | ندارد (بدون fetch) | خودش RTL است | تقویم و دیت‌پیکر **جلالی** با `calendar={persian}` و `locale={persian_fa}`؛ ورودی/خروجی ISO میلادی می‌ماند |
| react-date-object | 2.1.9 | MIT | ندارد | — | تبدیل میلادی↔جلالی؛ dependency همان دیت‌پیکر |
| dayjs | 1.11.x | MIT | ندارد | — | موتور تاریخ antd (transitive) |

### چرا antd 5 و نه 6

`antd@6.7.1` منتشر شده، ولی نسخهٔ major تازه است و بخش تاریخ/قالب آن با `rc-picker` جدید
عوض شده؛ مسیر جلالی و مستندات RTL آن هنوز در عمل آزموده نشده. `5.29.3` با React 18 و
Tailwind v3 ترکیب شناخته‌شده است و locale فارسی‌اش کامل. ارتقا به ۶ کار جدا با تست است.
همین دلیل نسخهٔ `@ant-design/cssinjs@1.x` و `@ant-design/icons@5.x` را قفل کرد (antd 5
با این نسخه‌ها ساخته شده؛ نصب ۲.x/۶.x ناسازگاری داخلی می‌سازد).

## ۳. بررسی‌شده و رد‌شده

| گزینه | مجوز | چرا رد شد |
|---|---|---|
| Radix UI primitives (Dialog/Switch/Select…) | MIT | بدون استایل است؛ هر کنترل باید از نو چیده و رنگ شود → عملاً همان «از صفر نوشتن» که Q11 منع می‌کند |
| Radix Themes | MIT | استایل دارد، ولی جدول، آپلود فایل و دیت‌پیکر ندارد؛ ترکیب دو سیستم، کار دو برابر |
| shadcn/ui | MIT | توزیع آن کپی‌کردن کد از registry شبکه‌ای است (در محیط ساخت بسته) و هر کامپوننت به مالکیت کد محلی تبدیل می‌شود |
| Headless UI | MIT | پوشش کم: بدون Select کامل، جدول و دیت‌پیکر؛ برای پنل داده‌محور کافی نیست |
| React Aria Components | Apache-2.0 | از نظر دسترس‌پذیری و تقویم فارسی (تقویم `persian` بومی) بهترین بود، ولی کاملاً بدون استایل است؛ هزینهٔ استایل‌دهی همهٔ کنترل‌ها + ریسک ناسازگاری با پوسته |
| Ark UI | MIT | headless و ۶۹ زیربستهٔ `@zag-js/*`؛ همان ایراد «بدون استایل» با سطح وابستگی بیشتر |
| Chakra UI v3 | MIT | استایل دارد ولی روی Emotion سوار است؛ دو موتور CSS کنار Tailwind و antd |
| Mantine 9 | MIT | استایل خوب، ولی تقویم جلالی ندارد و اندازهٔ بستهٔ `@mantine/core` چند برابر antd برای پوشش مشابه |
| Base UI (`@base-ui-components/react@1.0.0-rc.0`) | MIT | نسخهٔ منتشرشده در npm **deprecated** است (ناشر به `@base-ui/react` تغییر نام داده)؛ اتکا به آن بدهی فوری |
| `antd-jalali` | MIT | آخرین انتشار ۲۰۲۴-۰۶-۳۰ و peer آن `antd@^5.18.3`؛ نگهداری متوقف → جای آن `react-multi-date-picker` |
| `react-day-picker` + `date-fns-jalali` | MIT | `date-fns-jalali` نسخهٔ `4.4.0-0` (پیش‌انتشار) است؛ تقویم جلالی رسمی ندارد |
| `jalaliday` (پلاگین dayjs) | MIT | فقط تبدیل است، کنترل نمی‌سازد؛ با antd 5 یکپارچه نمی‌شود |

## ۴. آنچه واقعاً مهاجرت کرد (این نوبت)

| فایل | قبل | بعد |
|---|---|---|
| `src/components/PaymentPanel.tsx` | `<select>` خام | `Select` antd با `aria-label` |
| `src/components/RoleManager.tsx` | `<select>` خام | `Select` antd با نام دسترس‌پذیر «نقش …» |
| `src/pages/Nutrition.tsx` | `<select>` + `<input type="date">` | `Select` antd + `JalaliDateField` |
| `src/pages/Shop.tsx` | ۵ `<select>` + دیالوگ دست‌ساز رسید | `Select` antd + `Modal` antd |
| `src/components/AdaptiveNutritionPanel.tsx` | `<input type="date">` | `JalaliDateField` |
| `src/components/PhoneChangeDialog.tsx` | `<section role="dialog">` دست‌ساز با فوکوس‌تراپ دستی | `Modal` antd (فوکوس‌تراپ/Escape/بازگشت فوکوس از کتابخانه) |
| `src/components/Feedback.tsx` | `ConfirmDialog` دست‌ساز | `Modal` antd با همان API بیرونی؛ آیکون‌های toast از `@ant-design/icons` |

نتیجهٔ شمارش (خودکار، در گیت): **صفر** `<select>`، `type="date"`، `type="checkbox"`، `type="radio"`
و `role="dialog"` دست‌ساز در `src/`. فایل `tests/uiControlBudget.json` خالی است و هر ردیف تازه
تست را قرمز می‌کند.

## ۵. باقی‌مانده (صادقانه)

| مورد | وضعیت | مسیر |
|---|---|---|
| ۱۹ `<input>` خام در `Shop.tsx` (فرم محصول/قیمت/درگاه) | دست‌ساز مانده | تبدیل به `Input`/`InputNumber`/`Form` antd — فرم را عوض می‌کند، تست `shopPage` باید همراه بیاید |
| toast و skeleton در `Feedback.tsx` | دست‌ساز عمداً | کنترل ورودی نیستند؛ انتقال به `message`/`Skeleton` antd کار جدا با تست `a11y` |
| آپلود فیش کارت‌به‌کارت | هنوز ساخته نشده | `Upload.Dragger` antd + endpoint آپلود بک‌اند (بدون endpoint، UI دکوراتیو می‌شد) |
| ماتریس توانایی ادمین‌ها (QF-04) | هنوز ساخته نشده | `Switch`/`Checkbox` antd؛ هیچ toggle دست‌ساز نوشته نخواهد شد |
| کلاینت Flutter | بدون dependency تازه | `pub.dev` از محیط ساخت این مخزن در دسترس نیست (probe: کد ۰۰۰)؛ پس همان Material/Cupertino داخلی می‌ماند — که خودش کتابخانه است. تاریخ جلالی در کلاینت از `MaterialLocalizations` یا رشتهٔ آمادهٔ سرور می‌آید، نه فرمت‌بندی دست‌ساز |
| آپلود رسید در بک‌اند | `python-multipart` از قبل نصب است | اعتبارسنجی تصویر (Pillow در runtime) وقتی endpoint ساخته شد؛ الان dependency بی‌مصرف اضافه نشد |
| SBOM کامل transitive استودیو | باز | `npm audit` فعلی: ۰ critical (۳ moderate + ۱ high از `vite`/`vitest` که از قبل بود) |

## ۶. شاهد اجرا

```
cd mp-app/studio
npx vitest run tests/uiLibrary.test.ts tests/jalaliDate.test.tsx   # ۹ تست، سبز
npx vitest run                                                     # ۲۳۴ passed | ۹ skipped
npm run build                                                      # بدون هشدار اندازه
```

باندل بعد از تقسیم vendor: `vendor-antd` ۵۰۲KB (gzip ۱۶۵KB)، `vendor-charts` ۳۹۶KB،
`vendor-motion` ۱۱۵KB، `vendor-dates` ۷۷KB، کد اپ ۱۶۳KB. قبل از تقسیم، یک فایل ۱٬۲۶۰KB
بود و هشدار Vite را رد می‌کرد.

اثبات جلالی: `۲۰۲۶-۱۱-۱۹` در فیلد به‌صورت `۱۴۰۵/۰۸/۲۸` دیده می‌شود و رفت‌وبرگشت مقدار
بدون جابه‌جایی روز است (`mp-app/studio/tests/jalaliDate.test.tsx`).
