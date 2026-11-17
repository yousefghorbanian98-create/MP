"""KPI های واقعی ادمین (M29) — از دادهٔ DB، نه فرضی."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from db.models import ClassBooking, GymClass, Member, Membership, Payment


def admin_kpis(db: Session) -> dict:
    now = datetime.now(UTC)
    members_total = db.execute(select(func.count()).select_from(Member)).scalar() or 0
    active_members = (
        db.execute(
            select(func.count(func.distinct(Membership.member_id))).where(
                Membership.status == "active", Membership.expires_at > now
            )
        ).scalar()
        or 0
    )
    new_30d = (
        db.execute(
            select(func.count())
            .select_from(Member)
            .where(Member.created_at >= now - timedelta(days=30))
        ).scalar()
        or 0
    )
    revenue_paid = db.execute(
        select(func.coalesce(func.sum(Payment.amount_rial), 0)).where(Payment.status == "paid")
    ).scalar()
    active_memberships = (
        db.execute(
            select(func.count())
            .select_from(Membership)
            .where(Membership.status == "active", Membership.expires_at > now)
        ).scalar()
        or 0
    )
    classes = db.execute(select(func.count()).select_from(GymClass)).scalar() or 0
    bookings = (
        db.execute(
            select(func.count()).select_from(ClassBooking).where(ClassBooking.status == "confirmed")
        ).scalar()
        or 0
    )
    capacity = db.execute(select(func.coalesce(func.sum(GymClass.capacity), 0))).scalar() or 0
    return {
        "members_total": int(members_total),
        "active_members": int(active_members),
        "new_members_30d": int(new_30d),
        "revenue_paid_rial": int(revenue_paid),
        "active_memberships": int(active_memberships),
        "classes": int(classes),
        "class_fill_rate": round(bookings / capacity, 3) if capacity else None,  # ناشناخته ≠ صفر
        "generated_at": now.isoformat(),
    }
