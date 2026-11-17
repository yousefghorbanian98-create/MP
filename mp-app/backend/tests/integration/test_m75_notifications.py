"""M75 — inbox اعلان عضو، unread/read و ownership API موجود."""

from __future__ import annotations

import itertools

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from db.base import get_session_factory, init_db, reset_engine

_counter = itertools.count(825001)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from app.config import settings
    from cache.store import InMemoryCache, reset_cache
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/m75.db")
    reset_engine()
    init_db()
    limiter.reset()
    reset_cache(InMemoryCache())
    with TestClient(create_app()) as test_client:
        yield test_client
    reset_engine()


def _headers(role: str) -> dict[str, str]:
    from app.security.jwt import create_access_token
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
        json={"phone": phone, "full_name": "عضو اعلان", "gender": "male"},
        headers=staff,
    )
    assert response.status_code == 200, response.text
    return response.json()["id"]


def _member_headers(member_id: int) -> dict[str, str]:
    from app.security.jwt import create_access_token
    from db.models import Member, User

    with get_session_factory()() as session:
        member = session.get(Member, member_id)
        assert member is not None
        user = session.get(User, member.user_id)
        assert user is not None
        token = create_access_token(user.id, user.role)
    return {"Authorization": f"Bearer {token}"}


def _send(client: TestClient, staff: dict[str, str], member_id: int, title: str) -> int:
    response = client.post(
        "/api/v1/notifications",
        json={"member_id": member_id, "title": title, "body": "متن آزمایشی", "kind": "general"},
        headers=staff,
    )
    assert response.status_code == 200, response.text
    return response.json()["id"]


def test_member_cannot_read_another_members_notifications(client: TestClient) -> None:
    staff = _headers("manager")
    owner_id = _member(client, staff, "09120000051")
    actor_id = _member(client, staff, "09120000052")
    _send(client, staff, owner_id, "اعلان خصوصی")

    response = client.get(
        f"/api/v1/notifications/member/{owner_id}", headers=_member_headers(actor_id)
    )
    assert response.status_code == 403


def test_member_cannot_mark_another_members_notification_as_read(client: TestClient) -> None:
    staff = _headers("manager")
    owner_id = _member(client, staff, "09120000061")
    actor_id = _member(client, staff, "09120000062")
    notification_id = _send(client, staff, owner_id, "اعلان خصوصی")

    response = client.post(
        f"/api/v1/notifications/{notification_id}/read",
        headers=_member_headers(actor_id),
    )
    assert response.status_code == 403

    owner_notifications = client.get(
        f"/api/v1/notifications/member/{owner_id}", headers=staff
    ).json()
    assert owner_notifications[0]["read_at"] is None


def test_member_lists_and_marks_only_own_notifications_as_read(client: TestClient) -> None:
    staff = _headers("manager")
    member_id = _member(client, staff, "09120000071")
    member = _member_headers(member_id)
    notification_ids = [
        _send(client, staff, member_id, title) for title in ("تمرین امروز", "اشتراک", "پیام مربی")
    ]

    unread = client.get(
        f"/api/v1/notifications/member/{member_id}?unread_only=true", headers=member
    )
    assert unread.status_code == 200, unread.text
    assert len(unread.json()) == 3
    assert all(item["read_at"] is None for item in unread.json())

    marked = client.post(f"/api/v1/notifications/{notification_ids[0]}/read", headers=member)
    assert marked.status_code == 200, marked.text
    assert marked.json()["read_at"] is not None

    after = client.get(
        f"/api/v1/notifications/member/{member_id}?unread_only=true", headers=member
    ).json()
    assert len(after) == 2
    assert all(item["read_at"] is None for item in after)
