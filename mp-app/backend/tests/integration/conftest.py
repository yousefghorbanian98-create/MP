"""فیکسچرهای مشترک تست‌های یکپارچه.

چرا این فایل اضافه شد: `client` و `auth` داخل `test_api_contract.py` تعریف شده
بودند، یعنی هر فایل جدید مجبور بود همان بلوک را کپی کند یا خطای
«fixture 'client' not found» بگیرد (M61). ماژول‌هایی که تعریف خودشان را دارند
همان را می‌گیرند — این فایل فقط پیش‌فرض مشترک می‌دهد.
"""

from __future__ import annotations

import itertools

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from db.base import get_session_factory, init_db, reset_engine

_counter = itertools.count(10_000)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from app.config import settings
    from modules.auth.router import limiter

    db_url = f"sqlite:///{tmp_path}/shared_test.db"
    monkeypatch.setattr(settings, "database_url", db_url)
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
