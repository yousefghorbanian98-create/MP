"""کنترل مالکیت سطری (M18) — نقش member فقط به دادهٔ خودش دسترسی دارد.

قواعد مالک (۲۰۲۶-۱۱-۱۴):
- کلاینت (member) صرفاً محدود به پروفایل/دادهٔ خودش
- ورود دادهٔ پیکرسنجی فقط از ادمین/مربی (RBAC — member مسیر POST ندارد)
- خواندن نتایج/سوابق/پیشرفت برای صاحب داده آزاد
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import ForbiddenError
from db.models import Member, User


def get_own_member(db: Session, user: User) -> Member | None:
    """رکورد Member متعلق به کاربر جاری."""
    return db.scalar(select(Member).where(Member.user_id == user.id))


def ensure_member_scope(db: Session, user: User | None, member_id: int) -> None:
    """اگر کاربر نقش member دارد، فقط member_id خودش مجاز است."""
    if user is None or user.role != "member":
        return
    own = get_own_member(db, user)
    if own is None or own.id != member_id:
        raise ForbiddenError("دسترسی فقط به دادهٔ خودتان مجاز است")


def ensure_record_scope(db: Session, user: User | None, record) -> None:
    """برای رکوردهای دارای member_id (پرداخت، برنامه، ارزیابی و...)."""
    if record is None:
        return
    ensure_member_scope(db, user, record.member_id)
