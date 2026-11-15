"""G8 — چت مربی–شاگرد (M51-c1).

مهم‌ترین چیزی که این تست‌ها محافظت می‌کنند: **فرستنده از توکن می‌آید، نه از
بدنهٔ درخواست**. اگر از بدنه بیاید، هر کسی می‌تواند خودش را مربی جا بزند
و پیام‌های «تأییدشده» بسازد.
"""

from __future__ import annotations

import itertools

import pytest
from fastapi.testclient import TestClient

from app.config import settings

_counter = itertools.count(975001)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/chat.db")
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


def _user(role: str) -> tuple[dict, int]:
    from app.security.jwt import create_access_token
    from db.base import get_session_factory
    from db.models import User

    n = next(_counter)
    with get_session_factory()() as s:
        u = User(phone=f"09{n:09d}", full_name=f"{role}-{n}", role=role)
        s.add(u)
        s.commit()
        return {"Authorization": f"Bearer {create_access_token(u.id, u.role)}"}, u.id


def _member_for(user_id: int, gender: str = "male") -> int:
    """عضو متصل به کاربر — تا نقش member بتواند گفتگوی خودش را ببیند."""
    from db.base import get_session_factory
    from db.models import Member

    with get_session_factory()() as s:
        m = Member(user_id=user_id, gender=gender, goal="hypertrophy", branch_id=1)
        s.add(m)
        s.commit()
        return m.id


def _any_member(gender: str = "male") -> int:
    """عضو مستقل با کاربر واقعی — برای مواردی که خود عضو لاگین نمی‌کند."""
    _, uid = _user("member")
    return _member_for(uid, gender)


def _conversation(client: TestClient, h: dict, member_id: int, coach_id: int | None = None) -> int:
    r = client.post(
        "/api/v1/chat/conversations",
        json={"member_id": member_id, "coach_id": coach_id, "subject": "سوال برنامه"},
        headers=h,
    )
    assert r.status_code == 200, r.text
    return r.json()["id"]


def test_open_and_send_roundtrip(client: TestClient) -> None:
    h, uid = _user("manager")
    mid = _any_member()
    conv = _conversation(client, h, mid)

    r = client.post(
        f"/api/v1/chat/conversations/{conv}/messages",
        json={"body": "برنامهٔ هفتهٔ دوم را دیدم، ممنون."},
        headers=h,
    )
    assert r.status_code == 200, r.text
    msg = r.json()
    assert msg["body"] == "برنامهٔ هفتهٔ دوم را دیدم، ممنون."
    assert msg["sender_id"] == uid
    assert msg["sender_role"] == "coach"
    assert msg["read_at"] is None, "پیام تازه نباید خوانده‌شده علامت بخورد"

    listing = client.get(f"/api/v1/chat/conversations/{conv}/messages", headers=h).json()
    assert len(listing["messages"]) == 1


def test_sender_is_taken_from_token_not_body(client: TestClient) -> None:
    """تلاش برای جعل فرستنده باید بی‌اثر باشد."""
    h, uid = _user("manager")
    mid = _any_member()
    conv = _conversation(client, h, mid)

    r = client.post(
        f"/api/v1/chat/conversations/{conv}/messages",
        json={"body": "تست", "sender_id": 999999, "sender_role": "member"},
        headers=h,
    )
    assert r.status_code == 200
    assert r.json()["sender_id"] == uid
    assert r.json()["sender_role"] == "coach"


def test_member_sees_own_conversation_and_staff_sees_reply(client: TestClient) -> None:
    mh, muid = _user("member")
    ch, cuid = _user("manager")
    mid = _member_for(muid)
    conv = _conversation(client, ch, mid, coach_id=cuid)

    client.post(
        f"/api/v1/chat/conversations/{conv}/messages",
        json={"body": "سلام، زانویم درد می‌کند."},
        headers=mh,
    )
    staff_view = client.get(f"/api/v1/chat/conversations/{conv}/messages", headers=ch).json()
    assert staff_view["messages"][0]["sender_role"] == "member"
    assert staff_view["unread_count"] == 1

    client.post(
        f"/api/v1/chat/conversations/{conv}/messages",
        json={"body": "اسکوات را با پرس پا عوض کن."},
        headers=ch,
    )

    member_view = client.get(f"/api/v1/chat/conversations/{conv}/messages", headers=mh).json()
    assert len(member_view["messages"]) == 2
    assert member_view["messages"][1]["sender_role"] == "coach"
    assert member_view["unread_count"] == 1


def test_mark_read_clears_unread(client: TestClient) -> None:
    mh, muid = _user("member")
    ch, cuid = _user("manager")
    mid = _member_for(muid)
    conv = _conversation(client, ch, mid, coach_id=cuid)

    client.post(f"/api/v1/chat/conversations/{conv}/messages", json={"body": "پیام"}, headers=mh)

    before = client.get(f"/api/v1/chat/conversations/{conv}/messages", headers=ch).json()
    assert before["unread_count"] == 1

    marked = client.post(f"/api/v1/chat/conversations/{conv}/read", headers=ch).json()
    assert marked["marked_read"] == 1

    after = client.get(f"/api/v1/chat/conversations/{conv}/messages", headers=ch).json()
    assert after["unread_count"] == 0


def test_member_cannot_read_someone_elses_conversation(client: TestClient) -> None:
    ch, cuid = _user("manager")
    ah, auid = _user("member")
    _member_for(auid)
    victim_mid = _any_member()
    conv = _conversation(client, ch, victim_mid, coach_id=cuid)

    assert client.get(f"/api/v1/chat/conversations/{conv}/messages", headers=ah).status_code == 403
    assert (
        client.post(
            f"/api/v1/chat/conversations/{conv}/messages",
            json={"body": "سلام"},
            headers=ah,
        ).status_code
        == 403
    )


def test_other_coach_cannot_read_or_write(client: TestClient) -> None:
    ch, cuid = _user("manager")
    oh, _ = _user("manager")
    victim_mid = _any_member()
    conv = _conversation(client, ch, victim_mid, coach_id=cuid)

    assert client.get(f"/api/v1/chat/conversations/{conv}/messages", headers=oh).status_code == 403
    assert (
        client.post(
            f"/api/v1/chat/conversations/{conv}/messages", json={"body": "سلام"}, headers=oh
        ).status_code
        == 403
    )


def test_empty_message_is_rejected(client: TestClient) -> None:
    h, _ = _user("manager")
    mid = _any_member()
    conv = _conversation(client, h, mid)

    r = client.post(f"/api/v1/chat/conversations/{conv}/messages", json={"body": "   "}, headers=h)
    assert r.status_code == 400
    assert "empty_message" in r.text


def test_overlong_message_is_rejected(client: TestClient) -> None:
    h, _ = _user("manager")
    mid = _any_member()
    conv = _conversation(client, h, mid)

    r = client.post(
        f"/api/v1/chat/conversations/{conv}/messages", json={"body": "x" * 2001}, headers=h
    )
    assert r.status_code == 422  # Pydantic max_length


def test_missing_conversation_is_404(client: TestClient) -> None:
    h, _ = _user("manager")
    assert client.get("/api/v1/chat/conversations/999999/messages", headers=h).status_code == 404


def test_conversation_list_is_scoped_per_role(client: TestClient) -> None:
    ch, cuid = _user("manager")
    mh, muid = _user("member")
    mid = _member_for(muid)
    conv = _conversation(client, ch, mid, coach_id=cuid)

    staff = client.get("/api/v1/chat/conversations", headers=ch).json()
    assert [c["id"] for c in staff] == [conv]

    member = client.get("/api/v1/chat/conversations", headers=mh).json()
    assert [c["id"] for c in member] == [conv]

    other, _ = _user("manager")
    assert client.get("/api/v1/chat/conversations", headers=other).json() == []


def test_last_message_at_is_updated(client: TestClient) -> None:
    h, _ = _user("manager")
    mid = _any_member()
    conv = _conversation(client, h, mid)

    before = client.get("/api/v1/chat/conversations", headers=h).json()[0]
    assert before["last_message_at"] is None

    client.post(f"/api/v1/chat/conversations/{conv}/messages", json={"body": "پیام"}, headers=h)

    after = client.get("/api/v1/chat/conversations", headers=h).json()[0]
    assert after["last_message_at"] is not None


def test_member_role_has_chat_policy() -> None:
    """M51-c1 — کشف: نقش member هیچ policy برای /chat نداشت.

    نتیجه: عضوی که چت را باز می‌کرد، در POST پیام ۴۰۳ می‌گرفت. یعنی چت
    عملاً برای شاگرد کار نمی‌کرد — همان کاربری که باید استفاده کند.
    این تست جلوی برگشت رگرسیون RBAC را می‌گیرد.
    """
    from security.rbac import enforce

    assert enforce("member", "/api/v1/chat/conversations", "GET")
    assert enforce("member", "/api/v1/chat/conversations", "POST")
    assert enforce("member", "/api/v1/chat/conversations/5/messages", "GET")
    assert enforce("member", "/api/v1/chat/conversations/5/messages", "POST")
    assert enforce("member", "/api/v1/chat/conversations/5/read", "POST")
    assert enforce("coach", "/api/v1/chat/conversations", "GET")
    assert enforce("coach", "/api/v1/chat/conversations/5/messages", "POST")


def test_member_chat_scope_is_not_a_wildcard_escape() -> None:
    """دامنهٔ member برای چت نباید به مسیرهای دیگر سرایت کند."""
    from security.rbac import enforce

    # عضو نباید بتواند گفتگوی دیگران را با شناسه حدس بزند (مالکیت در سرویس)
    # ولی مهم‌تر: نباید policy عمومی مدیریتی بگیرد.
    assert not enforce("member", "/api/v1/admin/kpis", "GET")
    assert not enforce("member", "/api/v1/admin/users", "GET")
