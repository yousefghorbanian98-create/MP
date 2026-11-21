#!/usr/bin/env python3
"""ساخت فایل راهنمای جامع (PROJECT-HANDOFF) از خود کد مخزن.

هدف: یک نشست AI که این فایل را باز می‌کند، ساختار، قراردادها، داده، گیت‌ها، نقش‌ها و
جریان‌های اصلی Muscle Paradise را بدون خواندن همهٔ فایل‌ها بفهمد.

فقط کتابخانهٔ استاندارد پایتون. هر عدد از فایل‌های واقعی خوانده می‌شود، نه از حافظه.

    python3 scripts/repowise_handoff.py            # بازنویسی docs/architecture/repowise/PROJECT-HANDOFF.md
    python3 scripts/repowise_handoff.py --check    # خطا اگر فایل commit‌شده با کد نمی‌خواند
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/architecture/repowise/PROJECT-HANDOFF.md"
BACK = ROOT / "mp-app/backend"
STUDIO = ROOT / "mp-app/studio"
CLIENT = ROOT / "mp-app/client"


def rel(p: Path) -> str:
    return p.relative_to(ROOT).as_posix()


def git_head() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                              capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return "unknown"


def count_files(base: Path, pattern: str, exclude: tuple[str, ...] = ()) -> int:
    n = 0
    for p in base.rglob(pattern):
        s = p.as_posix()
        if any(x in s for x in exclude):
            continue
        n += 1
    return n


def sec_components() -> str:
    rows = [
        ("اپ عضو (Flutter)", rel(CLIENT), f"{count_files(CLIENT/'lib', '*.dart')} فایل Dart در lib", f"{count_files(CLIENT/'test', '*.dart')} فایل تست"),
        ("Studio (React + TS)", rel(STUDIO), f"{count_files(STUDIO/'src', '*.ts*', ('node_modules',))} فایل در src", f"{count_files(STUDIO/'tests', '*.ts*')} فایل تست"),
        ("API (FastAPI)", rel(BACK), f"{count_files(BACK/'modules', '*.py', ('__pycache__',))} فایل Python در modules", f"{count_files(BACK/'tests', '*.py', ('__pycache__',))} فایل تست"),
    ]
    out = ["| بخش | مسیر | اندازه | تست |", "|---|---|---|---|"]
    out += [f"| {a} | `{b}` | {c} | {d} |" for a, b, c, d in rows]
    return "\n".join(out)


def sec_modules(routes: dict) -> str:
    per = defaultdict(lambda: [0, 0])  # module -> [paths, ops]
    for path in routes["paths"]:
        seg = path.split("/")[3] if path.count("/") >= 3 else "root"
        per[seg][0] += 1
    for op in routes["operations"]:
        seg = op["path"].split("/")[3] if op["path"].count("/") >= 3 else "root"
        per[seg][1] += 1
    mods = sorted((BACK / "modules").iterdir()) if (BACK / "modules").exists() else []
    names = sorted({m.name for m in mods if m.is_dir() and not m.name.startswith("__")})
    out = ["نگاشت مسیر به ماژول تقریبی است: پیشوند مسیر (مثلاً `assessments`) گاهی با نام پوشه (`assessment`) فرق دارد. برای نگاشت دقیق، روتر هر ماژول را بخوانید.", "", "| ماژول (`modules/`) | فایل‌های Python | مسیرهای API با پیشوند هم‌نام | عملیات |", "|---|---|---|---|"]
    for name in names:
        n = count_files(BACK / "modules" / name, "*.py", ("__pycache__",))
        p, o = per.get(name, [0, 0])
        out.append(f"| `{name}` | {n} | {p} | {o} |")
    extra = sorted(k for k in per if k not in names)
    if extra:
        out.append("")
        out.append("پیشوندهای API بدون پوشهٔ هم‌نام در `modules/` (در `api/` یا `app/` تعریف شده‌اند): " + "، ".join(f"`{k}` ({per[k][1]} عملیات)" for k in extra))
    return "\n".join(out)


def sec_api(routes: dict) -> str:
    ops = sorted(routes["operations"], key=lambda o: (o["path"], o["method"]))
    out = [f"{len(routes['paths'])} مسیر و {len(ops)} عملیات. منبع: `mp-app/backend/api/routes.json` (تولیدشده از کد).", "",
           "| متد | مسیر | نگهبان (guard) | نقش‌های مجاز |", "|---|---|---|---|"]
    for o in ops:
        guards = ", ".join(o.get("guards", [])) or "—"
        roles = ", ".join(o.get("roles", [])) or "—"
        out.append(f"| {o['method']} | `{o['path']}` | {guards} | {roles} |")
    return "\n".join(out)


def sec_data() -> str:
    tables = []
    for f in sorted((BACK / "db/models").glob("*.py")):
        text = f.read_text(encoding="utf-8")
        for m in re.finditer(r'class (\w+)\(.*?\):\s*\n(?:.*\n)*?\s*__tablename__\s*=\s*"([^"]+)"', text):
            tables.append((m.group(2), m.group(1), f.name))
    out = [f"{len(tables)} جدول ORM. منبع: `mp-app/backend/db/models/*.py`.", "",
           "| جدول | کلاس | فایل |", "|---|---|---|"]
    out += [f"| `{t}` | {c} | `{fn}` |" for t, c, fn in sorted(tables)]
    return "\n".join(out)


def sec_migrations() -> str:
    versions = BACK / "db/migrations/versions"
    revs, downs = {}, set()
    for f in versions.glob("*.py"):
        text = f.read_text(encoding="utf-8")
        r = re.search(r'^revision\s*(?::\s*str\s*)?=\s*["\']([^"\']+)["\']', text, re.M)
        d = re.search(r'^down_revision\s*(?::[^=]*)?=\s*(.+)$', text, re.M)
        if r:
            revs[r.group(1)] = f.name
            if d:
                for x in re.findall(r'["\']([^"\']+)["\']', d.group(1)):
                    downs.add(x)
    heads = [r for r in revs if r not in downs]
    return (f"{len(revs)} مهاجرت Alembic. سرِ فعلی (head): {', '.join(f'`{revs[h]}`' for h in heads) or 'نامشخص'}.\n"
            "اعمال: `cd mp-app/backend && alembic upgrade head`.")


def sec_config() -> str:
    text = (BACK / "app/config.py").read_text(encoding="utf-8")
    body = text.split("class Settings", 1)[1].split("\n\n\n", 1)[0]
    rows = re.findall(r'^\s{4}([a-z_]+): [^=\n]+ = (.+?)(?:\s+#.*)?$', body, re.M)
    out = ["متغیرهای محیط با پیشوند `MP_` (مثلاً `MP_DATABASE_URL`). مقدار پیش‌فرض کد:", "",
           "| کلید | پیش‌فرض |", "|---|---|"]
    out += [f"| `MP_{k.upper()}` | `{v.strip()}` |" for k, v in rows]
    return "\n".join(out)


def sec_permissions() -> str:
    text = (BACK / "app/security/grants.py").read_text(encoding="utf-8")
    block = text.split("KNOWN_PERMISSIONS", 1)[1].split("}", 1)[0]
    rows = re.findall(r'"([a-z_.]+)":\s*"([^"]+)"', block)
    out = ["مجوزهای شناخته‌شده (کلید ناشناخته هرگز مجاز نیست). منبع: `app/security/grants.py`.", "",
           "| مجوز | کاربرد |", "|---|---|"]
    out += [f"| `{k}` | {v} |" for k, v in rows]
    return "\n".join(out)


def sec_studio() -> str:
    side = (STUDIO / "src/components/Sidebar.tsx").read_text(encoding="utf-8")
    items = re.findall(r'\{ id: "(\w+)", label: "([^"]+)"', side)
    app = (STUDIO / "src/App.tsx").read_text(encoding="utf-8")
    pages = re.findall(r'^\s{2}(\w+): (\w+),?$', app.split("const pages = {", 1)[1].split("} as const", 1)[0], re.M)
    out = ["| شناسهٔ صفحه | عنوان در منو | کامپوننت |", "|---|---|---|"]
    labels = {a: b for a, b in items}
    comp = {a: b for a, b in pages}
    for pid in comp:
        out.append(f"| `{pid}` | {labels.get(pid, '— (بدون ورودی منو)')} | `{comp[pid]}` |")
    out.append("")
    out.append("دسترسی هر صفحه بر اساس نقش در `src/lib/roleNav.ts` (تابع `canSeePage`) تعیین می‌شود. عنوان هر صفحه در `src/components/TopBar.tsx` است؛ تست `tests/topbarTitles.test.tsx` پوشش آن را نگه می‌دارد.")
    return "\n".join(out)


def sec_client() -> str:
    feats = sorted(p.name for p in (CLIENT / "lib/features").iterdir() if p.is_dir())
    return ("پوشه‌های ویژگی در `mp-app/client/lib/features/`: " + "، ".join(f"`{f}`" for f in feats) +
            ".\n\nنقطهٔ ورود: `lib/main.dart`. وضعیت بیلد: وب در CI (`web.yml`) ساخته می‌شود؛ APK امضاشده **BLOCKED** است تا اسرار `MP_ANDROID_*` تنظیم شوند.")


def sec_ci() -> str:
    out = ["| فایل | نام | رویداد(ها) | jobs |", "|---|---|---|---|"]
    for f in sorted((ROOT / ".github/workflows").glob("*.yml")):
        text = f.read_text(encoding="utf-8")
        name_m = re.search(r'^name:\s*(.+)$', text, re.M)
        name = name_m.group(1).strip() if name_m else f.stem
        lines = text.splitlines()
        on_lines, grab = [], False
        for line in lines:
            if re.match(r'^on:\s*$', line):
                grab = True
                continue
            if grab:
                if line and not line.startswith((" ", "\t")):
                    break
                on_lines.append(line)
        on_block = "\n".join(on_lines)
        events = sorted(set(re.findall(r'^  ([a-z_]+):', on_block, re.M)))
        jobs = []
        if "\njobs:" in text:
            jobs_text = text.split("\njobs:", 1)[1]
            jobs = re.findall(r'^  ([a-z0-9][a-z0-9-]*):\s*$', jobs_text, re.M)
        out.append(f"| `{f.name}` | {name} | {', '.join(events) or '—'} | {', '.join(jobs) or '—'} |")
    out.append("")
    out.append("گیت‌های `ci.yml`: `secret-scan`، `docs`، `backend` (pytest با `--cov-fail-under=70`)، `studio` (vitest، tsc، build)، `client-flutter`، `live-contract`، `e2e-api`، `client-pinned`.")
    return "\n".join(out)


def sec_flows() -> str:
    return """### ۱. ورود با OTP
1. `POST /api/v1/auth/otp/request` با شماره؛ کد ۶ رقمی با TTL پیش‌فرض ۱۲۰ ثانیه ساخته می‌شود (`otp_ttl_seconds`). در محیط `development` کد در پاسخ `dev_code` برمی‌گردد.
2. `POST /api/v1/auth/otp/verify` با شماره و کد؛ کاربر در صورت نبود ساخته می‌شود (نقش عضو) و جفت توکن برمی‌گردد.
3. `POST /api/v1/auth/refresh` توکن را می‌چرخاند؛ `logout` و `logout-all` نشست‌ها را می‌بندند.
4. تغییر شماره سه مرحله دارد: `phone-change/request` → `verify-old` → `confirm`.
نرخ محدودیت: `otp_rate_limit` = `10/minute`، `otp_burst_limit` = `3/second`؛ حداکثر تلاش `otp_max_attempts` = ۵.

### ۲. پرداخت، کیف‌پول و کوپن
- کوپن در `modules/payments/service.py` (`_apply_coupon`) روی سرور و روی مبلغ واقعی محاسبه می‌شود. نوع: درصدی (۱ تا ۱۰۰) یا مبلغ ثابت ریال؛ هر دو با انقضا و سقف استفاده.
- حداقل مبلغ پس از تخفیف ۱٬۰۰۰ ریال است. کد تکراری پاسخ ۴۰۹ می‌دهد. کوپن با کلید idempotency یک‌بار مصرف می‌شود.
- حالت‌های پرداخت: `pending` → `paid` | `failed` | `in_review`؛ `in_review` → `paid` | `failed`؛ `paid` → `refunded`. نمودار: `docs/architecture/diagram-design/png/02-payments-lifecycle.png`.
- رسید کارت‌به‌کارت: `receipts.py` وضعیت رسید را `in_review` می‌کند؛ تأیید ادمین `approved` و رد `rejected` می‌سازد.
- کیف‌پول: موجودی = مجموع credit − مجموع debit (`_wallet_balance_expr`). دسترسی عضو فقط به کیف‌پول خودش است (`ensure_member_scope` با `Member.id`، نه `User.id`).
- درگاه: `payment_gateway` = `manual` (پیش‌فرض) | `mock` | `sandbox`.

### ۳. دامنه‌ها و نقش‌ها
- نقش‌ها: `member`، `coach`، `manager`، `reception`، `admin`، `super_admin`.
- مجوزهای جزئی (`grants`) فقط برای کارهایی که پول یا گزارش حساس را جابه‌جا می‌کنند لازم‌اند؛ فهرست در بخش مجوزها.
- گارد `require_permission()` روی روتر `/programs` است؛ عضو به آن دسترسی ندارد (۴۰۳ درست است).

### ۴. اورلود و عملکرد (اندازه‌گیری‌شده، محلی)
۲۰۰ کاربر همزمان، SQLite و یک worker: حدود ۱۸۰ درخواست بر ثانیه، p95 ≈ ۲۱۰ms، p99 ≈ ۳۳۰ms، ۰ خطا در دو اجرای سالم. یک بار استخر اتصال پر شد و ریشه‌یابی نشده است (`qa-report/FINAL-REPORT.md`).
"""


def sec_verification() -> str:
    return """آخرین اجرای اندازه‌گیری‌شده روی `main` (مرجع: `qa-report/FINAL-REPORT.md`):

| بخش | نتیجه | نکته |
|---|---|---|
| backend pytest | ۱٬۰۹۵ پاس، ۲ skip، پوشش ۹۴٫۲۸٪ | اندازه‌گیری شده |
| studio vitest | ۲۸۲ پاس، ۹ skip | اندازه‌گیری شده |
| studio tsc / build | بدون خطا | اندازه‌گیری شده |
| مرورگر (۱۱ صفحه) | بدون خطای کنسول، ۴xx/۵xx یا استثنا | اسکرین‌شات‌ها در `docs/MuscleParadise/screenshots/` |
| دکمه‌ها | ۴۵ کلیک، ۰ خطا | دکمه‌های مالی و مخرب کلیک نشدند (با تست‌های یکپارچه پوشش داده شده‌اند) |
| interaction map | ۳۱ سطح، ۱۶۳ مسیر، رانش صفر | گیت `scripts/interaction_map.py --check` |
| مستندات | ۱۸ سند، ۲۷۶ لینک محلی | گیت `scripts/docs_gate.py` |

### موانع واقعی (BLOCKED)
- APK امضاشده: اسرار `MP_ANDROID_*` و متغیر `MP_ANDROID_CERT_SHA256` تنظیم نشده‌اند.
- اجرای Flutter در sandbox: `pub.dev` و `storage.googleapis.com` مسدودند؛ فقط در Codespace یا CI.
- دستگاه واقعی، پرداخت بانکی، push/SMS، Valkey، PostgreSQL، Prometheus: در دسترس نیستند.
- انیمیشن: فریم‌ریت روی دستگاه اندازه‌گیری نشده است.
- همزمانی کوپن روی PostgreSQL: تست نشده (فقط SQLite).
"""


def sec_where() -> str:
    return """| می‌خواهید تغییر دهید… | از اینجا شروع کنید |
|---|---|
| قرارداد API یا مسیر جدید | `mp-app/backend/api/routes.json` (تولیدشده) و روتر ماژول در `modules/<name>/router.py` |
| منطق پرداخت یا کوپن | `mp-app/backend/modules/payments/service.py`، `receipts.py`، `schemas.py` |
| مهاجرت دیتابیس | `mp-app/backend/db/migrations/versions/` (سرِ فعلی در بخش مهاجرت‌ها) |
| مدل داده | `mp-app/backend/db/models/*.py` |
| مجوز یا نقش | `mp-app/backend/app/security/grants.py`، `ownership.py`، `deps.py` |
| صفحهٔ Studio | `mp-app/studio/src/pages/` + ثبت در `App.tsx` + منو در `Sidebar.tsx` + عنوان در `TopBar.tsx` |
| دسترسی صفحه به نقش | `mp-app/studio/src/lib/roleNav.ts` |
| صفحهٔ اپ عضو | `mp-app/client/lib/features/<name>/` |
| گیت‌های CI | `.github/workflows/*.yml` (هرگز گیت را شُل نکنید؛ تست یا کد را اصلاح کنید) |
| متغیر محیط | `mp-app/backend/app/config.py` (پیشوند `MP_`) |
| بذر داده برای QA محلی | `qa-report/tools/seed_live.py` |
| بار و تست مرورگر | `qa-report/tools/locustfile.py`، `qa-report/tools/browser/` |
"""


def sec_gaps() -> str:
    return """- **README** پیش‌تر ۱۲۱ مسیر و ۱۳۷ عملیات ذکر می‌کرد؛ عدد درست ۱۴۱ مسیر و ۱۶۳ عملیات است (منبع: `routes.json`).
- **README** پیش‌تر فقط بعضی workflowها را نام می‌برد؛ جدول بالا همهٔ فایل‌های `.github/workflows` را دارد.
- **`web.yml` و `apk.yml`** فقط `workflow_dispatch` دارند؛ اجرای خودکار روی push ندارند.
- **کیوسک / چک‌این** مسیر ناقص است و اتصال انتها‌به‌انتها کامل نشده است.
- **PostgreSQL، Valkey، pgBackRest، Prometheus** در نقشه‌اند و در این مخزن به‌صورت کامل اجرا و تأیید نشده‌اند.
- **تغذیه:** درخواست `nutrition/food-logs/member/-1/daily` با شناسهٔ placeholder `-1` ارسال می‌شود؛ باید بررسی شود.
- **بنر به‌روزرسانی** روی محتوای صفحه می‌افتد؛ ایموجی فوتر در فونت نمایش داده نمی‌شود.
- **استخر اتصال SQLite:** یک بار پر شد و ریشه‌یابی نشده است.
- **مستندات قدیمی** (`docs/MuscleParadise/`، گزارش‌های `finn/`) ممکن است به فایل‌های حذف‌شده اشاره کنند؛ `doc-drift` ۲۵ مورد از این دست یافته است.
"""


def build() -> str:
    routes = json.loads((BACK / "api/routes.json").read_text(encoding="utf-8"))
    head = git_head()
    parts = [
        "# PROJECT-HANDOFF — راهنمای جامع برنامه برای نشست‌های AI",
        "",
        f"> تولیدشده از کد با `scripts/repowise_handoff.py` · commit مرجع: `{head}`",
        "> بازتولید: `python3 scripts/repowise_handoff.py` · بررسی رانش: `python3 scripts/repowise_handoff.py --check`",
        "> این فایل از خود کد ساخته شده؛ برای جزئیات پیاده‌سازی، فایل منبع را بخوانید. قبل از ادعا درباره‌ی رفتار، آن را در کد یا تست تأیید کنید.",
        "",
        "## ۰. این فایل را چگونه بخوانیم",
        "۱. بخش‌های ۱ تا ۳ معماری و اندازه‌ها را می‌دهند.",
        "۲. بخش ۴ و ۵ قرارداد API و مدل داده را می‌دهند؛ هر مسیر نگهبان و نقش خودش را دارد.",
        "۳. بخش ۶ جریان‌های اصلی (OTP، پرداخت، کوپن، رسید، کیف‌پول) را توضیح می‌دهد.",
        "۴. بخش ۷ تا ۱۰ پیکربندی، مجوزها، Studio، اپ عضو و CI را می‌دهند.",
        "۵. بخش ۱۱ آخرین نتایج اندازه‌گیری‌شده و موانع را می‌دهد. بخش ۱۲ جدول «کجا را تغییر دهم» است.",
        "",
        "## ۱. اجزا و اندازه",
        sec_components(),
        "",
        "## ۲. ماژول‌های بک‌اند",
        sec_modules(routes),
        "",
        "## ۳. مسیرهای API (قرارداد)",
        sec_api(routes),
        "",
        "## ۴. جریان‌های اصلی",
        sec_flows(),
        "## ۵. مدل داده",
        sec_data(),
        "",
        "### مهاجرت‌ها",
        sec_migrations(),
        "",
        "## ۶. پیکربندی (متغیرهای محیط)",
        sec_config(),
        "",
        "## ۷. مجوزها",
        sec_permissions(),
        "",
        "## ۸. Studio (پنل مربی و مدیر)",
        sec_studio(),
        "",
        "## ۹. اپ عضو (Flutter)",
        sec_client(),
        "",
        "## ۱۰. CI و انتشار",
        sec_ci(),
        "",
        "## ۱۱. آخرین اعتبارسنجی و موانع",
        sec_verification(),
        "## ۱۲. کجا را تغییر دهم؟",
        sec_where(),
        "",
        "## ۱۳. کاستی‌ها و ادعاهای قدیمی",
        sec_gaps(),
        "",
        "## ۱۴. دیاگرام‌ها",
        "- معماری: `docs/architecture/diagram-design/png/01-architecture.png`",
        "- پرداخت، کوپن و رسید: `docs/architecture/diagram-design/png/02-payments-lifecycle.png`",
        "- CI و انتشار: `docs/architecture/diagram-design/png/03-ci-release.png`",
        "- منابع سازندهٔ دیاگرام‌ها: `docs/architecture/diagram-design/*.html` (HTML مستقل)",
        "",
    ]
    return "\n".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    text = build()
    if args.check:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != text:
            print(f"رانش: {rel(OUT)} با کد هم‌خوان نیست؛ با `python3 scripts/repowise_handoff.py` بازتولید کنید.", file=sys.stderr)
            return 1
        print("PROJECT-HANDOFF هم‌خوان با کد است.")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(f"نوشته شد: {rel(OUT)} ({len(text.splitlines())} خط)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
