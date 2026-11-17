"""تست‌های M18 — سیاست دادهٔ سخت‌گیرانه: مالکیت سطری + پیکرسنجی فقط ادمین.

قواعد مالک:
(۱) کلاینت فقط دادهٔ خودش (۲) ورود پیکرسنجی فقط staff (۳) نتایج/سوابق/پیشرفت برای صاحب داده آزاد.
"""

from __future__ import annotations

import itertools

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture()
def client(tmp_path):
    from app.config import settings
    from cache.store import InMemoryCache, reset_cache
    from db.base import init_db, reset_engine
    from modules.auth.router import limiter

    settings.database_url = f"sqlite:///{tmp_path / 'own.db'}"
    reset_engine()
    init_db()
    app = create_app()
    app.state.limiter = limiter
    limiter.reset()
    reset_cache(InMemoryCache())
    with TestClient(app) as c:
        yield c
    limiter.reset()


def _user_headers(client, role: str, member_phone: str | None = None) -> tuple[dict, int | None]:
    """ساخت کاربر با نقش + (برای member) عضو متصل — برگرداندن (headers, member_id)."""
    from app.security.jwt import create_access_token
    from db.base import get_session_factory
    from db.models import Member, User

    n = next(_user_headers.counter)
    with get_session_factory()() as s:
        u = User(phone=f"09{n:09d}", full_name=f"{role}-{n}", role=role)
        s.add(u)
        s.commit()
        s.refresh(u)
        mid = None
        if member_phone:
            m = Member(user_id=u.id, goal="hypertrophy")
            s.add(m)
            s.commit()
            s.refresh(m)
            mid = m.id
        token = create_access_token(u.id, u.role)
    return {"Authorization": f"Bearer {token}"}, mid


_user_headers.counter = itertools.count(int(__import__("time").time() * 1000) % 10**8)


def test_member_cannot_read_other_members_data(client):
    """عضو A نباید به دادهٔ عضو B دسترسی داشته باشد (۴۰۳ در همهٔ مسیرها)."""
    staff, _ = _user_headers(client, "manager")
    # دو عضو واقعی
    client.post(
        "/api/v1/members/",
        json={"phone": "09121110001", "full_name": "عضو الف", "gender": "male"},
        headers=staff,
    )
    b = client.post(
        "/api/v1/members/",
        json={"phone": "09121110002", "full_name": "عضو ب", "gender": "male"},
        headers=staff,
    ).json()
    # اشتراک + ارزیابی + پرداخت برای B
    client.post(
        "/api/v1/members/memberships",
        json={
            "member_id": b["id"],
            "plan_name": "ماهانه",
            "duration_days": 30,
            "price_rial": 100000,
        },
        headers=staff,
    )
    client.post(
        "/api/v1/assessments/jp7",
        json={
            "member_id": b["id"],
            "age": 30,
            "gender": "male",
            "skinfolds_mm": {
                "chest": 10,
                "triceps": 8,
                "subscapular": 10,
                "suprailiac": 9,
                "abdomen": 15,
                "thigh": 12,
                "calf": 7,
            },
        },
        headers=staff,
    )
    client.post(
        "/api/v1/payments",
        json={"member_id": b["id"], "amount_rial": 100000, "method": "cash"},
        headers=staff,
    )

    a_headers, a_mid = _user_headers(client, "member", member_phone="09121110003")
    assert a_mid is not None

    # تلاش عضو A برای خواندن B — همه باید ۴۰۳ شوند
    forbidden = [
        ("GET", f"/api/v1/members/{b['id']}"),
        ("GET", f"/api/v1/members/{b['id']}/memberships"),
        ("GET", f"/api/v1/assessments/member/{b['id']}"),
        ("GET", f"/api/v1/programs/member/{b['id']}"),
        ("GET", f"/api/v1/payments/invoice/{b['id']}"),
        ("GET", f"/api/v1/payments/wallet/{b['id']}"),
    ]
    for method, url in forbidden:
        resp = client.request(method, url, headers=a_headers)
        assert resp.status_code == 403, f"{method} {url} → {resp.status_code} (باید ۴۰۳)"


def test_member_reads_own_data(client):
    """عضو به دادهٔ خودش (نتایج پیکرسنجی، سوابق، کیف پول) دسترسی دارد."""
    staff, _ = _user_headers(client, "manager")
    h, mid = _user_headers(client, "member", member_phone="09122220001")
    client.post(
        "/api/v1/memberships" if False else "/api/v1/members/memberships",
        json={"member_id": mid, "plan_name": "ماهانه", "duration_days": 30, "price_rial": 100000},
        headers=staff,
    )
    client.post(
        "/api/v1/assessments/jp7",
        json={
            "member_id": mid,
            "age": 25,
            "gender": "male",
            "skinfolds_mm": {
                "chest": 10,
                "triceps": 8,
                "subscapular": 10,
                "suprailiac": 9,
                "abdomen": 15,
                "thigh": 12,
                "calf": 7,
            },
        },
        headers=staff,
    )
    client.post(
        "/api/v1/payments/wallet/charge",
        json={"member_id": mid, "amount_rial": 50000},
        headers=staff,
    )

    assert client.get(f"/api/v1/members/{mid}", headers=h).status_code == 200
    assert client.get(f"/api/v1/members/{mid}/memberships", headers=h).status_code == 200
    assert client.get(f"/api/v1/assessments/member/{mid}", headers=h).status_code == 200
    assert client.get(f"/api/v1/programs/member/{mid}", headers=h).status_code == 200
    assert client.get(f"/api/v1/payments/wallet/{mid}", headers=h).status_code == 200
    assert client.get(f"/api/v1/payments/invoice/{mid}", headers=h).status_code == 200
    # لیست پرداخت‌ها برای member فقط دادهٔ خودش را برمی‌گرداند
    resp = client.get("/api/v1/payments", headers=h)
    assert resp.status_code == 200
    assert all(p["member_id"] == mid for p in resp.json())


def test_body_comp_entry_only_staff(client):
    """ورود دادهٔ پیکرسنجی فقط از ادمین/مربی — کلاینت ۴۰۳."""
    h, mid = _user_headers(client, "member", member_phone="09123330001")
    r1 = client.post(
        "/api/v1/assessments/jp7",
        json={
            "member_id": mid,
            "age": 30,
            "gender": "male",
            "skinfolds_mm": {
                "chest": 10,
                "triceps": 8,
                "subscapular": 10,
                "suprailiac": 9,
                "abdomen": 15,
                "thigh": 12,
                "calf": 7,
            },
        },
        headers=h,
    )
    assert r1.status_code == 403  # member: ثبت JP7 ممنوع
    scores = [{"domain": d, "score": 3, "notes": ""} for d in range(1, 15)]
    r2 = client.post("/api/v1/assessments/", json={"member_id": mid, "scores": scores}, headers=h)
    assert r2.status_code == 403  # member: ثبت ارزیابی ۱۴ دامنه ممنوع
    # مربی مجاز است
    coach, _ = _user_headers(client, "coach")
    r3 = client.post(
        "/api/v1/assessments/jp7",
        json={
            "member_id": mid,
            "age": 30,
            "gender": "male",
            "skinfolds_mm": {
                "chest": 10,
                "triceps": 8,
                "subscapular": 10,
                "suprailiac": 9,
                "abdomen": 15,
                "thigh": 12,
                "calf": 7,
            },
        },
        headers=coach,
    )
    assert r3.status_code == 200


def test_member_checkin_only_self(client):
    """عضو نمی‌تواند به‌جای دیگری چک‌این کند یا کیف پولش را خرج کند."""
    staff, _ = _user_headers(client, "manager")
    b = client.post(
        "/api/v1/members/",
        json={"phone": "09124440001", "full_name": "قربانی", "gender": "male"},
        headers=staff,
    ).json()
    h, mid = _user_headers(client, "member", member_phone="09124440002")
    # چک‌این به‌جای دیگری
    r = client.post("/api/v1/face/checkin", json={"member_id": b["id"], "method": "qr"}, headers=h)
    assert r.status_code == 403
    # خرج از کیف پول دیگری
    client.post(
        "/api/v1/payments/wallet/charge",
        json={"member_id": b["id"], "amount_rial": 90000},
        headers=staff,
    )
    r2 = client.post(
        "/api/v1/payments/wallet/pay", json={"member_id": b["id"], "amount_rial": 10000}, headers=h
    )
    assert r2.status_code == 403
    # حذف چهرهٔ دیگری
    r3 = client.delete(f"/api/v1/face/enroll/{b['id']}", headers=h)
    assert r3.status_code == 403


def test_staff_accesses_all(client):
    """ادمین به همهٔ داده‌ها دسترسی دارد (قاعدهٔ مالک)."""
    staff, _ = _user_headers(client, "manager")
    b = client.post(
        "/api/v1/members/",
        json={"phone": "09125550001", "full_name": "هر کسی", "gender": "male"},
        headers=staff,
    ).json()
    assert client.get(f"/api/v1/members/{b['id']}", headers=staff).status_code == 200
    assert client.get(f"/api/v1/payments/invoice/{b['id']}", headers=staff).status_code == 200
    assert client.get(f"/api/v1/assessments/member/{b['id']}", headers=staff).status_code == 200
