#!/usr/bin/env python3
"""نقشهٔ سطح تعامل استودیو و کلاینت (فاز ۱ نقشه): سطح ← endpoint ← تست.

چرا این اسکریپت: بند «Inspect» میکرو‌لوپ می‌گوید هر دکمه باید API و تست داشته
باشد و هر گپ باید ثبت شود. تا امروز این بررسی دستی و پرت بود. این ابزار همان
جدول را از منابع واقعی می‌سازد، نه از حافظه:

1. `mp-app/studio/src/lib/api.ts` و `adminApi.ts` — کدام تابع چه مسیری را می‌زند.
2. `mp-app/client/lib/**` — هر جا `api.get|post|put|delete('...')` صدا زده شده.
3. `mp-app/backend/api/routes.json` — مسیر واقعی، متد، guard و نقش‌های مجاز.
4. تست‌های `mp-app/studio/tests/*.test.*` و `mp-app/client/test/**`.

گیت (`--check`) دو چیز را قفل می‌کند:

- **رانش قرارداد:** endpointای که کلاینت صدایش می‌زند و در `routes.json` نیست.
- **سطح بی‌تست تازه:** هر صفحه/ویژگی که در خط مبنا نبوده و تست ندارد.

خط مبنا با `--write-baseline` نوشته می‌شود. عدد فقط می‌تواند کم شود.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUDIO = ROOT / "mp-app/studio"
CLIENT = ROOT / "mp-app/client"
API_MODULES = (STUDIO / "src/lib/api.ts", STUDIO / "src/lib/adminApi.ts")
PAGES_DIR = STUDIO / "src/pages"
COMPONENTS_DIR = STUDIO / "src/components"
TESTS_DIR = STUDIO / "tests"
ROUTES = ROOT / "mp-app/backend/api/routes.json"
DOC = ROOT / "docs/MuscleParadise/architecture/interaction-map-2026-11-19.md"
ARTIFACT = ROOT / "docs/MuscleParadise/architecture/interaction-map.json"
BASELINE = ROOT / "docs/MuscleParadise/architecture/interaction-baseline.json"

FUNCTION = re.compile(r"^(?:export\s+)?(?:async\s+)?function\s+(\w+)", re.MULTILINE)
PARAM = re.compile(r"\$\{[^}]+\}")
ROUTE_PARAM = re.compile(r"\{[^}]+\}")
QUERY_ASSIGN = re.compile(r"const\s+(\w+)\s*(?::[^=]+)?=\s*[^;\n]*\?[^;\n]*")

CALL_PATTERNS = (
    (re.compile(r"getJson<[^>]*>\(\s*[`\"]([^`\"]+)[`\"]"), "GET"),
    (re.compile(r"postJson<[^>]*>\(\s*[`\"]([^`\"]+)[`\"]"), "POST"),
)
FETCH_CALL = re.compile(r"sessionFetch\(\s*`\$\{API_BASE\}([^`]+)`")
BASE_CALL = re.compile(r"sessionFetch\(\s*`\$\{base\}([^`]+)`")
METHOD = re.compile(r"method:\s*[\"'](GET|POST|PUT|PATCH|DELETE)[\"']")
DART_CALL = re.compile(r"api\.(get|post|put|delete)\(\s*'([^']+)'")


def normalise(template: str) -> str:
    """مسیر را برای مقایسه یکدست می‌کند: پارامتر ← `*`، query حذف."""
    path = template.split("?")[0].strip()
    path = PARAM.sub("*", path)
    path = ROUTE_PARAM.sub("*", path)
    if path.startswith("${base}"):
        path = path[len("${base}") :]
    if not path.startswith("/"):
        path = "/" + path
    return path


def endpoint(path: str) -> str:
    """مسیر نسبی کلاینت به مسیر کامل API تبدیل می‌شود."""
    if path.startswith("/api/"):
        return normalise(path)
    return normalise("/api/v1" + path)


def api_functions() -> dict[str, dict[str, str]]:
    """تابع‌های کلاینت استودیو ← متد و مسیر."""
    found: dict[str, dict[str, str]] = {}
    for module in API_MODULES:
        text = module.read_text(encoding="utf-8")
        starts = [(m.start(), m.group(1)) for m in FUNCTION.finditer(text)]
        for index, (start, name) in enumerate(starts):
            end = starts[index + 1][0] if index + 1 < len(starts) else len(text)
            body = text[start:end]
            # متغیرهای query را از قالب جدا کن: `${q}` کوئری است، نه پارامتر مسیر.
            query_vars = set(QUERY_ASSIGN.findall(body))
            hit = None
            for pattern, method in CALL_PATTERNS:
                match = pattern.search(body)
                if match:
                    hit = (method, match.group(1))
                    break
            if hit is None:
                fetch = FETCH_CALL.search(body) or BASE_CALL.search(body)
                if fetch:
                    method_match = METHOD.search(body)
                    hit = (method_match.group(1) if method_match else "GET", fetch.group(1))
            if hit:
                template = hit[1]
                for name_ in query_vars:
                    template = template.replace("${" + name_ + "}", "")
                # کوئری تودرتو (`${qs ? `?${qs}` : ""}`) قالب را نصفه می‌گیرد؛
                # فقط بخش مسیر نگه داشته می‌شود.
                dangling = re.search(r"\$\{[^}]*$", template)
                if dangling:
                    template = template[: dangling.start()]
                found[name] = {"method": hit[0], "path": endpoint(template)}
    return found


def routes() -> dict[tuple[str, str], dict]:
    payload = json.loads(ROUTES.read_text(encoding="utf-8"))
    table: dict[tuple[str, str], dict] = {}
    for operation in payload["operations"]:
        table[(operation["method"].upper(), normalise(operation["path"]))] = operation
    return table


def controls_of(text: str) -> dict[str, int]:
    return {
        "buttons": len(re.findall(r"<button\b", text)),
        "inputs": len(re.findall(r"<Input\b", text)),
        "numbers": len(re.findall(r"<InputNumber\b", text)),
        "selects": len(re.findall(r"<Select\b", text)),
        "modals": len(re.findall(r"<Modal\b", text)),
    }


def merge_controls(base: dict[str, int], extra: dict[str, int]) -> dict[str, int]:
    return {key: base.get(key, 0) + extra.get(key, 0) for key in base}


def studio_endpoints(text: str, functions: dict[str, dict[str, str]]) -> list[dict]:
    used: dict[tuple[str, str], dict] = {}
    for name, target in functions.items():
        if re.search(rf"\b{re.escape(name)}\b", text):
            used[(target["method"], target["path"])] = {"function": name, **target}
    return sorted(used.values(), key=lambda item: (item["path"], item["method"]))


def studio_tests(page: str) -> list[str]:
    hits = []
    for path in sorted(TESTS_DIR.glob("*.test.*")):
        text = path.read_text(encoding="utf-8")
        if re.search(rf"pages/{re.escape(page)}\b", text):
            hits.append(str(path.relative_to(ROOT)))
    return hits


def component_files(text: str) -> list[Path]:
    names = set(re.findall(r"from\s+\"\.\./components/(\w+)\"", text))
    return [COMPONENTS_DIR / f"{name}.tsx" for name in sorted(names) if (COMPONENTS_DIR / f"{name}.tsx").is_file()]


def build_studio(functions: dict[str, dict[str, str]], route_table: dict) -> list[dict]:
    pages = []
    for page_file in sorted(PAGES_DIR.glob("*.tsx")):
        text = page_file.read_text(encoding="utf-8")
        components = component_files(text)
        full_text = text + "\n" + "\n".join(path.read_text(encoding="utf-8") for path in components)
        controls = controls_of(text)
        for component in components:
            controls = merge_controls(controls, controls_of(component.read_text(encoding="utf-8")))
        rows = []
        for item in studio_endpoints(full_text, functions):
            operation = route_table.get((item["method"], item["path"]))
            rows.append(
                {
                    "function": item["function"],
                    "method": item["method"],
                    "path": item["path"],
                    "in_contract": operation is not None,
                    "guards": operation["guards"] if operation else [],
                    "roles": operation["roles"] if operation else [],
                }
            )
        pages.append(
            {
                "surface": page_file.stem,
                "kind": "studio-page",
                "file": str(page_file.relative_to(ROOT)),
                "components": [str(path.relative_to(ROOT)) for path in components],
                "controls": controls,
                "endpoints": rows,
                "tests": studio_tests(page_file.stem),
            }
        )
    return pages


def client_surface_tests(name: str) -> list[str]:
    hits = []
    for path in sorted((CLIENT / "test").rglob("*.dart")):
        text = path.read_text(encoding="utf-8")
        if re.search(rf"features/{re.escape(name)}/", text):
            hits.append(str(path.relative_to(ROOT)))
    return hits


def build_client(route_table: dict) -> list[dict]:
    surfaces = []
    features = CLIENT / "lib/features"
    targets = [(feature.name, feature) for feature in sorted(features.iterdir()) if feature.is_dir()]
    targets.append(("core", CLIENT / "lib/core"))
    for name, folder in targets:
        endpoints: dict[tuple[str, str], dict] = {}
        for path in sorted(folder.rglob("*.dart")):
            text = path.read_text(encoding="utf-8")
            controls = None
            for method, template in DART_CALL.findall(text):
                # Dart پارامتر را با `$name` یا `${name}` می‌نویسد، نه `{name}`.
                full = endpoint(re.sub(r"\$\{[^}]+\}|\$\w+", "*", template))
                endpoints[(method.upper(), full)] = {"function": str(path.relative_to(ROOT)), **{}}
        rows = []
        for (method, full) in sorted(endpoints):
            operation = route_table.get((method, full))
            rows.append(
                {
                    "method": method,
                    "path": full,
                    "in_contract": operation is not None,
                    "guards": operation["guards"] if operation else [],
                    "roles": operation["roles"] if operation else [],
                }
            )
        surfaces.append(
            {
                "surface": name,
                "kind": "client-feature",
                "file": str(folder.relative_to(ROOT)),
                "components": [],
                "controls": controls_of(""),
                "endpoints": rows,
                "tests": client_surface_tests(name) if name != "core" else [],
            }
        )
    return surfaces


def build() -> dict:
    functions = api_functions()
    route_table = routes()
    surfaces = build_studio(functions, route_table) + build_client(route_table)
    return {"surfaces": surfaces, "contract_paths": len(route_table)}


PER_CODE_LIMIT = 20

SUGGESTIONS = {
    "MAP-001": "endpoint را به routes.json اضافه کنید، یا فراخوانی کلاینت را به مسیر موجود اصلاح کنید.",
    "MAP-002": "python3 scripts/interaction_map.py را اجرا و نتیجه را commit کنید.",
    "MAP-003": "تست بنویسید، یا خط مبنا را با دلیل در interaction-baseline.json به‌روز کنید.",
}


@dataclass(frozen=True)
class Finding:
    code: str
    path: str
    line: int | None
    message: str
    suggestion: str

    def render(self) -> str:
        # قالب ثابت C2: CODE path:line: پیام ← پیشنهاد (خط ناشناخته = «-»)
        return f"{self.code} {self.path}:{self.line or '-'}: {self.message} ← {self.suggestion}"


def print_capped(findings: list[Finding], stream) -> None:
    """دسته‌بندی کامل بر اساس کد؛ هر دسته حداکثر PER_CODE_LIMIT سطر، بقیه «+N»."""
    counts: dict[str, int] = {}
    for item in findings:
        counts[item.code] = counts.get(item.code, 0) + 1
        if counts[item.code] <= PER_CODE_LIMIT:
            print(item.render(), file=stream)
    for code, total in counts.items():
        if total > PER_CODE_LIMIT:
            print(f"+{total - PER_CODE_LIMIT} موردِ دیگر ({code})", file=stream)


def _rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def check_findings(report: dict, untested: list[str]) -> list[Finding]:
    """همان سه شرط گیت `--check`، با کد و مسیر. پیام‌ها همان متن قبلی‌اند."""
    findings: list[Finding] = []
    for surface in report["surfaces"]:
        for row in surface["endpoints"]:
            if not row["in_contract"]:
                message = f"{surface['surface']} ({surface['kind']}): {row['method']} {row['path']} در routes.json نیست"
                findings.append(Finding("MAP-001", surface["file"], None, message, SUGGESTIONS["MAP-001"]))
    # نقشهٔ کهنه = مستند دروغ. اگر خروجی امروز با فایل روی دیسک یکی نباشد،
    # یعنی کد عوض شده و کسی نقشه را بازتولید نکرده است.
    fresh = render_markdown(report, *gaps(report))
    if DOC.exists() and DOC.read_text(encoding="utf-8") != fresh:
        findings.append(
            Finding(
                "MAP-002",
                _rel(DOC),
                None,
                "نقشهٔ سطح تعامل کهنه است — python3 scripts/interaction_map.py را اجرا و commit کن",
                SUGGESTIONS["MAP-002"],
            )
        )
    baseline = json.loads(BASELINE.read_text(encoding="utf-8")) if BASELINE.exists() else {}
    allowed = set(baseline.get("untested_surfaces", untested))
    file_of = {f"{surface['kind']}:{surface['surface']}": surface["file"] for surface in report["surfaces"]}
    for surface in untested:
        if surface not in allowed:
            findings.append(
                Finding(
                    "MAP-003",
                    file_of.get(surface, "-"),
                    None,
                    f"سطح تازهٔ بی‌تست: {surface} — یا تست بنویس یا خط مبنا را با دلیل به‌روز کن",
                    SUGGESTIONS["MAP-003"],
                )
            )
    return sorted(set(findings), key=lambda f: (f.code, f.path, f.message))


def gaps(report: dict) -> tuple[list[str], list[str]]:
    drift = [
        f"{surface['surface']} ({surface['kind']}): {row['method']} {row['path']} در routes.json نیست"
        for surface in report["surfaces"]
        for row in surface["endpoints"]
        if not row["in_contract"]
    ]
    untested = [
        f"{surface['kind']}:{surface['surface']}"
        for surface in report["surfaces"]
        if not surface["tests"] and surface["endpoints"]
    ]
    return sorted(set(drift)), sorted(untested)


def render_markdown(report: dict, drift: list[str], untested: list[str]) -> str:
    studio = [s for s in report["surfaces"] if s["kind"] == "studio-page"]
    client = [s for s in report["surfaces"] if s["kind"] == "client-feature"]
    endpoints = {f"{row['method']} {row['path']}" for s in report["surfaces"] for row in s["endpoints"]}
    lines = [
        "# نقشهٔ سطح تعامل (فاز ۱ نقشه)",
        "",
        "این صفحه از منابع واقعی ساخته می‌شود و با دست نوشته نشده است:",
        "",
        "- `mp-app/studio/src/lib/api.ts` و `mp-app/studio/src/lib/adminApi.ts`",
        "- `mp-app/client/lib/**` (فراخوانی `api.get|post|put|delete`)",
        "- `mp-app/backend/api/routes.json`",
        "- `mp-app/studio/tests/*.test.*` و `mp-app/client/test/**`",
        "",
        "بازتولید و گیت:",
        "",
        "```bash",
        "python3 scripts/interaction_map.py",
        "python3 scripts/interaction_map.py --check",
        "```",
        "",
        "| سنجه | مقدار |",
        "|---|---|",
        f"| مسیر قرارداد API | {report['contract_paths']} |",
        f"| صفحهٔ استودیو | {len(studio)} |",
        f"| ویژگی کلاینت | {len(client)} |",
        f"| endpoint یکتای استفاده‌شده | {len(endpoints)} |",
        f"| سطح بی‌تست | {len(untested)} |",
        "",
        "## گپ‌های قرارداد",
        "",
    ]
    lines += [f"- {item}" for item in drift] if drift else ["- هیچ: هر endpointی که کلاینت صدا می‌زند در قرارداد هست."]
    lines += ["", "## سطح‌های بی‌تست", ""]
    lines += [f"- {item}" for item in untested] if untested else ["- هیچ."]
    lines += ["", "## استودیو", ""]
    for surface in studio:
        controls = surface["controls"]
        lines += [
            f"### {surface['surface']}",
            "",
            f"دکمه {controls['buttons']} · ورودی {controls['inputs']} · عدد {controls['numbers']} "
            f"· انتخاب {controls['selects']} · دیالوگ {controls['modals']}",
            "",
        ]
        if surface["endpoints"]:
            lines += ["| متد | مسیر | guard | نقش‌ها | در قرارداد |", "|---|---|---|---|---|"]
            for row in surface["endpoints"]:
                roles = ", ".join(row["roles"]) or "—"
                guards = ", ".join(row["guards"]) or "—"
                mark = "بله" if row["in_contract"] else "**نه**"
                lines.append(f"| {row['method']} | `{row['path']}` | {guards} | {roles} | {mark} |")
        else:
            lines.append("بدون فراخوانی API در این صفحه و کامپوننت‌هایش.")
        lines.append("")
        lines.append("تست: " + ("، ".join(f"`{path}`" for path in surface["tests"]) if surface["tests"] else "**ندارد**"))
        lines.append("")
    lines += ["## کلاینت", "", "| ویژگی | endpoint | guard | نقش‌ها | در قرارداد | تست |", "|---|---|---|---|---|---|"]
    for surface in client:
        if not surface["endpoints"]:
            lines.append(f"| {surface['surface']} | — | — | — | — | {'دارد' if surface['tests'] else '**ندارد**'} |")
            continue
        for row in surface["endpoints"]:
            roles = ", ".join(row["roles"]) or "—"
            guards = ", ".join(row["guards"]) or "—"
            mark = "بله" if row["in_contract"] else "**نه**"
            test_mark = f"{len(surface['tests'])} فایل" if surface["tests"] else "**ندارد**"
            lines.append(f"| {surface['surface']} | `{row['method']} {row['path']}` | {guards} | {roles} | {mark} | {test_mark} |")
    role_rows: dict[str, list[str]] = {}
    for surface in report["surfaces"]:
        for row in surface["endpoints"]:
            for role in row["roles"]:
                role_rows.setdefault(role, [])
                entry = f"{surface['surface']} · {row['method']} {row['path']}"
                if entry not in role_rows[role]:
                    role_rows[role].append(entry)
    lines += ["", "## پوشش نقش‌ها", "", "| نقش | تعداد endpoint | نمونهٔ سطح‌ها |", "|---|---|---|"]
    for role in sorted(role_rows):
        samples = "، ".join(sorted({item.split(" · ")[0] for item in role_rows[role]})[:6])
        lines.append(f"| {role} | {len(role_rows[role])} | {samples} |")
    lines += [
        "",
        "## محدودیت صریح",
        "",
        "- نقش‌ها از `routes.json` می‌آید، نه از خواندن UI؛ پس «چه کسی دکمه را می‌بیند» هنوز دستی مرور می‌شود.",
        "- جدول DB از این نقشه بیرون است: مسیر ← جدول نیاز به ردیابی مدل دارد و ادعای خودکار نمی‌کنیم.",
        "- کامپوننت‌ها فقط یک سطح از صفحه‌ها باز می‌شوند؛ کامپوننت تودرتوی عمیق‌تر ممکن است دیده نشود.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="گیت: رانش قرارداد و سطح بی‌تست تازه")
    parser.add_argument("--write-baseline", action="store_true", help="ثبت خط مبنا")
    parser.add_argument("--json", action="store_true", help="با --check: خروجی JSON تشخیص‌ها")
    args = parser.parse_args(argv)
    if args.json and not args.check:
        parser.error("--json فقط همراه --check معنی دارد")

    report = build()
    drift, untested = gaps(report)

    if args.check:
        findings = check_findings(report, untested)
        passed = (
            f"Interaction map gate passed: {len(report['surfaces'])} سطح، "
            f"{report['contract_paths']} مسیر قرارداد، رانش صفر."
        )
        if args.json:
            print(json.dumps([asdict(item) for item in findings], ensure_ascii=False, indent=2))
            if not findings:
                print(passed, file=sys.stderr)
            return 1 if findings else 0
        if findings:
            print("Interaction map gate FAILED:")
            print_capped(findings, sys.stdout)
            return 1
        print(passed)
        return 0

    if args.write_baseline:
        BASELINE.write_text(
            json.dumps({"untested_surfaces": untested}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"baseline نوشته شد: {len(untested)} سطح بی‌تست")

    DOC.write_text(render_markdown(report, drift, untested), encoding="utf-8")
    ARTIFACT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"نقشه نوشته شد: {DOC.relative_to(ROOT)} · {len(report['surfaces'])} سطح · "
        f"رانش قرارداد {len(drift)} · بی‌تست {len(untested)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
