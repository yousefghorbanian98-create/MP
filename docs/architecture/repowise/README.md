# معماری و بهداشت کد با RepoWise (ثبت ۲۰۲۶-۱۱-۲۰)

این پوشه خروجی **تولیدشده** ابزار متن‌باز [RepoWise](https://github.com/baunes/repowise) است، با حالت `--no-prose` (بدون مدل زبانی و بدون کلید API). ابزار روی کپی مخزن در `b194e96` اجرا شد؛ اعداد زیر فقط همان snapshot را توصیف می‌کنند.

## محتوا
| فایل | چیست |
|---|---|
| `architecture.dsl` | مدل C4 به فرمت Structurizr DSL (سیستم، کانتینرها، اجزا). با Structurizr Lite یا CLI باز می‌شود. |
| `findings-2026-11-20.md` | خلاصهٔ یافته‌های سلامت کد، کد مرده و drift مستندات. |

## آنچه commit نشده
- **ایندکس محلی** (`.repowise/`، حدود ۶۲ مگابایت): در `.gitignore` است و نباید وارد Git شود.
- **۴۲۱ صفحهٔ wiki** (حدود ۱٫۹ مگابایت، پوشهٔ `export` موقت): خروجی خام و پرحجم است؛ در صورت نیاز با دستور زیر تولید می‌شود.
- **فایل‌های agent/editor** که RepoWise اضافه می‌کند (`.claude/`، `.vscode/`، `.github/copilot-instructions.md`): گیت CI ورود `.claude/` به Git را می‌بندد و این فایل‌ها تصمیم جداگانه‌ای هستند.

## بازتولید
```bash
pip install repowise
repowise init --no-prose          # بدون -y: -y hook و تنظیمات کاربری نصب می‌کند
repowise export --format structurizr --standalone -o docs/architecture/repowise/architecture.dsl
repowise health
repowise dead-code
repowise doc-drift
```

## محدودیت‌ها
- یافته‌های RepoWise **شواهدی برای بررسی‌اند، نه اثبات خطا**. مثلاً `unused_export` فقط می‌گوید نام در جای دیگری ذکر شده؛ برای `UpdateService` جست‌وجوی دستی هم تأیید کرد که callerی در `lib/` ندارد، ولی باقی موارد باید بررسی شوند.
- Structurizr Lite (Docker) در این sandbox اجرا نشد؛ فایل فقط ساختار نحوی آن را بررسی کرده است، نه رندر بصری.
- ابزار حالت `--prose` (توضیح‌نویسی با مدل) را اجرا نکرده است.
