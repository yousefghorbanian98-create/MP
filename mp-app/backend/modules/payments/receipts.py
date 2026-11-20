"""فیش کارت‌به‌کارت — آپلود خصوصی، صف بازبینی، تأیید/رد اتمیک (QF-07/08/09).

# تصمیم‌های امنیتی

- **نوع فایل از محتوا** خوانده می‌شود (`Pillow`), نه از `Content-Type` کلاینت.
- فایل با نام تصادفی در `settings.receipts_dir` (بیرون از هر مسیر استاتیک)
  ذخیره می‌شود و هرگز با URL عمومی سرو نمی‌شود.
- آپلود فقط با عضوِ صاحب همان پرداخت؛ کادر نمی‌تواند به‌جای عضو فیش بگذارد.
- تأیید فقط با مجوز `finance.write` (لایهٔ `security/grants.py`) و هرگز توسط
  سازندهٔ همان پرداخت.
- تأیید/رد یک تراکنش است: پرداخت + رسید + اشتراک + اعلان + audit با هم
  commit می‌شوند (بدون commit میانی).
"""

from __future__ import annotations

import hashlib
import io
import secrets
from datetime import UTC, datetime, timedelta
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.errors import ApiError, ForbiddenError, NotFoundError
from db.models import Member, Payment, PaymentReceipt, User

ALLOWED_IMAGE_TYPES: dict[str, str] = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}
_PIL_FORMATS = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def _storage_dir() -> Path:
    path = Path(settings.receipts_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _validate(data: bytes, declared_type: str) -> tuple[str, str]:
    """(mime, extension) — با اعتبارسنجی محتوا؛ خطای صریح در صورت تخلف."""
    if len(data) > settings.receipt_max_bytes:
        raise ApiError(
            f"حجم فیش بیش از سقف {settings.receipt_max_bytes // (1024 * 1024)} مگابایت است",
            status_code=413,
            code="receipt_too_large",
        )
    if declared_type not in ALLOWED_IMAGE_TYPES:
        raise ApiError(
            "فقط تصویر JPEG/PNG/WebP پذیرفته می‌شود",
            status_code=422,
            code="unsupported_receipt_type",
        )
    try:
        with Image.open(io.BytesIO(data)) as img:
            img.verify()
            actual = _PIL_FORMATS.get(img.format or "")
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ApiError(
            "فایل تصویر معتبر نیست", status_code=422, code="invalid_receipt_image"
        ) from exc
    if actual is None:
        raise ApiError(
            "قالب تصویر پشتیبانی نمی‌شود", status_code=422, code="unsupported_receipt_type"
        )
    if actual != declared_type:
        # هدر کلاینت با محتوا نمی‌خواند؛ به محتوا اعتماد می‌کنیم ولی نمی‌پذیریم.
        raise ApiError(
            "نوع اعلام‌شده با محتوای فایل نمی‌خواند",
            status_code=422,
            code="receipt_type_mismatch",
        )
    return actual, ALLOWED_IMAGE_TYPES[actual]


def submit_receipt(
    db: Session,
    *,
    user: User,
    payment_id: int,
    data: bytes,
    declared_type: str,
) -> dict:
    from app.security.ownership import ensure_record_scope

    payment = db.get(Payment, payment_id)
    if payment is None:
        raise NotFoundError("پرداخت یافت نشد")
    if user.role != "member":
        raise ForbiddenError("آپلود فیش فقط از حساب عضو پذیرفته می‌شود", code="member_only")
    ensure_record_scope(db, user, payment)
    if payment.method != "card_to_card":
        raise ApiError("این پرداخت مسیر فیش ندارد", code="receipt_not_applicable")
    if payment.status != "pending":
        raise ApiError("این پرداخت قبلاً پردازش شده است", code="already_processed")

    mime, ext = _validate(data, declared_type)
    stored_name = f"{secrets.token_hex(16)}.{ext}"
    target = _storage_dir() / stored_name
    target.write_bytes(data)
    target.chmod(0o600)

    now = datetime.now(UTC)
    receipt = PaymentReceipt(
        payment_id=payment.id,
        review_id=secrets.token_urlsafe(24),
        stored_path=str(target),
        mime=mime,
        size_bytes=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
        uploaded_by_user_id=user.id,
        status="in_review",
        expires_at=now + timedelta(hours=settings.receipt_review_ttl_hours),
        created_at=now,
    )
    db.add(receipt)
    payment.status = "in_review"
    db.flush()

    from modules.admin.service import audit

    audit(
        db,
        user.id,
        "receipt_uploaded",
        "payment",
        payment.id,
        {"review_id": receipt.review_id, "size_bytes": receipt.size_bytes, "mime": mime},
        commit=False,
    )
    db.commit()
    db.refresh(receipt)
    return {
        "receipt_id": receipt.id,
        "review_id": receipt.review_id,
        "payment_id": payment.id,
        "status": "in_review",
        "expires_at": receipt.expires_at.isoformat(),
        "size_bytes": receipt.size_bytes,
        "mime": mime,
    }


def _open_review(db: Session, payment: Payment) -> PaymentReceipt:
    receipt = db.scalar(
        select(PaymentReceipt)
        .where(PaymentReceipt.payment_id == payment.id, PaymentReceipt.status == "in_review")
        .order_by(PaymentReceipt.id.desc())
        .limit(1)
    )
    if receipt is None:
        raise ApiError("رسیدی در انتظار بازبینی نیست", code="not_in_review")
    if _aware(receipt.expires_at) <= datetime.now(UTC):
        raise ApiError("مهلت بازبینی این فیش گذشته است؛ فیش تازه بفرستید", code="review_expired")
    return receipt


def approve_payment(db: Session, *, actor: User, payment_id: int) -> dict:
    """تأیید اتمیک: پول + رسید + (اختیاری) اشتراک + اعلان + audit."""
    from modules.admin.service import audit
    from modules.membership.service import create_membership_from_plan
    from modules.notification.service import send
    from modules.outbox.service import enqueue

    payment = db.get(Payment, payment_id)
    if payment is None:
        raise NotFoundError("پرداخت یافت نشد")
    if payment.status == "paid":
        raise ApiError("این پرداخت قبلاً پردازش شده است", code="already_processed")
    if payment.status != "in_review":
        raise ApiError("پرداخت در صف بازبینی نیست", code="not_in_review")
    if payment.created_by_user_id == actor.id:
        raise ForbiddenError(
            "تأیید پرداختی که خودتان ثبت کرده‌اید مجاز نیست", code="self_approval_forbidden"
        )
    receipt = _open_review(db, payment)

    now = datetime.now(UTC)
    membership_id: int | None = None
    if payment.plan_key:
        created = create_membership_from_plan(db, payment.member_id, payment.plan_key, commit=False)
        membership_id = created["membership"].id

    payment.status = "paid"
    payment.paid_at = now
    payment.reference_id = f"receipt-{receipt.review_id[:12]}"
    receipt.status = "approved"
    receipt.reviewed_by_user_id = actor.id
    receipt.reviewed_at = now

    send(
        db,
        payment.member_id,
        "فیش شما تأیید شد",
        f"پرداخت {payment.amount_rial:,} ریالی تأیید و ثبت شد."
        + (" اشتراک شما فعال شد." if membership_id else ""),
        kind="payment",
        commit=False,
    )
    enqueue(
        db,
        "payment.approved",
        {
            "payment_id": payment.id,
            "member_id": payment.member_id,
            "amount_rial": payment.amount_rial,
            "membership_id": membership_id,
        },
        dedup_key=f"payment-approved-{payment.id}",
        commit=False,
    )
    audit(
        db,
        actor.id,
        "payment_approved",
        "payment",
        payment.id,
        {
            "amount_rial": payment.amount_rial,
            "review_id": receipt.review_id,
            "membership_id": membership_id,
        },
        commit=False,
    )
    db.commit()
    db.refresh(payment)
    return _payment_payload(payment, membership_id)


def reject_receipt(db: Session, *, actor: User, payment_id: int, reason: str) -> dict:
    from modules.admin.service import audit
    from modules.notification.service import send
    from modules.outbox.service import enqueue

    if not reason.strip():
        raise ApiError("دلیل رد فیش لازم است", code="reason_required")
    payment = db.get(Payment, payment_id)
    if payment is None:
        raise NotFoundError("پرداخت یافت نشد")
    if payment.status != "in_review":
        raise ApiError("پرداخت در صف بازبینی نیست", code="not_in_review")
    if payment.created_by_user_id == actor.id:
        raise ForbiddenError(
            "بررسی پرداختی که خودتان ثبت کرده‌اید مجاز نیست", code="self_approval_forbidden"
        )
    receipt = _open_review(db, payment)

    now = datetime.now(UTC)
    payment.status = "failed"
    receipt.status = "rejected"
    receipt.reject_reason = reason.strip()[:500]
    receipt.reviewed_by_user_id = actor.id
    receipt.reviewed_at = now

    send(
        db,
        payment.member_id,
        "فیش شما رد شد",
        f"دلیل: {reason.strip()[:200]} — می‌توانید فیش درست را دوباره بفرستید.",
        kind="payment",
        commit=False,
    )
    enqueue(
        db,
        "payment.rejected",
        {"payment_id": payment.id, "member_id": payment.member_id, "review_id": receipt.review_id},
        dedup_key=f"payment-rejected-{receipt.review_id}",
        commit=False,
    )
    audit(
        db,
        actor.id,
        "payment_rejected",
        "payment",
        payment.id,
        {"review_id": receipt.review_id, "reason": receipt.reject_reason},
        commit=False,
    )
    db.commit()
    db.refresh(payment)
    return {"payment_id": payment.id, "status": payment.status, "review_id": receipt.review_id}


def _payment_payload(payment: Payment, membership_id: int | None) -> dict:
    return {
        "id": payment.id,
        "member_id": payment.member_id,
        "amount_rial": payment.amount_rial,
        "method": payment.method,
        "status": payment.status,
        "reference_id": payment.reference_id,
        "membership_id": membership_id,
        "paid_at": payment.paid_at.isoformat() if payment.paid_at else None,
    }


def member_has_receipt(db: Session, *, member_id: int) -> bool:
    """کمکی برای تست/گزارش: آیا این عضو فیشی فرستاده است."""
    if db.get(Member, member_id) is None:
        return False
    return (
        db.scalar(
            select(PaymentReceipt.id)
            .join(Payment, Payment.id == PaymentReceipt.payment_id)
            .where(Payment.member_id == member_id)
            .limit(1)
        )
        is not None
    )
