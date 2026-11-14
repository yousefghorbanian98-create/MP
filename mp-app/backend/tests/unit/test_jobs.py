"""تست‌های jobهای زمان‌بندی‌شده (M05) — انقضا، یادآوری تمدید، بازآزمایی."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from db.models import Assessment14Domain, Member, Membership, Notification, User
from jobs.scheduler import (
    expire_memberships,
    send_reassessment_reminders,
    send_renewal_reminders,
)


def _member_with_membership(session, days: int, status: str = "active"):
    user = User(
        phone=f"0912{abs(hash((days, status))) % 10_000_000:07d}", full_name="t", role="member"
    )
    session.add(user)
    session.flush()
    member = Member(user_id=user.id, goal="g")
    session.add(member)
    session.flush()
    now = datetime.now(UTC)
    ms = Membership(
        member_id=member.id,
        plan_name="m",
        started_at=now - timedelta(days=30),
        expires_at=now + timedelta(days=days),
        status=status,
    )
    session.add(ms)
    session.commit()
    return member, ms


def test_expire_memberships_marks_expired(session):
    _member_with_membership(session, days=-1)
    _member_with_membership(session, days=10)
    count = expire_memberships(session)
    assert count == 1
    statuses = [m.status for m in session.query(Membership).all()]
    assert statuses.count("expired") == 1
    assert statuses.count("active") == 1


def test_renewal_reminder_sent_once(session):
    member, ms = _member_with_membership(session, days=3)
    n1 = send_renewal_reminders(session)
    assert n1 == 1
    n2 = send_renewal_reminders(session)  # اجرای دوباره = یادآوری تکراری ممنوع
    assert n2 == 0
    notes = session.query(Notification).filter_by(member_id=member.id).all()
    assert len(notes) == 1
    assert notes[0].kind == "renewal"


def test_no_renewal_reminder_far_from_expiry(session):
    _member_with_membership(session, days=30)
    assert send_renewal_reminders(session) == 0


def test_reassessment_reminder_in_window(session):
    member, _ = _member_with_membership(session, days=30)
    a = Assessment14Domain(member_id=member.id, total_score=40)
    session.add(a)
    session.commit()
    # created_at اکنون است → خارج از پنجرهٔ ۶-۸ هفته
    assert send_reassessment_reminders(session) == 0
    # قدیمی‌اش می‌کنیم (۷ هفته پیش)
    a.created_at = datetime.now(UTC) - timedelta(weeks=7)
    session.commit()
    assert send_reassessment_reminders(session) == 1
    assert send_reassessment_reminders(session) == 0  # بدون تکرار


def test_scheduler_builds_with_jobs(session):
    from jobs.scheduler import build_scheduler

    sched = build_scheduler(lambda: session)
    ids = {j.id for j in sched.get_jobs()}
    assert ids == {"expire_memberships", "renewal_reminders", "reassessment_reminders"}
