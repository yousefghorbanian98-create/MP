"""سلامت و متریک صف outbox (QF-27).

# چرا heartbeat جداست از «آخرین ارسال»

صفِ خالی با worker مرده از بیرون یکی به نظر می‌رسد: هیچ خطایی نیست و هیچ
رویدادی هم ارسال نمی‌شود. heartbeat می‌گوید worker **زنده** است، حتی وقتی
کاری برای انجام دادن نیست. کهنگی heartbeat = worker مرده، نه «بی‌کار».

# چرا فقط عدد در متریک

`/metrics` بی‌احراز هویت می‌تواند خونده شود؛ پس payload رویداد، متن خطا و
شناسهٔ مالی هرگز آن‌جا نمی‌آید. فقط شمارش و سن.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from db.models import OutboxDeadLetter, OutboxEvent, WorkerHeartbeat

DEFAULT_STALE_AFTER_SECONDS = 300


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def heartbeat(
    db: Session,
    *,
    worker_key: str = "outbox",
    result: dict | None = None,
    now: datetime | None = None,
    commit: bool = False,
) -> WorkerHeartbeat:
    """ثبت حیات worker؛ ردیف موجود به‌روز می‌شود، نه تکثیر."""
    moment = now or datetime.now(UTC)
    row = db.scalar(select(WorkerHeartbeat).where(WorkerHeartbeat.worker_key == worker_key))
    payload = json.dumps(result or {}, ensure_ascii=False)
    if row is None:
        row = WorkerHeartbeat(
            worker_key=worker_key,
            started_at=moment,
            last_seen_at=moment,
            last_result=payload,
        )
        db.add(row)
    else:
        row.last_seen_at = moment
        row.last_result = payload
    db.flush()
    if commit:
        db.commit()
    return row


def worker_status(
    db: Session,
    *,
    worker_key: str = "outbox",
    now: datetime | None = None,
    stale_after_seconds: int = DEFAULT_STALE_AFTER_SECONDS,
) -> dict:
    moment = now or datetime.now(UTC)
    row = db.scalar(select(WorkerHeartbeat).where(WorkerHeartbeat.worker_key == worker_key))
    if row is None:
        return {
            "worker_key": worker_key,
            "ok": False,
            "age_seconds": None,
            "reason": "no_heartbeat",
        }
    seen = _aware(row.last_seen_at) or moment
    age = max(0, int((moment - seen).total_seconds()))
    return {
        "worker_key": worker_key,
        "ok": age <= stale_after_seconds,
        "age_seconds": age,
        "reason": "fresh" if age <= stale_after_seconds else "stale",
    }


def queue_stats(db: Session, *, now: datetime | None = None) -> dict:
    """شمارش وضعیت‌ها و سن قدیمی‌ترین رویداد در انتظار."""
    moment = now or datetime.now(UTC)
    counts = dict(
        db.execute(
            select(OutboxEvent.status, func.count(OutboxEvent.id)).group_by(OutboxEvent.status)
        ).all()
    )
    dead_letters = db.scalar(select(func.count(OutboxDeadLetter.id))) or 0
    oldest = db.scalar(
        select(func.min(OutboxEvent.created_at)).where(
            OutboxEvent.status.in_(("pending", "sending"))
        )
    )
    oldest_aware = _aware(oldest)
    return {
        "pending": int(counts.get("pending", 0)),
        "sending": int(counts.get("sending", 0)),
        "sent": int(counts.get("sent", 0)),
        "dead": int(counts.get("dead", 0)),
        "dead_letters": int(dead_letters),
        # سن منفی معنا ندارد (ساعت سیستم/دادهٔ ساختگی)؛ صفر = «تازه».
        "oldest_pending_age_seconds": max(0, int((moment - oldest_aware).total_seconds()))
        if oldest_aware
        else 0,
    }


def refresh_metrics(db: Session, *, now: datetime | None = None) -> dict:
    """مقادیر فعلی را به gaugeها می‌نویسد؛ خروجی برای لاگ/تست."""
    from app.metrics import metrics

    stats = queue_stats(db, now=now)
    metrics.set_gauge("mp_outbox_pending", stats["pending"])
    metrics.set_gauge("mp_outbox_sending", stats["sending"])
    metrics.set_gauge("mp_outbox_dead", stats["dead"])
    metrics.set_gauge("mp_outbox_dead_letters", stats["dead_letters"])
    metrics.set_gauge("mp_outbox_oldest_pending_seconds", stats["oldest_pending_age_seconds"])
    status = worker_status(db, now=now)
    metrics.set_gauge("mp_outbox_worker_stale", 0 if status["ok"] else 1)
    return stats
