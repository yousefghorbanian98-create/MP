"""M46-c2 — `/members/me` باید نقش کاربر را بدهد.

پیش از این، استودیو برای نمایش «مدیر» در نوار بالا مجبور بود نام و نقش را
hardcode کند، چون API نمی‌گفت کاربر واقعاً چه نقشی دارد. این تست آن گپ را قفل می‌کند.
"""

from __future__ import annotations

import itertools

import pytest
from fastapi.testclient import TestClient

from app.config import settings

_counter = itertools.count(970001)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/whoami.db")
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


def _token(role: str, full_name: str) -> str:
    from app.security.jwt import create_access_token
    from db.base import get_session_factory
    from db.models import User

    n = next(_counter)
    with get_session_factory()() as s:
        u = User(phone=f"09{n:09d}", full_name=full_name, role=role)
        s.add(u)
        s.commit()
        return create_access_token(u.id, u.role)


def test_me_returns_role_and_full_name(client: TestClient) -> None:
    tok = _token("coach", "مربی سارا")
    r = client.get("/api/v1/members/me", headers={"Authorization": f"Bearer {tok}"})

    assert r.status_code == 200
    body = r.json()
    assert body["role"] == "coach"
    assert body["full_name"] == "مربی سارا"


def test_me_role_reflects_admin(client: TestClient) -> None:
    tok = _token("admin", "مدیر باشگاه")
    body = client.get("/api/v1/members/me", headers={"Authorization": f"Bearer {tok}"}).json()
    assert body["role"] == "admin"


def test_me_role_reflects_member(client: TestClient) -> None:
    tok = _token("member", "عضو عادی")
    body = client.get("/api/v1/members/me", headers={"Authorization": f"Bearer {tok}"}).json()
    assert body["role"] == "member"
