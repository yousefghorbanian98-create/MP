# M97 — drift شناخته‌شدهٔ Alembic، تاریخچهٔ مهاجرت و مانور backup/restore

- تاریخ ثبت: ۲۰۲۶-۱۱-۱۸ (UTC)
- شاخه: `arena/4f336f66-mp`، وضعیت `active`، پایه `d64e3b008d1c6c20c65c5ebfa4816277d4d23ce0`
- نتیجهٔ loop: **`PASS` (دامنهٔ backend/docs؛ بدون تغییر رفتار محصول)**

## پرسش loop و پاسخ

معیار پذیرش سه چیز خواست: (۱) drift بین «DB scratch» و «migration history» تفکیک شود، (۲) migration روی DB آزمایشی قابل upgrade/downgrade باشد، (۳) backup/restore مستند باشد.

| پرسش | پاسخ با اجرای واقعی | شاهد |
|---|---|---|
| آیا `alembic upgrade head` و `Base.metadata.create_all` همان schema را می‌سازند؟ | بله — **۵۲ جدول، صفر اختلاف ستون (نوع/nullable)، صفر اختلاف ایندکس دستی** | `test_create_all_and_migrations_build_the_same_schema` + مقایسهٔ دستی `/tmp/m97/compare.py` (خروجی: `tables only in migrated: []`, `column diffs: 0`, `index diffs: 0`) |
| تاریخچهٔ migration سالم است؟ | بله — **۲۶ revision، یک head `f9b0c1d2e3f4`** (merge point)، بدون `down_revision` گم‌شده، بدون یتیم، فایل‌ها↔گراف یکسان | `test_migration_history_has_one_head_and_no_broken_links` + `alembic heads` / `alembic current` |
| drift باقی‌مانده هست؟ | نه روی این HEAD — `alembic check` روی DB تازه و روی DB round-trip‌شده «No new upgrade operations detected» می‌دهد | `test_m47_migration_drift.py` (۳ تست سبز؛ `upgrade head` → `downgrade base` → `upgrade head` سبز) |
| DB قدیمیِ ساخته‌شده با `create_all` قابل baseline است؟ | بله — `alembic stamp head` سپس `current` روی head و `check` بدون drift | `test_existing_create_all_database_can_be_baselined_by_migrations` |
| restore برای «تمرین scratch» امن است؟ | **قبلاً نه** — اصلاح شد؛ حالا `verify` و `restore --extras-to` هست | `test_backup_verify_and_scratch_restore`، `test_verify_rejects_a_tampered_archive` |

## یافتهٔ واقعی (و اصلاح)

1. **`restore` فایل‌های الحاقی را در مسیر زنده می‌نوشت.** `mp-app/backend/scripts/backup.py` بعد از برگرداندن DB، `modules/updates/registry.json` و `shared/design-tokens.json` را **در همان مسیر اصلی‌شان** بازنویسی می‌کرد. برای restore تولیدی این عمدی است (این فایل‌ها در ایمیج کنار DB‌اند)، اما همان رفتار باعث می‌شد:
   - «تمرین ماهانه روی scratch» که `OPS-RUNBOOK.md` §۲ لازم می‌داند، عملاً مسیرِ بدون‌خطر نداشته باشد؛
   - خودِ تست M30 (`test_backup_drill.py`) با هر اجرا درخت کاری را بازنویسی کند (محتوا یکسان، پس در `git status` دیده نمی‌شد).
   **اصلاح:** `verify <archive>` (فقط خواندن: manifest + SHA256 + `PRAGMA integrity_check` + نسخهٔ Alembic داخل آرشیو) و `restore --extras-to DIR`. مسیر پیش‌فرض بدون `--extras-to` عوض نشد تا دستورهای مستندشده بشکنند؛ تست M30 به scratch منتقل شد و حالا صریحاً بررسی می‌کند فایل‌های زنده بایت‌به‌بایت تغییر نکرده‌اند.
2. **دستورِ runbook از ریشهٔ مخزن اجرا نمی‌شد.** `OPS-RUNBOOK.md` §۲ `python scripts/backup.py …` را می‌داد؛ اسکریپت واقعی در `mp-app/backend/scripts/backup.py` است و مسیر کوتاه فقط داخل کانتینر (WORKDIR `/srv/mp/backend`) درست است. runbook هر دو حالت + دو دستور `verify`/`--extras-to` + بررسی `alembic current`/`check` روی DB بازگردانده‌شده را نوشت.
3. **منطق drift فقط یک سمت را می‌سنجید.** `alembic check` (گیت M47) «DB مهاجرت‌کرده = مدل» را اثبات می‌کند، ولی هیچ‌گاه «DB ساخته‌شده با `create_all` = DB مهاجرت‌کرده» را؛ در حالی که dev/test از مسیر دوم است و migration `8a1f2c3d4e5b_m58_drop_orphan_indexes` دقیقاً برای همان واگرایی نوشته شده بود. حالا آن مقایسه یک تست است، نه فرض.
4. **گیت تست شکننده نسبت به cwd (خارج از دامنه، ثبت‌شده).** `tests/integration/test_monitoring.py::test_alert_rules_cover_slo_and_down` مسیر `../infra/monitoring/alerts.yml` را نسبت به cwd باز می‌کرد؛ از `mp-app/backend` سبز و از ریشهٔ مخزن قرمز می‌شد. CI از `mp-app/backend` اجرا می‌کند، پس گیت هیچ‌وقت قرمز نبود. تغییر داده نشد (خارج از دامنهٔ M97 است و گیت CI را نمی‌شکند)؛ اینجا ثبت شد تا در loop پاک‌سازی تکرار نشود.

## فایل‌های تغییریافته

| فایل | تغییر |
|---|---|
| `mp-app/backend/scripts/backup.py` | `verify()` + `_validated_bundle()` مشترک + `restore(extras_dir=…)` + CLI `verify` و `--extras-to`؛ مستندسازی چرایی |
| `mp-app/backend/tests/integration/test_m97_migrations_and_backup.py` | ۵ تست جدید (schema parity، baseline با stamp، تاریخچهٔ یک‌head، مانور backup→verify→restore روی scratch، رد آرشیو دست‌کاری‌شده) |
| `mp-app/backend/tests/integration/test_backup_drill.py` | مانور به `extras_dir=tmp_path` منتقل شد + ادعای «فایل زنده دست‌نخورده» |
| `docs/MuscleParadise/OPS-RUNBOOK.md` | §۲: مسیر واقعی اسکریپت، `verify`، `--extras-to`، بررسی Alembic پس از restore |
| `docs/MuscleParadise/runbooks/provisioning.md` | بخش «مهاجرت schema و drift (M97)»: مرجع بودن migration، الگوی baseline، قانون یک head، دستور اجرای گیت‌ها |

هیچ migration تازه‌ای لازم نشد (drift صفر بود)؛ هیچ جدول/ستونی تغییر نکرد؛ `alembic.ini`، `env.py` و DB تولید/محلی دست‌نخورده‌اند.

## شواهد اجرا (همه محلی، SQLite موقت)

| گیت | نتیجه |
|---|---|
| `pytest tests/integration/test_m97_migrations_and_backup.py test_backup_drill.py test_m47_migration_drift.py test_infra.py regression/test_production_ops.py` | **36 passed** |
| `alembic upgrade head` / `downgrade base` / `upgrade head` / `check` روی DB scratch | rc=0؛ بدون drift (داخل تست‌ها اجرا شد) |
| `alembic heads` / `current` | `f9b0c1d2e3f4 (head)`؛ `current` همان head با `(mergepoint)` |
| مقایسهٔ schema دو مسیر | ۵۲↔۵۲ جدول، صفر اختلاف |
| `ruff check` + `ruff format --check` روی سه فایل تغییریافته | سبز |
| `bandit -ll` روی `scripts/backup.py` و تست جدید | بدون یافتهٔ medium/high |
| `python3 scripts/docs_gate.py` | **سبز: 7 فایل Markdown، 99 لینک محلی، 3 بلوک Mermaid** |
| `pytest -q mp-app/backend/tests` (کل suite، از ریشه) | **861 passed / 1 failed / 1 skipped** — تنها شکست، همان `test_monitoring` بالا (به‌دلیل cwd؛ از `mp-app/backend` سبز است: 10 passed) |

### راستی‌آزمایی «گیت‌ها توخالی نیستند»

پیش از `PASS`، حساسیت دو گیت جدید با تزریق خرابی سنجیده شد (اسکریپت `/tmp/m97/sens*.py`):

- افزودن یک ایندکس و یک ستون به DB ساخته‌شده با `create_all` → مقایسهٔ schema دقیقاً همان دو مورد را گزارش کرد.
- ساخت revision موازی → `get_heads()` دو تایی شد و ادعای «یک head» قرمز می‌شود؛ `down_revision` گم‌شده و revision تکراری هم در همان walk خطا می‌دهند (شکست بلند، نه سبز کاذب).

## محدودیت‌ها (صادقانه)

- همهٔ اعداد روی **SQLite موقت** و schema خالی/مصنوعی‌اند؛ DB واقعی باشگاه، `/data/mp.db` تولید و Postgres هرگز لمس نشدند. «restore روی محیط واقعی» همچنان تمرین‌نشده است.
- parity schema تا سطح جدول/ستون(نوع+nullable)/ایندکس دستی است؛ **CHECK expressions، دیفالت‌های پیچیده، view/trigger و FDOهای Postgres** مقایسه نمی‌شوند (در SQLite تفاوت‌سازند). یک diff واقعی در آن لایه‌ها می‌تواند از این گیت رد شود.
- اجرای Alembic با dialect SQLite سنجیده شد؛ اگر استقرار واقعی روی Postgres برود، همان تست‌ها باید با URL آن dialect اجرا شوند (فعلاً در این workspace شدنی نیست و ادعا نشده).
- ECC/REA: این sandbox هیچ زیرعامل اجراکننده‌ای ندارد — `node` هست ولی `claude`/REA نصب نیست و هیچ API key تنظیم نشده (تطبیق شد: مقدارها unset‌اند). بازبینی با چک‌لیست‌های `.claude/agents/{code-reviewer,security-reviewer}.md` **دستی** انجام شد؛ به‌عنوان اجرای subagent ثبت نمی‌شود.
- commit/push: فقط طبق D-047 برای بستهٔ نهایی؛ تا لحظهٔ نگارش این گزارش، هیچ commit در این loop انجام نشده بود.

## بازگشت

`git checkout -- mp-app/backend/scripts/backup.py mp-app/backend/tests/integration/test_backup_drill.py docs/MuscleParadise/OPS-RUNBOOK.md docs/MuscleParadise/runbooks/provisioning.md` و حذف فایل تست جدید، رفتار قبلی را برمی‌گرداند. اثر بازگشت: `verify` و `--extras-to` حذف می‌شوند و تست M30 دوباره فایل‌های الحاقی را در درخت کاری بازنویسی می‌کند.
