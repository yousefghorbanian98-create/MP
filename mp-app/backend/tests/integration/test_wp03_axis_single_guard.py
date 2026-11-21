"""WP 0.3 / F-13 — هر درخواست فقط یک بار گارد مجوز را اجرا کند.

پیش از اصلاح: `POST /axis-assessments/{id}/review` دو گارد `permission`
داشت (یکی روی روتر، یکی روی پارامتر تابع) و به‌ازای هر درخواست دو بار
`security.rbac.enforce` اجرا می‌شد. بعد از اصلاح باید دقیقاً یک بار باشد.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import settings

from ._actors import create_actor


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/wp03.db")
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


def test_review_route_runs_permission_guard_exactly_once(client, monkeypatch):
    import security.rbac as rbac

    calls: list[tuple[str, str, str]] = []
    real_enforce = rbac.enforce

    def counting_enforce(role: str, path: str, method: str) -> bool:
        if path.endswith("/review"):
            calls.append((role, path, method))
        return real_enforce(role, path, method)

    monkeypatch.setattr(rbac, "enforce", counting_enforce)

    headers = create_actor("manager")
    res = client.post(
        "/api/v1/axis-assessments/999999/review",
        json={"action": "reject"},
        headers=headers,
    )
    # بازبینی بدون دلیل پذیرفته نیست؛ مهم این است که گارد دقیقاً یک‌بار اجرا شود.
    assert res.status_code in (400, 404, 422)
    assert len(calls) == 1, f"گارد مجوز برای یک درخواست {len(calls)} بار اجرا شد"
