"""تست متن حریم خصوصی بیومتریک (M31)."""

from __future__ import annotations

import itertools

import pytest
from fastapi.testclient import TestClient

from app.config import settings

_counter = itertools.count(910001)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/fp.db")
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
    def _auth(role: str = "member") -> dict:
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


def test_privacy_notice_versioned_and_readable(client, auth):
    h = auth("member")
    r = client.get("/api/v1/face/privacy-notice", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["version"].startswith("faceid-privacy-")
    assert any("رضایت" in s["text"] or "رضایت" in s["heading"] for s in body["sections"])
    assert any("حذف" in s["text"] for s in body["sections"])  # حق حذف صریح
