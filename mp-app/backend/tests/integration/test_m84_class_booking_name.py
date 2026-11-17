"""M84 — رزرو کلاس نام معتبر عضو را نشان می‌دهد و از نشست/DB مشتق می‌شود."""

from __future__ import annotations

import itertools

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from db.base import get_session_factory, init_db, reset_engine

_counter = itertools.count(840001)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from app.config import settings
    from cache.store import InMemoryCache, reset_cache
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/m84.db")
    reset_engine()
    init_db()
    limiter.reset()
    reset_cache(InMemoryCache())
    with TestClient(create_app()) as test_client:
        yield test_client
    reset_engine()


def _user_headers(role: str, full_name: str) -> dict[str, str]:
    from app.security.jwt import create_access_token
    from db.models import User

    n = next(_counter)
    with get_session_factory()() as session:
        user = User(phone=f"09{n:09d}", full_name=full_name, role=role)
        session.add(user)
        session.commit()
        token = create_access_token(user.id, user.role)
    return {"Authorization": f"Bearer {token}"}


def _create_member(client: TestClient, staff: dict[str, str], name: str) -> int:
    n = next(_counter)
    response = client.post(
        "/api/v1/members",
        json={"phone": f"09{n:09d}", "full_name": name, "gender": "male"},
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


def test_member_booking_uses_authoritative_name_and_keeps_names_owner_scoped(
    client: TestClient,
) -> None:
    staff = _user_headers("manager", "مدیر آزمون")
    owner_name = "نام واقعی عضو"
    other_name = "نام عضو دیگر"
    owner_id = _create_member(client, staff, owner_name)
    other_id = _create_member(client, staff, other_name)
    owner = _member_headers(owner_id)
    other = _member_headers(other_id)
    class_id = _create_class(client, staff, capacity=1)

    confirmed = client.post(
        "/api/v1/classes/book",
        json={"class_id": class_id, "member_id": owner_id, "member_name": "نام دستکاری‌شده"},
        headers=owner,
    )
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["status"] == "confirmed"
    assert confirmed.json()["member_name"] == owner_name

    owner_row = client.get("/api/v1/classes", headers=owner).json()[0]
    assert owner_row["member_booking_status"] == "confirmed"
    assert owner_row["member_booking_name"] == owner_name

    # یک عضو دیگر نه نام مالک را در feed می‌بیند و نه می‌تواند با شناسهٔ او رزرو بسازد.
    other_before = client.get("/api/v1/classes", headers=other).json()[0]
    assert other_before["member_booking_status"] is None
    assert other_before["member_booking_name"] is None
    spoofed = client.post(
        "/api/v1/classes/book",
        json={"class_id": class_id, "member_id": owner_id},
        headers=other,
    )
    assert spoofed.status_code == 403

    waiting = client.post(
        "/api/v1/classes/book",
        json={"class_id": class_id, "member_id": other_id},
        headers=other,
    )
    assert waiting.status_code == 200, waiting.text
    assert waiting.json()["status"] == "waitlisted"
    assert waiting.json()["member_name"] == other_name
    other_row = client.get("/api/v1/classes", headers=other).json()[0]
    assert other_row["member_booking_status"] == "waitlisted"
    assert other_row["member_booking_name"] == other_name
    assert owner_name not in str(other_row)

    # فهرست staff فقط شمارنده‌ها را دارد؛ feed عمومی نام رزروکنندگان را لو نمی‌دهد.
    staff_row = client.get("/api/v1/classes", headers=staff).json()[0]
    assert "member_booking_name" not in staff_row
    assert owner_name not in str(staff_row)
    assert other_name not in str(staff_row)


def test_staff_booking_response_returns_name_from_database(client: TestClient) -> None:
    staff = _user_headers("manager", "مدیر آزمون")
    member_name = "نام عضو رزروشده"
    member_id = _create_member(client, staff, member_name)
    class_id = _create_class(client, staff)

    response = client.post(
        "/api/v1/classes/book",
        json={"class_id": class_id, "member_id": member_id},
        headers=staff,
    )

    assert response.status_code == 200, response.text
    assert response.json()["member_name"] == member_name
