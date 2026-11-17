"""Repository ماژول membership — فقط دسترسی داده (بدون منطق تجاری)."""

from __future__ import annotations

from datetime import UTC

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import Member, Membership, User


class MemberRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, member_id: int) -> Member | None:
        return self.db.get(Member, member_id)

    def get_by_phone(self, phone: str) -> User | None:
        return self.db.scalar(select(User).where(User.phone == phone))

    def add(self, member: Member) -> Member:
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        return member

    def list(self, offset: int = 0, limit: int = 50, gender: str | None = None) -> list[Member]:
        stmt = select(Member)
        if gender:
            stmt = stmt.where(Member.gender == gender)
        return list(self.db.scalars(stmt.offset(offset).limit(limit)))


class MembershipRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, membership: Membership) -> Membership:
        self.db.add(membership)
        self.db.commit()
        self.db.refresh(membership)
        return membership

    def active_for_member(self, member_id: int) -> Membership | None:
        from datetime import datetime

        now = datetime.now(UTC)
        rows = self.db.scalars(
            select(Membership)
            .where(Membership.member_id == member_id, Membership.status == "active")
            .order_by(Membership.expires_at.desc())
        )
        for row in rows:
            expires = (
                row.expires_at if row.expires_at.tzinfo else row.expires_at.replace(tzinfo=UTC)
            )
            if expires > now:
                return row
        return None

    def history(self, member_id: int) -> list[Membership]:
        return list(
            self.db.scalars(
                select(Membership)
                .where(Membership.member_id == member_id)
                .order_by(Membership.id.desc())
            )
        )
