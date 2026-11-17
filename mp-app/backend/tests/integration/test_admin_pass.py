"""تست‌های admin pass — اعطا/ابطال نقش (M43-c1)."""

from __future__ import annotations

import itertools

import pytest
from fastapi.testclient import TestClient

from app.config import settings

_counter = itertools.count(960001)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/roles.db")
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


def _make_user(role: str) -> tuple[int, dict]:
    from app.security.jwt import create_access_token
    from db.base import get_session_factory
    from db.models import User

    n = next(_counter)
    with get_session_factory()() as s:
        u = User(phone=f"09{n:09d}", full_name=f"{role}-{n}", role=role)
        s.add(u)
        s.commit()
        return u.id, {"Authorization": f"Bearer {create_access_token(u.id, u.role)}"}


def test_grant_and_revoke_admin_pass_with_audit(client) -> None:
    """M43-c1 — super_admin نقش می‌دهد/می‌گیرد؛ هر تغییر در AuditLog می‌نشیند."""
    from db.base import get_session_factory
    from db.models import AuditLog, User

    owner_id, owner_h = _make_user("super_admin")
    target_id, _ = _make_user("member")

    # اعطا: member ← coach
    res = client.post(
        f"/api/v1/admin/users/{target_id}/role", json={"role": "coach"}, headers=owner_h
    )
    assert res.status_code == 200, res.text
    assert res.json()["changed"] is True

    with get_session_factory()() as s:
        assert s.get(User, target_id).role == "coach"
        logs = s.query(AuditLog).filter_by(action="role_grant", entity_id=target_id).all()
        assert len(logs) == 1
        assert "coach" in logs[0].detail

    # ابطال ← member
    res = client.delete(f"/api/v1/admin/users/{target_id}/role", headers=owner_h)
    assert res.status_code == 200
    with get_session_factory()() as s:
        assert s.get(User, target_id).role == "member"

    # فهرست کاربران
    res = client.get("/api/v1/admin/users", headers=owner_h)
    assert res.status_code == 200
    assert any(row["id"] == owner_id for row in res.json())


def test_only_super_admin_and_no_self_change(client) -> None:
    """M43-c1 — manager نمی‌تواند نقش بدهد؛ تغییر نقش خود ممنوع؛ نقش نامعتبر رد."""
    _, manager_h = _make_user("manager")
    owner_id, owner_h = _make_user("super_admin")
    target_id, _ = _make_user("member")

    res = client.post(
        f"/api/v1/admin/users/{target_id}/role", json={"role": "coach"}, headers=manager_h
    )
    assert res.status_code == 403

    res = client.post(
        f"/api/v1/admin/users/{owner_id}/role", json={"role": "member"}, headers=owner_h
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "self_role_change"

    res = client.post(
        f"/api/v1/admin/users/{target_id}/role", json={"role": "boss"}, headers=owner_h
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "invalid_role"

    res = client.get("/api/v1/admin/users", headers=manager_h)
    assert res.status_code == 403
