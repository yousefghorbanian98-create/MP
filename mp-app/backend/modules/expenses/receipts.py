"""فیش خصوصی هزینه (QF-06) — آپلود یک‌باره، خواندن فقط با `finance.read`.

از همان اعتبارسنجی محتوا و پوشهٔ خصوصی فیش پرداخت استفاده می‌کند؛ یک منطق امنیتی
برای دو جا، نه دو کپی.
"""

from __future__ import annotations

import hashlib
import secrets
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import ApiError, NotFoundError
from db.models import Expense, ExpenseReceipt
from modules.admin.service import audit
from modules.payments.receipts import _storage_dir, _validate


def _live_expense(db: Session, expense_id: int) -> Expense:
    row = db.get(Expense, expense_id)
    if row is None:
        raise NotFoundError("هزینه یافت نشد")
    return row


def upload(db: Session, *, actor, expense_id: int, data: bytes, declared_type: str) -> dict:
    row = _live_expense(db, expense_id)
    if row.deleted_at is not None:
        raise ApiError("هزینهٔ حذف‌شده فیش نمی‌پذیرد", code="expense_deleted")
    if db.scalar(select(ExpenseReceipt.id).where(ExpenseReceipt.expense_id == expense_id)):
        raise ApiError("این هزینه قبلاً فیش دارد", status_code=409, code="receipt_exists")

    mime, ext = _validate(data, declared_type)
    target: Path = _storage_dir() / f"exp-{secrets.token_hex(16)}.{ext}"
    target.write_bytes(data)
    target.chmod(0o600)

    from datetime import UTC, datetime

    receipt = ExpenseReceipt(
        expense_id=expense_id,
        stored_path=str(target),
        mime=mime,
        size_bytes=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
        uploaded_by_user_id=getattr(actor, "id", None),
        created_at=datetime.now(UTC),
    )
    db.add(receipt)
    db.flush()
    # ممیزی: نوع و حجم، بدون مبلغ و بدون مسیر فایل.
    audit(
        db,
        getattr(actor, "id", None),
        "expense_receipt_uploaded",
        "expense",
        expense_id,
        {"mime": mime, "size_bytes": receipt.size_bytes},
        commit=False,
    )
    db.commit()
    return {"expense_id": expense_id, "mime": mime, "size_bytes": receipt.size_bytes}


def read(db: Session, expense_id: int) -> tuple[Path, str]:
    _live_expense(db, expense_id)
    receipt = db.scalar(select(ExpenseReceipt).where(ExpenseReceipt.expense_id == expense_id))
    if receipt is None:
        raise NotFoundError("این هزینه فیش ندارد")
    path = Path(receipt.stored_path)
    if not path.is_file():
        raise NotFoundError("فایل فیش در دسترس نیست")
    return path, receipt.mime
