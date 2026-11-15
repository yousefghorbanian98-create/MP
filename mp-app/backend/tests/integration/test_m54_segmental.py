"""M54-c1 — API آنالیز سگمنتال آنتروپومتریک.

مهم‌ترین چیز: ثبت رکورد **خالی** باید رد شود، و گزارش برای عضوی که
هیچ اندازه‌گیری ندارد باید ۲۰۰ با دلیل صریح بدهد، نه ۴۰۴ گیج‌کننده.
"""

from __future__ import annotations

import itertools

import pytest
from fastapi.testclient import TestClient

from app.config import settings

_counter = itertools.count(986001)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/limb.db")
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


def _staff() -> dict:
    from app.security.jwt import create_access_token
    from db.base import get_session_factory
    from db.models import User

    n = next(_counter)
    with get_session_factory()() as s:
        u = User(phone=f"09{n:09d}", full_name=f"coach-{n}", role="manager")
        s.add(u)
        s.commit()
        return {"Authorization": f"Bearer {create_access_token(u.id, u.role)}"}


def _member(height_cm: float | None = 178.0, gender: str = "male") -> int:
    from db.base import get_session_factory
    from db.models import Member, User

    n = next(_counter)
    with get_session_factory()() as s:
        u = User(phone=f"09{n:09d}", full_name=f"member-{n}", role="member")
        s.add(u)
        s.commit()
        m = Member(user_id=u.id, gender=gender, goal="x", height_cm=height_cm, branch_id=1)
        s.add(m)
        s.commit()
        return m.id


def _post(client: TestClient, h: dict, mid: int, **kwargs) -> dict:
    r = client.post("/api/v1/assessments/limb", json={"member_id": mid, **kwargs}, headers=h)
    assert r.status_code == 200, r.text
    return r.json()


def test_record_and_report_roundtrip(client: TestClient) -> None:
    h = _staff()
    mid = _member()

    created = _post(
        client,
        h,
        mid,
        waist_cm=88.0,
        hip_cm=100.0,
        upper_arm_right_cm=34.0,
        upper_arm_left_cm=34.2,
        thigh_right_cm=58.0,
        thigh_left_cm=58.4,
    )
    assert created["waist_cm"] == 88.0
    assert created["member_id"] == mid
    assert created["measured_at"]

    report = client.get(f"/api/v1/assessments/limb/member/{mid}/report", headers=h).json()
    assert report["measurements_count"] == 1
    assert report["latest"]["waist_cm"] == 88.0

    ratios = report["analysis"]["ratios"]
    assert ratios["waist_to_height"]["band"] == "normal"  # 88/178 = 0.494
    assert ratios["waist_to_hip"]["value"] == 0.88
    assert report["analysis"]["asymmetry"]["upper_arm"]["band"] == "normal"
    assert report["analysis"]["rule_version"] == "segmental-1.0"


def test_height_comes_from_the_member_profile_not_the_request(client: TestClient) -> None:
    """قد باید از پروفایل خوانده شود — وگرنه کاربر می‌تواند نسبت را دستکاری کند."""
    h = _staff()
    mid = _member(height_cm=None)
    _post(client, h, mid, waist_cm=88.0)

    report = client.get(f"/api/v1/assessments/limb/member/{mid}/report", headers=h).json()
    assert report["analysis"]["ratios"]["waist_to_height"]["value"] is None
    assert "whtr" in report["analysis"]["missing"]


def test_empty_measurement_is_rejected(client: TestClient) -> None:
    h = _staff()
    mid = _member()
    r = client.post("/api/v1/assessments/limb", json={"member_id": mid}, headers=h)
    assert r.status_code == 400
    assert "no_measurement" in r.text


def test_absurd_value_is_rejected(client: TestClient) -> None:
    h = _staff()
    mid = _member()
    r = client.post(
        "/api/v1/assessments/limb", json={"member_id": mid, "waist_cm": 999}, headers=h
    )
    assert r.status_code == 422  # Pydantic le=300


def test_no_measurements_gives_200_with_a_reason(client: TestClient) -> None:
    h = _staff()
    mid = _member()
    r = client.get(f"/api/v1/assessments/limb/member/{mid}/report", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["latest"] is None
    assert body["analysis"] is None
    assert body["measurements_count"] == 0
    assert "هیچ اندازه‌گیری" in body["reason"]


def test_unknown_member_is_404(client: TestClient) -> None:
    h = _staff()
    assert (
        client.get("/api/v1/assessments/limb/member/999999/report", headers=h).status_code == 404
    )


def test_member_cannot_read_another_members_report(client: TestClient) -> None:
    from app.security.jwt import create_access_token
    from db.base import get_session_factory
    from db.models import Member, User

    _staff()  # فقط برای ساخت نقش مربی لازم است، در این تست استفاده نمی‌شود
    victim = _member()

    n = next(_counter)
    with get_session_factory()() as s:
        u = User(phone=f"09{n:09d}", full_name="intruder", role="member")
        s.add(u)
        s.commit()
        s.add(Member(user_id=u.id, gender="male", goal="x", branch_id=1))
        s.commit()
        intruder_h = {"Authorization": f"Bearer {create_access_token(u.id, 'member')}"}

    assert (
        client.get(f"/api/v1/assessments/limb/member/{victim}/report", headers=intruder_h).status_code
        == 403
    )


def test_trend_appears_after_two_measurements(client: TestClient) -> None:
    h = _staff()
    mid = _member()

    _post(client, h, mid, waist_cm=95.0)
    # نقطهٔ دوم را مستقیم با تاریخ قدیمی‌تر می‌سازیم تا روند واقعی شود
    from db.base import get_session_factory
    from db.models import LimbMeasurement

    with get_session_factory()() as s:
        s.add(
            LimbMeasurement(
                member_id=mid,
                waist_cm=95.0,
                measured_at=__import__("datetime").datetime(2026, 9, 1, tzinfo=__import__("datetime").UTC),
            )
        )
        s.commit()

    report = client.get(f"/api/v1/assessments/limb/member/{mid}/report", headers=h).json()
    assert report["measurements_count"] == 2
    assert report["trend"] is not None
    assert report["trend"]["changes_cm"]["waist_cm"] == 0.0


def test_single_measurement_has_no_trend(client: TestClient) -> None:
    h = _staff()
    mid = _member()
    _post(client, h, mid, chest_cm=102.0)

    report = client.get(f"/api/v1/assessments/limb/member/{mid}/report", headers=h).json()
    assert report["measurements_count"] == 1
    assert report["trend"] is None, "یک نقطه روند نیست"


def test_member_role_can_record_own_measurement() -> None:
    """policy عضو برای POST /assessments/limb — همان کلاس باگی که چت داشت."""
    from security.rbac import enforce

    assert enforce("member", "/api/v1/assessments/limb", "POST")
    assert enforce("member", "/api/v1/assessments/limb/member/1/report", "GET")
