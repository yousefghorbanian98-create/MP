"""G6 — روندنمای JP7 + تفسیر خودکار (M50-c1).

نکتهٔ کلیدی این تست‌ها: `body_fat_pct` عمداً قفل است (D-012). اگر روزی
کسی قفل را باز کند و درصد چربی برگردد، این تست‌ها باید آن را نشان دهند —
چون روند نباید روی عدد تأییدنشده ساخته شود.
"""

from __future__ import annotations

import itertools
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.config import settings

_counter = itertools.count(974001)

SITES = ("chest", "triceps", "subscapular", "suprailiac", "abdomen", "thigh", "calf")


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/jp7.db")
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


def _member(client: TestClient, h: dict) -> int:
    n = next(_counter)
    r = client.post(
        "/api/v1/members",
        json={"phone": f"09{n:09d}", "full_name": f"عضو {n}", "gender": "male"},
        headers=h,
    )
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def _add_measurement(mid: int, *, days_ago: int, folds: dict[str, float]) -> None:
    """درج مستقیم اندازه‌گیری با تاریخ مشخص (endpoint تاریخ نمی‌پذیرد)."""
    import json

    from db.base import get_session_factory
    from db.models import JacksonPollockMeasurement

    with get_session_factory()() as s:
        s.add(
            JacksonPollockMeasurement(
                member_id=mid,
                measured_at=datetime.now(UTC) - timedelta(days=days_ago),
                age=30,
                gender="male",
                skinfolds_mm=json.dumps(folds),
                equation_version="LOCKED:pending-independent-reference",
                branch_id=1,
            )
        )
        s.commit()


def _flat(value: float) -> dict[str, float]:
    return {site: value for site in SITES}


def test_single_measurement_reports_insufficient(client: TestClient) -> None:
    h = _staff()
    mid = _member(client, h)
    _add_measurement(mid, days_ago=10, folds=_flat(10.0))

    body = client.get(f"/api/v1/assessments/jp7/member/{mid}/trend", headers=h).json()

    assert body["data_state"] == "insufficient_measurements"
    assert body["trend"] is None
    assert body["interpretation"]["status"] == "insufficient"
    assert "یک نقطه، روند نیست" in body["interpretation"]["detail"]


def test_zero_measurements_is_not_an_error(client: TestClient) -> None:
    h = _staff()
    mid = _member(client, h)

    r = client.get(f"/api/v1/assessments/jp7/member/{mid}/trend", headers=h)

    assert r.status_code == 200
    assert r.json()["measurements"] == []


def test_decreasing_trend_is_interpreted_as_fat_loss(client: TestClient) -> None:
    h = _staff()
    mid = _member(client, h)
    _add_measurement(mid, days_ago=70, folds=_flat(14.0))
    _add_measurement(mid, days_ago=35, folds=_flat(12.0))
    _add_measurement(mid, days_ago=1, folds=_flat(10.0))

    body = client.get(f"/api/v1/assessments/jp7/member/{mid}/trend", headers=h).json()

    assert body["data_state"] == "trend_available"
    # ۷ نقطه × ۱۴ = ۹۸ → ۷ × ۱۰ = ۷۰ ⇒ −۲۸
    assert body["trend"]["first_sum_mm"] == 98.0
    assert body["trend"]["last_sum_mm"] == 70.0
    assert body["trend"]["delta_mm"] == -28.0
    assert body["interpretation"]["status"] == "decreasing"
    assert "کاهش چربی" in body["interpretation"]["detail"]
    # هشدار تحلیل عضله باید حاضر باشد
    assert "افت قدرت" in body["interpretation"]["detail"]


def test_increasing_trend(client: TestClient) -> None:
    h = _staff()
    mid = _member(client, h)
    _add_measurement(mid, days_ago=60, folds=_flat(8.0))
    _add_measurement(mid, days_ago=1, folds=_flat(11.0))

    body = client.get(f"/api/v1/assessments/jp7/member/{mid}/trend", headers=h).json()

    assert body["trend"]["delta_mm"] == 21.0
    assert body["interpretation"]["status"] == "increasing"
    assert "کالری را بازبینی کنید" in body["interpretation"]["detail"]


def test_change_below_measurement_error_is_stable(client: TestClient) -> None:
    """۱ میلی‌متر اختلاف = خطای کالیپر، نه تغییر واقعی."""
    h = _staff()
    mid = _member(client, h)
    _add_measurement(mid, days_ago=40, folds=_flat(10.0))
    _add_measurement(mid, days_ago=1, folds=_flat(10.14))  # مجموع +۱

    body = client.get(f"/api/v1/assessments/jp7/member/{mid}/trend", headers=h).json()

    assert body["trend"]["delta_mm"] == pytest.approx(1.0, abs=0.2)
    assert body["interpretation"]["status"] == "stable"
    assert "بدون تغییر" in body["interpretation"]["detail"]


def test_biggest_change_site_is_identified(client: TestClient) -> None:
    h = _staff()
    mid = _member(client, h)
    _add_measurement(mid, days_ago=60, folds=_flat(10.0))
    changed = _flat(10.0)
    changed["abdomen"] = 22.0  # +۱۲ در یک ناحیه
    _add_measurement(mid, days_ago=1, folds=changed)

    body = client.get(f"/api/v1/assessments/jp7/member/{mid}/trend", headers=h).json()

    assert body["trend"]["biggest_change_site"] == "abdomen"
    assert body["trend"]["biggest_change_mm"] == 12.0
    assert body["site_deltas"]["abdomen"]["delta_mm"] == 12.0
    assert "abdomen" in body["interpretation"]["suggestion"]


def test_body_fat_stays_locked_and_is_declared(client: TestClient) -> None:
    """E07/D-012 — روند نباید درصد چربی تأییدنشده بسازد یا نمایش دهد."""
    h = _staff()
    mid = _member(client, h)
    _add_measurement(mid, days_ago=40, folds=_flat(12.0))
    _add_measurement(mid, days_ago=1, folds=_flat(11.0))

    body = client.get(f"/api/v1/assessments/jp7/member/{mid}/trend", headers=h).json()

    assert all(p["body_fat_pct"] is None for p in body["measurements"])
    assert "D-012" in body["body_fat_note"]
    assert "قفل" in body["body_fat_note"]


def test_rate_per_week_is_computed_over_the_real_span(client: TestClient) -> None:
    h = _staff()
    mid = _member(client, h)
    _add_measurement(mid, days_ago=28, folds=_flat(12.0))
    _add_measurement(mid, days_ago=0, folds=_flat(8.0))

    body = client.get(f"/api/v1/assessments/jp7/member/{mid}/trend", headers=h).json()

    assert body["trend"]["span_days"] == pytest.approx(28, abs=1)
    # (8*7 - 12*7) / 4 weeks = -28 / 4 = -7 mm/week
    assert body["trend"]["delta_mm_per_week"] == pytest.approx(-7.0, abs=0.6)


def test_member_cannot_read_another_members_trend(client: TestClient) -> None:
    h = _staff()
    mid = _member(client, h)

    from app.security.jwt import create_access_token
    from db.base import get_session_factory
    from db.models import User

    n = next(_counter)
    with get_session_factory()() as s:
        u = User(phone=f"09{n:09d}", full_name=f"other-{n}", role="member")
        s.add(u)
        s.commit()
        other = {"Authorization": f"Bearer {create_access_token(u.id, u.role)}"}

    assert (
        client.get(f"/api/v1/assessments/jp7/member/{mid}/trend", headers=other).status_code == 403
    )
