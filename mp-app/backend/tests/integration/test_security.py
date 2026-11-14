"""تست‌های امنیتی M09 — هدرها، audit log عملیات حساس."""

from __future__ import annotations

import itertools

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from db.base import get_session_factory, init_db, reset_engine

_counter = itertools.count(1000)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from app.config import settings
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/sec.db")
    monkeypatch.setattr(settings, "environment", "production")  # HSTS هم تست شود
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
    def _auth(role: str = "manager") -> dict:
        from app.security.jwt import create_access_token
        from db.models import User

        n = next(_counter)
        with get_session_factory()() as s:
            u = User(phone=f"09{n:09d}", full_name=f"{role}-{n}", role=role)
            s.add(u)
            s.commit()
            return {"Authorization": f"Bearer {create_access_token(u.id, u.role)}"}

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
        "/api/v1/members", json={"phone": "09120001111", "full_name": "aud"}, headers=reception
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
        "/api/v1/members", json={"phone": "09120002222", "full_name": "face"}, headers=coach
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
        "/api/v1/members", json={"phone": "09120003333", "full_name": "prog"}, headers=coach
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


def test_otp_never_stored_plain(client):
    """R-002 — کد OTP خام در DB ذخیره نمی‌شود."""
    from db.models import OtpCode

    r = client.post("/api/v1/auth/otp/request", json={"phone": "09120004444"})
    code = r.json()["dev_code"]
    with get_session_factory()() as s:
        row = s.query(OtpCode).filter_by(phone="09120004444").first()
        assert row is not None
        assert code not in row.code_hash
        assert "$" in row.code_hash
