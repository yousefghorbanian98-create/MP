"""تست‌های قرارداد API (M04) — نسخه‌بندی، OpenAPI، rate-limit، اعتبارسنجی، جریان OTP."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from db.base import init_db


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from app.config import settings
    from db.base import reset_engine

    db_url = f"sqlite:///{tmp_path}/api_test.db"
    monkeypatch.setattr(settings, "database_url", db_url)
    reset_engine()
    init_db()
    app = create_app()
    with TestClient(app) as c:
        yield c
    reset_engine()


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_api_versioned_under_v1(client):
    client.get("/api/v1/openapi.json")
    # openapi در ریشه است؛ مسیرها باید /api/v1 داشته باشند
    spec = client.get("/openapi.json").json()
    paths = spec["paths"]
    assert "/api/v1/auth/otp/request" in paths
    assert "/api/v1/members" in paths
    assert "/api/v1/payments" in paths
    assert "/api/v1/assessments" in paths
    assert "/api/v1/programs/{program_id}/approve" in paths
    assert "/api/v1/face/checkin" in paths
    assert "/api/v1/admin/flags" in paths
    assert "/api/v1/notifications" in paths
    assert "/api/v1/nutrition/plans" in paths


def test_openapi_documented_titles(client):
    spec = client.get("/openapi.json").json()
    assert spec["info"]["title"] == "Muscle Paradise API"
    assert "tags" in spec


def test_validation_error_structured(client):
    r = client.post("/api/v1/auth/otp/request", json={"phone": "123"})
    assert r.status_code == 422
    body = r.json()
    assert body["error"]["code"] == "validation_error"
    assert body["error"]["details"]


def test_otp_flow_issue_and_verify(client):
    r = client.post("/api/v1/auth/otp/request", json={"phone": "09121234567"})
    assert r.status_code == 200
    code = r.json()["dev_code"]
    r2 = client.post("/api/v1/auth/otp/verify", json={"phone": "09121234567", "code": code})
    assert r2.status_code == 200
    tokens = r2.json()
    assert "access_token" in tokens and "refresh_token" in tokens
    # refresh کار می‌کند
    r3 = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r3.status_code == 200
    # refresh قبلی بعد از rotation باطل است
    r4 = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r4.status_code == 401


def test_otp_wrong_code_rejected(client):
    client.post("/api/v1/auth/otp/request", json={"phone": "09121234567"})
    r = client.post("/api/v1/auth/otp/verify", json={"phone": "09121234567", "code": "000000"})
    assert r.status_code == 401


def test_otp_rate_limit(client):
    """گیت M04: slowapi روی OTP."""
    codes = []
    for _i in range(7):
        r = client.post("/api/v1/auth/otp/request", json={"phone": "09121234567"})
        codes.append(r.status_code)
    assert 429 in codes, f"rate-limit اعمال نشد: {codes}"


def test_member_crud(client):
    r = client.post(
        "/api/v1/members",
        json={"phone": "09123334455", "full_name": "علی رضایی", "goal": "hypertrophy"},
    )
    assert r.status_code == 200
    member = r.json()
    assert member["branch_id"] == 1
    r2 = client.post(
        "/api/v1/members",
        json={"phone": "09123334455", "full_name": "تکراری"},
    )
    assert r2.status_code == 409  # شماره تکراری
    r3 = client.get(f"/api/v1/members/{member['id']}")
    assert r3.status_code == 200
    r4 = client.patch(f"/api/v1/members/{member['id']}", json={"goal": "strength"})
    assert r4.status_code == 200 and r4.json()["goal"] == "strength"


def test_payment_flow(client):
    member = client.post(
        "/api/v1/members", json={"phone": "09125556677", "full_name": "عضو پرداخت"}
    ).json()
    r = client.post(
        "/api/v1/payments",
        json={"member_id": member["id"], "amount_rial": 5_000_000, "method": "cash"},
    )
    assert r.status_code == 200
    payment = r.json()
    assert payment["status"] == "pending"
    r2 = client.post(f"/api/v1/payments/{payment['id']}/verify", json={"reference_id": "r1"})
    assert r2.json()["status"] == "paid"
    # تأیید مجدد ممنوع
    r3 = client.post(f"/api/v1/payments/{payment['id']}/verify", json={})
    assert r3.status_code == 400


def test_assessment_requires_14_domains(client):
    member = client.post(
        "/api/v1/members", json={"phone": "09126667788", "full_name": "عضو ارزیابی"}
    ).json()
    bad = [{"domain": i, "score": 3} for i in range(1, 14)]  # فقط ۱۳ دامنه
    r = client.post("/api/v1/assessments", json={"member_id": member["id"], "scores": bad})
    assert r.status_code == 422
    good = [{"domain": i, "score": 3} for i in range(1, 15)]
    r2 = client.post("/api/v1/assessments", json={"member_id": member["id"], "scores": good})
    assert r2.status_code == 200
    assert r2.json()["total_score"] == 42


def test_jp7_computation(client):
    member = client.post(
        "/api/v1/members", json={"phone": "09127778899", "full_name": "عضو JP7"}
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
    )
    assert r.status_code == 200
    assert 5 < r.json()["body_fat_pct"] < 40


def test_face_enroll_requires_consent(client):
    import base64

    member = client.post(
        "/api/v1/members", json={"phone": "09128889900", "full_name": "عضو چهره"}
    ).json()
    emb = base64.b64encode(b"\x01" * 128).decode()
    r = client.post("/api/v1/face/enroll", json={"member_id": member["id"], "embedding_b64": emb})
    assert r.status_code == 403  # بدون رضایت
    client.post("/api/v1/face/consent", json={"member_id": member["id"]})
    r2 = client.post("/api/v1/face/enroll", json={"member_id": member["id"], "embedding_b64": emb})
    assert r2.status_code == 200
    # حذف چهره (حق حذف)
    r3 = client.delete(f"/api/v1/face/enroll/{member['id']}")
    assert r3.status_code == 200


def test_checkin_denied_without_membership(client):
    member = client.post(
        "/api/v1/members", json={"phone": "09129990011", "full_name": "عضو چک‌این"}
    ).json()
    r = client.post("/api/v1/face/checkin", json={"member_id": member["id"], "method": "qr"})
    assert r.status_code == 200
    assert r.json()["result"] == "denied"
    assert r.json()["denial_reason"] == "membership_expired"


def test_feature_flags(client):
    r = client.put(
        "/api/v1/admin/flags",
        json={"key": "new_dashboard", "enabled": True, "description": "داشبورد جدید"},
    )
    assert r.status_code == 200
    r2 = client.get("/api/v1/admin/flags/new_dashboard")
    assert r2.json()["enabled"] is True


def test_program_approve_reject(client):
    member = client.post(
        "/api/v1/members", json={"phone": "09131112233", "full_name": "عضو برنامه"}
    ).json()
    # گردش approve/reject از API — تولید اعداد با موتور قواعد در M15 (G8)
    from db.base import get_session_factory
    from db.models import WorkoutProgram

    session_factory = get_session_factory()
    with session_factory() as s:
        prog = WorkoutProgram(
            member_id=member["id"], goal="hypertrophy", engine_version="t", branch_id=1
        )
        s.add(prog)
        s.commit()
        pid = prog.id
    r = client.post(f"/api/v1/programs/{pid}/approve")
    assert r.status_code == 200 and r.json()["status"] == "approved"
    r2 = client.post(f"/api/v1/programs/{pid}/approve")
    assert r2.status_code == 400  # دوباره ممنوع
