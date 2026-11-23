"""M74 — لغو member-scoped رزرو کلاس، تکرار و تازه‌شدن ظرفیت."""

from __future__ import annotations

import itertools

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from db.base import get_session_factory, init_db, reset_engine

_counter = itertools.count(815001)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from app.config import settings
    from cache.store import InMemoryCache, reset_cache
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/m74.db")
    reset_engine()
    init_db()
    limiter.reset()
    reset_cache(InMemoryCache())
    with TestClient(create_app()) as test_client:
        yield test_client
    reset_engine()


def _user_headers(role: str) -> dict[str, str]:
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
        json={"phone": phone, "full_name": "عضو کلاس", "gender": "male"},
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
        return {"Authorization": f"Bearer {create_access_token(user.id, user.role)}"}


def _create_class(client: TestClient, staff: dict[str, str], capacity: int = 1) -> int:
    response = client.post(
        "/api/v1/classes",
        json={"name": "یوگا", "capacity": capacity, "schedule_text": "امروز"},
        headers=staff,
    )
    assert response.status_code == 200, response.text
    return response.json()["id"]


def _book(client: TestClient, staff: dict[str, str], class_id: int, member_id: int) -> dict:
    response = client.post(
        "/api/v1/classes/book",
        json={"class_id": class_id, "member_id": member_id},
        headers=staff,
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_member_cannot_cancel_another_members_booking(client: TestClient) -> None:
    staff = _user_headers("manager")
    owner_id = _member(client, staff, "09120000011")
    other_id = _member(client, staff, "09120000012")
    class_id = _create_class(client, staff)
    _book(client, staff, class_id, owner_id)

    response = client.post(
        "/api/v1/classes/cancel",
        json={"class_id": class_id, "member_id": owner_id},
        headers=_member_headers(other_id),
    )

    assert response.status_code == 403
    listing = client.get("/api/v1/classes", headers=staff).json()
    assert listing[0]["confirmed"] == 1


def test_member_cannot_create_booking_for_another_member(client: TestClient) -> None:
    staff = _user_headers("manager")
    target_id = _member(client, staff, "09120000021")
    actor_id = _member(client, staff, "09120000022")
    class_id = _create_class(client, staff)

    response = client.post(
        "/api/v1/classes/book",
        json={"class_id": class_id, "member_id": target_id},
        headers=_member_headers(actor_id),
    )

    assert response.status_code == 403
    listing = client.get("/api/v1/classes", headers=staff).json()
    assert listing[0]["confirmed"] == 0


def test_member_cancels_own_booking_and_duplicate_cancel_is_rejected(client: TestClient) -> None:
    staff = _user_headers("manager")
    member_id = _member(client, staff, "09120000031")
    member = _member_headers(member_id)
    class_id = _create_class(client, staff)
    original = _book(client, staff, class_id, member_id)

    before = client.get("/api/v1/classes", headers=member).json()[0]
    assert before["member_booking_status"] == "confirmed"

    cancelled = client.post(
        "/api/v1/classes/cancel",
        json={"class_id": class_id, "member_id": member_id},
        headers=member,
    )
    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()["status"] == "cancelled"

    duplicate = client.post(
        "/api/v1/classes/cancel",
        json={"class_id": class_id, "member_id": member_id},
        headers=member,
    )
    assert duplicate.status_code == 404

    after = client.get("/api/v1/classes", headers=member).json()[0]
    assert after["member_booking_status"] is None
    assert after["confirmed"] == 0
    assert after["seats_left"] == 1

    rebooked = client.post(
        "/api/v1/classes/book",
        json={"class_id": class_id, "member_id": member_id},
        headers=member,
    )
    assert rebooked.status_code == 200, rebooked.text
    assert rebooked.json()["id"] == original["id"]  # قید یکتا: همان ردیف دوباره فعال می‌شود
    assert rebooked.json()["status"] == "confirmed"
    listed_again = client.get("/api/v1/classes", headers=member).json()[0]
    assert listed_again["member_booking_status"] == "confirmed"
    assert listed_again["confirmed"] == 1


def test_rebooked_waitlisted_member_joins_queue_at_tail(client: TestClient) -> None:
    staff = _user_headers("manager")
    first_id = _member(client, staff, "09120000051")
    waiting_id = _member(client, staff, "09120000052")
    later_id = _member(client, staff, "09120000053")
    first = _member_headers(first_id)
    waiting = _member_headers(waiting_id)
    later = _member_headers(later_id)
    class_id = _create_class(client, staff, capacity=1)

    assert _book(client, staff, class_id, first_id)["status"] == "confirmed"
    assert _book(client, staff, class_id, waiting_id)["status"] == "waitlisted"
    assert (
        client.post(
            "/api/v1/classes/cancel",
            json={"class_id": class_id, "member_id": first_id},
            headers=first,
        ).status_code
        == 200
    )
    assert _book(client, staff, class_id, later_id)["status"] == "waitlisted"

    rebooked = client.post(
        "/api/v1/classes/book",
        json={"class_id": class_id, "member_id": first_id},
        headers=first,
    )
    assert rebooked.status_code == 200, rebooked.text
    assert rebooked.json()["status"] == "waitlisted"

    # لغو نفر تأییدشده باید C را جلوتر از A بفرستد؛ رزرو مجدد نباید با id قدیمی صف را دور بزند.
    cancelled = client.post(
        "/api/v1/classes/cancel",
        json={"class_id": class_id, "member_id": waiting_id},
        headers=waiting,
    )
    assert cancelled.status_code == 200, cancelled.text
    later_view = client.get("/api/v1/classes", headers=later).json()[0]
    first_view = client.get("/api/v1/classes", headers=first).json()[0]
    assert later_view["member_booking_status"] == "confirmed"
    assert first_view["member_booking_status"] == "waitlisted"


def test_cancelling_confirmed_booking_promotes_waitlist_and_refreshes_status(
    client: TestClient,
) -> None:
    staff = _user_headers("manager")
    first_id = _member(client, staff, "09120000041")
    waiting_id = _member(client, staff, "09120000042")
    first = _member_headers(first_id)
    waiting = _member_headers(waiting_id)
    class_id = _create_class(client, staff, capacity=1)
    _book(client, staff, class_id, first_id)
    assert _book(client, staff, class_id, waiting_id)["status"] == "waitlisted"

    response = client.post(
        "/api/v1/classes/cancel",
        json={"class_id": class_id, "member_id": first_id},
        headers=first,
    )
    assert response.status_code == 200, response.text

    first_view = client.get("/api/v1/classes", headers=first).json()[0]
    waiting_view = client.get("/api/v1/classes", headers=waiting).json()[0]
    assert first_view["member_booking_status"] is None
    assert waiting_view["member_booking_status"] == "confirmed"
    assert waiting_view["confirmed"] == 1
    assert waiting_view["waitlisted"] == 0
    assert waiting_view["seats_left"] == 0
