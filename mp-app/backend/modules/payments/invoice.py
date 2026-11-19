"""رسید و فاکتور (M16) — خروجی قطعی و قابل‌استناد."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.errors import NotFoundError
from db.models import Member, Payment, WalletTransaction


def _member_name(db: Session, member_id: int | None) -> str | None:
    if member_id is None:
        return None
    from db.models import User

    member = db.get(Member, member_id)
    if member is None:
        return None
    user = db.get(User, member.user_id)
    return user.full_name if user else None


def build_receipt(db: Session, payment_id: int, user=None) -> dict:
    """رسید پرداخت — برای نمایش/چاپ (US-303)."""
    payment = db.get(Payment, payment_id)
    if payment is None:
        raise NotFoundError("پرداخت یافت نشد")
    from app.security.ownership import ensure_record_scope

    ensure_record_scope(db, user, payment)
    member_name = _member_name(db, payment.member_id)
    return {
        "receipt_no": f"R-{payment.id:06d}",
        "payment_id": payment.id,
        # عضو با `user_id` نمایش داده نمی‌شد: رسید چاپی باید نام داشته باشد،
        # نه کلید داخلی. (یافتهٔ M60/R5 هنگام افزودن رسید سفارش.)
        "member_name": member_name,
        "amount_rial": payment.amount_rial,
        "method": payment.method,
        "status": payment.status,
        "reference_id": payment.reference_id,
        "refund_reference": payment.refund_reference,
        "paid_at": payment.paid_at.isoformat() if payment.paid_at else None,
        "issued_at": datetime.now(UTC).isoformat(),
        "branch": "Muscle Paradise",
    }


def build_invoice(db: Session, member_id: int, user=None) -> dict:
    """فاکتور تجمعی عضو — مجموع پرداخت‌ها + کیف‌پول (US-403)."""
    from app.security.ownership import ensure_member_scope

    ensure_member_scope(db, user, member_id)
    from sqlalchemy import select

    member = db.get(Member, member_id)
    if member is None:
        raise NotFoundError("عضو یافت نشد")
    payments = db.scalars(
        select(Payment).where(Payment.member_id == member_id, Payment.status == "paid")
    ).all()
    wallet_rows = db.scalars(
        select(WalletTransaction).where(WalletTransaction.member_id == member_id)
    ).all()
    total_paid = sum(p.amount_rial for p in payments)
    wallet_credit = sum(t.amount_rial for t in wallet_rows if t.kind == "credit")
    wallet_debit = sum(t.amount_rial for t in wallet_rows if t.kind == "debit")
    return {
        "invoice_no": f"INV-{member_id:05d}-{datetime.now(UTC):%Y%m}",
        "member_id": member_id,
        "generated_at": datetime.now(UTC).isoformat(),
        "payments": [
            {
                "payment_id": p.id,
                "amount_rial": p.amount_rial,
                "method": p.method,
                "reference_id": p.reference_id,
                "paid_at": p.paid_at.isoformat() if p.paid_at else None,
            }
            for p in payments
        ],
        "total_paid_rial": total_paid,
        "wallet_credit_rial": wallet_credit,
        "wallet_debit_rial": wallet_debit,
        "wallet_balance_rial": wallet_credit - wallet_debit,
        "due_rial": 0,  # بدهی در مدل فعلی وجود ندارد (M17: اقساط)
    }


def build_order_receipt(db: Session, order_id: int, user=None) -> dict:
    """رسید سفارش فروشگاه — برای چاپ/تحویل در انبار (M60/R5).

    چرا جدا از `build_receipt`: آن رسید برای **پرداخت** است (یک تراکنش)،
    این یکی برای **سفارش** است (چند قلم + وضعیت تحویل). قبلاً هیچ مسیری
    جمع این دو را نمی‌داد و انباردار برای دیدن اقلام سفارش باید کل
    `/shop/orders` را می‌گرفت و در کلاینت فیلتر می‌کرد.
    """
    from sqlalchemy import select

    from db.models import Order, OrderItem, Payment, ProductVariant

    order = db.get(Order, order_id)
    if order is None:
        raise NotFoundError("سفارش یافت نشد")
    # همان قرارداد بقیهٔ رکوردهای دارای member_id؛ برای سفارش تابع جدا لازم
    # نیست (ensure_record_scope فقط member_id را می‌بیند).
    from app.security.ownership import ensure_record_scope

    ensure_record_scope(db, user, order)

    items = list(db.scalars(select(OrderItem).where(OrderItem.order_id == order.id)))
    payment = db.get(Payment, order.payment_id) if order.payment_id else None
    lines = []
    for it in items:
        variant = db.get(ProductVariant, it.variant_id) if it.variant_id else None
        lines.append(
            {
                "product_id": it.product_id,
                "title": it.title_snapshot,
                "variant": variant.label if variant is not None else None,
                "unit_price_rial": it.unit_price_rial,
                "qty": it.qty,
                "line_total_rial": it.unit_price_rial * it.qty,
            }
        )
    return {
        "receipt_no": f"O-{order.id:06d}",
        "order_id": order.id,
        "member_id": order.member_id,
        "member_name": _member_name(db, order.member_id),
        "status": order.status,
        "note": order.note,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "lines": lines,
        "items_total_rial": sum(line["line_total_rial"] for line in lines),
        "total_rial": order.total_rial,
        "payment": (
            {
                "id": payment.id,
                "method": payment.method,
                "status": payment.status,
                "reference_id": payment.reference_id,
                "paid_at": payment.paid_at.isoformat() if payment.paid_at else None,
            }
            if payment is not None
            else None
        ),
        "issued_at": datetime.now(UTC).isoformat(),
        "branch": "Muscle Paradise",
    }
