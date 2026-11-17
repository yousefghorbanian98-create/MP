"""M46-c1 — فهرست feature flags: استودیو باید همه را یک‌جا بخواند (نه یکی‌یکی).

قاعدهٔ M45 که اینجا هم حاکم است: نبودِ داده ⇒ لیست خالی، نه ۴۰۴ و نه مقدار ساختگی.
"""

from __future__ import annotations

import itertools

import pytest
from fastapi.testclient import TestClient

from app.config import settings

_counter = itertools.count(960001)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/flags.db")
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


def _headers(role: str) -> dict:
    from app.security.jwt import create_access_token
    from db.base import get_session_factory
    from db.models import User

    n = next(_counter)
    with get_session_factory()() as s:
        u = User(phone=f"09{n:09d}", full_name=f"{role}-{n}", role=role)
        s.add(u)
        s.commit()
        return {"Authorization": f"Bearer {create_access_token(u.id, u.role)}"}


def test_list_flags_returns_all(client: TestClient) -> None:
    h = _headers("admin")
    client.put("/api/v1/admin/flags", json={"key": "face_gate", "enabled": True}, headers=h)
    client.put("/api/v1/admin/flags", json={"key": "sms_provider", "enabled": False}, headers=h)

    r = client.get("/api/v1/admin/flags", headers=h)

    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)
    keys = {f["key"] for f in body}
    assert {"face_gate", "sms_provider"} <= keys
    for f in body:
        assert set(f) >= {"id", "key", "enabled", "description"}


def test_list_flags_empty_is_empty_list_not_error(client: TestClient) -> None:
    r = client.get("/api/v1/admin/flags", headers=_headers("admin"))
    assert r.status_code == 200
    assert r.json() == []


def test_list_flags_requires_permission(client: TestClient) -> None:
    r = client.get("/api/v1/admin/flags", headers=_headers("member"))
    assert r.status_code == 403


def test_put_flag_then_list_reflects_change(client: TestClient) -> None:
    import json

    h = _headers("admin")
    client.put("/api/v1/admin/flags", json={"key": "new_dashboard", "enabled": False}, headers=h)
    client.put("/api/v1/admin/flags", json={"key": "new_dashboard", "enabled": True}, headers=h)

    body = client.get("/api/v1/admin/flags", headers=h).json()
    row = next(f for f in body if f["key"] == "new_dashboard")
    assert row["enabled"] is True

    logs = client.get("/api/v1/admin/audit?action=feature_flag_updated", headers=h).json()
    assert len(logs) == 2
    assert all(row["actor_user_id"] is not None for row in logs)
    assert json.loads(logs[0]["detail"])["key"] == "new_dashboard"
