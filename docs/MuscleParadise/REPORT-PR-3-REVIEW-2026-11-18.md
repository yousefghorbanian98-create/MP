# گزارش بازبینی PR شمارهٔ ۳ و گراف‌های آن

**مبنای بررسی:** `da73f2e81bd9e70b9ed395407481fe133a4ca731` در برابر `main` روی `5482930587ce18e14f136d78296542a2de5af091`؛ ۱۳ commit و ۸۴ مسیر در زمان بازبینی. [PR پیش‌نویس](https://github.com/yousefghorbanian98-create/MP/pull/3) · [CI همان head](https://github.com/yousefghorbanian98-create/MP/actions/runs/44511373788): هشت job موفق. **نتیجهٔ بازبینی: تغییر لازم است؛ تا رسیدگی به یافتهٔ مالی، ادغام توصیه نمی‌شود.** CI سبز ناسازگار با یافتن یک سناریوی آزموده‌نشده نیست.

## یافته‌ها

### R1 — P2: جستجوی ناموفق پرداخت، انتخاب و عملیات قبلی را نگه می‌دارد

در [`PaymentPanel.tsx`](../../mp-app/studio/src/components/PaymentPanel.tsx)، `lookup` فقط در مسیر موفق `setTx`، `setStarted` و `setReceipt` را تغییر می‌دهد. اگر پرداخت A بارگذاری شود و کاربر شناسهٔ B ناموجود/نامعتبر را جستجو کند یا fetch شکست بخورد، UI خطا می‌دهد اما پرداخت A و دکمهٔ بازگشت آن باقی می‌مانند. `refund` همچنان `tx.id` قبلی را ارسال می‌کند. تأیید مرورگر شماره و مبلغ A را نشان می‌دهد، اما زمینهٔ انتخاب نادرست می‌تواند به بازگشت وجه اشتباه پس از تأیید کاربر منجر شود. تغییر lookup/refund در همین PR است.

**تأیید تجربی:** در کپی ایزوله از کد این commit، با `npm ci --ignore-scripts` و `npm test -- tests/paymentPanel.test.tsx`، تست‌های موجود ۷ passed و یک تست جدید زیر failed شد: پس از جستجوی `7` موفق و `999` ناموفق، دکمهٔ `بازگشت وجه` هنوز وجود داشت. fetch ساختگی بود؛ هیچ API یا پرداخت واقعی فراخوانی نشد.

**بازتولید در کپی آزمایشی:** قطعهٔ زیر را به انتهای `mp-app/studio/tests/paymentPanel.test.tsx` همان snapshot اضافه و فایل را با دستور بالا اجرا کن. `paid`، `PaymentPanel` و imports از همان فایل تست موجودند. انتظار ایمن: دکمه پس از خطا در دسترس نباشد؛ کد فعلی تست را fail می‌کند.

```tsx
describe("Review: stale lookup state", () => {
  it("failed lookup must not leave a prior refund action available", async () => {
    localStorage.setItem("mp_token", "t");
    const paidGateway = { ...paid, gateway_authority: "AUTH-1" };
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => {
      if (String(input).endsWith("/payments")) return new Response(JSON.stringify([paidGateway]));
      return new Response("{}", { status: 404 });
    }));
    const user = userEvent.setup();
    render(<PaymentPanel />);
    const input = screen.getByLabelText("شناسهٔ پرداخت موجود");
    await user.type(input, "7");
    await user.click(screen.getByRole("button", { name: "بارگذاری پرداخت" }));
    expect(await screen.findByRole("button", { name: "بازگشت وجه" })).toBeTruthy();
    await user.clear(input);
    await user.type(input, "999");
    await user.click(screen.getByRole("button", { name: "بارگذاری پرداخت" }));
    expect(await screen.findByText("پرداخت یافت نشد")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "بازگشت وجه" })).toBeNull();
  });
});
```

**اقدام پیشنهادی:** state انتخابی و رسید را با شروع جستجوی تازه یا خطا به‌شکل fail-closed مدیریت کن، سپس برای شناسهٔ نامعتبر، پیدا نشدن، خطای شبکه و تغییر ورودی و همچنین موفقیت بعدی تست رگرسیون بنویس. رفتار در حال جستجو و race بین درخواست‌ها را نیز روشن کن. این گزارش خود کد محصول را تغییر نداده است.

### R2 — P2: workflow فرمت QR قبل از اجرای تست همان شاخه را push می‌کند

در [client-format-fix.yml](../../.github/workflows/client-format-fix.yml)، job دستی `format-qr` پس از `dart format` ابتدا commit و push را انجام می‌دهد و فقط در مرحلهٔ بعد widget test را اجرا می‌کند. بنابراین اگر آن تست شکست بخورد، commit قبلاً روی branch مقصد منتشر شده است. شرط `arena/*` فقط نام را محدود می‌کند؛ موفقیت تست قبل از push را تضمین نمی‌کند. این یافته از ترتیب صریح گام‌ها در YAML است، نه اجرای workflow با دسترسی نوشتن در این بازبینی.

**اقدام پیشنهادی:** تست/اعتبارسنجی blobهای نهایی را پیش از هر push انجام بده یا workflow را به خروجی قابل‌بازبینی بدون push مستقیم تغییر بده؛ هنگام اجرای هر workflow شاخه و اختیار مجاز آن نشست رعایت شود. سپس با fixture امن failure و success و CI همان commit بررسی کن.

## بررسی‌های دیگر و نقاط تحویل

- تغییرات پرداخت شامل migration مستقل `refund_reference`، بازخوانی آن در receipt/API و UI جدید هستند. تست موجود happy path و تکرار ترتیبی را بررسی می‌کند. تابع backend از قبل به درگاه متصل بود؛ این بازبینی رقابت دو درخواست، اثر crash، مجوز نهایی نقش‌ها یا درگاه واقعی را تأیید نکرد. `GET /payments` بدون pagination به UI بازمی‌گردد؛ ظرفیت و حداقل داده نیز نیازمند بررسی‌اند.
- QR شامل local_auth محلی، timeout و lifecycle است؛ CI widget و Android debug موفق بوده‌اند، ولی آزمون حسگر و چرخهٔ واقعی دستگاه برای همین تغییر انجام نشده است.
- امضای Android از fallback به debug دور شده و به کلید/گواهی اختصاصی نیاز دارد؛ [گزارش کلید بازنشسته](REPORT-OLD-ANDROID-KEY-REVIEW-2026-11-18.md) و [سخت‌سازی release](../../finn/reports/m112-release-signing-hardening.md). وضعیت کلید جدید، release امضاشده و نصب/upgrade دستگاه باید مستقل احراز شود.
- استثناهای secret تاریخی محدود و تأییدشده‌اند؛ اسکن موفق جای بازبینی داده‌های جدید، مدیریت امن کلید و جلوگیری از استفادهٔ مجدد کلید قدیمی را نمی‌گیرد.
- نام فایل‌ها و diff کامل PR فهرست شدند و تغییرات runtime، workflowهای مرتبط، معماری و مستندات اصلی به‌صورت هدفمند مرور شدند. این مرور ممیزی مستقل امنیتی، بررسی خط‌به‌خط تمام ۸۴ فایل، آزمون واقعی بانک یا تأیید تولید نیست. QF و OV همچنان `NOT RUN` هستند.

## گراف به‌روزشده

[گراف RepoWise](architecture/repowise-pr-review-2026-11-18.dsl) و [manifest ورودی](architecture/repowise-pr-review-scope-2026-11-18.txt) از ۵۷۶ فایل tracked انتخابی از head بازبینی‌شده ساخته شدند؛ فقط blobهای Git و نه فایل محلی اصلاح‌شده استفاده شدند. Gitleaks بر snapshot ورودی صفر یافته داد. RepoWise 0.61.0 در mirror با Git مصنوعی و HOME جدا، `fast`، بدون مدل، hook و editor اجرا شد؛ provider تهی، ۰ صفحه و جستجوی full-text و semantic غیرفعال بود. ابزار ۵۵۸ working-tree file، ۲ container، ۲۱ component و ۹۸ relation گزارش کرد، در حالی که DSL شامل ۴۴ خط فلش است؛ تفاوت هنوز تبیین نشده. گراف، یافته‌های این گزارش و تغییرات پس از snapshot را شامل نمی‌شود، پوشش کامل نیست و رابطهٔ غایب به معنی نبود وابستگی نیست. [نقشهٔ Mermaid بازبینی](architecture/pr-review-flows-2026-11-18.md) با خواندن کد و بدون ادعای runtime کامل تهیه شده است.

## اقدام بعدی

PR را draft نگه دار؛ ابتدا R1 را اصلاح و آزمون‌های موفق و ناموفق آن را روی tree تازه اجرا کن و دربارهٔ R2 تصمیم و گیت مناسب را اعمال کن. سپس diff کامل، secret scan، docs و CI همان SHA را دوباره مرور و نتیجه را در PR ثبت کن. ادغام در `main` و انتشار محصول دو تصمیم جدا هستند.
