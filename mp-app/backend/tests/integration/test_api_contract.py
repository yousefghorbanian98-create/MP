"""تست‌های قرارداد API (M04+M08) — نسخه‌بندی، OpenAPI، rate-limit، OTP، RBAC."""

from __future__ import annotations

import itertools

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from db.base import get_session_factory, init_db, reset_engine

_counter = itertools.count(1)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from app.config import settings
    from modules.auth.router import limiter

    db_url = f"sqlite:///{tmp_path}/api_test.db"
    monkeypatch.setattr(settings, "database_url", db_url)
    reset_engine()
    init_db()
    limiter.reset()  # جلوگیری از آلودگی شمارندهٔ rate-limit بین تست‌ها
    app = create_app()
    with TestClient(app) as c:
        yield c
    reset_engine()


@pytest.fixture()
def auth():
    """ساخت کاربر با نقش دلخواه و برگرداندن header احراز هویت."""

    def _auth(role: str = "manager") -> dict:
        from app.security.jwt import create_access_token
        from db.models import User

        n = next(_counter)
        with get_session_factory()() as s:
            u = User(phone=f"09{n:09d}", full_name=f"{role}-{n}", role=role)
            s.add(u)
            s.commit()
            token = create_access_token(u.id, u.role)
            return {"Authorization": f"Bearer {token}"}

    return _auth


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_api_versioned_under_v1(client):
    spec = client.get("/openapi.json").json()
    paths = spec["paths"]
    for p in [
        "/api/v1/auth/otp/request",
        "/api/v1/members",
        "/api/v1/payments",
        "/api/v1/assessments",
        "/api/v1/programs/{program_id}/approve",
        "/api/v1/face/checkin",
        "/api/v1/admin/flags",
        "/api/v1/notifications",
        "/api/v1/nutrition/plans",
    ]:
        assert p in paths, f"مسیر {p} در OpenAPI نیست"


def test_validation_error_structured(client):
    r = client.post("/api/v1/auth/otp/request", json={"phone": "123"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation_error"


def test_otp_flow_issue_and_verify(client):
    r = client.post("/api/v1/auth/otp/request", json={"phone": "09121234567"})
    assert r.status_code == 200
    code = r.json()["dev_code"]
    r2 = client.post("/api/v1/auth/otp/verify", json={"phone": "09121234567", "code": code})
    assert r2.status_code == 200
    tokens = r2.json()
    assert "access_token" in tokens and "refresh_token" in tokens
    r3 = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r3.status_code == 200
    r4 = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r4.status_code == 401  # rotation: توکن قبلی باطل


def test_otp_wrong_code_rejected(client):
    client.post("/api/v1/auth/otp/request", json={"phone": "09121234567"})
    r = client.post("/api/v1/auth/otp/verify", json={"phone": "09121234567", "code": "000000"})
    assert r.status_code == 401


def test_otp_rate_limit(client):
    codes = []
    for _i in range(7):
        r = client.post("/api/v1/auth/otp/request", json={"phone": "09121234567"})
        codes.append(r.status_code)
    assert 429 in codes, f"rate-limit اعمال نشد: {codes}"


def test_member_crud(client, auth):
    h = auth("reception")
    r = client.post(
        "/api/v1/members",
        json={"phone": "09123334455", "full_name": "علی رضایی", "goal": "hypertrophy"},
        headers=h,
    )
    assert r.status_code == 200
    member = r.json()
    assert member["branch_id"] == 1
    r2 = client.post(
        "/api/v1/members", json={"phone": "09123334455", "full_name": "تکراری"}, headers=h
    )
    assert r2.status_code == 409
    r3 = client.get(f"/api/v1/members/{member['id']}", headers=auth("coach"))
    assert r3.status_code == 200
    r4 = client.patch(f"/api/v1/members/{member['id']}", json={"goal": "strength"}, headers=h)
    assert r4.status_code == 200 and r4.json()["goal"] == "strength"


def test_member_create_forbidden_for_member_role(client, auth):
    r = client.post(
        "/api/v1/members",
        json={"phone": "09123334466", "full_name": "x y z"},
        headers=auth("member"),
    )
    assert r.status_code == 403


def test_unauthenticated_rejected(client):
    r = client.get("/api/v1/members")
    assert r.status_code == 401


def test_payment_flow(client, auth):
    reception = auth("reception")
    member = client.post(
        "/api/v1/members",
        json={"phone": "09125556677", "full_name": "عضو پرداخت"},
        headers=reception,
    ).json()
    r = client.post(
        "/api/v1/payments",
        json={"member_id": member["id"], "amount_rial": 5_000_000, "method": "cash"},
        headers=reception,
    )
    assert r.status_code == 200
    payment = r.json()
    assert payment["status"] == "pending"
    r2 = client.post(
        f"/api/v1/payments/{payment['id']}/verify", json={"reference_id": "r1"}, headers=reception
    )
    assert r2.json()["status"] == "paid"
    r3 = client.post(f"/api/v1/payments/{payment['id']}/verify", json={}, headers=reception)
    assert r3.status_code == 400


def test_assessment_requires_14_domains(client, auth):
    coach = auth("coach")
    member = client.post(
        "/api/v1/members", json={"phone": "09126667788", "full_name": "عضو ارزیابی"}, headers=coach
    ).json()
    bad = [{"domain": i, "score": 3} for i in range(1, 14)]
    r = client.post(
        "/api/v1/assessments", json={"member_id": member["id"], "scores": bad}, headers=coach
    )
    assert r.status_code == 422
    good = [{"domain": i, "score": 3} for i in range(1, 15)]
    r2 = client.post(
        "/api/v1/assessments", json={"member_id": member["id"], "scores": good}, headers=coach
    )
    assert r2.status_code == 200
    assert r2.json()["total_score"] == 42


def test_jp7_computation(client, auth):
    coach = auth("coach")
    member = client.post(
        "/api/v1/members", json={"phone": "09127778899", "full_name": "عضو JP7"}, headers=coach
    ).json()
    skinfolds = {
        "chest": 12,
        "triceps": 10,
        "subscapular": 14,
        "suprailiac": 12,
        "abdomen": 16,
        "thigh": 18,
        "calf": 12,
    }
    r = client.post(
        "/api/v1/assessments/jp7",
        json={"member_id": member["id"], "age": 30, "gender": "male", "skinfolds_mm": skinfolds},
        headers=coach,
    )
    assert r.status_code == 200
    assert 5 < r.json()["body_fat_pct"] < 40


def test_face_enroll_requires_consent(client, auth):
    import base64

    coach = auth("coach")
    member = client.post(
        "/api/v1/members", json={"phone": "09128889900", "full_name": "عضو چهره"}, headers=coach
    ).json()
    emb = base64.b64encode(b"\x01" * 128).decode()
    r = client.post(
        "/api/v1/face/enroll", json={"member_id": member["id"], "embedding_b64": emb}, headers=coach
    )
    assert r.status_code == 403  # بدون رضایت
    client.post("/api/v1/face/consent", json={"member_id": member["id"]}, headers=auth("member"))
    r2 = client.post(
        "/api/v1/face/enroll", json={"member_id": member["id"], "embedding_b64": emb}, headers=coach
    )
    assert r2.status_code == 200
    r3 = client.delete(f"/api/v1/face/enroll/{member['id']}", headers=auth("member"))
    assert r3.status_code == 200


def test_checkin_denied_without_membership(client, auth):
    reception = auth("reception")
    member = client.post(
        "/api/v1/members",
        json={"phone": "09129990011", "full_name": "عضو چک‌این"},
        headers=reception,
    ).json()
    r = client.post(
        "/api/v1/face/checkin", json={"member_id": member["id"], "method": "qr"}, headers=reception
    )
    assert r.status_code == 200
    assert r.json()["result"] == "denied"
    assert r.json()["denial_reason"] == "membership_expired"


def test_feature_flags_manager_only(client, auth):
    r = client.put(
        "/api/v1/admin/flags",
        json={"key": "new_dashboard", "enabled": True, "description": "داشبورد جدید"},
        headers=auth("manager"),
    )
    assert r.status_code == 200
    r2 = client.get("/api/v1/admin/flags/new_dashboard", headers=auth("manager"))
    assert r2.json()["enabled"] is True
    r3 = client.put(
        "/api/v1/admin/flags",
        json={"key": "x2", "enabled": True},
        headers=auth("coach"),
    )
    assert r3.status_code == 403  # فقط مدیر


def test_program_approve_reject(client, auth):
    coach = auth("coach")
    member = client.post(
        "/api/v1/members", json={"phone": "09131112233", "full_name": "عضو برنامه"}, headers=coach
    ).json()
    from db.base import get_session_factory as gsf
    from db.models import WorkoutProgram

    with gsf()() as s:
        prog = WorkoutProgram(
            member_id=member["id"], goal="hypertrophy", engine_version="t", branch_id=1
        )
        s.add(prog)
        s.commit()
        pid = prog.id
    r = client.post(f"/api/v1/programs/{pid}/approve", headers=coach)
    assert r.status_code == 200 and r.json()["status"] == "approved"
    r2 = client.post(f"/api/v1/programs/{pid}/approve", headers=coach)
    assert r2.status_code == 400
    # عضو مجاز به تأیید نیست
    r3 = client.post(f"/api/v1/programs/{pid}/approve", headers=auth("member"))
    assert r3.status_code == 403


def test_logout_all_revokes_every_session(client, auth):
    """US-404 — خروج از همهٔ دستگاه‌ها."""
    from db.base import get_session_factory as gsf
    from db.models import RefreshToken, User

    # دو نشست برای یک کاربر
    with gsf()() as s:
        u = User(phone="09134445566", full_name="multi", role="member")
        s.add(u)
        s.commit()
        uid = u.id
    tokens = []
    for _ in range(2):
        r = client.post("/api/v1/auth/otp/request", json={"phone": "09134445566"})
        code = r.json()["dev_code"]
        rv = client.post("/api/v1/auth/otp/verify", json={"phone": "09134445566", "code": code})
        tokens.append(rv.json())
    h = {"Authorization": f"Bearer {tokens[0]['access_token']}"}
    r = client.post("/api/v1/auth/logout-all", headers=h)
    assert r.status_code == 200
    with gsf()() as s:
        revoked = (
            s.query(RefreshToken)
            .filter(RefreshToken.user_id == uid, RefreshToken.revoked_at.is_(None))
            .count()
        )
        assert revoked == 0
    # refresh هیچ‌کدام کار نمی‌کند
    for t in tokens:
        rr = client.post("/api/v1/auth/refresh", json={"refresh_token": t["refresh_token"]})
        assert rr.status_code == 401
