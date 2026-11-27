#!/usr/bin/env python3
"""P0 — تست رگرسیون برای «حالت کور» گیت digest در artifact‌های STALE.

## باگی که این تست‌ها می‌بندند

در `verify_crosswalk_digests.py::inspect_stale()` مقایسه به این شکل بود:

    actual = actual_digest(SOURCE_ROOT / relative)   # None اگر فایل نباشد
    expected = recorded_hex(recorded)                # None اگر digest خراب باشد
    f"...{'' if actual == expected else '  ← کهنه'}"

اگر **هم** منبع از checkout حذف شده باشد و **هم** digest ثبت‌شده خراب باشد،
`None == None` می‌شود و هیچ `← کهنه`/خطایی چاپ نمی‌شد؛ artifact «سالم» گزارش می‌شد.
یعنی با `git rm` یک منبع، گیت بی‌صدا خاموش می‌شد — همان دسته خطایی که گیت برای
گرفتنش ساخته شد. مسیر غیر-STALE این باگ را نداشت (`check()` هر دو حالت را
`problems` می‌کرد)؛ فقط STALE این‌طور بود.

## سه حالتی که اینجا قفل می‌شوند

1. STALE + فایل موجود + digest کهنه → **گزارش** «← کهنه»، `EXIT=0` (طبق قاعده:
   STALE داوری نمی‌شود، فقط گزارش می‌شود).
2. STALE + فایل غایب → **`EXIT=1`**.
3. STALE + digest خراب → **`EXIT=1`**.

اجرا: `python3 scripts/tests/test_digest_gate.py` (بدون نیاز به pytest)
یا `pytest scripts/tests/test_digest_gate.py`.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "verify_crosswalk_digests.py"


def load_gate():
    spec = importlib.util.spec_from_file_location("verify_crosswalk_digests", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_artifact(root: Path, digest: str, *, source: str = "studio/src/lib/x.ts",
                    source_body: str = "export const x = 1;\n") -> Path:
    """یک ریشهٔ موقت با یک منبع و یک artifact STALE می‌سازد."""
    (root / "mp-app" / "studio" / "src" / "lib").mkdir(parents=True, exist_ok=True)
    (root / "mp-app" / source).write_text(source_body, encoding="utf-8")

    artifact_dir = root / "evidence" / "2026-01-01" / "INV-99-v0"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact = artifact_dir / "x-crosswalk.STALE.json"
    artifact.write_text(
        json.dumps(
            {
                "meta": {
                    "sha": "0" * 40,
                    "tracked_dirty": False,
                    "sources": {source: digest},
                },
                "rows": [],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return artifact


def _point_gate_at(gate, root: Path) -> None:
    gate.ROOT = root
    gate.EVIDENCE = root / "evidence"
    gate.SOURCE_ROOT = root / "mp-app"


def _run_main(gate) -> tuple[int, str, str]:
    import contextlib
    import io

    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = gate.main()
    return code, out.getvalue(), err.getvalue()


def test_stale_artifact_with_stale_digest_is_reported_but_still_passes(tmp_path) -> None:
    gate = load_gate()
    # digest معتبر ولی مربوط به محتوای دیگر ⇒ «کهنه»، نه خطا.
    other = hashlib.sha256(b"different content").hexdigest()
    artifact = _write_artifact(tmp_path, other)
    _point_gate_at(gate, tmp_path)

    problems, report, _dirty = gate.inspect_stale(artifact)
    assert problems == [], problems
    assert any("← کهنه" in line for line in report), report

    code, _out, _err = _run_main(gate)
    assert code == 0


def test_stale_artifact_with_missing_source_fails(tmp_path) -> None:
    gate = load_gate()
    good = hashlib.sha256(b"export const x = 1;\n").hexdigest()
    artifact = _write_artifact(tmp_path, good)
    # منبع را حذف می‌کنیم؛ digest ثبت‌شده هنوز معتبر است.
    (tmp_path / "mp-app" / "studio" / "src" / "lib" / "x.ts").unlink()
    _point_gate_at(gate, tmp_path)

    problems, _report, _dirty = gate.inspect_stale(artifact)
    assert any("در checkout نیست" in problem for problem in problems), problems

    code, _out, err = _run_main(gate)
    assert code == 1, err


def test_stale_artifact_with_corrupt_digest_fails(tmp_path) -> None:
    gate = load_gate()
    artifact = _write_artifact(tmp_path, "garbage-not-a-digest")
    _point_gate_at(gate, tmp_path)

    problems, _report, _dirty = gate.inspect_stale(artifact)
    assert any("digest نامعتبر" in problem for problem in problems), problems

    code, _out, err = _run_main(gate)
    assert code == 1, err


def test_both_broken_at_once_is_still_an_error(tmp_path) -> None:
    """حالت کور اصلی: digest خراب **و** فایل غایب — این هرگز نباید pass شود."""
    gate = load_gate()
    artifact = _write_artifact(tmp_path, "garbage-not-a-digest")
    (tmp_path / "mp-app" / "studio" / "src" / "lib" / "x.ts").unlink()
    _point_gate_at(gate, tmp_path)

    problems, report, _dirty = gate.inspect_stale(artifact)
    assert len(problems) == 2, problems
    assert any("digest نامعتبر" in problem for problem in problems)
    assert any("در checkout نیست" in problem for problem in problems)
    # خط گزارش نباید بگوید «تازه است».
    assert any("← کهنه" in line for line in report), report

    code, _out, _err = _run_main(gate)
    assert code == 1


def main() -> int:
    import tempfile

    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    failures = 0
    for test in tests:
        with tempfile.TemporaryDirectory() as tmp:
            try:
                test(Path(tmp))
            except AssertionError as exc:  # pragma: no cover - گزارش شکست
                failures += 1
                print(f"FAIL {test.__name__}: {exc}")
            else:
                print(f"PASS {test.__name__}")
    print(f"{len(tests) - failures}/{len(tests)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
