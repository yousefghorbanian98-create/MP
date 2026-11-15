"""تست‌های M41 — تفکیک جنسیت (c1) + پلن جنسیت‌محور (c2/c3)."""

from __future__ import annotations

import itertools

import pytest
from fastapi.testclient import TestClient

from app.config import settings

_counter = itertools.count(910001)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/m41.db")
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
def staff_headers(client):
    from app.security.jwt import create_access_token
    from db.base import get_session_factory
    from db.models import User

    n = next(_counter)
    with get_session_factory()() as s:
        u = User(phone=f"09{n:09d}", full_name=f"rec-{n}", role="reception")
        s.add(u)
        s.commit()
        return {"Authorization": f"Bearer {create_access_token(u.id, u.role)}"}


def _register(client, headers, phone: str, gender=None):
    payload = {"phone": phone, "full_name": "عضو تست M41", "goal": "hypertrophy"}
    if gender is not None:
        payload["gender"] = gender
    return client.post("/api/v1/members", json=payload, headers=headers)


def test_registration_requires_gender(client, staff_headers) -> None:
    """M41-c1 — جنسیت در ثبت‌نام اجباری است (تفکیک آقایان/بانوان)."""
    res = _register(client, staff_headers, "09121110001")
    assert res.status_code == 422, res.text

    res = _register(client, staff_headers, "09121110002", gender="other")
    assert res.status_code == 422, res.text

    res = _register(client, staff_headers, "09121110003", gender="female")
    assert res.status_code == 200, res.text
    assert res.json()["gender"] == "female"

    res = _register(client, staff_headers, "09121110004", gender="male")
    assert res.status_code == 200, res.text
    assert res.json()["gender"] == "male"


def test_admin_can_filter_members_by_gender(client, staff_headers) -> None:
    """M41-c1 — نسخهٔ ادمین: فیلتر/تب جنسیت."""
    _register(client, staff_headers, "09121120001", gender="female")
    _register(client, staff_headers, "09121120002", gender="male")
    _register(client, staff_headers, "09121120003", gender="female")

    res = client.get("/api/v1/members?gender=female", headers=staff_headers)
    assert res.status_code == 200
    females = res.json()
    assert females and all(m["gender"] == "female" for m in females)
    assert len(females) == 2

    res = client.get("/api/v1/members?gender=male", headers=staff_headers)
    males = res.json()
    assert len(males) == 1 and males[0]["gender"] == "male"

    res = client.get("/api/v1/members", headers=staff_headers)
    assert len(res.json()) == 3


def test_gender_plan_purchase_and_invoice(client, staff_headers) -> None:
    """M41-c2/c3 — خرید پلن بانوان = ۳۷ روز + صورتحساب با reason سیاست."""
    res = _register(client, staff_headers, "09121130001", gender="female")
    member_id = res.json()["id"]

    # فهرست پلن‌ها
    res = client.get("/api/v1/members/memberships/plans", headers=staff_headers)
    assert res.status_code == 200, res.text
    plans = res.json()
    assert any(p["gender"] == "female" and p["duration_days"] == 37 for p in plans)

    # خرید ماهانهٔ بانوان
    res = client.post(
        "/api/v1/members/memberships/from-plan",
        json={"member_id": member_id, "plan_key": "monthly_basic"},
        headers=staff_headers,
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["invoice"]["duration_days"] == 37
    assert "۳۷" in body["invoice"]["reason"]
    membership_id = body["membership"]["id"]

    # صورتحساب — reason سیاست + نسخه
    res = client.get(f"/api/v1/members/memberships/{membership_id}/invoice", headers=staff_headers)
    assert res.status_code == 200, res.text
    invoice = res.json()
    assert invoice["duration_days"] == 37
    assert invoice["gender"] == "female"
    assert "سیاست" in invoice["policy_note"]
    assert invoice["policy_version"]


def test_plan_purchase_requires_gender(client, staff_headers) -> None:
    """M41 — بدون جنسیت ثبت‌شده: خطا (داده ناشناخته است نه صفر)."""
    from db.base import get_session_factory
    from db.models import Member

    res = _register(client, staff_headers, "09121140001", gender="male")
    member_id = res.json()["id"]
    with get_session_factory()() as s:
        m = s.get(Member, member_id)
        m.gender = "unknown"
        s.commit()
    res = client.post(
        "/api/v1/members/memberships/from-plan",
        json={"member_id": member_id, "plan_key": "monthly_basic"},
        headers=staff_headers,
    )
    assert res.status_code == 400, res.text
    assert res.json()["error"]["code"] == "missing_gender"
