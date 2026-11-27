"""MEM-04 / PWA-33 — دسترسی عضو به برنامه، صریح و fail-closed.

چرا این فایل جدا از `test_ownership.py` است: آن تست مالکیت را کلی می‌سنجد و فقط
مسیر `/programs/member/{id}` را پوشش می‌دهد. MEM-04 روی همین مسیرها یک صفحهٔ
محصول می‌سازد، پس نیاز به شاهدی هست که هر چهار مسیرِ مصرف‌شده را نام ببرد:
`/programs/member/{id}`، `/readiness`، `/volume` و `/programs/{program_id}`.

قاعده: برنامهٔ عضو A نباید با شناسهٔ عضو B خوانده شود — نه فهرست، نه آمادگی، نه
حجم، نه جزئیات برنامهٔ B. پاسخ باید 403 باشد، نه 200 با دادهٔ خالی.
"""

from __future__ import annotations

import itertools

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture()
def client(tmp_path):
    from app.config import settings
    from cache.store import InMemoryCache, reset_cache
    from db.base import init_db, reset_engine
    from modules.auth.router import limiter

    settings.database_url = f"sqlite:///{tmp_path / 'mem04.db'}"
    reset_engine()
    init_db()
    app = create_app()
    app.state.limiter = limiter
    limiter.reset()
    reset_cache(InMemoryCache())
    with TestClient(app) as c:
        yield c
    limiter.reset()


_counter = itertools.count(200_000)


def _member(client, role: str = "member") -> tuple[dict, int]:
    """کاربر با نقش + عضو متصل؛ شناسهٔ عضو از DB می‌آید، نه از کلاینت."""
    from app.security.jwt import create_access_token
    from db.base import get_session_factory
    from db.models import Member, User

    n = next(_counter)
    with get_session_factory()() as s:
        user = User(phone=f"09{n:09d}", full_name=f"member-{n}", role=role)
        s.add(user)
        s.commit()
        s.refresh(user)
        member = Member(user_id=user.id, goal="hypertrophy", gender="male")
        s.add(member)
        s.commit()
        s.refresh(member)
        token = create_access_token(user.id, user.role)
        member_id = member.id
    return {"Authorization": f"Bearer {token}"}, member_id


def _approved_program(client, member_id: int) -> int:
    """برنامهٔ واقعی برای عضو B از همان endpoint سرور ساخته می‌شود."""
    from db.base import get_session_factory
    from db.models import ProgramWeek, WorkoutProgram

    with get_session_factory()() as s:
        program = WorkoutProgram(
            member_id=member_id,
            coach_id=None,
            status="approved",
            goal="hypertrophy",
            engine_version="rules-2.3.0",
            llm_explanation="",
            reject_reason="",
        )
        s.add(program)
        s.commit()
        s.refresh(program)
        s.add(ProgramWeek(program_id=program.id, week_number=1, focus="پایه"))
        s.commit()
        return program.id


def test_member_a_cannot_read_member_b_program_routes(client):
    _, member_b = _member(client)
    program_id = _approved_program(client, member_b)
    headers_a, member_a = _member(client)
    assert member_a != member_b

    forbidden = [
        f"/api/v1/programs/member/{member_b}",
        f"/api/v1/programs/member/{member_b}/readiness",
        f"/api/v1/programs/member/{member_b}/volume",
        f"/api/v1/programs/{program_id}",
    ]
    for url in forbidden:
        response = client.get(url, headers=headers_a)
        assert response.status_code == 403, f"GET {url} → {response.status_code} (باید ۴۰۳)"


def test_member_a_reads_own_program_and_readiness(client):
    """کنترل مثبت: همان مسیرها برای دادهٔ خودِ عضو کار می‌کنند (۴۰۳ یک خطای عمومی نیست)."""
    headers_a, member_a = _member(client)
    _approved_program(client, member_a)

    listing = client.get(f"/api/v1/programs/member/{member_a}", headers=headers_a)
    assert listing.status_code == 200
    body = listing.json()
    assert len(body) == 1
    # هر عددی که UI نشان می‌دهد از همین پاسخ می‌آید.
    assert body[0]["engine_version"] == "rules-2.3.0"
    assert body[0]["status"] == "approved"

    readiness = client.get(f"/api/v1/programs/member/{member_a}/readiness", headers=headers_a)
    assert readiness.status_code == 200
    payload = readiness.json()
    # بدون بازخورد ست، آمادگی «سنجیده نشد» است؛ عدد جعلی ساخته نمی‌شود.
    assert payload["readiness"] is None
    assert payload["reason"]
    assert payload["rule_version"]


def test_anonymous_member_program_route_is_401_or_403(client):
    _, member_b = _member(client)
    response = client.get(f"/api/v1/programs/member/{member_b}")
    assert response.status_code in (401, 403)
