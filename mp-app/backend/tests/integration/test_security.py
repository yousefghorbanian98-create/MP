"""تست‌های امنیتی M09 — هدرها، audit log عملیات حساس."""

from __future__ import annotations

import itertools

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from db.base import get_session_factory, init_db, reset_engine

from ._actors import create_actor

_counter = itertools.count(1000)


# WP 1.2 / F-02: این ماژول کد OTP را از پاسخ dev می‌خواند ⇒ opt-in صریح.
pytestmark = pytest.mark.usefixtures("dev_otp_echo")


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from app.config import settings
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/sec.db")
    monkeypatch.setattr(settings, "environment", "production")  # HSTS هم تست شود
    # در production کلید بیومتریک اختصاصی الزامی است (D-028/تست crypto)؛
    # این فایل هدفش HSTS/RBAC است، پس کلید آزمایشی می‌دهیم.
    import base64 as _b64

    monkeypatch.setattr(settings, "biometric_key", _b64.b64encode(b"t" * 32).decode())
    reset_engine()
    init_db()
    limiter.reset()
    from cache.store import InMemoryCache, reset_cache

    reset_cache(InMemoryCache())
    app = create_app()
    with TestClient(app) as c:
        yield c
    reset_engine()


@pytest.fixture()
def auth():
    """هدر کاربر تازه؛ `grants` مجوزهای شخصی فاز ۵ را هم می‌سازد."""

    def _auth(role: str = "manager", grants: list[str] | None = None) -> dict:
        return create_actor(role, grants)

    return _auth


def test_security_headers_present(client):
    r = client.get("/health")
    h = r.headers
    assert h["X-Content-Type-Options"] == "nosniff"
    assert h["X-Frame-Options"] == "DENY"
    assert h["Referrer-Policy"] == "no-referrer"
    assert "default-src 'self'" in h["Content-Security-Policy"]
    assert h["Strict-Transport-Security"].startswith("max-age=")


def test_audit_log_payment_verify(client, auth):
    reception = auth("reception")
    member = client.post(
        "/api/v1/members",
        json={"phone": "09120001111", "full_name": "aud", "gender": "male"},
        headers=reception,
    ).json()
    p = client.post(
        "/api/v1/payments",
        json={"member_id": member["id"], "amount_rial": 100000, "method": "cash"},
        headers=reception,
    ).json()
    client.post(f"/api/v1/payments/{p['id']}/verify", json={}, headers=reception)
    logs = client.get("/api/v1/admin/audit?action=payment_verified", headers=auth("manager")).json()
    assert any(row["entity_id"] == p["id"] for row in logs)


def test_audit_log_face_delete(client, auth):
    import base64

    coach = auth("coach")
    member = client.post(
        "/api/v1/members",
        json={"phone": "09120002222", "full_name": "face", "gender": "male"},
        headers=coach,
    ).json()
    from app.security.jwt import create_access_token

    own = {"Authorization": f"Bearer {create_access_token(member['user_id'], 'member')}"}
    client.post("/api/v1/face/consent", json={"member_id": member["id"]}, headers=own)
    emb = base64.b64encode(b"\x02" * 128).decode()
    client.post(
        "/api/v1/face/enroll", json={"member_id": member["id"], "embedding_b64": emb}, headers=coach
    )
    client.delete(f"/api/v1/face/enroll/{member['id']}", headers=own)
    logs = client.get("/api/v1/admin/audit?action=face_deleted", headers=auth("manager")).json()
    assert len(logs) >= 1


def test_audit_log_program_approve(client, auth):
    coach = auth("coach")
    member = client.post(
        "/api/v1/members",
        json={"phone": "09120003333", "full_name": "prog", "gender": "male"},
        headers=coach,
    ).json()
    from db.models import WorkoutProgram

    with get_session_factory()() as s:
        prog = WorkoutProgram(member_id=member["id"], goal="g", engine_version="t", branch_id=1)
        s.add(prog)
        s.commit()
        pid = prog.id
    client.post(f"/api/v1/programs/{pid}/approve", headers=coach)
    logs = client.get("/api/v1/admin/audit?action=program_approved", headers=auth("manager")).json()
    assert any(row["entity_id"] == pid for row in logs)


def test_otp_never_stored_plain(client, monkeypatch):
    """R-002 — کد OTP خام در DB ذخیره نمی‌شود (test-only dev delivery)."""
    from app.config import settings
    from db.models import OtpCode

    # This fixture exercises production headers; this specific storage test uses
    # the development response to learn the code without calling an SMS provider.
    monkeypatch.setattr(settings, "environment", "development")
    monkeypatch.setattr(settings, "sms_provider", "dev")
    r = client.post("/api/v1/auth/otp/request", json={"phone": "09120004444"})
    code = r.json()["dev_code"]
    with get_session_factory()() as s:
        row = s.query(OtpCode).filter_by(phone="09120004444").first()
        assert row is not None
        assert code not in row.code_hash
        assert "$" in row.code_hash
