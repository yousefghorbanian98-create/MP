"""Repository ماژول payments."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import Payment, WalletTransaction


class PaymentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, payment_id: int) -> Payment | None:
        return self.db.get(Payment, payment_id)

    def add(self, payment: Payment) -> Payment:
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def list(self, member_id: int | None = None, status: str | None = None) -> list[Payment]:
        stmt = select(Payment).order_by(Payment.id.desc())
        if member_id is not None:
            stmt = stmt.where(Payment.member_id == member_id)
        if status is not None:
            stmt = stmt.where(Payment.status == status)
        return list(self.db.scalars(stmt))


class WalletRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, tx: WalletTransaction) -> WalletTransaction:
        self.db.add(tx)
        self.db.commit()
        self.db.refresh(tx)
        return tx

    def entries(self, member_id: int) -> list[WalletTransaction]:
        return list(
            self.db.scalars(
                select(WalletTransaction).where(WalletTransaction.member_id == member_id)
            )
        )
