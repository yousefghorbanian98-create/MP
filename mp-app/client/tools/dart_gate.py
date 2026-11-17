#!/usr/bin/env python3
"""M60 / R16 — گیتِ ایستای Dart بدون Flutter SDK.

# چرا این فایل وجود دارد (و چرا «blocked» نبود)

تودوی R16 «صف آفلاین Dart» و بازبینی کلاینت فلاتر در ذهن من به «Flutter SDK
لازم است» گره خورده بود. آن گره **نادرست** بود: برای تحلیل ایستا نه `flutter`
لازم است، نه `dart`, نه `dl.google.com`. تنها چیزی که لازم است یک **grammar**
است — و `tree-sitter-dart` هم روی npm و هم روی PyPI نصب می‌شود (چک‌شده).

پس این گیت همان چیزی را می‌دهد که `flutter analyze` برای این کلاس خطاها
می‌دهد، بدون ابزار گوگل:

  ۱) **خطای نحوی** — هر `ERROR`/missing node در درخت نحو. این همان کلاسی است
     که یک‌بار `Expanded` زیر `Padding` را به‌عنوان «کد سالم» رد کرد و CI کلاینت
     را سه بار قرمز کرد. (توجه: `Expanded` زیر `Padding` خطای *نحوی* نیست،
     خطای runtime از جنس ParentDataWidget است — آن را تست ویجت می‌گیرد؛ این
     گیت نحو را می‌گیرد.)
  ۲) **HTTP ناامن** — هر `http://` که میزبانش loopback یا RFC1918 نباشد.
     قرارداد پروژه (`network_security_config.xml` + `ApiClient._validated`)
     فقط LAN را مجاز می‌کند؛ یک آدرس عمومی باید در بازبینی گیر کند.
  ۳) **`as Map` بدون `Map.from`** — ریشهٔ باگ واقعی M59 که سه صفحه را
     بی‌صدا خراب کرده بود (`_decode` بدنهٔ آرایه‌ای را Map می‌کرد). این گیت
     موارد جدید را علامت می‌زند تا همان الگو برنگردد.

# اجرا

    python3 -m venv /tmp/dartlint
    /tmp/dartlint/bin/pip install tree-sitter tree-sitter-dart
    /tmp/dartlint/bin/python mp-app/client/tools/dart_gate.py

کد خروج ۰ = پاک، ۱ = یافته. در CI اختیاری است (وابستگی PyPI اضافه نمی‌خواهد
به جاب فلاتر تحمیل شود).
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # mp-app/client

# میزبان‌هایی که HTTP بدون TLS برایشان مجاز است (هم‌راستا با
# network_security_config.xml و ApiClient.isPrivateHost).
_PRIVATE_HOST = re.compile(
    r"^(localhost|127\.0\.0\.1|10\.\d+\.\d+\.\d+|10\.0\.2\.2|192\.168\.\d+\.\d+"
    r"|172\.(1[6-9]|2\d|3[01])\.\d+\.\d+)$"
)
_HTTP_URL = re.compile(r"http://([A-Za-z0-9_.:\-\[\]]+)")

# ── قانون «cast بدنهٔ API» (نسخهٔ دقیق) ──
#
# نسخهٔ اول این قانون هر `as Map<String, dynamic>` را علامت می‌زد و ۱۵ یافته
# داد — همه مثبت کاذب: آن‌ها روی آیتم‌های یک List که _decode از قبل به Map
# تبدیل کرده بود cast می‌کردند (`list[i] as Map<...>`، `w as Map<...>`).
# آن‌ها هرگز کرش نمی‌کنند.
#
# خطای واقعی M59 این بود: **کل پاسخ** (که ممکن است List باشد) به Map cast شود.
# پس الگو دو بخشی شد و فقط روی همان تمرکز می‌کند:
#   variable = await <api>.get(...)      ← منبع، نوع dynamic
#   ... variable as Map<...> ...          ← cast مستقیم روی همان variable
# `Map<String, dynamic>.from(x as Map)` امن است و علامت نمی‌خورد.
_AWAIT_API = re.compile(
    r"\b(\w+)\s*=\s*(?:await\s+)?(?:_?api|ApiClient|client)\s*\.\s*(get|post|put|patch|delete)\s*\("
)
_MAP_CAST = re.compile(r"\bas Map(?:<[^>]*>)?")

# استثناهای مستند — هر کدام باید دلیل داشته باشد، نه سکوت.
ALLOWED_HTTP = {
    "schemas.android.com",  # namespace XML، نه درخواست شبکه
    "www.w3.org",
}

# استثناهای مستند برای قانون `api-body-cast` — هر ورودی **باید** دلیل داشته باشد.
# بدون این فهرست، گیت یا باید خاموش شود یا باید مثبت کاذب تحمل کند؛ هیچ‌کدام خوب نیست.
# استثنا برای همان قانون insecure-http: تستِ سیاست شبکه **باید** یک آدرس
# عمومی داشته باشد تا ثابت کند رد می‌شود. آدرس عمومی در تست، نقض سیاست نیست.
ALLOWED_HTTP_LINES: dict[tuple[str, int], str] = {
    ("test/api_client_test.dart", 91): "تست منفی سیاست شبکه — این آدرس باید رد شود",
}

ALLOWED_CASTS: dict[tuple[str, int], str] = {
    ("test/api_client_test.dart", 23): (
        "تست، شکل پاسخ /members/me را تأیید می‌کند؛ mock همیشه Map برمی‌گرداند "
        "و همین ادعا موضوع تست است"
    ),
}


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    rule: str
    detail: str

    def render(self) -> str:
        return f"{self.path}:{self.line}  [{self.rule}] {self.detail}"


def _parser():
    import tree_sitter
    import tree_sitter_dart

    return tree_sitter.Parser(tree_sitter.Language(tree_sitter_dart.language()))


def syntax_errors(parser, path: Path) -> list[Finding]:
    src = path.read_bytes()
    tree = parser.parse(src)
    out: list[Finding] = []

    def walk(node):
        if node.type == "ERROR" or node.is_missing:
            snippet = src[node.start_byte : node.end_byte][:60].decode("utf-8", "replace")
            out.append(
                Finding(
                    _rel(path),
                    node.start_point[0] + 1,
                    "syntax",
                    f"{node.type}: {snippet!r}",
                )
            )
        for child in node.children:
            walk(child)

    walk(tree.root_node)
    return out


def _api_body_cast_findings(rel: str, lines: list[str]) -> list[Finding]:
    """متغیرهایی که مستقیم از `api.get/post(...)` می‌آیند و بعد `as Map` می‌شوند."""
    out: list[Finding] = []
    sources: dict[str, int] = {}
    for i, line in enumerate(lines, start=1):
        stripped = _strip_comment(line)
        for m in _AWAIT_API.finditer(stripped):
            sources[m.group(1)] = i
    for i, line in enumerate(lines, start=1):
        stripped = _strip_comment(line)
        for var, src_line in sources.items():
            # cast مستقیم روی همان متغیر، و نه داخل Map.from(...)
            for m in _MAP_CAST.finditer(stripped):
                before = stripped[: m.start()]
                if not re.search(rf"\b{re.escape(var)}\s*$", before):
                    continue
                if ".from(" in before[-40:] or "Map<" in before[-40:]:
                    continue
                if (rel, i) in ALLOWED_CASTS:
                    continue
                out.append(
                    Finding(
                        rel,
                        i,
                        "api-body-cast",
                        f"`{var}` مستقیماً از پاسخ API (خط {src_line}) می‌آید و به Map cast "
                        "می‌شود؛ پاسخ می‌تواند List باشد (باگ M59). از "
                        f"`Map<String, dynamic>.from({var} as Map)` استفاده کنید.",
                    )
                )
    return out


def _strip_comment(line: str) -> str:
    return re.sub(r"(?<!:)//.*$", "", line)


def _rel(path: Path) -> str:
    """مسیر نسبی برای گزارش — با مسیر مطلق هم باید کار کند (تست‌ها)."""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


# الگوی خطای واقعی CI (اجرای 43836603926):
#   `_fmtRial((p['amount_rial'] as num?) ?? 0)`  → num به int نمی‌خورد.
# این نوع خطا را بدون Dart SDK می‌شود گرفت، چون شکلش همیشه یکی است: یک
# عبارت `as num` که مستقیم به تابعی با پارامتر int داده می‌شود (بدون toInt).
_NUM_CAST = re.compile(r"as\s+num\??")
_CALL_WITH_NUM = re.compile(r"\b(_?[A-Za-z_][A-Za-z0-9_]*)\s*\(([^()]*(?:\([^()]*\)[^()]*)*)\)")


def _num_to_int_findings(rel: str, lines: list[str]) -> list[Finding]:
    """`as num` که به تابع int-پذیر پاس می‌شود بدون `.toInt()`.

    فقط توابعی بررسی می‌شوند که تعریف‌شان در همین فایل پارامتر `int` دارد
    (`fn(int n)` / `fn(String s, int n)`) — تا مثبت کاذب تولید نشود.
    """
    source = "\n".join(lines)
    int_params: set[str] = set()
    for m in re.finditer(
        r"\b(?:String|void|int|double|bool|Widget|num|dynamic)?\s*"
        r"(_?[A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]*)\)\s*(?:async\s*)?\{",
        source,
    ):
        params = m.group(2)
        if re.search(r"\bint\b", params):
            int_params.add(m.group(1))
    if not int_params:
        return []

    out: list[Finding] = []
    for i, raw in enumerate(lines, start=1):
        line = _strip_comment(raw)
        if not _NUM_CAST.search(line):
            continue
        if ".toInt()" in line:
            continue
        for call in _CALL_WITH_NUM.finditer(line):
            if call.group(1) not in int_params:
                continue
            if not _NUM_CAST.search(call.group(2)):
                continue
            out.append(
                Finding(
                    rel,
                    i,
                    "num-to-int",
                    f"`{call.group(1)}` پارامتر int می‌خواهد ولی مقدار `num` می‌گیرد "
                    "— `.toInt()` لازم است (خطای واقعی CI: argument_type_not_assignable)",
                )
            )
            break
    return out


def text_rules(path: Path) -> list[Finding]:
    rel = _rel(path)
    out: list[Finding] = []
    all_lines = path.read_text(encoding="utf-8").splitlines()
    out += _api_body_cast_findings(rel, all_lines)
    out += _num_to_int_findings(rel, all_lines)
    in_block_comment = False
    for i, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw
        stripped = line.strip()
        # رد کردن کامنت‌ها: گیت نباید مستندات را جریمه کند
        if in_block_comment:
            if "*/" in stripped:
                in_block_comment = False
            continue
        if stripped.startswith("/*"):
            in_block_comment = "*/" not in stripped
            continue
        if stripped.startswith("//"):
            continue
        # نکته: `//` داخل «http://» هم شبیه کامنت است. نسخهٔ اول همین‌جا
        # آدرس را می‌بلعید و قانون insecure-http هرگز شلیک نمی‌کرد (تست گرفت).
        line = re.sub(r"(?<!:)//.*$", "", line)

        for m in _HTTP_URL.finditer(line):
            host = m.group(1).split("/")[0].split(":")[0]
            if host in ALLOWED_HTTP or _PRIVATE_HOST.match(host):
                continue
            if (rel, i) in ALLOWED_HTTP_LINES:
                continue
            out.append(
                Finding(rel, i, "insecure-http", f"http://{host} — خارج از LAN؛ HTTPS لازم است")
            )
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="گیت ایستای Dart — بدون Flutter SDK")
    ap.add_argument("--dir", default=str(ROOT / "lib"))
    ap.add_argument("--include-tests", action="store_true", help="test/ را هم بررسی کن")
    args = ap.parse_args()

    parser = _parser()
    files = sorted(Path(args.dir).rglob("*.dart"))
    if args.include_tests:
        files += sorted((ROOT / "test").rglob("*.dart"))

    findings: list[Finding] = []
    for f in files:
        findings += syntax_errors(parser, f)
        findings += text_rules(f)

    for f in findings:
        print(f.render())
    print(f"\n{len(files)} فایل Dart · {len(findings)} یافته")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
