#!/usr/bin/env python3
"""Fast, dependency-free checks for the Git-backed AI documentation entrypoints."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def _module_docs() -> tuple[Path, ...]:
    """هر صفحهٔ ماژول زیر `architecture/modules/` هم در گیت لینک شرکت می‌کند.

    دلیل: DX-REP-01 می‌گوید سند هر زیرسیستم باید Git-tracked و قابل‌بازتولید باشد؛
    اگر gate فقط فهرست ثابت را ببیند، یک صفحهٔ تازه با لینک شکسته می‌تواند بی‌صدا
    وارد Git شود. پوشه که نبود، فهرست خالی است و گیت نمی‌شکند.
    """
    folder = ROOT / "docs/MuscleParadise/architecture/modules"
    if not folder.is_dir():
        return ()
    return tuple(
        path.relative_to(ROOT) for path in sorted(folder.glob("*.md"))
    )


CORE_MARKDOWN_FILES = (
    Path("AGENTS.md"),
    Path("README.md"),
    Path("docs/README.md"),
    Path("docs/MuscleParadise/SESSION_HANDOFF.md"),
    Path("docs/MuscleParadise/HANDOFF-PROJECT-2026-11-18.md"),
    Path("docs/MuscleParadise/architecture/README.md"),
    Path("docs/MuscleParadise/architecture/system-atlas.md"),
    Path("docs/MuscleParadise/architecture/cloud-finance-access.md"),
    Path("docs/MuscleParadise/adr/README.md"),
    Path("docs/MuscleParadise/adr/TEMPLATE.md"),
    # M107: دستور کار اجرای بیرون از sandbox هم تحت گیت لینک می‌آید؛ مسیرهای
    # داخلش (devcontainer، runbookها، گزارش‌ها) واقعی‌اند و باید شکستنشان دیده شود.
    Path("docs/MuscleParadise/runbooks/codespaces-execution.md"),
    # M109: صف تصمیم‌های مالک هم زیر گیت لینک می‌آید؛ این صفحه تنها جایی است که
    # «منتظر مالک» به یک متن خواندنی تبدیل می‌شود، پس لینک‌هایش نباید بمیرند.
    Path("docs/MuscleParadise/OWNER-DECISIONS.md"),
    # ۲۰۲۶-۱۱-۱۹: چهار سند تصمیم/نقشه که تا امروز بیرون از گیت بودند. اگر فقط
    # CORE را ببیند، دیاگرام Mermaid و لینک شکسته در همین اسناد دیده نمی‌شود.
    Path("docs/MuscleParadise/UI-CONTROLS-Q11.md"),
    Path("docs/MuscleParadise/AGENT-TOOLING-REVIEWS.md"),
    Path("docs/MuscleParadise/ROADMAP-NEXT-2026-11-19.md"),
    Path("docs/MuscleParadise/ARCHITECTURE-LAYERS-AND-STAGES.md"),
    # ۲۰۲۶-۱۱-۱۹ (فاز ۱): نقشهٔ سطح تعامل از کد ساخته می‌شود؛ همان هم باید
    # فاصلهٔ اضافه و لینک مرده نداشته باشد.
    Path("docs/MuscleParadise/architecture/interaction-map-2026-11-19.md"),
    # P‑C: جدول کدهای گیت (DOC-### / MAP-###) هم باید لینک‌هایش زنده باشند.
    Path("docs/MuscleParadise/audit/GATE-CODES.md"),
    # برنامهٔ کلان محصول تا production/AI autonomy: لینک‌ها و وضعیت‌های آن نیز تحت گیت‌اند.
    Path("docs/MuscleParadise/architecture/ai-autonomous-production-plan-v1-2026-11-23.md"),
    # Crosswalk ایستای reduced-motionِ درخت جاری؛ لینک‌ها و Markdown آن نیز validate شوند.
    Path("docs/MuscleParadise/architecture/studio-motion-current-tree-static-crosswalk-2026-11-23.fa.md"),
    # فهرست قابل‌اجرا در sandbox و بستهٔ انتقال به Codespace؛ همین handoff نیز زیر گیت لینک است.
    Path("docs/MuscleParadise/architecture/motion-pwa-availability-matrix-2026-11-23.fa.md"),
)
MARKDOWN_FILES = (*CORE_MARKDOWN_FILES, *_module_docs())
SVG_FILES = (
    Path("docs/MuscleParadise/assets/knowledge-atlas.svg"),
    Path("docs/MuscleParadise/assets/system-architecture.svg"),
)
REQUIRED_FILES = (*MARKDOWN_FILES, *SVG_FILES)
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
HTML_REFERENCE = re.compile(r"\b(?:href|src)=[\"']([^\"']+)[\"']", re.IGNORECASE)
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
DIAGRAM_START = re.compile(
    r"^(?:flowchart|graph|sequenceDiagram|classDiagram|stateDiagram(?:-v2)?|erDiagram|"
    r"journey|gantt|pie|mindmap|timeline|gitGraph|quadrantChart|xychart(?:-beta)?|"
    r"block-beta|architecture-beta|packet-beta|kanban)\b"
)
REQUIRED_HANDOFF_HEADINGS = (
    "## Snapshot فعلی",
    "## نتیجه و شواهد آخرین کار",
    "## اقدام بعدی",
    "## قالب به‌روزرسانی برای نشست‌های بعد",
)


PER_CODE_LIMIT = 20

SUGGESTIONS = {
    "DOC-001": "فایل را بازگردانید یا فهرست REQUIRED_FILES در scripts/docs_gate.py را اصلاح کنید.",
    "DOC-002": "فاصلهٔ انتهای سطر را حذف کنید.",
    "DOC-003": "بلوک Mermaid خالی است؛ محتوا بنویسید یا بلوک را حذف کنید.",
    "DOC-004": "اولین خط بلوک Mermaid باید اعلان نمودار معتبر باشد (مثلاً flowchart).",
    "DOC-005": "بلوک کد را با همان تعداد علامت ببندید.",
    "DOC-006": "مسیر را اصلاح کنید یا فایل مقصد را بسازید.",
    "DOC-007": "عنوان الزامی SESSION_HANDOFF را اضافه کنید.",
    "DOC-008": "لینک ورودی را در README.md اضافه کنید.",
    "DOC-009": "فایل SVG را با XML معتبر ذخیره کنید.",
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


def finding(code: str, path: str, line: int | None, message: str) -> Finding:
    return Finding(code, path, line, message, SUGGESTIONS[code])


def ordered(findings: list[Finding]) -> list[Finding]:
    return sorted(set(findings), key=lambda f: (f.code, f.path, f.line or 0, f.message))


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


def report(findings: list[Finding], *, as_json: bool, summary: str) -> int:
    items = ordered(findings)
    if as_json:
        # stdout فقط JSON است؛ خلاصهٔ سبز روی stderr.
        print(json.dumps([asdict(item) for item in items], ensure_ascii=False, indent=2))
        if not items:
            print(summary, file=sys.stderr)
        return 1 if items else 0
    if items:
        print("Documentation gate failed:", file=sys.stderr)
        print_capped(items, sys.stderr)
        return 1
    print(summary)
    return 0


def parse_fences(path: Path, text: str, errors: list[Finding]) -> tuple[int, list[str]]:
    open_fence: tuple[str, int, str, int] | None = None
    mermaid_blocks: list[str] = []
    current_body: list[str] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        match = FENCE.match(line)
        if not match:
            if open_fence is not None and open_fence[2] == "mermaid":
                current_body.append(line)
            continue

        marker, info = match.groups()
        language = info.strip().split(maxsplit=1)[0].lower() if info.strip() else ""
        if open_fence is None:
            open_fence = (marker[0], len(marker), language, line_number)
            current_body = []
            continue

        if marker[0] == open_fence[0] and len(marker) >= open_fence[1] and not info.strip():
            _, _, opened_language, opened_at = open_fence
            if opened_language == "mermaid":
                body = "\n".join(current_body).strip()
                if not body:
                    errors.append(finding("DOC-003", path.as_posix(), opened_at, "empty Mermaid block"))
                elif not DIAGRAM_START.match(body.splitlines()[0].strip()):
                    errors.append(finding("DOC-004", path.as_posix(), opened_at, "Mermaid block has no recognized diagram declaration"))
                mermaid_blocks.append(body)
            open_fence = None
            current_body = []

    if open_fence is not None:
        errors.append(finding("DOC-005", path.as_posix(), open_fence[3], "unclosed fenced code block"))
    return len(mermaid_blocks), mermaid_blocks


def local_link_targets(path: Path, text: str) -> list[tuple[str, int]]:
    """Return local Markdown/HTML targets, ignoring fenced code examples."""
    targets: list[tuple[str, int]] = []
    in_fence: tuple[str, int] | None = None
    for line_number, line in enumerate(text.splitlines(), start=1):
        match = FENCE.match(line)
        if match:
            marker, info = match.groups()
            if in_fence is None:
                in_fence = (marker[0], len(marker))
            elif marker[0] == in_fence[0] and len(marker) >= in_fence[1] and not info.strip():
                in_fence = None
            continue
        if in_fence is not None:
            continue
        targets.extend((target.strip(), line_number) for target in MARKDOWN_LINK.findall(line))
        targets.extend((target.strip(), line_number) for target in HTML_REFERENCE.findall(line))
    return targets


def resolve_local_target(source: Path, raw_target: str) -> Path | None:
    target = html.unescape(raw_target.strip().strip("<>"))
    parts = urlsplit(target)
    if parts.scheme or target.startswith("//") or not parts.path:
        return None
    relative = Path(unquote(parts.path))
    return (source.parent / relative).resolve()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="گیت مستندات؛ کدها در docs/MuscleParadise/audit/GATE-CODES.md")
    parser.add_argument("--json", action="store_true", help="خروجی JSON؛ خلاصهٔ سبز روی stderr")
    args = parser.parse_args(argv)

    errors: list[Finding] = []
    missing = [path.as_posix() for path in REQUIRED_FILES if not (ROOT / path).exists()]
    errors.extend(finding("DOC-001", path, None, f"required file missing: {path}") for path in missing)

    checked_links = 0
    total_mermaid = 0
    for relative in MARKDOWN_FILES:
        path = ROOT / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), start=1):
            if line.rstrip() != line:
                errors.append(finding("DOC-002", relative.as_posix(), line_number, "trailing whitespace"))

        mermaid_count, _ = parse_fences(relative, text, errors)
        total_mermaid += mermaid_count
        for raw_target, line_number in local_link_targets(relative, text):
            target = resolve_local_target(relative, raw_target)
            if target is None:
                continue
            checked_links += 1
            if not target.exists():
                errors.append(finding("DOC-006", relative.as_posix(), line_number, f"broken local link: {raw_target}"))

    handoff_path = ROOT / "docs/MuscleParadise/SESSION_HANDOFF.md"
    if handoff_path.is_file():
        handoff = handoff_path.read_text(encoding="utf-8")
        for heading in REQUIRED_HANDOFF_HEADINGS:
            if heading not in handoff:
                errors.append(finding("DOC-007", "docs/MuscleParadise/SESSION_HANDOFF.md", None, f"missing heading: {heading}"))

    readme = (ROOT / "README.md").read_text(encoding="utf-8") if (ROOT / "README.md").is_file() else ""
    for required_target in (
        "AGENTS.md",
        "docs/README.md",
        "docs/MuscleParadise/SESSION_HANDOFF.md",
    ):
        if not re.search(rf"\]\({re.escape(required_target)}(?:#[^)]+)?\)", readme):
            errors.append(finding("DOC-008", "README.md", None, f"missing documentation entry: {required_target}"))

    for relative in SVG_FILES:
        svg_path = ROOT / relative
        if svg_path.is_file():
            try:
                ET.parse(svg_path)
            except ET.ParseError as exc:
                errors.append(finding("DOC-009", relative.as_posix(), None, f"invalid XML: {exc}"))

    summary = (
        "Documentation gate passed: "
        f"{len(MARKDOWN_FILES)} Markdown files, {checked_links} local links, "
        f"{total_mermaid} Mermaid diagram block(s), handoff headings, README entrypoints, SVG XML."
    )
    return report(errors, as_json=args.json, summary=summary)


if __name__ == "__main__":
    raise SystemExit(main())
