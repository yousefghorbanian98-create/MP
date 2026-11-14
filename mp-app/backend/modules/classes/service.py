"""رزرو کلاس با ظرفیت/لیست انتظار (M27)."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.errors import ApiError, NotFoundError
from db.models import ClassBooking, GymClass, Member


def create_class(
    db: Session, *, name: str, capacity: int, schedule_text: str = "", coach_id: int | None = None
) -> GymClass:
    if capacity < 1:
        raise ApiError("ظرفیت باید ≥ 1 باشد", code="invalid_capacity")
    c = GymClass(
        name=name, capacity=capacity, schedule_text=schedule_text, coach_id=coach_id, branch_id=1
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def book(db: Session, *, class_id: int, member_id: int) -> ClassBooking:
    cls = db.get(GymClass, class_id)
    if cls is None:
        raise NotFoundError("کلاس یافت نشد")
    if db.get(Member, member_id) is None:
        raise NotFoundError("عضو یافت نشد")
    existing = (
        db.execute(
            select(ClassBooking).where(
                ClassBooking.class_id == class_id, ClassBooking.member_id == member_id
            )
        )
        .scalars()
        .first()
    )
    if existing and existing.status != "cancelled":
        raise ApiError("عضو قبلاً رزرو کرده است", code="already_booked")
    confirmed = (
        db.execute(
            select(func.count())
            .select_from(ClassBooking)
            .where(ClassBooking.class_id == class_id, ClassBooking.status == "confirmed")
        ).scalar()
        or 0
    )
    status = "confirmed" if confirmed < cls.capacity else "waitlisted"
    b = ClassBooking(class_id=class_id, member_id=member_id, status=status, branch_id=1)
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


def cancel(db: Session, *, class_id: int, member_id: int) -> ClassBooking:
    b = (
        db.execute(
            select(ClassBooking).where(
                ClassBooking.class_id == class_id, ClassBooking.member_id == member_id
            )
        )
        .scalars()
        .first()
    )
    if b is None or b.status == "cancelled":
        raise NotFoundError("رزروی یافت نشد")
    b.status = "cancelled"
    # ارتقای نفر اول لیست انتظار
    next_waiting = (
        db.execute(
            select(ClassBooking)
            .where(ClassBooking.class_id == class_id, ClassBooking.status == "waitlisted")
            .order_by(ClassBooking.id.asc())
        )
        .scalars()
        .first()
    )
    if next_waiting is not None:
        next_waiting.status = "confirmed"
    db.commit()
    db.refresh(b)
    return b


def list_classes(db: Session) -> list[dict]:
    out = []
    for c in db.execute(select(GymClass).order_by(GymClass.id)).scalars():
        confirmed = (
            db.execute(
                select(func.count())
                .select_from(ClassBooking)
                .where(ClassBooking.class_id == c.id, ClassBooking.status == "confirmed")
            ).scalar()
            or 0
        )
        waiting = (
            db.execute(
                select(func.count())
                .select_from(ClassBooking)
                .where(ClassBooking.class_id == c.id, ClassBooking.status == "waitlisted")
            ).scalar()
            or 0
        )
        out.append(
            {
                "id": c.id,
                "name": c.name,
                "capacity": c.capacity,
                "schedule_text": c.schedule_text,
                "coach_id": c.coach_id,
                "confirmed": confirmed,
                "waitlisted": waiting,
                "seats_left": max(c.capacity - confirmed, 0),
            }
        )
    return out
