"""تست‌های regression بازبینی REA (2026-11-15) — باگ‌های واقعی پیداشده و فیکس‌شده.

- باگ ۱: `require_roles` شامل super_admin نبود ← مالک سیستم از گزارش‌ها/کلاس‌ها قفل می‌شد.
- باگ ۲: `/population` برای عضو بسته بود ← فرم ورودی کلاینت (intake) ۴۰۳ می‌گرفت.
"""

from __future__ import annotations

import itertools

import pytest
from fastapi.testclient import TestClient

from app.config import settings

_counter = itertools.count(950001)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/rea.db")
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


def test_super_admin_not_locked_out_by_require_roles(client) -> None:
    """باگ ۱ — super_admin باید به مسیرهای require_roles دسترسی داشته باشد."""
    h = _headers("super_admin")
    # گزارش‌ها (require_roles admin/coach)
    res = client.get("/api/v1/population/paths", headers=h)
    assert res.status_code == 200, res.text
    # قرارداد بدنهٔ JSON با Flutter
    res = client.post("/api/v1/population/gate-check", json={"path": "adult"}, headers=h)
    assert res.status_code == 200, res.text


def test_member_intake_flow_not_blocked(client) -> None:
    """باگ ۲ — عضو باید بتواند فرم ورودی خودش را کامل کند (gate-check + intake/next)."""
    h = _headers("member")
    res = client.post("/api/v1/population/gate-check", json={"path": "adult"}, headers=h)
    assert res.status_code == 200, res.text
    res = client.post(
        "/api/v1/population/intake/next",
        json={"goal": "hypertrophy", "constraints": [], "answered_ids": []},
        headers=h,
    )
    assert res.status_code == 200, res.text


def test_require_roles_still_blocks_unknown_role(client) -> None:
    """hardening — guard بعد از فیکس همچنان نقش ناشناخته/غیرمجاز را رد می‌کند."""
    h = _headers("member")
    # گزارش محرمانه: فقط admin/coach — عضو نباید ببیند
    res = client.get("/api/v1/reports/confidential/1", headers=h)
    assert res.status_code == 403
