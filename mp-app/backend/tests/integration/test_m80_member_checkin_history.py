"""M80 — تاریخچهٔ حضور فقط برای عضو جاری و بدون مسیر ادمین."""

from __future__ import annotations

import itertools
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.config import settings

_counter = itertools.count(980001)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/m80.db")
    from db.base import init_db, reset_engine

    reset_engine()
    init_db()
    limiter.reset()
    from cache.store import InMemoryCache, reset_cache

    reset_cache(InMemoryCache())
    app = __import__("app.main", fromlist=["create_app"]).create_app()
    with TestClient(app) as test_client:
        yield test_client
    reset_engine()


def _new_user(role: str, *, with_member: bool = False) -> tuple[dict, int | None]:
    from app.security.jwt import create_access_token
    from db.base import get_session_factory
    from db.models import Member, User

    n = next(_counter)
    with get_session_factory()() as session:
        user = User(phone=f"09{n:09d}", full_name=f"{role}-{n}", role=role)
        session.add(user)
        session.flush()
        member_id = None
        if with_member:
            member = Member(
                user_id=user.id,
                goal="hypertrophy",
                constraints="[]",
                gender="male",
                branch_id=1,
            )
            session.add(member)
            session.flush()
            member_id = member.id
        user_id, user_role = user.id, user.role
        session.commit()
    headers = {"Authorization": f"Bearer {create_access_token(user_id, user_role)}"}
    return headers, member_id


def _seed_checkin(
    member_id: int,
    *,
    minutes_ago: int,
    result: str = "ok",
    method: str = "qr",
    checked_out: bool = False,
) -> int:
    from db.base import get_session_factory
    from db.models import CheckIn

    now = datetime.now(UTC)
    created_at = now - timedelta(minutes=minutes_ago)
    row = CheckIn(
        member_id=member_id,
        method=method,
        result=result,
        denial_reason="membership_expired" if result == "denied" else "",
        created_at=created_at,
        checked_out_at=created_at + timedelta(minutes=45) if checked_out else None,
        branch_id=1,
    )
    with get_session_factory()() as session:
        session.add(row)
        session.commit()
        return row.id


def test_member_history_is_self_scoped_paginated_and_keeps_denials(client: TestClient) -> None:
    own_headers, own_member_id = _new_user("member", with_member=True)
    _, other_member_id = _new_user("member", with_member=True)
    assert own_member_id is not None and other_member_id is not None

    denied_id = _seed_checkin(own_member_id, minutes_ago=2, result="denied", method="face")
    own_ok_id = _seed_checkin(own_member_id, minutes_ago=60, checked_out=True)
    other_id = _seed_checkin(other_member_id, minutes_ago=1)

    first = client.get("/api/v1/members/me/checkins?limit=1", headers=own_headers)
    assert first.status_code == 200, first.text
    first_body = first.json()
    assert first_body["rule_version"] == "member-checkin-history-1.0"
    assert first_body["has_more"] is True
    assert [item["checkin_id"] for item in first_body["items"]] == [denied_id]
    denied = first_body["items"][0]
    assert denied["result"] == "denied"
    assert denied["denial_reason"] == "membership_expired"
    assert denied["is_open"] is False
    assert "member_id" not in denied and "member_name" not in denied

    second = client.get("/api/v1/members/me/checkins?limit=1&offset=1", headers=own_headers)
    assert second.status_code == 200, second.text
    second_body = second.json()
    assert second_body["has_more"] is False
    assert [item["checkin_id"] for item in second_body["items"]] == [own_ok_id]
    assert second_body["items"][0]["checked_out_at"] is not None
    assert second_body["items"][0]["is_open"] is False
    assert other_id not in {
        item["checkin_id"] for item in first_body["items"] + second_body["items"]
    }

    # The self-history route explicitly rejects attempts to select another member.
    spoofed = client.get(
        f"/api/v1/members/me/checkins?member_id={other_member_id}&limit=100",
        headers=own_headers,
    )
    assert spoofed.status_code == 403, spoofed.text

    # ID-addressed member data and the staff-wide attendance feed are forbidden cross-scope.
    assert client.get(f"/api/v1/members/{other_member_id}", headers=own_headers).status_code == 403
    assert (
        client.get(
            f"/api/v1/admin/checkins?member_id={other_member_id}", headers=own_headers
        ).status_code
        == 403
    )


def test_member_history_is_empty_for_member_without_visits(client: TestClient) -> None:
    headers, _member_id = _new_user("member", with_member=True)
    response = client.get("/api/v1/members/me/checkins", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["items"] == []
    assert body["has_more"] is False


def test_member_history_requires_member_role_and_existing_profile(client: TestClient) -> None:
    coach_headers, _ = _new_user("coach")
    assert client.get("/api/v1/members/me/checkins", headers=coach_headers).status_code == 403

    member_headers, _ = _new_user("member")
    assert client.get("/api/v1/members/me/checkins", headers=member_headers).status_code == 404


def test_member_history_requires_auth_and_valid_pagination(client: TestClient) -> None:
    assert client.get("/api/v1/members/me/checkins").status_code in (401, 403)
    headers, _member_id = _new_user("member", with_member=True)
    assert client.get("/api/v1/members/me/checkins?limit=0", headers=headers).status_code == 422
    assert client.get("/api/v1/members/me/checkins?limit=101", headers=headers).status_code == 422
    assert client.get("/api/v1/members/me/checkins?offset=-1", headers=headers).status_code == 422
