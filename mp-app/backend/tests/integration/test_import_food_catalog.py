"""تست‌های scripts/import_food_catalog.py (WP 0.4 / F‑07).

پوشش شاخه‌های بدون DB: تجزیهٔ منبع، محاسبهٔ چربی از آتووتر، حذف تکراری‌ها، و
کدهای خروج `main`. `import_rows` با یک session جعلی تست می‌شود (DB واقعی لازم نیست).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "import_food_catalog.py"


@pytest.fixture
def fc(monkeypatch):
    name = "import_food_catalog_under_test"
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, name, mod)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


JS_SOURCE = """\
export const foods = [
  { name: 'مرغ', protein: 31, carbs: 0, calories: 165, category: 'گوشت' },
  { name: 'برنج', protein: 2.7, carbs: 28, calories: 130.4, category: 'غلات' },
  { name: 'مرغ', protein: 31, carbs: 0, calories: 165, category: 'گوشت' },
  { name: '', protein: 1, carbs: 1, calories: 10, category: 'x' },
];
"""


def test_parse_source_extracts_every_matching_row(fc) -> None:
    rows = fc.parse_source(JS_SOURCE)
    assert [r["name_fa"] for r in rows] == ["مرغ", "برنج", "مرغ", ""]
    assert rows[1] == {
        "name_fa": "برنج",
        "protein_g": 2.7,
        "carbs_g": 28.0,
        "kcal": 130,
        "category": "غلات",
    }


def test_parse_source_on_unrelated_text_returns_nothing(fc) -> None:
    assert fc.parse_source("const x = 1;") == []


def test_derive_fat_is_exact_when_macros_agree(fc) -> None:
    # 4·10 + 4·10 = 80، باقی‌مانده 70 کیلوکالری ⇒ 70/9 ≈ 7.8 گرم
    assert fc.derive_fat(10, 10, 150) == (7.8, "")


def test_derive_fat_small_negative_remainder_is_rounding(fc) -> None:
    # 4·10 + 4·10 = 80 > 75 ⇒ اختلاف ۵ کیلوکالری (زیر آستانه) ⇒ چربی صفر و بدون یادداشت
    assert fc.derive_fat(10, 10, 75) == (0.0, "")


def test_derive_fat_large_negative_remainder_is_flagged(fc) -> None:
    fat, note = fc.derive_fat(100, 0, 0)
    assert fat == 0.0
    assert note.startswith("چربی نامعلوم: کالری گزارش‌شده")


def test_derive_fat_impossible_value_is_flagged(fc) -> None:
    # 1000/9 ≈ 111 گرم در ۱۰۰ گرم — ناممکن
    fat, note = fc.derive_fat(0, 0, 1000)
    assert fat == 0.0
    assert "ناممکن" in note


def test_build_rows_skips_empty_and_duplicate_names(fc) -> None:
    rows = fc.build_rows(JS_SOURCE)
    assert [r["name_fa"] for r in rows] == ["مرغ", "برنج"]
    chicken = rows[0]
    assert chicken["external_id"] == f"{fc.SOURCE_REPO}:مرغ"
    assert chicken["kcal_per_100g"] == 165
    assert chicken["notes"] == ""


class _FakeRow:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class _FakeSession:
    def __init__(self, existing: dict):
        self.existing = existing
        self.added: list = []
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def scalar(self, stmt):
        # کلید یکتا external_id؛ استخراج از کلاس where ساده برای این تست کافی است.
        key = stmt.whereclause.right.value
        return self.existing.get(key)

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        self.committed = True


def _rows(fc):
    return fc.build_rows(JS_SOURCE)


def test_import_rows_inserts_updates_and_skips(fc, monkeypatch) -> None:
    rows = _rows(fc)
    chicken, rice = rows
    existing = {
        # موجود و یکسان ⇒ بدون تغییر
        chicken["external_id"]: _FakeRow(
            kcal_per_100g=165,
            protein_g_per_100g=31.0,
            carbs_g_per_100g=0.0,
            fat_g_per_100g=0.0,
        ),
        # موجود با کالری متفاوت ⇒ به‌روزرسانی
        rice["external_id"]: _FakeRow(
            kcal_per_100g=1,
            protein_g_per_100g=2.7,
            carbs_g_per_100g=28.0,
            fat_g_per_100g=0.0,
        ),
    }
    session = _FakeSession(existing)
    import db.base

    monkeypatch.setattr(db.base, "get_session_factory", lambda: lambda: session)

    result = fc.import_rows(rows)
    assert result["inserted"] == 0
    assert result["updated"] == 1
    assert result["unchanged"] == 1
    assert result["dry_run"] is False
    assert session.committed is True
    assert existing[rice["external_id"]].kcal_per_100g == rice["kcal_per_100g"]


def test_import_rows_inserts_new_rows(fc, monkeypatch) -> None:
    rows = _rows(fc)
    session = _FakeSession({})
    import db.base

    monkeypatch.setattr(db.base, "get_session_factory", lambda: lambda: session)
    result = fc.import_rows(rows)
    assert result["inserted"] == len(rows)
    assert len(session.added) == len(rows)
    assert session.added[0].external_id == rows[0]["external_id"]


def test_import_rows_dry_run_writes_nothing(fc, monkeypatch) -> None:
    rows = _rows(fc)
    session = _FakeSession({})
    import db.base

    monkeypatch.setattr(db.base, "get_session_factory", lambda: lambda: session)
    result = fc.import_rows(rows, dry_run=True)
    assert result["inserted"] == len(rows)
    assert result["dry_run"] is True
    assert session.added == []


def test_main_missing_source_returns_2(fc, tmp_path, capsys) -> None:
    assert fc.main(["--source", str(tmp_path / "nope.js")]) == 2
    assert "فایل منبع پیدا نشد" in capsys.readouterr().err


def test_main_unrecognised_source_returns_3(fc, tmp_path, capsys) -> None:
    src = tmp_path / "fit4.js"
    src.write_text("export const foods = [];\n", encoding="utf-8")
    assert fc.main(["--source", str(src)]) == 3
    assert "الگوی فایل تغییر کرده" in capsys.readouterr().err


def test_main_success_reports_counts(fc, tmp_path, monkeypatch, capsys) -> None:
    src = tmp_path / "fit4.js"
    src.write_text(JS_SOURCE, encoding="utf-8")
    seen = {}

    def fake_import(rows, *, dry_run=False):
        seen["n"] = len(rows)
        seen["dry"] = dry_run
        return {"inserted": 2, "updated": 0, "unchanged": 0}

    monkeypatch.setattr(fc, "import_rows", fake_import)
    assert fc.main(["--source", str(src), "--dry-run"]) == 0
    assert seen == {"n": 2, "dry": True}
    out = capsys.readouterr().out
    assert "2 درج" in out and "منبع:" in out
