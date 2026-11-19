# ECC native setup — نتیجهٔ اجرای محیطی

- شاخه: `arena/b0e55b62-mp`؛ این گزارش جای نقشهٔ محصول را نمی‌گیرد.
- فرمان درخواستی `npx ecc-universal@2.2.3 setup` با `npm_config_yes=true` اجرا شد و با exit 1 متوقف شد: interactive setup requires a terminal. ابزار bash این محیط stdin بسته و ترمینال تعاملی ندارد.
- بررسی حالت غیرتعاملی نخست `CLAUDE_NOT_FOUND` برگرداند؛ فایل اجرایی `claude` روی PATH اولیه نبود.
- از npm، `@anthropic-ai/claude-code@2.1.328` به همراه `ecc-universal@2.2.3` در محیط موقتی npx فراهم شد. dry-run حالت `local` با hooks خاموش `would-install` داد؛ سپس دستور غیرتعاملی همان حالت اجرا و `action: installed`, `pluginId: ecc@ecc`, `scope: local`, `hooks: off`, `restartRequired: true` بازگرداند.
- بررسی `claude plugin list --json` در همان پروژه `ecc@ecc` نسخهٔ 2.2.3 را با `enabled: true`, `scope: local`, `projectPath: /home/user/MP` و همچنین `projectEnabled: false` گزارش کرد؛ این دو فیلد را فراتر از آنچه خروجی می‌گوید تفسیر نمی‌کنیم. manifest موجود و ۷۲ فایل تعریف agent در cache شمارش شد. RestartRequired پابرجاست.
- خروجی خود Claude هشدار `dependencies-refused` داشت: بسته‌های فهرست‌شده در plugin به‌دلیل overrides نصب نشده‌اند؛ پوشش کامل اجزای runtime یا hooks و شروع agentها اثبات نشده است. hooks عمداً خاموش و هیچ حساب یا مدل بیرونی فراخوانی نشده است.
- این راه‌اندازی افزونهٔ **Claude Code** است؛ به‌تنهایی ابزار subagent جدید به رابط همین نشست Arena اضافه نمی‌کند. هیچ subagent ECC یا review مستقل در این کار اجرا نشده است. فایل‌های home، npx cache و تنظیمات local ignored ممکن است در sandbox تازه باقی نمانند؛ وجودشان در آینده فرض نشود.
- برای بازبینی بدون چاپ دادهٔ حساس: `npx --yes --package=@anthropic-ai/claude-code@2.1.328 -c 'claude plugin list --json'` و سپس بررسی فقط متادیتای plugin موردنظر. هیچ secret یا دادهٔ واقعی در این گزارش ثبت نشده است.
