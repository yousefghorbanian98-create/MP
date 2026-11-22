"""تست‌های scripts/attach_exercise_media.py (WP 0.4 / F‑07).

`STATIC_DIR` به یک پوشهٔ موقت اشاره می‌شود و session جعلی جایگزین DB می‌شود؛
کاتالوگ واقعی یا فایل‌های تصویر مخزن لازم نیست.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "attach_exercise_media.py"


@pytest.fixture
def am(monkeypatch, tmp_path):
    name = "attach_exercise_media_under_test"
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, name, mod)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    static = tmp_path / "static"
    static.mkdir()
    monkeypatch.setattr(mod, "STATIC_DIR", static)
    return mod


def _touch_all_frames(am) -> None:
    for eid in am.MAPPING:
        for frame in (0, 1):
            (am.STATIC_DIR / f"{eid}_{frame}.jpg").write_bytes(b"x")


def test_media_path_is_the_public_first_frame(am) -> None:
    assert am.media_path(7) == "/static/exercises/7_0.jpg"


def test_missing_files_lists_ids_without_both_frames(am) -> None:
    _touch_all_frames(am)
    (am.STATIC_DIR / "3_1.jpg").unlink()  # فریم دوم حرکت ۳ غایب
    (am.STATIC_DIR / "5_0.jpg").unlink()  # فریم اول حرکت ۵ غایب
    assert am.missing_files() == [3, 5]


def test_main_reports_missing_files_with_exit_1(am, monkeypatch, capsys) -> None:
    monkeypatch.setattr(sys, "argv", ["attach_exercise_media.py"])
    assert am.main() == 1
    assert "فایل‌های غایب" in capsys.readouterr().err


def test_main_check_mode_is_read_only(am, monkeypatch, capsys) -> None:
    _touch_all_frames(am)
    monkeypatch.setattr(sys, "argv", ["attach_exercise_media.py", "--check"])
    opened = []
    monkeypatch.setattr(am, "get_session_factory", lambda: opened.append(1))
    assert am.main() == 0
    assert opened == []  # حالت --check نباید به DB وصل شود
    assert "فایل‌ها کامل‌اند" in capsys.readouterr().out


class _Query:
    def __init__(self, rows):
        self._rows = rows

    def filter(self, *_):
        return self

    def all(self):
        return self._rows


class _FakeDB:
    def __init__(self, rows: dict[int, SimpleNamespace]):
        self.rows = rows
        self.committed = False

    def query(self, *_):
        return _Query(list(self.rows.values()))

    def get(self, _model, eid):
        return self.rows.get(eid)

    def commit(self):
        self.committed = True


def test_attach_updates_only_rows_whose_media_changed(am, monkeypatch) -> None:
    _touch_all_frames(am)
    import engine.catalog_sync as catalog_sync

    monkeypatch.setattr(catalog_sync, "ensure_exercises", lambda _db, _ids: None)
    rows = {eid: SimpleNamespace(id=eid, video_url=None) for eid in am.MAPPING}
    # حرکت ۱ از قبل مسیر درست را دارد ⇒ بدون تغییر
    rows[1].video_url = am.media_path(1)
    # حرکت ۲ فایل تصویر ندارد ⇒ دست‌نخورده
    (am.STATIC_DIR / "2_0.jpg").unlink()
    db = _FakeDB(rows)

    updated = am.attach(db)
    assert updated == len(am.MAPPING) - 2  # ۱ (یکسان) و ۲ (فایل غایب) کنار گذاشته شدند
    assert rows[1].video_url == am.media_path(1)
    assert rows[2].video_url is None
    assert rows[3].video_url == am.media_path(3)
    assert db.committed is True


def test_attach_skips_ids_missing_from_catalog(am, monkeypatch) -> None:
    _touch_all_frames(am)
    import engine.catalog_sync as catalog_sync

    monkeypatch.setattr(catalog_sync, "ensure_exercises", lambda _db, _ids: None)
    rows = {eid: SimpleNamespace(id=eid, video_url=None) for eid in am.MAPPING if eid != 4}
    db = _FakeDB(rows)
    assert am.attach(db) == len(rows)
    assert 4 not in rows
