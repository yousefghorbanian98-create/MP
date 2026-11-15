"""گیت M45-c2 — جریان ورودهای اخیر باشگاه (نمای زندهٔ چک‌این استودیو).

صفحهٔ «چک‌این» تا امروز فهرست ساختگی نشان می‌داد. این endpoint چک‌این‌های
واقعی را با نام عضو، روش (qr/face/manual)، نتیجه و زمان برمی‌گرداند.
"""

from __future__ import annotations

import itertools
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.config import settings

_counter = itertools.count(970001)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/feed.db")
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


def _seed_checkin(*, result: str = "ok", method: str = "qr", minutes_ago: int = 5) -> int:
    from db.base import get_session_factory
    from db.models import CheckIn, Member, User

    n = next(_counter)
    with get_session_factory()() as s:
        u = User(phone=f"09{n:09d}", full_name=f"عضو {n}", role="member")
        s.add(u)
        s.commit()
        m = Member(user_id=u.id, goal="hypertrophy", constraints="[]", gender="male")
        s.add(m)
        s.commit()
        c = CheckIn(
            member_id=m.id,
            method=method,
            result=result,
            denial_reason="" if result == "ok" else "اشتراک منقضی",
            created_at=datetime.now(UTC) - timedelta(minutes=minutes_ago),
        )
        s.add(c)
        s.commit()
        return c.id


def test_feed_requires_auth(client: TestClient) -> None:
    assert client.get("/api/v1/admin/checkins").status_code in (401, 403)


def test_feed_rejects_member(client: TestClient) -> None:
    assert client.get("/api/v1/admin/checkins", headers=_headers("member")).status_code == 403


def test_feed_returns_real_rows_newest_first(client: TestClient) -> None:
    _seed_checkin(minutes_ago=30)
    recent = _seed_checkin(minutes_ago=2)
    res = client.get("/api/v1/admin/checkins?limit=10", headers=_headers("coach"))
    assert res.status_code == 200
    body = res.json()
    assert body["rule_version"]
    assert body["items"][0]["checkin_id"] == recent, "جدیدترین ورود اول"
    assert body["items"][0]["member_name"]
    assert body["items"][0]["method"] == "qr"


def test_feed_keeps_denied_entries_visible(client: TestClient) -> None:
    """ورود رد‌شده باید دیده شود — پنهان‌کردنش یعنی گزارش ناقص."""
    _seed_checkin(result="denied", minutes_ago=3)
    body = client.get("/api/v1/admin/checkins", headers=_headers("coach")).json()
    denied = [i for i in body["items"] if i["result"] == "denied"]
    assert len(denied) == 1
    assert denied[0]["denial_reason"]


def test_feed_empty_is_empty_not_fabricated(client: TestClient) -> None:
    body = client.get("/api/v1/admin/checkins", headers=_headers("coach")).json()
    assert body["items"] == []
