"""M78 — self logging for adaptive nutrition, exact RBAC and owner isolation."""

from __future__ import annotations

import itertools

import pytest
from fastapi.testclient import TestClient

from app.config import settings

_counter = itertools.count(826001)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from cache.store import InMemoryCache, reset_cache
    from db.base import init_db, reset_engine
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/m78.db")
    reset_engine()
    init_db()
    limiter.reset()
    reset_cache(InMemoryCache())
    from app.main import create_app

    with TestClient(create_app()) as test_client:
        yield test_client
    reset_engine()


def _headers(role: str) -> dict[str, str]:
    from app.security.jwt import create_access_token
    from db.base import get_session_factory
    from db.models import User

    n = next(_counter)
    with get_session_factory()() as session:
        user = User(phone=f"09{n:09d}", full_name=f"{role}-{n}", role=role)
        session.add(user)
        session.commit()
        token = create_access_token(user.id, user.role)
    return {"Authorization": f"Bearer {token}"}


def _member(client: TestClient, staff: dict[str, str], phone: str) -> int:
    response = client.post(
        "/api/v1/members",
        json={"phone": phone, "full_name": "عضو تغذیهٔ سازگار", "gender": "male"},
        headers=staff,
    )
    assert response.status_code == 200, response.text
    return response.json()["id"]


def _member_headers(member_id: int) -> dict[str, str]:
    from app.security.jwt import create_access_token
    from db.base import get_session_factory
    from db.models import Member, User

    with get_session_factory()() as session:
        member = session.get(Member, member_id)
        assert member is not None
        user = session.get(User, member.user_id)
        assert user is not None
        return {"Authorization": f"Bearer {create_access_token(user.id, user.role)}"}


def _weight_payload(member_id: int, kg: float = 74.5) -> dict:
    return {
        "member_id": member_id,
        "entries": [{"weight_kg": kg, "logged_for_date": "2026-11-16"}],
    }


def test_member_can_log_own_weight_but_not_another_members_weight(client: TestClient) -> None:
    staff = _headers("manager")
    owner_id = _member(client, staff, "09120000081")
    other_id = _member(client, staff, "09120000082")
    owner = _member_headers(owner_id)

    own = client.post(
        "/api/v1/nutrition/weight-logs", json=_weight_payload(owner_id), headers=owner
    )
    assert own.status_code == 200, own.text
    assert own.json()["logged"] == 1
    assert own.json()["updated"] == 0

    adaptive = client.get(f"/api/v1/nutrition/member/{owner_id}/adaptive", headers=owner)
    assert adaptive.status_code == 200, adaptive.text
    assert adaptive.json()["data_counts"]["weight_entries"] == 1
    assert adaptive.json()["estimate"]["tdee_kcal"] is None
    assert adaptive.json()["suggestion"]["action"] == "none"

    cross_member = client.post(
        "/api/v1/nutrition/weight-logs", json=_weight_payload(other_id), headers=owner
    )
    assert cross_member.status_code == 403

    from sqlalchemy import select

    from db.base import get_session_factory
    from db.models import BodyWeightLog

    with get_session_factory()() as session:
        owner_rows = session.scalars(
            select(BodyWeightLog).where(BodyWeightLog.member_id == owner_id)
        ).all()
        other_rows = session.scalars(
            select(BodyWeightLog).where(BodyWeightLog.member_id == other_id)
        ).all()
    assert len(owner_rows) == 1
    assert other_rows == []
