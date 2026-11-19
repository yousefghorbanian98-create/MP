# Synthetic ECC/QA smoke fixture

این پوشه فقط داده و منطق **کاملاً ساختگی** برای آزمون ابزار و harness است؛ نه بخشی از backend MP، نه اعتبارسنج بانکی، نه الگوی امنیت production. `unsafe_policy.py` عمداً ناامن است تا تست شکست بخورد؛ `safe_fixture.py` فقط مقایسهٔ آموزشی است و مستقل از بانک و DB واقعی عمل می‌کند. نتیجهٔ این تست‌ها به معنی اجرای QA مستقل یا امنیت پرداخت MP نیست.

از داخل همین پوشه با Python 3:

```bash
# انتظار: exit 1، چهار تست، سه شکست عمدی
TRIAL_VARIANT=unsafe_policy python3 -m unittest -v trial_tests

# انتظار: exit 0، چهار تست موفق
TRIAL_VARIANT=safe_fixture python3 -m unittest -v trial_tests
```

`contract.json` یک OpenAPI ساختگی دو عملیات است؛ بررسی REA فقط مسیرهای inline را inventory می‌کند و وجود security policy، تأیید بانک، استقلال QA یا اتصال UI/API/DB واقعی را اثبات نمی‌کند. شرح و محدودیت اجرای آزمایشی در [گزارش](../../../docs/MuscleParadise/REPORT-ECC-QA-TRIAL-2026-11-18.md) است.
