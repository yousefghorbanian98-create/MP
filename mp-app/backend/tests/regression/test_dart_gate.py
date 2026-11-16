"""M60/R16 — تست خودِ گیت Dart (بدون Flutter SDK).

گیت‌های ایستا دو حالت شکست دارند و هر دو بی‌صدا هستند:
  ۱) همیشه سبز شوند (قانون اشتباه، مثبت کاذب صفر ولی یافته هم صفر)
  ۲) روی درختِ سالم قرمز شوند (مثبت کاذب) و بعد کسی خاموشش کند

این تست هر دو را می‌بندد: قانون را روی نمونهٔ «بد» و «خوب» می‌سنجد، و بعد
روی **درخت واقعی** اجرا می‌کند تا مطمئن شویم صفر یافته یعنی واقعاً صفر.

اگر `tree-sitter-dart` نصب نباشد، کل ماژول skip می‌شود — CI بک‌اند نباید به
یک وابستگی اختیاری گره بخورد.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

CLIENT = Path(__file__).resolve().parents[3] / "client"
GATE = CLIENT / "tools" / "dart_gate.py"

pytest.importorskip("tree_sitter", reason="tree-sitter نصب نیست")
pytest.importorskip("tree_sitter_dart", reason="tree-sitter-dart نصب نیست")


def _load():
    spec = importlib.util.spec_from_file_location("dart_gate", GATE)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["dart_gate"] = mod
    spec.loader.exec_module(mod)
    return mod


gate = _load()


def test_flags_body_cast_of_api_response():
    """الگوی دقیقِ باگ M59 باید گرفته شود."""
    lines = [
        "void f() async {",
        "  final r = await api.get('/classes');",
        "  final x = (r as Map)['a'];",
        "}",
    ]
    found = gate._api_body_cast_findings("lib/x.dart", lines)
    assert [f.rule for f in found] == ["api-body-cast"]


def test_accepts_map_from_pattern():
    lines = [
        "void f() async {",
        "  final r = await api.get('/x');",
        "  final m = Map<String, dynamic>.from(r as Map);",
        "}",
    ]
    assert gate._api_body_cast_findings("lib/x.dart", lines) == []


def test_does_not_flag_casts_on_list_items():
    """مثبت کاذبِ نسخهٔ اول: cast روی آیتم‌های لیست بی‌خطر است."""
    lines = [
        "  final w = w0['exercises'];",
        "  final item = list[i] as Map<String, dynamic>;",
    ]
    assert gate._api_body_cast_findings("lib/x.dart", lines) == []


def test_detects_syntax_error():
    parser = gate._parser()
    tmp = CLIENT / "lib" / "_gate_probe.dart"
    tmp.write_text("class A { void f() { if ( } }\n")
    try:
        found = gate.syntax_errors(parser, tmp)
        assert found and found[0].rule == "syntax"
    finally:
        tmp.unlink()


def test_flags_public_http():
    tmp = CLIENT / "lib" / "_gate_probe2.dart"
    tmp.write_text("final u = 'http://api.example.com/v1';\n")
    try:
        found = gate.text_rules(tmp)
        assert any(f.rule == "insecure-http" for f in found)
    finally:
        tmp.unlink()


def test_repo_is_clean():
    """کنترل مثبت: درخت واقعی باید صفر یافته بدهد."""
    parser = gate._parser()
    files = sorted((CLIENT / "lib").rglob("*.dart")) + sorted((CLIENT / "test").rglob("*.dart"))
    assert len(files) > 25, f"فایل Dart کم پیدا شد: {len(files)}"
    findings = []
    for f in files:
        findings += gate.syntax_errors(parser, f)
        findings += gate.text_rules(f)
    assert findings == [], "\n".join(x.render() for x in findings)
