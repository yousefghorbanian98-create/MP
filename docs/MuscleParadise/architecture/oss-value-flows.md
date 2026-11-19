# جریان ارزش‌های تمرین و حضور — نقشهٔ هدف با پشتوانهٔ RepoWise

**وضعیت: هدف/برنامه‌ریزی‌شده، نه اثبات کارکرد انتهابه‌انتها.** شناسه‌ها برش‌های [برنامهٔ ارزش‌ها](../PLAN-OSS-VALUE-MICROLOOPS-2026-11-18.md) هستند. پیکان‌های نقطه‌چین به معنی تطبیق یا اتصال نیازمند بررسی‌اند. RepoWise 0.61.0 روی mirror گزینشی بدون مدل، ساختار کد و نشانه‌های وابستگی را بررسی کرد؛ سپس این نقشه با خواندن کد توسط عامل اصلی ترسیم شد. index موقت و مصنوعی، پوشش کامل یا QA نیست؛ [گزارش روش](../REPORT-OSS-VALUE-DEEP-DIVE-2026-11-18.md).

## تعامل عضو، کادر و backend

```mermaid
flowchart LR
    Member[عضو - Flutter] --> Workout[برنامه و ثبت ست<br/>OV-03 / OV-04]
    Coach[مربی و کادر - Studio] --> Plans[طراحی و مشاهده برنامه<br/>OV-03 / OV-05]
    Member --> Meals[وعده و جمع روزانه<br/>OV-06]
    Member --> Chat[چت عضو و مربی<br/>OV-07]
    Member --> QR[QR و عضویت<br/>OV-01 / OV-02]
    Workout -. قرارداد و ذخیره نیازمند آزمون .-> API[FastAPI و مجوز سروری]
    Plans -. قرارداد و مالکیت نیازمند آزمون .-> API
    Meals -. محاسبه و ثبت نیازمند آزمون .-> API
    Chat -. ownership و retry نیازمند آزمون .-> API
    QR -. انقضا و ضدبازپخش نیازمند آزمون .-> API
    API --> DB[(SQLAlchemy و پایگاه داده)]
    Workout -. عضله و محتوای مجاز .-> Catalog[کاتالوگ و نقشه<br/>OV-08 / OV-10]
    Catalog -. منشأ و مجوز پیش از استفاده .-> Sources[منابع و دارایی تأییدشده]
```

نقاط فعلی برای بازبینی: `mp-app/backend/modules/{programs,exercises,nutrition,face_id}`، `mp-app/client/lib/features/{today,nutrition,checkin,chat}` و `mp-app/studio/src/components/ExerciseLibrary.tsx`. وجود source به معنی اتصال یا آمادگی نیست.

## فیش و عضویت: OCR تأییدکنندهٔ پرداخت نیست

```mermaid
flowchart LR
    Member[عضو] --> Receipt[ارسال فیش خصوصی<br/>OV-09 / QF-07]
    Receipt -. انتخابی و پس از تأیید حقوق و امنیت .-> OCR[OCR پیشنهاد متن]
    OCR -. نیاز به بازبینی انسانی .-> Review[صف بررسی مجاز]
    Receipt --> Review
    Bank[منبع مستقل بانکی] --> Human[تطبیق توسط انسان مجاز]
    Review --> Human
    Human -. فقط پس از تأیید .-> Tx[تراکنش تأیید پرداخت<br/>و فعال‌سازی اشتراک]
    Tx -. نیازمند آزمون idempotency و crash .-> Notice[رویداد اعلان]
```

مسیر هدف است؛ `manual_transfer_policy.py` مستقل محلی به‌خودی‌خود جریان متصل یا تأیید بانکی نیست. عکس پیشرفت بدن خارج scope است؛ تصویر فیش و کالا سیاست خود را دارند.
