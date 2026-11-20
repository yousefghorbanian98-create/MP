"""دفتر پول عضو — رویداد فقط-افزودنی، idempotency و معکوس‌سازی (QF-05).

# چه چیزی در دفتر می‌آید

هر حرکتی که **موجودی کیف‌پول** را تغییر می‌دهد: شارژ (+)، پرداخت از کیف‌پول
(−)، بازگشت به کیف‌پول (+) و معکوس‌سازی (علامت مخالف). پرداخت نقدی/کارت‌خوان
حرکت کیف‌پول نیست و در `payments` می‌ماند؛ دفتر ادعای «حسابداری دوطرفه» ندارد.

# چرا معکوس‌سازی و نه ویرایش

تاریخچهٔ پول باید قابل حسابرسی باشد. ردیف اصلی هرگز تغییر نمی‌کند؛ یک ردیف
جبرانی ساخته می‌شود و ردیف اصلی `reversed_by_entry_id` می‌گیرد. نتیجه:
هم تاریخچه دست‌نخورده است، هم دو بار معکوس‌کردن ممکن نیست.

# تطبیق

`reconcile()` مجموع دفتر را با موجودی کیف‌پول مقایسه می‌کند؛ اگر اختلاف باشد
یعنی یک مسیر پول از دفتر رد نشده — همان چیزی که این لایه باید بگیرد.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.errors import ApiError, ConflictError, NotFoundError
from db.models import LedgerEntry, Member, WalletTransaction

KINDS = ("charge", "pay", "refund", "reversal")
SOURCE_TYPES = ("wallet", "payment")


def record(
    db: Session,
    *,
    member_id: int,
    amount_rial: int,
    kind: str,
    source_type: str,
    source_id: int | None = None,
    idempotency_key: str | None = None,
    created_by_user_id: int | None = None,
    note: str = "",
    commit: bool = False,
) -> LedgerEntry:
    """ثبت یک رویداد؛ با کلید تکراری، همان ردیف برمی‌گردد (یا ۴۰۹ اگر متفاوت باشد)."""
    if kind not in KINDS:
        raise ApiError(f"نوع رویداد «{kind}» شناخته نیست", code="unknown_ledger_kind")
    if source_type not in SOURCE_TYPES:
        raise ApiError(f"منبع «{source_type}» شناخته نیست", code="unknown_ledger_source")
    if amount_rial == 0:
        raise ApiError("مبلغ صفر در دفتر ثبت نمی‌شود", code="zero_amount")
    if idempotency_key:
        existing = db.scalar(
            select(LedgerEntry).where(LedgerEntry.idempotency_key == idempotency_key)
        )
        if existing is not None:
            if existing.amount_rial != amount_rial or existing.kind != kind:
                raise ConflictError(
                    "همین کلید idempotency قبلاً با مبلغ/نوع دیگری ثبت شده است",
                    code="idempotency_conflict",
                )
            return existing

    entry = LedgerEntry(
        member_id=member_id,
        amount_rial=amount_rial,
        kind=kind,
        source_type=source_type,
        source_id=source_id,
        idempotency_key=idempotency_key,
        created_by_user_id=created_by_user_id,
        note=note[:200],
        created_at=datetime.now(UTC),
    )
    db.add(entry)
    db.flush()
    if commit:
        db.commit()
        db.refresh(entry)
    return entry


def entries(db: Session, member_id: int, *, limit: int = 200) -> list[LedgerEntry]:
    return list(
        db.scalars(
            select(LedgerEntry)
            .where(LedgerEntry.member_id == member_id)
            .order_by(LedgerEntry.id.desc())
            .limit(limit)
        )
    )


def balance(db: Session, member_id: int) -> int:
    return int(
        db.scalar(
            select(func.coalesce(func.sum(LedgerEntry.amount_rial), 0)).where(
                LedgerEntry.member_id == member_id
            )
        )
        or 0
    )


def reconcile(db: Session, member_id: int) -> dict:
    """تطبیق دفتر با کیف‌پول؛ اختلاف گزارش می‌شود، نه پنهان."""
    from modules.payments.service import wallet_balance

    wallet = wallet_balance(db, member_id)
    ledger = balance(db, member_id)
    return {
        "member_id": member_id,
        "wallet_balance_rial": wallet,
        "ledger_balance_rial": ledger,
        "matches": wallet == ledger,
        "difference_rial": ledger - wallet,
    }


def reverse(
    db: Session,
    *,
    entry_id: int,
    actor,
    reason: str,
    commit: bool = True,
) -> dict:
    """معکوس‌سازی یک رویداد با ردیف جبرانی + بازگشت اثر روی کیف‌پول."""
    if not reason or not reason.strip():
        raise ApiError("دلیل معکوس‌سازی لازم است", code="reason_required")
    entry = db.get(LedgerEntry, entry_id)
    if entry is None:
        raise NotFoundError("رویداد دفتر یافت نشد")
    if entry.kind == "reversal":
        raise ApiError("معکوس‌سازی یک ردیف جبرانی مجاز نیست", code="cannot_reverse_reversal")
    if entry.reversed_by_entry_id is not None:
        raise ApiError("این رویداد قبلاً معکوس شده است", code="already_reversed")

    reversal = record(
        db,
        member_id=entry.member_id,
        amount_rial=-entry.amount_rial,
        kind="reversal",
        source_type=entry.source_type,
        source_id=entry.source_id,
        idempotency_key=f"reversal-{entry.id}",
        created_by_user_id=getattr(actor, "id", None),
        note=reason.strip()[:200],
    )
    entry.reversed_by_entry_id = reversal.id

    # اثر واقعی روی کیف‌پول: اگر رویداد اصلی حرکت کیف‌پول بود، ردیف مخالف بزن.
    if entry.source_type == "wallet" and entry.kind in ("charge", "pay", "refund"):
        db.add(
            WalletTransaction(
                member_id=entry.member_id,
                amount_rial=abs(entry.amount_rial),
                kind="debit" if entry.amount_rial > 0 else "credit",
                description=f"معکوس‌سازی رویداد #{entry.id}: {reason.strip()[:120]}",
            )
        )
        db.flush()

    from modules.admin.service import audit

    audit(
        db,
        getattr(actor, "id", None),
        "ledger_reversal",
        "ledger_entry",
        entry.id,
        {
            "reversal_entry_id": reversal.id,
            "amount_rial": entry.amount_rial,
            "reason": reason.strip()[:200],
        },
        commit=False,
    )
    if commit:
        db.commit()
        db.refresh(reversal)
        db.refresh(entry)
    return {"original_entry_id": entry.id, "reversal_entry": reversal}


def serialize(entry: LedgerEntry) -> dict:
    return {
        "id": entry.id,
        "member_id": entry.member_id,
        "amount_rial": entry.amount_rial,
        "kind": entry.kind,
        "source_type": entry.source_type,
        "source_id": entry.source_id,
        "note": entry.note or "",
        "reverses_entry_id": entry.reverses_entry_id,
        "reversed_by_id": entry.reversed_by_entry_id,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
    }


def ensure_member(db: Session, member_id: int) -> None:
    if db.get(Member, member_id) is None:
        raise NotFoundError("عضو یافت نشد")
