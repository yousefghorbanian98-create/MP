# لایه‌های ساخت و مراحل تولید — دیاگرام‌ها

> **منبع این دیاگرام‌ها:** مدل معماری تولیدشده با `repowise 0.61.0` روی commit `c3821b4`
> (فایل خام: `architecture/repowise-model-2026-11-19.dsl`). عددها از همان ایندکس و از
> گیت‌های پروژه می‌آیند، نه از حافظه.
>
> **مجوز و محدودیت:** repowise خودش AGPL-3.0 است؛ فقط ابزار توسعهٔ محلی است، در محصول
> لینک یا توزیع نمی‌شود، و با `DO_NOT_TRACK=1` و `REPOWISE_OFFLINE=1` اجرا شد. ایندکس
> ۵۷ مگابایتی در `.repowise/` است و gitignore شده؛ گیت `scripts/repo_hygiene_gate.py`
> نمی‌گذارد دوباره وارد Git شود یا hook خودکار بنویسد.
>
> **رندر:** دیاگرام‌ها Mermaid هستند و روی GitHub رندر می‌شوند. در این محیط ساخت
> Chrome و Structurizr نیست، پس PNG/SVG ساخته نشد — این محدودیت است، نه ادعا.

## ۱. لایه‌های ساخت (چه چیزی ساخته می‌شود، با چه حجمی)

```mermaid
flowchart TB
    subgraph ENTRY["ورودی‌ها"]
        U1["عضو — اپ موبایل / کیوسک / PWA"]
        U2["مربی و پذیرش — Studio دسکتاپ"]
        U3["مالک — مرورگر از بیرون باشگاه"]
    end

    subgraph CLIENT["کلاینت عضو — Flutter"]
        C1["۴۴ فایل Dart در lib"]
        C2["۲۸ فایل تست"]
        C3["ویجت‌های Material/Cupertino — بدون dependency تازه"]
    end

    subgraph STUDIO["Studio — React 18 + TypeScript"]
        S1["۹۵ فایل، ۴۴۸ نماد"]
        S2["۲۲ کامپوننت + ۱۲ صفحه"]
        S3["کنترل‌ها از antd 5 — گیت Q11، صفر کنترل دست‌ساز"]
    end

    subgraph BACKEND["بک‌اند — FastAPI"]
        B1["۳۲۷ فایل، ۲۵۱۰ نماد"]
        B2["۱۲۱ مسیر / ۱۳۷ operation با guard و roles"]
        B3["۹۵۵ تست · coverage ۸۲.۶۲٪"]
    end

    subgraph DATA["داده"]
        D1["SQLite امروز · PostgreSQL در QF-24"]
        D2["static/ رسانهٔ تمرین"]
        D3["Valkey — cache و rate-limit"]
    end

    subgraph OPS["عملیات"]
        O1["CI — ۸ job"]
        O2["گیت مستندات + گیت بهداشت مخزن"]
        O3["backup / restore با اسکریپت"]
    end

    U1 --> C1
    U2 --> S1
    U3 --> S1
    C1 --> B1
    S1 --> B1
    B1 --> D1
    B1 --> D2
    B1 --> D3
    O1 --> BACKEND
    O1 --> STUDIO
    O1 --> CLIENT
    O3 --> D1
```

## ۲. مسیر تولید یک میکرو‌لوپ (چهار ایستگاه و گیت‌هایش)

```mermaid
flowchart TD
    A["Forge — طراحی برش n<br/>فایل‌های دقیق + دامنهٔ اثبات"] --> B["Inspect — بازرسی<br/>routes.json + route_guard_gate + grep + REA دستی"]
    B --> C{"گپ بدون API یا تست؟"}
    C -- بله --> D["ثبت گپ در نقشهٔ تعامل<br/>و برش تازه"]
    D --> A
    C -- خیر --> E["Normalize — سخت‌سازی<br/>pytest · ruff · vitest · tsc · flutter analyze · docs_gate · gitleaks"]
    E --> F{"Q0–Q11 سبز؟"}
    F -- خیر --> G["اصلاح و اجرای دوباره<br/>گیت تضعیف نمی‌شود"]
    G --> E
    F -- بله --> H{"تغییر پول/قیمت است؟"}
    H -- بله --> I["گیت ۲.۲<br/>فرض‌ها + ۱۰–۲۰ سناریوی زنده + تأیید مالک"]
    H -- خیر --> J["Next — checkpoint"]
    I --> J
    J --> K["commit انتخابی + push به شاخهٔ جاری"]
    K --> L{"CI همان SHA — ۸ از ۸؟"}
    L -- خیر --> M["FAIL ثبت می‌شود<br/>لوپ بسته نیست"]
    L -- بله --> N["ثبت ledger + فهرست تصمیم‌های کم‌اطمینان<br/>سپس n+1"]
```

## ۳. جریان پول — کارت‌به‌کارت (فاز ۶ نقشه)

```mermaid
sequenceDiagram
    autonumber
    participant M as عضو (اپ)
    participant S as سرور محلی
    participant A as ادمین/سوپرادمین (Studio)
    participant D as پایگاه داده

    M->>S: درخواست تمدید + انتخاب پلن
    S->>S: بررسی ساعت کاری و لایو بودن سرور
    alt خارج از تایم کاری یا سرور خاموش
        S-->>M: ۴۰۹ + «خارج از تایم کاری»
    else مجاز
        S->>D: ساخت draft با UUID و snapshot قیمت
        S-->>M: 202 + review_id + شمارهٔ کارت (masked)
        M->>S: آپلود فیش (multipart، حجم/نوع محدود)
        S->>D: رسید خصوصی + وضعیت in_review
        S-->>M: «در صف بررسی» — نه «تأیید شد»
        A->>S: صف بازبینی (فقط نقش واجد)
        S->>S: ادمین نمی‌تواند پرداخت خودش را تأیید کند
        A->>S: تأیید یا رد با دلیل
        S->>D: تراکنش اتمیک: پرداخت + سفارش + فعال‌سازی اشتراک + audit
        S-->>M: اعلان نتیجه
    end
```

## ۴. توپولوژی اجرا (سطح ۲: سرور محلی + ورودی HTTPS ارزان)

```mermaid
flowchart LR
    subgraph GYM["باشگاه"]
        SRV["سرور محلی<br/>FastAPI + پایگاه داده + static"]
        ST["Studio دسکتاپ<br/>شبکهٔ داخلی"]
        KIOSK["کیوسک حضور"]
    end
    subgraph OUT["بیرون"]
        PH["گوشی عضو"]
        OW["مالک — مرورگر"]
    end
    EDGE["ورودی HTTPS<br/>VPS کوچک یا تونل"]
    BAK["نسخهٔ پشتیبان<br/>خارج از ماشین"]

    ST --> SRV
    KIOSK --> SRV
    PH --> EDGE
    OW --> EDGE
    EDGE --> SRV
    SRV --> BAK
```

## ۵. هر دیاگرام از چه داده‌ای ساخته شد

| دیاگرام | دادهٔ منبع | دستور/فایل |
|---|---|---|
| لایه‌های ساخت | container/component و شمارش فایل و نماد | `repowise export --format structurizr --components` |
| مراحل تولید | چرخهٔ چهارایستگاهی، گیت Q0–Q11 و بند ۲.۲ | `PLAN-FINN-ECC-MICROLOOPS-QA.md` |
| جریان پول | تصمیم ۲۰۲۶-۱۱-۱۹ و طرح QF-07/08/09 | `TODO-CLOUD-FINANCE-ACCESS.md` |
| توپولوژی اجرا | تصمیم سطح ۲ (سرور محلی + ورودی HTTPS) | `OWNER-DECISIONS.md` |

## ۶. بازتولید مدل

```sh
python3 -m venv .venv-repowise           # بیرون از ردیابی Git
.venv-repowise/bin/pip install repowise==0.61.0
DO_NOT_TRACK=1 REPOWISE_OFFLINE=1 .venv-repowise/bin/repowise init --no-prose -y .
DO_NOT_TRACK=1 REPOWISE_OFFLINE=1 \
  .venv-repowise/bin/repowise export --format structurizr --components -o /tmp/model.dsl .
python3 scripts/repo_hygiene_gate.py     # ایندکس gitignore، بدون .claude/ و بدون hook
```

اگر روزی خواستید PNG/SVG واقعی داشته باشید، روی ماشین خودتان یا در CI با Node 20 و
`@mermaid-js/mermaid-cli` (MIT) یا Structurizr CLI رندر کنید؛ در محیط ساخت فعلی
Chrome و Docker نیست، پس خروجی تصویری ساخته نشد.
