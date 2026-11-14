"""تست‌های قفل/نگهبان‌های مدل عمیق چهره (D-008 / بستن کار باز)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.errors import ApiError
from modules.face_id.deep import (
    DeepFaceAdapter,
    lock_status,
    verify_model_file,
)


def test_html_disguised_as_model_is_rejected(tmp_path: Path):
    """درس قدیمی: دانلود ناموفق HTML بود — هرگز به‌عنوان مدل پذیرفته نشود."""
    fake = tmp_path / "model.onnx"
    fake.write_bytes(b"<!DOCTYPE html><html><body>404</body></html>" + b" " * 2_000_000)
    with pytest.raises(ApiError) as e:
        verify_model_file(fake)
    assert e.value.code == "model_not_onnx"


def test_missing_and_tiny_files_rejected(tmp_path: Path):
    with pytest.raises(ApiError):
        verify_model_file(tmp_path / "nope.onnx")
    tiny = tmp_path / "tiny.onnx"
    tiny.write_bytes(b"\x08\x00\x00")
    with pytest.raises(ApiError) as e:
        verify_model_file(tiny)
    assert e.value.code == "model_too_small"


def test_valid_onnx_magic_and_sha(tmp_path: Path):
    ok = tmp_path / "ok.onnx"
    ok.write_bytes(b"\x08\x01" + b"\x00" * (1024 * 1024 + 8))
    info = verify_model_file(ok)
    assert info["size"] > 1024 * 1024 and len(info["sha256"]) == 64


def test_lock_status_truthful_when_unset(monkeypatch):
    for var in (
        "MP_FACE_MODEL_PATH",
        "MP_FACE_MODEL_SHA256",
        "MP_FACE_MODEL_LICENSE",
        "MP_FACE_POPULATION_FIT",
    ):
        monkeypatch.delenv(var, raising=False)
    st = lock_status()
    assert st["unlocked"] is False
    assert st["active_backend"] == "hog-dlib"
    assert st["note"]  # همیشه توضیح صریح


def test_adapter_refuses_when_locked(monkeypatch):
    for var in (
        "MP_FACE_MODEL_PATH",
        "MP_FACE_MODEL_SHA256",
        "MP_FACE_MODEL_LICENSE",
        "MP_FACE_POPULATION_FIT",
    ):
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(ApiError) as e:
        DeepFaceAdapter()
    assert e.value.code == "model_locked"


def test_lock_opens_only_with_all_four_conditions(tmp_path: Path, monkeypatch):
    ok = tmp_path / "ok.onnx"
    ok.write_bytes(b"\x08\x01" + b"\x00" * (1024 * 1024 + 8))
    monkeypatch.setenv("MP_FACE_MODEL_PATH", str(ok))
    monkeypatch.setenv("MP_FACE_MODEL_SHA256", "abc123")
    monkeypatch.setenv("MP_FACE_MODEL_LICENSE", "Apache-2.0")
    monkeypatch.setenv("MP_FACE_POPULATION_FIT", "adults-fa-v1")
    st = lock_status()
    assert st["unlocked"] is True and st["active_backend"] == "deep-onnx"


def test_deep_status_endpoint_locked_by_default(client):
    from app.security.jwt import create_access_token
    from db.base import get_session_factory
    from db.models import User

    n = next(_counter)
    with get_session_factory()() as s_:
        u = User(phone=f"09{n:09d}", full_name="deep-test", role="member")
        s_.add(u)
        s_.commit()
        h = {"Authorization": f"Bearer {create_access_token(u.id, u.role)}"}
    r = client.get("/api/v1/face/deep-status", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["unlocked"] is False and body["active_backend"] == "hog-dlib"
    assert body["checks"]["weights_present"] is False


# فایکسچر client برای تست endpoint (الگوی هر-فایلی)
import itertools  # noqa: E402

_counter = itertools.count(930001)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from app.config import settings
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/deep.db")
    from db.base import init_db, reset_engine

    reset_engine()
    init_db()
    limiter.reset()
    from cache.store import InMemoryCache, reset_cache

    reset_cache(InMemoryCache())
    app = __import__("app.main", fromlist=["create_app"]).create_app()
    with TestClient(app) as c:
        yield c
    reset_engine()
