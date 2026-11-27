"""MEM-01 identity negative: User.id must never be substituted for Member.id."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta


def _user_id(headers: dict[str, str]) -> int:
    from app.security.jwt import decode_access_token

    token = headers["Authorization"].removeprefix("Bearer ")
    return int(decode_access_token(token)["sub"])


def _create_member_profile(user_id: int) -> int:
    from db.base import get_session_factory
    from db.models import Member

    with get_session_factory()() as session:
        member = Member(
            user_id=user_id,
            gender="female",
            goal="hypertrophy",
            constraints="[]",
            branch_id=1,
        )
        session.add(member)
        session.commit()
        return member.id


def _two_member_actors(auth) -> tuple[dict[str, str], int, int, dict[str, str], int, int]:
    # Offset the users table so neither member's User.id accidentally equals its Member.id.
    auth("manager")
    auth("manager")
    member_a_headers = auth("member")
    member_a_user_id = _user_id(member_a_headers)
    member_a_id = _create_member_profile(member_a_user_id)
    member_b_headers = auth("member")
    member_b_user_id = _user_id(member_b_headers)
    member_b_id = _create_member_profile(member_b_user_id)
    assert member_a_user_id not in {member_a_id, member_b_id}
    assert member_b_user_id != member_b_id
    return (
        member_a_headers,
        member_a_user_id,
        member_a_id,
        member_b_headers,
        member_b_user_id,
        member_b_id,
    )


def _seed_membership(member_id: int) -> None:
    from db.base import get_session_factory
    from db.models import Membership

    now = datetime.now(UTC)
    with get_session_factory()() as session:
        session.add(
            Membership(
                member_id=member_id,
                plan_name="اشتراک مصنوعی تست مالکیت",
                started_at=now,
                expires_at=now + timedelta(days=30),
                status="active",
                price_rial=0,
                branch_id=1,
            )
        )
        session.commit()


def test_me_returns_member_id_separately_from_authenticated_user_id(client, auth) -> None:
    headers_a, user_a_id, member_a_id, _headers_b, _user_b_id, _member_b_id = _two_member_actors(
        auth
    )

    response = client.get("/api/v1/members/me", headers=headers_a)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["role"] == "member"
    assert body["user_id"] == user_a_id
    assert body["id"] == member_a_id
    assert body["user_id"] != body["id"]

    own_history = client.get(f"/api/v1/members/{member_a_id}/memberships", headers=headers_a)
    assert own_history.status_code == 200, own_history.text
    assert own_history.json() == []


def test_user_id_is_rejected_when_used_as_a_member_id(client, auth) -> None:
    headers_a, user_a_id, member_a_id, _headers_b, _user_b_id, member_b_id = _two_member_actors(
        auth
    )
    assert user_a_id not in {member_a_id, member_b_id}, (
        "fixture must distinguish User.id from Member.id"
    )

    response = client.get(f"/api/v1/members/{user_a_id}/memberships", headers=headers_a)
    assert response.status_code in (403, 404), response.text


def test_member_cannot_read_another_membership_history(client, auth) -> None:
    headers_a, _user_a_id, _member_a_id, _headers_b, _user_b_id, member_b_id = _two_member_actors(
        auth
    )
    _seed_membership(member_b_id)

    response = client.get(f"/api/v1/members/{member_b_id}/memberships", headers=headers_a)
    assert response.status_code == 403, response.text
