"""M46-c5 — ماتریس امنیتی: هر ترکیب نقش × مسیر باید پاسخ درست بدهد.

سه خطای کلاسیک که این تست قفل می‌کند:
  ۱) endpoint بدون احراز هویت (۴۰۱ نمی‌دهد)
  ۲) عضو عادی که به مسیر اداری می‌رسد (۴۰۳ نمی‌دهد)
  ۳) توکن با امضای جعلی که پذیرفته می‌شود
"""

from __future__ import annotations

import itertools

import pytest
from fastapi.testclient import TestClient

from app.config import settings

_counter = itertools.count(990001)

ADMIN_ONLY = [
    "/api/v1/admin/kpis",
    "/api/v1/admin/flags",
    "/api/v1/admin/audit",
    "/api/v1/admin/members-summary",
    "/api/v1/admin/checkins?limit=10",
]

# /admin/users فقط برای مالک سیستم است (super_admin) — نه admin
SUPER_ADMIN_ONLY = ["/api/v1/admin/users"]


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/sec.db")
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


def _headers(role: str) -> dict:
    from app.security.jwt import create_access_token
    from db.base import get_session_factory
    from db.models import User

    n = next(_counter)
    with get_session_factory()() as s:
        u = User(phone=f"09{n:09d}", full_name=f"{role}-{n}", role=role)
        s.add(u)
        s.commit()
        return {"Authorization": f"Bearer {create_access_token(u.id, u.role)}"}


@pytest.mark.parametrize("path", ADMIN_ONLY)
def test_admin_routes_reject_anonymous(client: TestClient, path: str) -> None:
    assert client.get(path).status_code == 401


@pytest.mark.parametrize("path", ADMIN_ONLY)
def test_admin_routes_reject_member(client: TestClient, path: str) -> None:
    assert client.get(path, headers=_headers("member")).status_code == 403


@pytest.mark.parametrize("path", ADMIN_ONLY)
def test_admin_routes_allow_admin(client: TestClient, path: str) -> None:
    assert client.get(path, headers=_headers("admin")).status_code == 200


@pytest.mark.parametrize("path", SUPER_ADMIN_ONLY)
def test_super_admin_only_routes(client: TestClient, path: str) -> None:
    assert client.get(path).status_code == 401
    assert client.get(path, headers=_headers("member")).status_code == 403
    assert client.get(path, headers=_headers("admin")).status_code == 403
    assert client.get(path, headers=_headers("super_admin")).status_code == 200


def test_forged_unsigned_token_rejected(client: TestClient) -> None:
    """توکن alg=none نباید پذیرفته شود — کلاسیک‌ترین حملهٔ JWT."""
    forged = "eyJhbGciOiJub25lIn0.eyJzdWIiOiIxIiwicm9sZSI6ImFkbWluIn0."
    r = client.get("/api/v1/admin/kpis", headers={"Authorization": f"Bearer {forged}"})
    assert r.status_code == 401


def test_wrong_signature_rejected(client: TestClient) -> None:
    """امضای جعلی روی payload معتبر."""
    import jwt

    forged = jwt.encode({"sub": "1", "role": "admin"}, "wrong-key", algorithm="HS256")
    r = client.get("/api/v1/admin/kpis", headers={"Authorization": f"Bearer {forged}"})
    assert r.status_code == 401


def test_security_headers_present(client: TestClient) -> None:
    r = client.get("/health")
    h = {k.lower(): v for k, v in r.headers.items()}
    assert h.get("x-content-type-options") == "nosniff"
    assert h.get("x-frame-options") == "DENY"
    assert "frame-ancestors 'none'" in h.get("content-security-policy", "")
    assert h.get("referrer-policy") == "no-referrer"


def test_cors_does_not_allow_wildcard(client: TestClient) -> None:
    """مبدأ ناشناس نباید allow-origin بگیرد."""
    r = client.get("/health", headers={"Origin": "http://evil.example"})
    assert r.headers.get("access-control-allow-origin") in (None, "")


def test_approve_records_real_coach_not_zero(client: TestClient) -> None:
    """M46-c4 — پیش‌تر approved_by=0 بود (TODO رهاشده). حالا باید JWT واقعی باشد."""
    from db.base import get_session_factory
    from db.models import User, WorkoutProgram

    h = _headers("admin")
    n = next(_counter)
    created = client.post(
        "/api/v1/members",
        json={"phone": f"09{n:09d}", "full_name": f"عضو {n}", "gender": "male"},
        headers=h,
    )
    assert created.status_code in (200, 201), created.text
    mid = created.json()["id"]  # شناسهٔ عضو، نه شناسهٔ کاربر
    r = client.post(
        "/api/v1/ai/program/generate",
        json={
            "member_id": mid,
            "goal": "hypertrophy",
            "level": "beginner",
            "days_per_week": 3,
            "weeks_count": 2,
            "constraints": [],
        },
        headers=h,
    )
    assert r.status_code == 200, r.text
    pid = r.json()["id"]

    body = client.post(f"/api/v1/programs/{pid}/approve", headers=h).json()
    assert body["status"] == "approved"
    assert body["approved_by"] is not None and body["approved_by"] != 0

    with get_session_factory()() as s:
        row = s.get(WorkoutProgram, pid)
        assert row.approved_by is not None and row.approved_by != 0
        assert s.get(User, row.approved_by) is not None, "approved_by باید به کاربر موجود اشاره کند"
