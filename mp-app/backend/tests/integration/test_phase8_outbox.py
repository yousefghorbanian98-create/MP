"""فاز ۸ (QF-20) — outbox تراکنشی: رویداد پول در همان commitِ پول.

# قرارداد

| مورد | قاعده |
|---|---|
| ثبت | رویداد در **همان تراکنش** عملیات مالی ساخته می‌شود (`commit=False` تا انتها) |
| rollback | اگر عملیات مالی شکست بخورد، رویدادی منتشر نمی‌شود |
| dedup | کلید یکتا؛ ثبت دوبارهٔ همان رویداد ردیف دوم نمی‌سازد |
| claim | هر رویداد یک‌بار به یک worker داده می‌شود (وضعیت `sending`) |
| retry | خطای handler ← attempts+1 و `available_at` آینده؛ پس از سقف، `dead` |
| ارسال | `sent` فقط پس از موفقیت handler |

# چرا این‌جا و نه فقط در «صف کارها»

اسناد پروژه می‌گوید هر dispatch ممکن است تکراری باشد؛ پس گیت اصلی،
**at-least-once + idempotent consumer** است، نه «دقیقاً یک‌بار». این تست
همان مرز را می‌سنجد و ادعای exactly-once نمی‌کند.

# آنچه تست نمی‌کند
- چند پردازش موازی روی PostgreSQL (اینجا SQLite در یک فرایند است).
- تحویل واقعی به push/SMS (`BLOCKED`: بدون سرویس بیرونی).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from db.base import get_session_factory
from db.models import Member, OutboxDeadLetter, OutboxEvent, User
from modules.outbox.service import (
    claim_batch,
    enqueue,
    pending_count,
    reclaim_stale,
    relay_once,
)
from tests.integration._actors import create_actor


def _member() -> tuple[int, dict]:
    from app.security.jwt import create_access_token

    with get_session_factory()() as s:
        user = User(
            phone=f"0951{abs(hash(datetime.now(UTC).isoformat())) % 10**7:07d}",
            full_name="عضو صندوق",
            role="member",
        )
        s.add(user)
        s.commit()
        member = Member(user_id=user.id, goal="hypertrophy", constraints="[]")
        s.add(member)
        s.commit()
        token = create_access_token(user.id, user.role)
        return member.id, {"Authorization": f"Bearer {token}"}


def _card_payment_in_review(client: TestClient, member_h: dict, member_id: int) -> int:
    import io

    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (16, 16), (10, 10, 10)).save(buf, format="PNG")
    res = client.post(
        "/api/v1/payments",
        json={"member_id": member_id, "amount_rial": 1_500_000, "method": "card_to_card"},
        headers=member_h,
    )
    payment_id = res.json()["id"]
    up = client.post(
        f"/api/v1/payments/{payment_id}/receipt",
        files={"file": ("r.png", buf.getvalue(), "image/png")},
        headers=member_h,
    )
    assert up.status_code == 202, up.text
    return payment_id


def test_payment_approval_enqueues_event_in_the_same_transaction(client: TestClient) -> None:
    member_id, member_h = _member()
    payment_id = _card_payment_in_review(client, member_h, member_id)
    staff_h = create_actor("manager", ["finance.write"])

    res = client.post(f"/api/v1/payments/{payment_id}/approve", json={}, headers=staff_h)
    assert res.status_code == 200, res.text

    with get_session_factory()() as s:
        events = s.query(OutboxEvent).filter(OutboxEvent.topic == "payment.approved").all()
        assert len(events) == 1
        assert str(payment_id) in events[0].payload
        assert events[0].status == "pending"


def test_rejected_approval_leaves_no_event(client: TestClient) -> None:
    member_id, member_h = _member()
    # یک پرداخت در صف بازبینی هم می‌سازیم تا ثابت شود رویداد فقط برای تأییدِ
    # موفق ساخته می‌شود، نه برای هر پرداخت کارت‌به‌کارت.
    _card_payment_in_review(client, member_h, member_id)
    creator_h = create_actor("manager", ["finance.write"])
    # سازندهٔ پرداخت همان کسی است که تلاش می‌کند تأیید کند → ۴۰۳ و rollback.
    res = client.post(
        "/api/v1/payments",
        json={"member_id": member_id, "amount_rial": 900_000, "method": "card_to_card"},
        headers=creator_h,
    )
    own_payment = res.json()["id"]
    up = client.post(
        f"/api/v1/payments/{own_payment}/receipt",
        files={"file": ("r.png", _png(), "image/png")},
        headers=member_h,
    )
    assert up.status_code == 202, up.text

    denied = client.post(f"/api/v1/payments/{own_payment}/approve", json={}, headers=creator_h)
    assert denied.status_code == 403
    with get_session_factory()() as s:
        assert s.query(OutboxEvent).filter(OutboxEvent.topic == "payment.approved").count() == 0


def _png() -> bytes:
    import io

    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (16, 16), (200, 40, 40)).save(buf, format="PNG")
    return buf.getvalue()


def test_enqueue_is_idempotent_by_dedup_key(session) -> None:
    first = enqueue(session, "payment.approved", {"payment_id": 1}, dedup_key="pay-1-approved")
    second = enqueue(session, "payment.approved", {"payment_id": 1}, dedup_key="pay-1-approved")
    session.commit()
    assert first.id == second.id
    assert pending_count(session, "payment.approved") == 1


def test_claim_is_exclusive_and_relay_marks_sent(session) -> None:
    enqueue(session, "member.welcome", {"member_id": 7})
    enqueue(session, "member.welcome", {"member_id": 8})
    session.commit()

    # claim انحصاری: دستهٔ دوم چیزی نمی‌گیرد تا اولین دسته رها شود.
    claimed = claim_batch(session, limit=10)
    assert len(claimed) == 2
    assert {row.status for row in claimed} == {"sending"}
    assert claim_batch(session, limit=10) == []
    # مسیر crash-safe: claim رهاشده برمی‌گردد.
    assert reclaim_stale(session, older_than_seconds=0) == 2
    session.commit()

    sent: list[str] = []
    result = relay_once(session, handler=lambda event: sent.append(str(event.id)))
    session.commit()
    assert result["sent"] == 2 and result["dead"] == 0 and result["retried"] == 0
    assert len(sent) == 2
    assert session.query(OutboxEvent).filter(OutboxEvent.status == "sent").count() == 2


def test_failures_retry_then_dead_letter(session) -> None:
    event = enqueue(session, "payment.approved", {"payment_id": 42}, dedup_key="dead-1")
    session.commit()

    def boom(_event):
        raise RuntimeError("downstream down")

    for _ in range(5):
        relay_once(session, handler=boom, limit=1)
        session.commit()
        # برای آزمون بدون sleep، زمان در دسترس را به عقب می‌بریم.
        row = session.get(OutboxEvent, event.id)
        if row.status == "pending":
            row.available_at = datetime.now(UTC) - timedelta(seconds=1)
            session.commit()

    row = session.get(OutboxEvent, event.id)
    assert row.status == "dead"
    assert row.attempts == 5
    assert (
        session.query(OutboxDeadLetter).filter(OutboxDeadLetter.outbox_id == event.id).count() == 1
    )
