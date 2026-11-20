"""سرویس notification — اعلان‌ها."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import NotFoundError
from db.models import Member, Notification


def send(
    db: Session,
    member_id: int,
    title: str,
    body: str = "",
    kind: str = "general",
    *,
    commit: bool = True,
) -> Notification:
    """اعلان عضو؛ `commit=False` برای ماندن در همان تراکنشِ عملیات مالی."""
    if db.get(Member, member_id) is None:
        raise NotFoundError("عضو یافت نشد")
    n = Notification(member_id=member_id, title=title, body=body, kind=kind)
    db.add(n)
    if commit:
        db.commit()
        db.refresh(n)
    else:
        db.flush()
    return n


def list_member_notifications(
    db: Session, member_id: int, unread_only: bool = False, user=None
) -> list[Notification]:
    from app.security.ownership import ensure_member_scope

    ensure_member_scope(db, user, member_id)
    stmt = (
        select(Notification)
        .where(Notification.member_id == member_id)
        .order_by(Notification.id.desc())
    )
    if unread_only:
        stmt = stmt.where(Notification.read_at.is_(None))
    return list(db.scalars(stmt))


def mark_read(db: Session, notification_id: int, user=None) -> Notification:
    from app.security.ownership import ensure_member_scope

    n = db.get(Notification, notification_id)
    if n is None:
        raise NotFoundError("اعلان یافت نشد")
    ensure_member_scope(db, user, n.member_id)
    if n.read_at is None:
        n.read_at = datetime.now(UTC)
        db.commit()
        db.refresh(n)
    return n


# ── G11 — یادآوری‌های پویا (reminders-1.0) ──


def member_reminders(db: Session, member_id: int, user=None) -> dict:
    """محاسبهٔ یادآوری‌های یک عضو از دادهٔ واقعی، و ثبت هر یادآوریِ تازه
    به‌عنوان اعلان درون‌برنامه‌ای.

    Idempotency: اگر همان `kind` در ۲۴ ساعت گذشته برای این عضو ثبت شده
    باشد، دوباره ساخته نمی‌شود. بدون این، هر بازخوانی صفحه یک اعلان
    تکراری می‌ساخت.
    """
    from app.security.ownership import ensure_member_scope
    from db.models import Membership, Payment, SetFeedback
    from engine import reminders

    ensure_member_scope(db, user, member_id)
    if db.get(Member, member_id) is None:
        raise NotFoundError("عضو یافت نشد")

    membership = db.scalar(
        select(Membership)
        .where(Membership.member_id == member_id)
        .order_by(Membership.expires_at.desc())
        .limit(1)
    )
    last_feedback = db.scalar(
        select(SetFeedback)
        .where(SetFeedback.member_id == member_id)
        .order_by(SetFeedback.created_at.desc())
        .limit(1)
    )
    pending = db.scalar(
        select(Payment).where(Payment.member_id == member_id, Payment.status == "pending")
    )

    last_assessment = _last_assessment_at(db, member_id)
    result = reminders.plan(
        membership_end=membership.expires_at if membership else None,
        last_workout_at=last_feedback.created_at if last_feedback else None,
        last_assessment_at=last_assessment,
        pending_amount_rial=pending.amount_rial if pending else 0,
    )

    created = _materialize(db, member_id, result["reminders"])
    return {
        "member_id": member_id,
        **result,
        "created_notifications": created,
        "data_sources": {
            "membership": bool(membership),
            "workout_feedback": bool(last_feedback),
            "assessment": last_assessment is not None,
            "pending_payment": pending is not None,
        },
    }


def _last_assessment_at(db: Session, member_id: int):
    from db.models import Assessment14Domain, JacksonPollockMeasurement

    a = db.scalar(
        select(Assessment14Domain)
        .where(Assessment14Domain.member_id == member_id)
        .order_by(Assessment14Domain.created_at.desc())
        .limit(1)
    )
    j = db.scalar(
        select(JacksonPollockMeasurement)
        .where(JacksonPollockMeasurement.member_id == member_id)
        .order_by(JacksonPollockMeasurement.measured_at.desc())
        .limit(1)
    )
    candidates = [x for x in (a.created_at if a else None, j.measured_at if j else None) if x]
    return max(candidates) if candidates else None


def _materialize(db: Session, member_id: int, due: list[dict]) -> int:
    """ثبت یادآوری‌های تازه به‌عنوان اعلان، با جلوگیری از تکرار ۲۴ ساعته."""
    from datetime import timedelta

    now = datetime.now(UTC)
    cutoff = now - timedelta(hours=24)
    created = 0
    for item in due:
        existing = db.scalar(
            select(Notification).where(
                Notification.member_id == member_id,
                Notification.kind == item["key"],
                Notification.created_at >= cutoff,
            )
        )
        if existing is not None:
            continue
        db.add(
            Notification(
                member_id=member_id,
                title=item["title"],
                body=item["body"],
                kind=item["key"],
                channel="inapp",
            )
        )
        created += 1
    if created:
        db.commit()
    return created
