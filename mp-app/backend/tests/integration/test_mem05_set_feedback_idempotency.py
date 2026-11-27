"""MEM-05 / PWA-34 — آزمون idempotency نوشتن بازخورد ست.

پرسش گیت MEM-05 این بود: «آیا `POST /programs/set-feedback` شناسهٔ یکتا/نسخه
می‌گیرد یا فقط append می‌کند؟» پاسخ با فایل/خط: کلید ندارد (`modules/programs/
schemas.py:103-106` + `service.py:183-197`) ⇒ هر ارسال یک ردیف تازه.

این فایل دو چیز را با اجرا ثابت می‌کند:
1. مسیر بدون کلید **واقعاً** رکورد تکراری می‌سازد (پس UI نباید از آن استفاده کند).
2. مسیر `POST /programs/sync/set-feedback` با `device_id:client_id` + `updated_at`
   idempotent است: ارسال دوبارهٔ همان نوشته ردیف تازه نمی‌سازد و به‌صورت
   `unchanged` گزارش می‌شود؛ نوشتهٔ جدیدتر همان ردیف را به‌روز می‌کند؛ نوشتهٔ
   قدیمی‌تر رد می‌شود.
"""

from __future__ import annotations

import itertools

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

_counter = itertools.count(300_000)


@pytest.fixture()
def client(tmp_path):
    from app.config import settings
    from cache.store import InMemoryCache, reset_cache
    from db.base import init_db, reset_engine
    from modules.auth.router import limiter

    settings.database_url = f"sqlite:///{tmp_path / 'mem05.db'}"
    reset_engine()
    init_db()
    app = create_app()
    app.state.limiter = limiter
    limiter.reset()
    reset_cache(InMemoryCache())
    with TestClient(app) as c:
        yield c
    limiter.reset()


def _member(client) -> tuple[dict, int, int]:
    """(headers, member_id, program_id) — همه از DB و API واقعی، نه mock."""
    from app.security.jwt import create_access_token
    from db.base import get_session_factory
    from db.models import Member, User, WorkoutProgram

    n = next(_counter)
    with get_session_factory()() as s:
        user = User(phone=f"09{n:09d}", full_name=f"member-{n}", role="member")
        s.add(user)
        s.commit()
        s.refresh(user)
        member = Member(user_id=user.id, goal="hypertrophy", gender="male")
        s.add(member)
        s.commit()
        s.refresh(member)
        program = WorkoutProgram(
            member_id=member.id,
            status="approved",
            goal="hypertrophy",
            engine_version="rules-2.3.0",
            llm_explanation="",
            reject_reason="",
        )
        s.add(program)
        s.commit()
        s.refresh(program)
        token = create_access_token(user.id, user.role)
        return {"Authorization": f"Bearer {token}"}, member.id, program.id


def _rows(member_id: int) -> list[tuple]:
    from sqlalchemy import select

    from db.base import get_session_factory
    from db.models import SetFeedback

    with get_session_factory()() as s:
        rows = s.scalars(select(SetFeedback).where(SetFeedback.member_id == member_id)).all()
        return [(r.id, r.movement_id, r.weight, r.client_id, r.device_id) for r in rows]


def _item(*, client_id: str, program_id: int, updated_at: str, weight: float = 80.0) -> dict:
    return {
        "client_id": client_id,
        "device_id": "device-ci-1",
        "updated_at": updated_at,
        "program_id": program_id,
        "movement_id": "bench_press",
        "weight": weight,
        "target_reps": 8,
        "reps_done": 8,
        "rir": 2,
        "soreness": 1,
        "notes": "",
    }


def test_unkeyed_set_feedback_endpoint_duplicates_on_retry(client):
    """مسیر بدون کلید: همان درخواست دوبار ⇒ دو ردیف. این دلیل استفاده‌نکردن از آن است."""
    headers, member_id, program_id = _member(client)
    body = {
        "member_id": member_id,
        "program_id": program_id,
        "entries": [
            {
                "movement_id": "bench_press",
                "weight": 80,
                "target_reps": 8,
                "reps_done": 8,
                "rir": 2,
                "soreness": 1,
            }
        ],
    }

    first = client.post("/api/v1/programs/set-feedback", json=body, headers=headers)
    assert first.status_code == 200
    second = client.post("/api/v1/programs/set-feedback", json=body, headers=headers)
    assert second.status_code == 200

    rows = _rows(member_id)
    assert len(rows) == 2, "قرارداد بدون کلید عمداً idempotent نیست؛ این سنجه است، نه باگ جدید"
    assert all(row[3] is None and row[4] is None for row in rows)  # client_id/device_id ثبت نمی‌شوند


def test_sync_set_feedback_is_idempotent_for_the_same_write(client):
    headers, member_id, program_id = _member(client)
    item = _item(client_id="set-abc-1", program_id=program_id, updated_at="2026-11-27T10:00:00Z")

    first = client.post(
        "/api/v1/programs/sync/set-feedback",
        json={"member_id": member_id, "items": [item]},
        headers=headers,
    )
    assert first.status_code == 200
    payload = first.json()
    assert payload["applied_keys"] == ["device-ci-1:set-abc-1"]

    # همان نوشته، دوباره (تلاش مجدد شبکه یا دوبار کلیک)
    second = client.post(
        "/api/v1/programs/sync/set-feedback",
        json={"member_id": member_id, "items": [item]},
        headers=headers,
    )
    assert second.status_code == 200
    repeated = second.json()
    assert repeated["applied_keys"] == []
    assert repeated["unchanged_keys"] == ["device-ci-1:set-abc-1"]

    rows = _rows(member_id)
    assert len(rows) == 1, "ارسال دوباره نباید ردیف تازه بسازد"
    assert rows[0][3] == "set-abc-1"
    assert rows[0][4] == "device-ci-1"


def test_newer_client_timestamp_updates_the_same_row_and_older_one_is_rejected(client):
    headers, member_id, program_id = _member(client)
    item = _item(client_id="set-abc-2", program_id=program_id, updated_at="2026-11-27T10:00:00Z")
    client.post(
        "/api/v1/programs/sync/set-feedback",
        json={"member_id": member_id, "items": [item]},
        headers=headers,
    )

    newer = _item(
        client_id="set-abc-2",
        program_id=program_id,
        updated_at="2026-11-27T11:00:00Z",
        weight=85.0,
    )
    applied = client.post(
        "/api/v1/programs/sync/set-feedback",
        json={"member_id": member_id, "items": [newer]},
        headers=headers,
    ).json()
    assert applied["applied_keys"] == ["device-ci-1:set-abc-2"]

    older = _item(
        client_id="set-abc-2",
        program_id=program_id,
        updated_at="2026-11-27T09:00:00Z",
        weight=70.0,
    )
    rejected = client.post(
        "/api/v1/programs/sync/set-feedback",
        json={"member_id": member_id, "items": [older]},
        headers=headers,
    ).json()

    rows = _rows(member_id)
    assert len(rows) == 1
    assert rows[0][2] == 85.0, "نوشتهٔ جدیدتر همان ردیف را بازنویسی می‌کند"
    # نوشتهٔ قدیمی‌تر بی‌صدا دور ریخته نمی‌شود؛ با action صریح گزارش می‌شود.
    assert "device-ci-1:set-abc-2" not in rejected["applied_keys"]


def test_a_different_device_with_the_same_client_key_is_a_different_row(client):
    """کلید سرور `device_id:client_id` است؛ صف دو دستگاه نباید روی هم بیفتد."""
    headers, member_id, program_id = _member(client)
    first = _item(client_id="set-shared", program_id=program_id, updated_at="2026-11-27T10:00:00Z")
    second = dict(first)
    second["device_id"] = "device-ci-2"

    for item in (first, second):
        response = client.post(
            "/api/v1/programs/sync/set-feedback",
            json={"member_id": member_id, "items": [item]},
            headers=headers,
        )
        assert response.status_code == 200

    rows = _rows(member_id)
    assert len(rows) == 2
    assert {row[4] for row in rows} == {"device-ci-1", "device-ci-2"}


def test_sync_write_denies_another_members_id(client):
    """نوشتن برای عضو دیگر باید ۴۰۳ بدهد، نه ردیف یتیم."""
    _, other_member, other_program = _member(client)
    headers, _, _ = _member(client)

    response = client.post(
        "/api/v1/programs/sync/set-feedback",
        json={
            "member_id": other_member,
            "items": [
                _item(
                    client_id="set-forbidden",
                    program_id=other_program,
                    updated_at="2026-11-27T10:00:00Z",
                )
            ],
        },
        headers=headers,
    )
    assert response.status_code == 403
    assert _rows(other_member) == []
