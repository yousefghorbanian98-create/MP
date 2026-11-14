"""تست‌های API هوشمندی تمرین + KPI (M29)."""

from __future__ import annotations

import itertools

import pytest
from fastapi.testclient import TestClient

from app.config import settings

_counter = itertools.count(800001)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/ai.db")
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


@pytest.fixture()
def auth():
    def _auth(role: str = "admin") -> dict:
        from app.security.jwt import create_access_token
        from db.base import get_session_factory
        from db.models import User

        n = next(_counter)
        with get_session_factory()() as s:
            u = User(phone=f"09{n:09d}", full_name=f"{role}-{n}", role=role)
            s.add(u)
            s.commit()
            return {"Authorization": f"Bearer {create_access_token(u.id, u.role)}"}

    return _auth


def test_suggest_weight_endpoint(client, auth):
    h = auth("coach")
    r = client.post(
        "/api/v1/ai/suggest-weight",
        json={"last_weight": 60, "reps_done": 13, "target_reps": 10, "rpe": 7},
        headers=h,
    )
    assert r.status_code == 200
    assert r.json()["action"] == "increase"
    bad = client.post(
        "/api/v1/ai/suggest-weight",
        json={"last_weight": -1, "reps_done": 5, "target_reps": 10},
        headers=h,
    )
    assert bad.status_code == 422  # اعتبارسنجی pydantic


def test_admin_kpis_endpoint(client, auth):
    h = auth("admin")
    r = client.get("/api/v1/admin/kpis", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["active_members"] == 0
    assert body["class_fill_rate"] is None  # ناشناخته ≠ صفر
    assert "generated_at" in body
