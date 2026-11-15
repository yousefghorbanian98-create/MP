"""گیت M45-c2 — فهرست برنامه‌های باشگاه برای استودیو (وضعیت گردش کاری + مربی).

صفحهٔ «برنامه‌ها» تا امروز از دادهٔ ساختگی استفاده می‌کرد. این endpoint دادهٔ
واقعی می‌دهد: هر برنامه با status واقعی، موتور قواعد و نام عضو.
"""

from __future__ import annotations

import itertools
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.config import settings

_counter = itertools.count(960001)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/progs.db")
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


def _seed_program(status: str) -> int:
    from db.base import get_session_factory
    from db.models import Member, User, WorkoutProgram

    n = next(_counter)
    with get_session_factory()() as s:
        u = User(phone=f"09{n:09d}", full_name="عضو برنامه", role="member")
        s.add(u)
        s.commit()
        m = Member(user_id=u.id, goal="hypertrophy", constraints="[]", gender="male")
        s.add(m)
        s.commit()
        p = WorkoutProgram(
            member_id=m.id,
            status=status,
            goal="hypertrophy",
            engine_version="rules-1.0",
            approved_at=datetime.now(UTC) if status == "approved" else None,
        )
        s.add(p)
        s.commit()
        return p.id


def test_programs_list_requires_auth(client: TestClient) -> None:
    assert client.get("/api/v1/programs").status_code in (401, 403)


def test_programs_list_rejects_member(client: TestClient) -> None:
    assert client.get("/api/v1/programs", headers=_headers("member")).status_code == 403


def test_programs_list_returns_real_rows(client: TestClient) -> None:
    _seed_program("draft")
    _seed_program("approved")
    res = client.get("/api/v1/programs", headers=_headers("coach"))
    assert res.status_code == 200
    body = res.json()
    assert body["rule_version"]
    statuses = {row["status"] for row in body["items"]}
    assert {"draft", "approved"} <= statuses
    row = next(r for r in body["items"] if r["status"] == "draft")
    assert row["engine_version"] == "rules-1.0"
    assert row["member_name"]


def test_programs_list_filters_by_status(client: TestClient) -> None:
    _seed_program("draft")
    _seed_program("approved")
    res = client.get("/api/v1/programs?status=approved", headers=_headers("coach"))
    assert res.status_code == 200
    assert all(r["status"] == "approved" for r in res.json()["items"])


def test_programs_list_empty_is_empty_not_fabricated(client: TestClient) -> None:
    res = client.get("/api/v1/programs", headers=_headers("coach"))
    assert res.status_code == 200
    assert res.json()["items"] == []
