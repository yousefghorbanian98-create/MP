"""سرویس membership — عضو، پروفایل، اشتراک (منطق تجاری فقط اینجا)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import ConflictError, NotFoundError
from db.models import Member, Membership, User


def create_member(
    db: Session,
    phone: str,
    full_name: str,
    goal: str = "",
    gender: str = "unknown",
    height_cm: int | None = None,
    constraints: str = "[]",
) -> Member:
    existing = db.scalar(select(User).where(User.phone == phone))
    if existing is not None:
        raise ConflictError("این شماره قبلاً ثبت شده است")
    user = User(phone=phone, full_name=full_name, role="member")
    db.add(user)
    db.flush()
    member = Member(
        user_id=user.id,
        goal=goal,
        gender=gender,
        height_cm=height_cm,
        constraints=constraints,
        branch_id=1,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def get_member(db: Session, member_id: int) -> Member:
    member = db.get(Member, member_id)
    if member is None:
        raise NotFoundError("عضو یافت نشد")
    return member


def list_members(db: Session, offset: int = 0, limit: int = 50) -> list[Member]:
    return list(db.scalars(select(Member).offset(offset).limit(limit)))


def update_member(db: Session, member_id: int, **fields) -> Member:
    member = get_member(db, member_id)
    for key, value in fields.items():
        if value is not None and hasattr(member, key):
            setattr(member, key, value)
    db.commit()
    db.refresh(member)
    return member


def create_membership(
    db: Session,
    member_id: int,
    plan_name: str,
    duration_days: int,
    price_rial: int,
) -> Membership:
    member = get_member(db, member_id)
    now = datetime.now(UTC)
    # اگر اشتراک فعالی هست، از پایان همان ادامه می‌یابد (تمدید)
    active = db.scalar(
        select(Membership)
        .where(Membership.member_id == member.id, Membership.status == "active")
        .order_by(Membership.expires_at.desc())
        .limit(1)
    )
    start = active.expires_at if active and _aware(active.expires_at) > now else now
    if active and _aware(active.expires_at) > now:
        active.status = "cancelled"  # ادغام تمدید در اشتراک جدید
    ms = Membership(
        member_id=member.id,
        plan_name=plan_name,
        started_at=start,
        expires_at=start + timedelta(days=duration_days),
        status="active",
        price_rial=price_rial,
        branch_id=member.branch_id,
    )
    db.add(ms)
    db.commit()
    db.refresh(ms)
    return ms


def get_active_membership(db: Session, member_id: int) -> Membership | None:
    now = datetime.now(UTC)
    rows = db.scalars(
        select(Membership)
        .where(Membership.member_id == member_id, Membership.status == "active")
        .order_by(Membership.expires_at.desc())
    )
    for row in rows:
        if _aware(row.expires_at) > now:
            return row
    return None


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
