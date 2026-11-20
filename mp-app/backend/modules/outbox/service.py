"""سرویس outbox — ثبت در تراکنش، claim انحصاری، retry با backoff، dead-letter.

`relay_once` یک batch را claim می‌کند، به handler می‌دهد و نتیجه را ثبت می‌کند.
handler پیش‌فرض فقط لاگ می‌کند؛ اتصال واقعی push/SMS در لایهٔ زیرساخت است و
در این مخزن شاهد اجرایی ندارد (`BLOCKED`).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.logging import get_logger
from db.models import OutboxDeadLetter, OutboxEvent

log = get_logger("outbox")

MAX_ATTEMPTS = 5
BACKOFF_SECONDS = (30, 120, 600, 1800)


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def enqueue(
    db: Session,
    topic: str,
    payload: dict | None = None,
    *,
    dedup_key: str | None = None,
    available_at: datetime | None = None,
    commit: bool = True,
) -> OutboxEvent:
    """ثبت رویداد؛ با `dedup_key` تکراری، همان ردیف برمی‌گردد (idempotent)."""
    if dedup_key:
        existing = db.scalar(select(OutboxEvent).where(OutboxEvent.dedup_key == dedup_key))
        if existing is not None:
            return existing
    event = OutboxEvent(
        topic=topic,
        payload=json.dumps(payload or {}, ensure_ascii=False),
        dedup_key=dedup_key,
        status="pending",
        attempts=0,
        available_at=available_at or datetime.now(UTC),
    )
    db.add(event)
    db.flush()
    if commit:
        db.commit()
        db.refresh(event)
    return event


def claim_batch(db: Session, *, limit: int = 50, now: datetime | None = None) -> list[OutboxEvent]:
    """claimِ انحصاری: ابتدا UPDATE شرطی، سپس خواندن همان شناسه‌ها."""
    moment = now or datetime.now(UTC)
    ids = list(
        db.scalars(
            select(OutboxEvent.id)
            .where(OutboxEvent.status == "pending", OutboxEvent.available_at <= moment)
            .order_by(OutboxEvent.id)
            .limit(limit)
        )
    )
    claimed: list[OutboxEvent] = []
    for event_id in ids:
        result = db.execute(
            update(OutboxEvent)
            .where(OutboxEvent.id == event_id, OutboxEvent.status == "pending")
            .values(status="sending")
        )
        if result.rowcount == 1:
            row = db.get(OutboxEvent, event_id)
            if row is not None:
                claimed.append(row)
    return claimed


def reclaim_stale(
    db: Session, *, older_than_seconds: int = 300, now: datetime | None = None
) -> int:
    """رویدادهای `sending` که worker رهایشان کرده را برمی‌گرداند (crash-safe)."""
    moment = now or datetime.now(UTC)
    rows = list(db.scalars(select(OutboxEvent).where(OutboxEvent.status == "sending")))
    reclaimed = 0
    for row in rows:
        # تازه claim شده و هنوز در مهلت است؛ دست نزن.
        age = (moment - _aware(row.available_at)).total_seconds()
        if age < older_than_seconds:
            continue
        row.status = "pending"
        reclaimed += 1
    return reclaimed


def relay_once(
    db: Session,
    *,
    handler: Callable[[OutboxEvent], None] | None = None,
    limit: int = 50,
) -> dict:
    """یک دور ارسال؛ خروجی شمارش sent/retried/dead."""
    send = handler or (lambda event: log.info("outbox_dispatch", topic=event.topic))
    batch = claim_batch(db, limit=limit)
    sent = retried = dead = 0
    for event in batch:
        try:
            send(event)
        except Exception as exc:  # noqa: BLE001 — هر خطای handler باید ثبت شود
            _mark_failed(db, event, f"{type(exc).__name__}: {exc}")
            if event.status == "dead":
                dead += 1
            else:
                retried += 1
            continue
        event.status = "sent"
        event.sent_at = datetime.now(UTC)
        sent += 1
    db.flush()
    return {"sent": sent, "retried": retried, "dead": dead}


def _mark_failed(db: Session, event: OutboxEvent, error: str) -> None:
    event.attempts += 1
    event.last_error = error[:1000]
    if event.attempts >= MAX_ATTEMPTS:
        event.status = "dead"
        db.add(
            OutboxDeadLetter(
                outbox_id=event.id,
                topic=event.topic,
                payload=event.payload,
                attempts=event.attempts,
                last_error=event.last_error,
            )
        )
        return
    event.status = "pending"
    delay = BACKOFF_SECONDS[min(event.attempts - 1, len(BACKOFF_SECONDS) - 1)]
    event.available_at = datetime.now(UTC) + timedelta(seconds=delay)


def pending_count(db: Session, topic: str | None = None) -> int:
    stmt = select(OutboxEvent.id).where(OutboxEvent.status == "pending")
    if topic:
        stmt = stmt.where(OutboxEvent.topic == topic)
    return len(list(db.scalars(stmt)))


def dead_letter_count(db: Session) -> int:
    return len(list(db.scalars(select(OutboxDeadLetter.id))))
