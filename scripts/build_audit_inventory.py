#!/usr/bin/env python3
"""تولید فهرست کامل ممیزی (stdlib فقط).

ورودی‌ها:
  docs/MuscleParadise/audit/findings.json  — ۵۸ مشکل، ۲۹ یافته، موارد «مشکل نیست»، موانع محیطی
  docs/MuscleParadise/audit/status.json    — وضعیت هر مورد (OPEN / IN-PROGRESS / FIXED / DEFERRED / NOT-REPRODUCED)

خروجی‌ها:
  docs/MuscleParadise/audit/CHECKLIST.md   — فهرست خط‌به‌خط همهٔ موارد با وضعیت
  docs/MuscleParadise/audit/INVENTORY.md   — هر فایل ترک‌شده، هر مسیر API، هر دکمه/هندلر استودیو، هر workflow

اجرا:  python3 scripts/build_audit_inventory.py          (تولید)
       python3 scripts/build_audit_inventory.py --check  (شکست اگر خروجی کهنه باشد)
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "docs" / "MuscleParadise" / "audit"
TEXT_SUFFIXES = {
    ".py", ".ts", ".tsx", ".js", ".mjs", ".cjs", ".jsx", ".dart", ".kt", ".kts", ".java",
    ".gradle", ".md", ".yml", ".yaml", ".json", ".toml", ".ini", ".cfg", ".txt", ".sh",
    ".html", ".css", ".svg", ".sql", ".dsl", ".xml", ".properties", ".arb", ".conf",
    ".dockerfile", ".env", ".example", ".gitignore", ".mod", ".lock",
}
ROUTE_DECORATOR = re.compile(r'@router\.(get|post|put|patch|delete)\(\s*["\']([^"\']*)["\']')
ROUTER_PREFIX = re.compile(r'APIRouter\(\s*[^)]*?prefix\s*=\s*["\']([^"\']*)["\']', re.S)
JOB_KEY = re.compile(r"^  ([A-Za-z0-9_-]+):\s*$")


def tracked_files() -> list[str]:
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True)
    return [line for line in out.stdout.splitlines() if line]


def area_of(path: str) -> str:
    parts = path.split("/")
    if path.startswith("mp-app/backend/"):
        return "بک‌اند (FastAPI)"
    if path.startswith("mp-app/studio/"):
        return "استودیو (React)"
    if path.startswith("mp-app/client/"):
        return "اپ عضو (Flutter)"
    if path.startswith("mp-app/infra/") or parts[0] in {".devcontainer"}:
        return "زیرساخت و کانتینر"
    if path.startswith(".github/"):
        return "CI/CD"
    if path.startswith("docs/"):
        return "مستندات"
    if path.startswith("scripts/") or path.startswith("tools/") or path.startswith("harness/"):
        return "اسکریپت و ابزار"
    if path.startswith("qa-report/") or path.startswith("evidence/"):
        return "شواهد QA"
    if path.startswith("finn/") or path.startswith(".finn/"):
        return "گزارش‌های عامل"
    if path.startswith("mp-app/"):
        return "سایر mp-app"
    return "ریشه و تنظیمات"


def line_count(path: Path) -> tuple[int | None, int]:
    size = path.stat().st_size
    if path.suffix.lower() not in TEXT_SUFFIXES and path.suffix:
        return None, size
    try:
        with path.open("rb") as fh:
            return sum(1 for _ in fh), size
    except OSError:
        return None, size


def collect_routes() -> list[tuple[str, str, str, int]]:
    rows: list[tuple[str, str, str, int]] = []
    for path in sorted((ROOT / "mp-app" / "backend").rglob("*.py")):
        if "tests" in path.parts or ".venv" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        prefix_match = ROUTER_PREFIX.search(text)
        prefix = prefix_match.group(1) if prefix_match else ""
        for number, line in enumerate(text.splitlines(), 1):
            match = ROUTE_DECORATOR.search(line)
            if match:
                rel = path.relative_to(ROOT).as_posix()
                rows.append((match.group(1).upper(), prefix + match.group(2), rel, number))
    return rows


def collect_openapi() -> list[tuple[str, str]] | None:
    """عملیات‌های واقعی از app.openapi() (اگر وابستگی‌های بک‌اند نصب باشد)."""
    code = (
        "import json,os,sys;os.environ.setdefault('MP_ENVIRONMENT','development');"
        "from app.main import app;s=app.openapi();"
        "print(json.dumps(sorted((m.upper(),p) for p,v in s['paths'].items()"
        " for m in v if m in ('get','post','put','patch','delete'))))"
    )
    try:
        out = subprocess.run(
            [sys.executable, "-c", code], cwd=ROOT / "mp-app" / "backend",
            capture_output=True, text=True, timeout=120, check=True,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return None
    return [(m, p) for m, p in json.loads(out.stdout)]


def collect_studio() -> list[dict]:
    rows = []
    for path in sorted((ROOT / "mp-app" / "studio" / "src").rglob("*.tsx")):
        text = path.read_text(encoding="utf-8", errors="replace")
        rows.append({
            "file": path.relative_to(ROOT).as_posix(),
            "buttons": len(re.findall(r"<button\b", text)),
            "antd_button": len(re.findall(r"<Button\b", text)),
            "onclick": len(re.findall(r"onClick\s*=", text)),
            "dynamic_import": len(re.findall(r"await\s+import\(", text)),
            "lines": text.count("\n") + 1,
        })
    return rows


def collect_workflows() -> list[dict]:
    rows = []
    for path in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
        lines = path.read_text(encoding="utf-8").splitlines()
        jobs, in_jobs = [], False
        for line in lines:
            if re.match(r"^jobs:\s*$", line):
                in_jobs = True
                continue
            if in_jobs and line and not line.startswith(" "):
                break
            if in_jobs:
                match = JOB_KEY.match(line)
                if match:
                    jobs.append(match.group(1))
        uses_unpinned = sum(
            1 for line in lines if re.search(r"uses:\s*\S+@", line) and not re.search(r"@[0-9a-f]{40}\b", line)
        )
        rows.append({
            "file": path.relative_to(ROOT).as_posix(),
            "jobs": jobs,
            "unpinned_uses": uses_unpinned,
        })
    return rows


def md_escape(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def build_checklist(data: dict, status: dict) -> str:
    out = [
        "# فهرست خط‌به‌خط ممیزی MP",
        "",
        "> تولیدشده با `scripts/build_audit_inventory.py` — **دستی ویرایش نکنید.** وضعیت هر مورد در `status.json` است.",
        "",
        "منبع: بستهٔ ممیزی `MP-PROBLEMS-2026-11-20.md` و `MP-FINAL-AUDIT-REPORT-2026-11-20.md` (از مخزن `Chat2DB` شاخهٔ `arena/2cde32d6-chat2db`).",
        "",
        "وضعیت‌ها: `OPEN` باز · `IN-PROGRESS` در حال کار · `FIXED` رفع‌شده با شاهد · `DEFERRED` به تصمیم مالک · `NOT-REPRODUCED` بازتولید نشد · `VERIFIED-IN-CODE` در کد دیده شد (هنوز بازتولید اجرایی نشده).",
        "",
    ]
    sections = [
        ("problems", "الف) ۵۸ مشکل (بخش‌های A–D بریف)"),
        ("findings", "ب) ۲۹ یافته (F-01 … F-29)"),
        ("blocked", "ج) موانع محیطی (BLOCKED)"),
        ("non_issues", "د) مواردی که مشکل نیستند (دوباره بررسی نشوند)"),
    ]
    counts: Counter = Counter()
    for key, heading in sections:
        out += [f"## {heading}", "", "| شناسه | عنوان | وضعیت | یادداشت |", "|---|---|---|---|"]
        for item in data[key]:
            st = status.get(item["id"], {"status": "OPEN", "note": ""})
            counts[(key, st["status"])] += 1
            out.append(f"| {item['id']} | {md_escape(item['title'])} | {st['status']} | {md_escape(st.get('note', ''))} |")
        out.append("")
    out += ["## خلاصه", "", "| بخش | وضعیت | تعداد |", "|---|---|---|"]
    for (key, st), n in sorted(counts.items()):
        out.append(f"| {key} | {st} | {n} |")
    out.append("")
    return "\n".join(out)


def build_inventory(files: list[str]) -> str:
    out = [
        "# فهرست کامل ریپو و سطوح ممیزی",
        "",
        "> تولیدشده با `scripts/build_audit_inventory.py` — **دستی ویرایش نکنید.**",
        "",
        "این فهرست همهٔ فایل‌های ترک‌شده، همهٔ مسیرهای API (از دکوراتورها)، همهٔ صفحه‌های استودیو با تعداد دکمه/هندلر، و همهٔ workflowها را ثبت می‌کند.",
        "ستون «بازبینی» نشان می‌دهد هر فایل تا کنون خط‌به‌خط بازبینی شده یا نه؛ در این مرحله همه `NOT-REVIEWED` هستند.",
        "",
    ]
    by_area: dict[str, list[tuple[str, int | None, int]]] = {}
    for rel in files:
        lines, size = line_count(ROOT / rel)
        by_area.setdefault(area_of(rel), []).append((rel, lines, size))
    total_lines = sum(l or 0 for rows in by_area.values() for _, l, _ in rows)
    out += [
        "## ۱. خلاصهٔ تعداد فایل",
        "",
        f"- کل فایل‌های ترک‌شده: **{len(files)}** (خطوط متنی: {total_lines})",
        "",
        "| ناحیه | تعداد فایل | خطوط متنی |",
        "|---|---|---|",
    ]
    for area in sorted(by_area):
        rows = by_area[area]
        out.append(f"| {area} | {len(rows)} | {sum(l or 0 for _, l, _ in rows)} |")
    out.append("")

    routes = collect_routes()
    ops = collect_openapi()
    if ops is not None:
        out += [
            "## ۲. عملیات API (از `app.openapi()`، مرجع اصلی)",
            "",
            f"مسیرها: **{len({p for _, p in ops})}**؛ عملیات (روش×مسیر): **{len(ops)}**.",
            "",
            "| روش | مسیر |",
            "|---|---|",
        ]
        for method, path in ops:
            out.append(f"| {method} | `{path}` |")
        out.append("")
    else:
        out += ["## ۲. عملیات API (ایستا؛ `app.openapi()` در این اجرا در دسترس نبود)", ""]
    out += [
        "### ۲-الف. دکوراتورهای `@router.*` (ایستا)",
        "",
        f"تعداد دکوراتورهای مسیر در فایل‌ها: **{len(routes)}**.",
        "",
        "| روش | مسیر کامل | فایل | خط |",
        "|---|---|---|---|",
    ]
    for method, path, rel, number in routes:
        out.append(f"| {method} | `{path}` | `{rel}` | {number} |")
    out.append("")

    studio = collect_studio()
    out += [
        "## ۳. صفحه‌ها و دکمه‌های استودیو",
        "",
        f"فایل‌های TSX در `src/`: **{len(studio)}**؛ دکمهٔ `<button>`: **{sum(r['buttons'] for r in studio)}**؛ `onClick`: **{sum(r['onclick'] for r in studio)}**؛ `await import()` پویا: **{sum(r['dynamic_import'] for r in studio)}**.",
        "",
        f"کامپوننت `<Button>` (antd): **{sum(r['antd_button'] for r in studio)}**. شمارش `onClick` شامل هر دو است.",
        "",
        "| فایل | `<button>` | `<Button>` | `onClick` | `await import()` | خطوط |",
        "|---|---|---|---|---|---|",
    ]
    for row in studio:
        out.append(f"| `{row['file']}` | {row['buttons']} | {row['antd_button']} | {row['onclick']} | {row['dynamic_import']} | {row['lines']} |")
    out.append("")

    workflows = collect_workflows()
    out += [
        "## ۴. Workflowهای CI",
        "",
        "| فایل | jobs | `uses:` بدون SHA |",
        "|---|---|---|",
    ]
    for wf in workflows:
        out.append(f"| `{wf['file']}` | {', '.join(wf['jobs']) or '—'} | {wf['unpinned_uses']} |")
    out.append("")

    out += ["## ۵. فهرست کامل فایل‌ها", "", "| ناحیه | مسیر | خطوط | اندازه (بایت) | بازبینی |", "|---|---|---|---|---|"]
    for area in sorted(by_area):
        for rel, lines, size in sorted(by_area[area]):
            shown = "—" if lines is None else str(lines)
            out.append(f"| {area} | `{rel}` | {shown} | {size} | NOT-REVIEWED |")
    out.append("")
    return "\n".join(out)


def main() -> int:
    check = "--check" in sys.argv
    data = json.loads((AUDIT / "findings.json").read_text(encoding="utf-8"))
    status_path = AUDIT / "status.json"
    status = json.loads(status_path.read_text(encoding="utf-8")) if status_path.exists() else {}
    files = tracked_files()
    outputs = {
        AUDIT / "CHECKLIST.md": build_checklist(data, status),
        AUDIT / "INVENTORY.md": build_inventory(files),
    }
    if check:
        stale = [p.name for p, text in outputs.items() if not p.exists() or p.read_text(encoding="utf-8") != text]
        if stale:
            print("کهنه:", ", ".join(stale))
            return 1
        print("فهرست‌ها هم‌خوان‌اند")
        return 0
    AUDIT.mkdir(parents=True, exist_ok=True)
    for path, text in outputs.items():
        path.write_text(text, encoding="utf-8")
        print(f"نوشته شد: {path.relative_to(ROOT)} ({text.count(chr(10))} خط)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
