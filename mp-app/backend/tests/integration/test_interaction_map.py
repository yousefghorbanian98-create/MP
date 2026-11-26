"""Regression tests for page-test discovery in the interaction-map gate."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[4] / "scripts" / "interaction_map.py"


@pytest.fixture()
def interaction_map(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    name = "interaction_map_under_test"
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, name, module)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    root = tmp_path / "repo"
    tests_dir = root / "mp-app" / "studio" / "tests"
    tests_dir.mkdir(parents=True)
    monkeypatch.setattr(module, "ROOT", root)
    monkeypatch.setattr(module, "TESTS_DIR", tests_dir)
    return module, tests_dir


def test_only_tests_importing_a_page_count_for_that_page(interaction_map) -> None:
    module, tests_dir = interaction_map
    (tests_dir / "motion.test.tsx").write_text(
        'const consumers = [["Members.tsx", "pages/Members.tsx"]];\n',
        encoding="utf-8",
    )
    (tests_dir / "money.test.ts").write_text(
        'it.each(["pages/Members.tsx"])("checks a label", () => {});\n',
        encoding="utf-8",
    )
    (tests_dir / "members.test.tsx").write_text(
        'import { Members } from "../src/pages/Members";\n',
        encoding="utf-8",
    )
    (tests_dir / "members-lazy.test.tsx").write_text(
        'const page = await import("../src/pages/Members");\n',
        encoding="utf-8",
    )

    assert module.studio_tests("Members") == [
        "mp-app/studio/tests/members-lazy.test.tsx",
        "mp-app/studio/tests/members.test.tsx",
    ]
