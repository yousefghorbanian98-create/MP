"""jobهای زمان‌بندی‌شده (APScheduler) — یادآوری تمدید، بازآزمایی ۶–۸ هفته، انقضای اشتراک.

هر job یک تابع خالص/قابل تست است؛ زمان‌بندی فقط wrapper است.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.logging import get_logger
from db.models import Assessment14Domain, Member, Membership, Notification

log = get_logger("jobs")

RENEWAL_REMINDER_DAYS = 7
REASSESSMENT_MIN_WEEKS = 6
REASSESSMENT_MAX_WEEKS = 8


def expire_memberships(db: Session, now: datetime | None = None) -> int:
    """اشتراک‌های منقضی‌شده را expired می‌کند. خروجی: تعداد تغییر."""
    now = now or datetime.now(UTC)
    count = 0
    for ms in db.scalars(select(Membership).where(Membership.status == "active")):
        expires = ms.expires_at if ms.expires_at.tzinfo else ms.expires_at.replace(tzinfo=UTC)
        if expires <= now:
            ms.status = "expired"
            count += 1
    if count:
        db.commit()
        log.info("memberships_expired", count=count)
    return count


def send_renewal_reminders(db: Session, now: datetime | None = None) -> int:
    """یادآوری تمدید برای اشتراک‌های رو به انقضا (≤ ۷ روز) — هر عضو حداکثر یک بار در دوره."""
    now = now or datetime.now(UTC)
    horizon = now + timedelta(days=RENEWAL_REMINDER_DAYS)
    sent = 0
    for ms in db.scalars(select(Membership).where(Membership.status == "active")):
        expires = ms.expires_at if ms.expires_at.tzinfo else ms.expires_at.replace(tzinfo=UTC)
        if now < expires <= horizon:
            already = db.scalar(
                select(Notification).where(
                    Notification.member_id == ms.member_id,
                    Notification.kind == "renewal",
                    Notification.body.contains(str(ms.id)),
                )
            )
            if already is None:
                db.add(
                    Notification(
                        member_id=ms.member_id,
                        title="یادآوری تمدید اشتراک",
                        body=f"اشتراک شما تا چند روز دیگر به پایان می‌رسد (شناسهٔ اشتراک {ms.id}).",
                        kind="renewal",
                    )
                )
                sent += 1
    if sent:
        db.commit()
        log.info("renewal_reminders_sent", count=sent)
    return sent


def send_reassessment_reminders(db: Session, now: datetime | None = None) -> int:
    """یادآوری بازآزمایی ارزیابی در پنجرهٔ ۶–۸ هفته پس از آخرین ارزیابی."""
    now = now or datetime.now(UTC)
    sent = 0
    for member in db.scalars(select(Member)):
        last = db.scalar(
            select(Assessment14Domain)
            .where(Assessment14Domain.member_id == member.id)
            .order_by(Assessment14Domain.id.desc())
            .limit(1)
        )
        if last is None:
            continue
        created = last.created_at if last.created_at.tzinfo else last.created_at.replace(tzinfo=UTC)
        weeks = (now - created).days / 7
        if REASSESSMENT_MIN_WEEKS <= weeks <= REASSESSMENT_MAX_WEEKS:
            already = db.scalar(
                select(Notification).where(
                    Notification.member_id == member.id,
                    Notification.kind == "reassessment",
                    Notification.body.contains(str(last.id)),
                )
            )
            if already is None:
                db.add(
                    Notification(
                        member_id=member.id,
                        title="زمان بازآزمایی فرا رسیده",
                        body=f"ارزیابی شما (شناسهٔ {last.id}) بیش از ۶ هفته پیش انجام شده است.",
                        kind="reassessment",
                    )
                )
                sent += 1
    if sent:
        db.commit()
        log.info("reassessment_reminders_sent", count=sent)
    return sent


def build_scheduler(session_factory) -> BackgroundScheduler:  # noqa: F821
    """ساخت APScheduler با jobهای روزانه."""
    from apscheduler.schedulers.background import BackgroundScheduler

    scheduler = BackgroundScheduler(timezone="UTC")

    def _with_session(fn):
        def _run():
            db = session_factory()
            try:
                fn(db)
            finally:
                db.close()

        return _run

    scheduler.add_job(
        _with_session(expire_memberships), "cron", hour=0, minute=5, id="expire_memberships"
    )
    scheduler.add_job(
        _with_session(send_renewal_reminders), "cron", hour=8, minute=0, id="renewal_reminders"
    )
    scheduler.add_job(
        _with_session(send_reassessment_reminders),
        "cron",
        hour=8,
        minute=30,
        id="reassessment_reminders",
    )
    return scheduler
