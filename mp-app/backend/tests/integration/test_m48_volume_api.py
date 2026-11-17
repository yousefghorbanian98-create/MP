"""G2 — گزارش حجم هفتگی از دادهٔ واقعی برنامه + بازخورد (M48-c2)."""

from __future__ import annotations

import itertools

import pytest
from fastapi.testclient import TestClient

from app.config import settings

_counter = itertools.count(971001)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/vol.db")
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


def _staff() -> dict:
    from app.security.jwt import create_access_token
    from db.base import get_session_factory
    from db.models import User

    n = next(_counter)
    with get_session_factory()() as s:
        u = User(phone=f"09{n:09d}", full_name=f"coach-{n}", role="manager")
        s.add(u)
        s.commit()
        return {"Authorization": f"Bearer {create_access_token(u.id, u.role)}"}


def _member_with_program(client: TestClient, h: dict) -> tuple[int, int]:
    n = next(_counter)
    m = client.post(
        "/api/v1/members",
        json={"phone": f"09{n:09d}", "full_name": f"عضو {n}", "gender": "male"},
        headers=h,
    )
    mid = m.json()["id"]
    p = client.post(
        "/api/v1/ai/program/generate",
        json={
            "member_id": mid,
            "goal": "hypertrophy",
            "level": "beginner",
            "days_per_week": 3,
            "weeks_count": 4,
            "constraints": [],
        },
        headers=h,
    )
    return mid, p.json()["id"]


def test_volume_report_uses_planned_sets_when_no_feedback(client: TestClient) -> None:
    h = _staff()
    mid, pid = _member_with_program(client, h)

    r = client.get(f"/api/v1/programs/member/{mid}/volume", headers=h)

    assert r.status_code == 200, r.text
    body = r.json()
    assert body["program_id"] == pid
    assert body["muscles"], "باید حداقل یک گروه عضلانی داشته باشد"
    for m in body["muscles"]:
        assert m["data_state"] == "no_feedback"
        assert m["source_of_number"] == "planned"
        assert m["effective_sets"] == m["planned_sets"]
        assert m["landmarks"]["rule_version"] == "volume-landmarks-1.0"
        assert "Israetel" in m["landmarks"]["source"]


def test_feedback_switches_source_to_reported_hard_sets(client: TestClient) -> None:
    h = _staff()
    mid, _pid = _member_with_program(client, h)

    # یک ست سخت + یک ست راحت برای همان حرکت
    client.post(
        "/api/v1/programs/set-feedback",
        json={
            "member_id": mid,
            "entries": [
                {
                    "movement_id": "اسکوات پشت",
                    "weight": 60,
                    "target_reps": 10,
                    "reps_done": 10,
                    "rir": 1,
                    "soreness": 2,
                },
                {
                    "movement_id": "اسکوات پشت",
                    "weight": 60,
                    "target_reps": 10,
                    "reps_done": 10,
                    "rir": 5,
                    "soreness": 2,
                },
            ],
        },
        headers=h,
    )

    body = client.get(f"/api/v1/programs/member/{mid}/volume", headers=h).json()
    squats = [m for m in body["muscles"] if m["muscle"] == "quads"]
    assert squats, f"گروه quads باید حاضر باشد؛ موجود: {[m['muscle'] for m in body['muscles']]}"
    q = squats[0]
    assert q["data_state"] == "reported"
    assert q["source_of_number"] == "reported_hard_sets"
    assert q["hard_sets"] == 1
    assert q["soft_sets"] == 1
    assert q["effective_sets"] == 1


def test_no_program_returns_empty_not_error(client: TestClient) -> None:
    h = _staff()
    n = next(_counter)
    m = client.post(
        "/api/v1/members",
        json={"phone": f"09{n:09d}", "full_name": f"بی‌برنامه {n}", "gender": "female"},
        headers=h,
    )
    mid = m.json()["id"]

    r = client.get(f"/api/v1/programs/member/{mid}/volume", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["muscles"] == []
    assert "هیچ برنامه‌ای" in body["reason"]


def test_member_cannot_read_another_members_volume(client: TestClient) -> None:
    h = _staff()
    mid, _ = _member_with_program(client, h)

    from app.security.jwt import create_access_token
    from db.base import get_session_factory
    from db.models import User

    n = next(_counter)
    with get_session_factory()() as s:
        u = User(phone=f"09{n:09d}", full_name=f"other-{n}", role="member")
        s.add(u)
        s.commit()
        other = {"Authorization": f"Bearer {create_access_token(u.id, u.role)}"}

    r = client.get(f"/api/v1/programs/member/{mid}/volume", headers=other)
    assert r.status_code == 403


def test_pool_capacity_covers_threadpool() -> None:
    """M48-c2 — ظرفیت استخر باید تردهای anyio را بپوشاند، نه کمتر.

    کشف واقعی: با ۱۰+۳۰ ظرفیت و ۴۰۰ کاربر، لاگ پر شد از
      QueuePool limit reached ... timed out
    و p50 از ۴ms به ۱۹۰ms رفت — صف اتصال، نه کندی کد.
    این تست جلوی برگشت آن رگرسیون را می‌گیرد.
    """
    from db import base as db_base

    total = db_base._POOL_SIZE + db_base._MAX_OVERFLOW
    # anyio پیش‌فرض ۴۰ ترد برای endpointهای sync
    assert total >= 40, f"ظرفیت استخر {total} از تعداد تردها کمتر است"
    assert db_base._POOL_TIMEOUT <= 10, "انتظار طولانی، درخواست را معلق می‌کند نه خطا"


def test_volume_endpoint_is_cheap_enough_to_serve_under_load(client: TestClient) -> None:
    """محاسبهٔ حجم نباید سنگین باشد؛ اگر شد، استخر زیر بار خالی می‌شود."""
    import time

    h = _staff()
    mid, _ = _member_with_program(client, h)

    client.get(f"/api/v1/programs/member/{mid}/volume", headers=h)  # warm-up
    samples = []
    for _ in range(20):
        t0 = time.perf_counter()
        r = client.get(f"/api/v1/programs/member/{mid}/volume", headers=h)
        samples.append((time.perf_counter() - t0) * 1000)
        assert r.status_code == 200

    samples.sort()
    p50 = samples[len(samples) // 2]
    assert p50 < 150, f"p50 مسیر حجم {p50:.0f}ms است — بهینه‌سازی لازم دارد"


def test_secret_key_meets_rfc7518_minimum() -> None:
    """M48-c2 — کلید HMAC کمتر از ۳۲ بایت، هشدار PyJWT در هر درخواست می‌داد.

    آن هشدار در لاگ تولید هم می‌آمد. مقدار پیش‌فرض ۳۱ بایت بود (یک کاراکتر کم).
    """
    from app.config import MIN_SECRET_BYTES, settings

    assert len(settings.secret_key.encode("utf-8")) >= MIN_SECRET_BYTES


def test_production_refuses_default_secret() -> None:
    """کلید توسعه نباید بتواند به production برسد — در زمان راه‌اندازی می‌شکند."""
    import os
    from unittest.mock import patch

    from app.config import DEFAULT_DEV_SECRET, Settings

    with patch.dict(os.environ, {"MP_ENVIRONMENT": "production"}, clear=False):
        with pytest.raises(Exception) as exc:
            Settings(secret_key=DEFAULT_DEV_SECRET)
        assert "کلید" in str(exc.value)
