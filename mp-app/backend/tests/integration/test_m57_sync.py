"""G7 — همگام‌سازی صف آفلاین روی API واقعی.

سناریوی واقعی: کاربر در باشگاه بدون اینترنت سه ست ثبت می‌کند، بعد
وصل می‌شود و صف ارسال می‌شود. تست‌ها این مسیر را با تعارض واقعی
(دو دستگاه، ساعت متفاوت) می‌سنجند.
"""

from __future__ import annotations

import itertools
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.config import settings

_counter = itertools.count(979001)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/sync.db")
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


def _member() -> int:
    from db.base import get_session_factory
    from db.models import Member, User

    n = next(_counter)
    with get_session_factory()() as s:
        u = User(phone=f"09{n:09d}", full_name=f"m{n}", role="member")
        s.add(u)
        s.commit()
        m = Member(user_id=u.id, gender="male", goal="x", branch_id=1)
        s.add(m)
        s.commit()
        return m.id


def _staff() -> dict:
    from app.security.jwt import create_access_token
    from db.base import get_session_factory
    from db.models import User

    n = next(_counter)
    with get_session_factory()() as s:
        u = User(phone=f"09{n:09d}", full_name=f"c{n}", role="manager")
        s.add(u)
        s.commit()
        return {"Authorization": f"Bearer {create_access_token(u.id, u.role)}"}


def _item(client_id: str, device: str, minutes_ago: int = 0, reps: int = 10) -> dict:
    return {
        "client_id": client_id,
        "device_id": device,
        "updated_at": (datetime.now(UTC) - timedelta(minutes=minutes_ago)).isoformat(),
        "movement_id": "squat",
        "weight": 80.0,
        "target_reps": 10,
        "reps_done": reps,
        "rir": 2,
        "soreness": 3,
        "notes": "",
    }


def _sync(client: TestClient, h: dict, mid: int, items: list[dict]) -> dict:
    r = client.post(
        "/api/v1/programs/sync/set-feedback",
        json={"member_id": mid, "items": items},
        headers=h,
    )
    assert r.status_code == 200, r.text
    return r.json()


def test_offline_queue_is_applied_in_order(client: TestClient) -> None:
    h = _staff()
    mid = _member()

    result = _sync(
        client,
        h,
        mid,
        [_item("a1", "phone-1", 30), _item("a2", "phone-1", 20), _item("a3", "phone-1", 10)],
    )
    assert result["member_id"] == mid
    assert result["counts"]["received"] == 3
    assert result["unchanged_keys"] == []
    assert result["counts"]["applied"] == 3
    assert result["counts"]["rejected"] == 0

    from db.base import get_session_factory
    from db.models import SetFeedback

    with get_session_factory()() as s:
        rows = s.query(SetFeedback).filter(SetFeedback.member_id == mid).all()
        assert len(rows) == 3
        assert all(r.device_id == "phone-1" for r in rows)


def test_resending_the_same_queue_is_idempotent(client: TestClient) -> None:
    """قطعی شبکهٔ موبایل: صف دوباره فرستاده می‌شود — نباید رکورد تکراری بسازد."""
    h = _staff()
    mid = _member()
    items = [_item("b1", "phone-1", 10)]

    _sync(client, h, mid, items)
    second = _sync(client, h, mid, items)

    assert second["counts"]["applied"] == 0
    assert second["counts"]["rejected"] == 1
    # همان نوشتهٔ قبلی دوباره رسیده: نه اعمال دوباره، نه «رد» گمراه‌کننده
    assert second["results"][0]["action"] == "conflict_resolved"
    assert second["unchanged_keys"] == ["phone-1:b1"]

    from db.base import get_session_factory
    from db.models import SetFeedback

    with get_session_factory()() as s:
        assert s.query(SetFeedback).filter(SetFeedback.member_id == mid).count() == 1


def test_newer_edit_from_same_device_updates_the_row(client: TestClient) -> None:
    h = _staff()
    mid = _member()

    _sync(client, h, mid, [_item("c1", "phone-1", 20, reps=8)])
    updated = _sync(client, h, mid, [_item("c1", "phone-1", 5, reps=11)])

    assert updated["counts"]["applied"] == 1

    from db.base import get_session_factory
    from db.models import SetFeedback

    with get_session_factory()() as s:
        rows = s.query(SetFeedback).filter(SetFeedback.member_id == mid).all()
        assert len(rows) == 1, "ویرایش نباید رکورد تکراری بسازد"
        assert rows[0].reps_done == 11


def test_stale_edit_is_rejected_and_reported(client: TestClient) -> None:
    h = _staff()
    mid = _member()

    _sync(client, h, mid, [_item("d1", "phone-1", 5, reps=12)])
    stale = _sync(client, h, mid, [_item("d1", "phone-1", 60, reps=3)])

    assert stale["counts"]["rejected"] == 1
    assert stale["results"][0]["action"] == "reject_stale"
    assert stale["results"][0]["winner"] == "server"

    from db.base import get_session_factory
    from db.models import SetFeedback

    with get_session_factory()() as s:
        row = s.query(SetFeedback).filter(SetFeedback.member_id == mid).one()
        assert row.reps_done == 12, "نوشتهٔ قدیمی نباید دادهٔ جدید را بازنویسی کند"


def test_future_dated_write_is_rejected_for_clock_skew(client: TestClient) -> None:
    h = _staff()
    mid = _member()
    future = _item("e1", "phone-1")
    future["updated_at"] = (datetime.now(UTC) + timedelta(hours=3)).isoformat()

    result = _sync(client, h, mid, [future])
    assert result["results"][0]["action"] == "reject_clock_skew"
    assert "ساعت" in result["results"][0]["reason"]


def test_two_devices_do_not_clobber_each_other(client: TestClient) -> None:
    h = _staff()
    mid = _member()

    _sync(client, h, mid, [_item("x1", "phone-A", 10)])
    other = _sync(client, h, mid, [_item("x1", "phone-B", 5)])

    assert other["counts"]["applied"] == 1

    from db.base import get_session_factory
    from db.models import SetFeedback

    with get_session_factory()() as s:
        rows = s.query(SetFeedback).filter(SetFeedback.member_id == mid).all()
        assert len(rows) == 2, "کلید رکورد (device_id, client_id) است، نه client_id تنها"
        assert {r.device_id for r in rows} == {"phone-A", "phone-B"}


def test_empty_queue_is_accepted(client: TestClient) -> None:
    h = _staff()
    mid = _member()
    result = _sync(client, h, mid, [])
    assert result["counts"]["received"] == 0
    assert result["results"] == []


def test_member_cannot_sync_for_another_member(client: TestClient) -> None:
    from app.security.jwt import create_access_token
    from db.base import get_session_factory
    from db.models import Member, User

    _staff()  # نقش مربی در این تست استفاده نمی‌شود
    victim = _member()

    n = next(_counter)
    with get_session_factory()() as s:
        u = User(phone=f"09{n:09d}", full_name="intruder", role="member")
        s.add(u)
        s.commit()
        s.add(Member(user_id=u.id, gender="male", goal="x", branch_id=1))
        s.commit()
        ih = {"Authorization": f"Bearer {create_access_token(u.id, 'member')}"}

    r = client.post(
        "/api/v1/programs/sync/set-feedback",
        json={"member_id": victim, "items": [_item("z1", "attacker")]},
        headers=ih,
    )
    assert r.status_code == 403


def test_queue_over_500_is_rejected_by_schema(client: TestClient) -> None:
    h = _staff()
    mid = _member()
    r = client.post(
        "/api/v1/programs/sync/set-feedback",
        json={"member_id": mid, "items": [_item(f"q{i}", "d") for i in range(501)]},
        headers=h,
    )
    assert r.status_code == 422


def test_response_never_silently_drops_a_write(client: TestClient) -> None:
    """هر آیتم ارسالی باید دقیقاً یک نتیجه داشته باشد."""
    h = _staff()
    mid = _member()
    items = [_item(f"m{i}", "phone-1", i * 3) for i in range(5)]
    result = _sync(client, h, mid, items)
    assert len(result["results"]) == len(items)
    assert result["counts"]["applied"] + result["counts"]["rejected"] == len(items)
    assert result["note"]


def test_member_role_has_sync_policy() -> None:
    from security.rbac import enforce

    assert enforce("member", "/api/v1/programs/sync/set-feedback", "POST")


def test_synced_feedback_links_to_the_program(client: TestClient) -> None:
    """باگ E2E: بازخورد آفلاین هیچ‌گاه به برنامه وصل نمی‌شد.

    نتیجه: G13 برای همان شاگرد می‌گفت «هیچ بازخورد ستی برای این برنامه
    ثبت نشده». یعنی چرخهٔ بازخورد در حالت آفلاین **بسته نمی‌شد** — دقیقاً
    همان حالتی که برای آن طراحی شده بود.
    """
    from db.base import get_session_factory
    from db.models import Member, SetFeedback, User
    from modules.programs.service import create_program_from_engine_output

    h = _staff()
    mid = _member()

    with get_session_factory()() as s:
        program = create_program_from_engine_output(
            s,
            mid,
            {
                "goal": "hypertrophy",
                "engine_version": "t",
                "weeks": [
                    {
                        "week_number": 1,
                        "exercises": [
                            {
                                "exercise_id": 1,
                                "day": 1,
                                "order": 0,
                                "sets": 3,
                                "reps": "8-12",
                                "movement": "squat",
                            }
                        ],
                    }
                ],
            },
        )
        program_id = program.id

    item = _item("p1", "phone-1", 10)
    item["program_id"] = program_id
    client.post(
        "/api/v1/programs/sync/set-feedback",
        json={"member_id": mid, "items": [item]},
        headers=h,
    )

    with get_session_factory()() as s:
        row = s.query(SetFeedback).filter(SetFeedback.member_id == mid).one()
        assert row.program_id == program_id

    readiness = client.get(f"/api/v1/programs/member/{mid}/readiness", headers=h).json()
    assert readiness["readiness"] is not None, readiness["reason"]
    assert readiness["data_counts"]["feedback_rows"] >= 1

    _ = (Member, User)
