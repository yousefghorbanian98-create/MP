# یافته‌های RepoWise — snapshot از `main` در `e5c8891` (بعد از merge PR #21)

این سند جایگزین نسخهٔ قبلی نمی‌شود؛ نسخهٔ `findings-2026-11-20.md` (snapshot از `b194e96`) برای مقایسه باقی می‌ماند.
همهٔ عددها از خروجی JSON خود RepoWise (نسخهٔ 0.61.0) روی کپی مخزن (بدون `node_modules`، `dist` و `.git`) گرفته شده‌اند.

## ۱. بهداشت کد (`repowise health`)
| شاخص | مقدار |
|---|---|
| فایل‌های تحلیل‌شده | ۵۸۲ (۹۹٫۵٪ از فایل‌ها) |
| میانگین سلامت | ۹٫۲۶ از ۱۰ |
| میانگین کد تولیدی (production، ۲۸۷ فایل) | ۸٫۹۵ |
| بدترین فایل | `mp-app/studio/src/pages/Shop.tsx` با ۶٫۰ |
| یافته‌ها | ۶۷۰ (critical: ۲۵، high: ۷۰، medium: ۴۱۶، low: ۱۵۹) |

**Critical بیشتر در این فایل‌ها:** `client/lib/core/app_state.dart` (۳)، `client/lib/core/offline_feedback_outbox.dart` (۳)، `backend/app/config.py` (۲)، `studio/src/pages/Shop.tsx` (۲)، `client/lib/features/wallet/wallet_ledger.dart` (۲)، `client/lib/features/chat/member_chat_data.dart` (۲).

> یافتهٔ سلامت «شاهد» است، نه خطای اثبات‌شده. بسیاری از موارد `io_in_loop` در اسکریپت‌های ابزار (`tools/`، `scripts/`) هستند و در مسیر تولید اجرا نمی‌شوند.

## ۲. کد مرده (`repowise dead-code`)
- ۳۵ یافته: ۲۹ `unused_export` و ۶ `unreachable_file`.
- اطمینان بالا: ۲ مورد؛ متوسط: ۱ مورد؛ بقیه پایین (۰٫۴).
- **هشدار:** بیشتر `unused_export`ها در `backend/modules/shop/service.py` و `studio/src/…` هستند و ممکن است از مسیرهای پویا یا تست‌ها فراخوانی شوند. قبل از حذف، بررسی دستی لازم است.

## ۳. رانش مستندات (`repowise doc-drift`)
- ۲۵ یافته در ۱۴ سند (از ۲۰۲ سند و ۴٬۰۴۸ ارجاع بررسی‌شده).
- همه از نوع `path`: ارجاع به فایلی که وجود ندارد. نمونه: `docs/apk-signature.md` در گزارش‌های قدیمی `finn/reports/` و `docs/architecture/repowise/findings-2026-11-20.md`.
- **اقدام پیشنهادی:** این ارجاع‌های قدیمی در اسناد تاریخی بمانند یا به مسیر جدید اصلاح شوند؛ تصمیم با مالک است.

## ۴. معماری (`architecture.dsl`)
- مدل committed در `docs/architecture/repowise/architecture.dsl` دست‌نخورده ماند.
- خروجی خودکار `repowise export --format structurizr` بسیار خلاصه‌تر است (۱۱ خط با `--standalone --components`) و جای مدل curated را نمی‌گیرد. بنابراین بازنویسی نشد.

## ۵. نمودار
- `qa-report/graphs/load-latency-200users.png`: تأخیر p50/p95/p99 به تفکیک مسیر در اورلود ۲۰۰ کاربر (SQLite، محلی).

## ۶. خارج از این snapshot
- `interaction-map` (`scripts/interaction_map.py --check`): پاس؛ ۳۱ سطح، ۱۶۳ مسیر قرارداد، رانش صفر.
- `docs_gate.py`: پاس؛ ۱۸ سند Markdown، ۲۷۳ لینک محلی، ۱۵ بلوک Mermaid.
- خروجی کامل JSON RepoWise در `.repowise` روی کپی باقی ماند و به مخزن commit نشد (طبق سیاست قبلی برای فایل‌های بزرگ).
