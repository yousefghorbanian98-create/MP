"""P‑C · کدهای پایدار گیت‌های مستندات و نقشه (DOC-### / MAP-###) و خروجی‌ها.

red-first: این تست‌ها پیش از تغییر scripts/docs_gate.py و scripts/interaction_map.py نوشته شدند.
ROOT = parents[4]: از mp-app/backend/tests/integration به ریشهٔ ریپو (الگو: test_ci_artifacts.py:12).
"""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
PY = sys.executable
GATE_CODES = ROOT / "docs/MuscleParadise/audit/GATE-CODES.md"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    # dataclasses (Python 3.11) ستون sys.modules[__module__] را لازم دارد.
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([PY, *args], cwd=ROOT, capture_output=True, text=True, timeout=120)


@pytest.fixture()
def docs_gate():
    return _load("docs_gate")


@pytest.fixture()
def interaction_map():
    return _load("interaction_map")


BASE = {
    "README.md": "[a](AGENTS.md) [b](docs/README.md) [c](docs/MuscleParadise/SESSION_HANDOFF.md)\n",
    "AGENTS.md": "# agents\n",
    "docs/README.md": "# docs\n",
    "docs/MuscleParadise/SESSION_HANDOFF.md": (
        "## Snapshot فعلی\n\n## نتیجه و شواهد آخرین کار\n\n## اقدام بعدی\n\n"
        "## قالب به‌روزرسانی برای نشست‌های بعد\n"
    ),
}


# resolve_local_target گام‌های لینک را نسبت به cwd حل می‌کند (نه ROOT)؛ CI از ریشهٔ ریپو
# اجرا می‌کند. نمونهٔ آزمایشی باید cwd را به خودش ببرد تا لینک‌ها همان‌جا سنجیده شوند.
def _sandbox(gate, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, docs: dict[str, str]) -> None:
    monkeypatch.chdir(tmp_path)
    for rel, text in docs.items():
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    names = tuple(Path(rel) for rel in docs)
    gate.ROOT = tmp_path
    gate.CORE_MARKDOWN_FILES = names
    gate.MARKDOWN_FILES = names
    gate.REQUIRED_FILES = names
    gate.SVG_FILES = ()


# ---------- گیت مستندات ----------


def test_green_summary_counts_current_markdown_files_and_mermaid_blocks():
    result = _run("scripts/docs_gate.py")
    assert result.returncode == 0, result.stderr
    assert "Documentation gate passed: 20 Markdown files" in result.stdout
    assert "12 Mermaid diagram block(s)" in result.stdout


def test_green_json_is_empty_array():
    result = _run("scripts/docs_gate.py", "--json")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == []


def test_gate_codes_doc_is_in_docs_gate_scope(docs_gate):
    assert Path("docs/MuscleParadise/audit/GATE-CODES.md") in docs_gate.CORE_MARKDOWN_FILES


def test_broken_link_is_doc006_in_json_with_path_line_and_suggestion(
    docs_gate, tmp_path, monkeypatch, capsys
):
    _sandbox(docs_gate, tmp_path, monkeypatch, {**BASE, "bad.md": "# t\n\nx\n\n[y](missing.md)\n"})
    rc = docs_gate.main(["--json"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 1
    assert len(out) == 1
    assert out[0]["code"] == "DOC-006"
    assert out[0]["path"] == "bad.md"
    assert out[0]["line"] == 5
    assert out[0]["message"] == "broken local link: missing.md"
    assert out[0]["suggestion"]


def test_human_line_format_is_code_path_line_message_arrow_suggestion(
    docs_gate, tmp_path, monkeypatch, capsys
):
    _sandbox(docs_gate, tmp_path, monkeypatch, {**BASE, "bad.md": "# t\n\nx\n\n[y](missing.md)\n"})
    rc = docs_gate.main([])
    err = capsys.readouterr().err
    assert rc == 1
    assert re.search(r"^DOC-006 bad\.md:5: broken local link: missing\.md ← .+$", err, re.M), err


def test_per_code_cap_is_20_then_plus_n(docs_gate, tmp_path, monkeypatch, capsys):
    links = "\n".join(f"[x{i}](m{i}.md)" for i in range(25))
    _sandbox(docs_gate, tmp_path, monkeypatch, {**BASE, "bad.md": links + "\n"})
    rc = docs_gate.main([])
    err = capsys.readouterr().err
    assert rc == 1
    assert len(re.findall(r"^DOC-006 ", err, re.M)) == 20, err
    assert "+5 موردِ دیگر (DOC-006)" in err


# ---------- نقشهٔ سطح تعامل ----------


def test_green_check_json_is_empty_array_and_exit_0():
    result = _run("scripts/interaction_map.py", "--check", "--json")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == []


def test_stale_map_is_map002_and_check_never_writes(interaction_map, tmp_path, capsys, monkeypatch):
    stale = tmp_path / "interaction-map.md"
    stale.write_text("stale\n", encoding="utf-8")
    monkeypatch.setattr(interaction_map, "DOC", stale)
    rc = interaction_map.main(["--check"])
    out = capsys.readouterr().out
    assert rc == 1
    assert re.search(r"^MAP-002 .+interaction-map\.md:-: ", out, re.M), out
    assert stale.read_text(encoding="utf-8") == "stale\n"


def test_stale_map_json_carries_map002(interaction_map, tmp_path, capsys, monkeypatch):
    stale = tmp_path / "interaction-map.md"
    stale.write_text("stale\n", encoding="utf-8")
    monkeypatch.setattr(interaction_map, "DOC", stale)
    rc = interaction_map.main(["--check", "--json"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 1
    assert [item["code"] for item in out] == ["MAP-002"]


# ---------- فهرست کدها ----------


def test_gate_codes_doc_lists_every_active_code():
    assert GATE_CODES.is_file(), "GATE-CODES.md missing"
    text = GATE_CODES.read_text(encoding="utf-8")
    codes = (
        [f"DOC-{i:03d}" for i in range(1, 10)]
        + [f"MAP-{i:03d}" for i in range(1, 4)]
        + [f"DRV-{i:03d}" for i in range(1, 6)]
    )
    missing = [code for code in codes if code not in text]
    assert not missing, missing
