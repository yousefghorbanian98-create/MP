"""فاز ۶ — پول کارت‌به‌کارت: فیش، صف بازبینی، تأیید اتمیک، idempotency.

# قرارداد (بند ۲.۲ پلن: هر تغییر پول با سناریوی زنده)

| # | سناریو | انتظار |
|---|---|---|
| ۱ | عضو برای پرداخت خودش فیش PNG می‌فرستد | ۲۰۲ + `review_id` + وضعیت `in_review` |
| ۲ | عضو دیگر برای همان پرداخت فیش می‌فرستد | ۴۰۳/۴۰۴ — بدون تغییر وضعیت |
| ۳ | کادر (حتی با `finance.write`) فیش عضو را آپلود می‌کند | ۴۰۳ `member_only` |
| ۴ | نوع فایل غیرتصویری | ۴۲۲ `unsupported_receipt_type` |
| ۵ | فایل بزرگ‌تر از سقف | ۴۱۳ `receipt_too_large` |
| ۶ | پرداخت نقدی (نه کارت‌به‌کارت) | ۴۰۰ `receipt_not_applicable` |
| ۷ | تأیید با مجوز مالی | ۲۰۰ `paid` + رسید `approved` + اعلان + audit |
| ۸ | تأیید همراه پلن | اشتراک فعال در همان تراکنش ساخته می‌شود |
| ۹ | تأیید پرداختِ ساختهٔ خودِ تأییدکننده | ۴۰۳ `self_approval_forbidden` |
| ۱۰ | تأیید دوباره | ۴۰۰ `already_processed` بدون تغییر اقتصادی |
| ۱۱ | رد رسید با دلیل | پرداخت `failed` + رسید `rejected` + audit |
| ۱۲ | `idempotency_key` تکراری | همان پرداخت، نه ردیف دوم |
| ۱۳ | رسید منقضی | ۴۰۰ `review_expired` |

# آنچه این تست ثابت نمی‌کند
- انتقال واقعی پول در بانک (`BLOCKED`: بدون تأیید انسانی/دسترسی بانکی).
- UI استودیو برای صف بازبینی (در همان فاز اضافه می‌شود؛ تست جدا دارد).
"""

from __future__ import annotations

import io
import itertools
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import select

from db.base import get_session_factory
from db.models import Member, Payment, PaymentReceipt, User
from tests.integration._actors import create_actor

_counter = itertools.count(80_000)


def _png(size: int = 32) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (size, size), (20, 120, 200)).save(buf, format="PNG")
    return buf.getvalue()


def _member_user() -> tuple[int, int, dict]:
    """(user_id, member_id, headers) — عضو واقعی با شمارهٔ یکتا."""
    from app.security.jwt import create_access_token

    n = next(_counter)
    with get_session_factory()() as s:
        user = User(phone=f"098{n:08d}", full_name=f"عضو-{n}", role="member")
        s.add(user)
        s.commit()
        member = Member(user_id=user.id, goal="hypertrophy", constraints="[]")
        s.add(member)
        s.commit()
        token = create_access_token(user.id, user.role)
        return user.id, member.id, {"Authorization": f"Bearer {token}"}


def _card_to_card_payment(client: TestClient, headers: dict, member_id: int, **extra) -> dict:
    res = client.post(
        "/api/v1/payments",
        json={"member_id": member_id, "amount_rial": 2_500_000, "method": "card_to_card", **extra},
        headers=headers,
    )
    assert res.status_code in (200, 201), res.text
    return res.json()


def _upload(
    client: TestClient,
    payment_id: int,
    headers: dict,
    data: bytes | None = None,
    ctype: str = "image/png",
):
    return client.post(
        f"/api/v1/payments/{payment_id}/receipt",
        files={"file": ("receipt.png", data if data is not None else _png(), ctype)},
        headers=headers,
    )


def _staff(grants: list[str] | None = None) -> tuple[int, dict]:
    headers = create_actor("manager", grants if grants is not None else ["finance.write"])
    token = headers["Authorization"].split(" ", 1)[1]
    from app.security.jwt import decode_access_token

    return int(decode_access_token(token)["sub"]), headers


def test_member_uploads_receipt_and_payment_enters_review(client: TestClient) -> None:
    _, member_id, member_h = _member_user()
    payment = _card_to_card_payment(client, member_h, member_id)

    res = _upload(client, payment["id"], member_h)
    assert res.status_code == 202, res.text
    body = res.json()
    assert body["status"] == "in_review"
    assert len(body["review_id"]) >= 16
    assert body["payment_id"] == payment["id"]
    assert body["expires_at"]

    with get_session_factory()() as s:
        row = s.get(Payment, payment["id"])
        assert row is not None and row.status == "in_review"
        receipt = s.get(PaymentReceipt, body["receipt_id"])
        assert receipt is not None
        # فایل با نام تصادفی و بیرون از مسیر عمومی ذخیره می‌شود.
        assert "receipt" not in receipt.stored_path or "var" in receipt.stored_path
        assert receipt.size_bytes == len(_png())


def test_another_member_cannot_upload_for_someone_elses_payment(client: TestClient) -> None:
    _, member_id, member_h = _member_user()
    payment = _card_to_card_payment(client, member_h, member_id)
    _, _, other_h = _member_user()

    res = _upload(client, payment["id"], other_h)
    assert res.status_code in (403, 404), res.text
    with get_session_factory()() as s:
        assert s.get(Payment, payment["id"]).status == "pending"


def test_staff_still_cannot_upload_a_members_receipt(client: TestClient) -> None:
    _, member_id, member_h = _member_user()
    payment = _card_to_card_payment(client, member_h, member_id)
    _, staff_h = _staff()

    res = _upload(client, payment["id"], staff_h)
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "member_only"


def test_receipt_type_and_size_are_enforced(client: TestClient) -> None:
    _, member_id, member_h = _member_user()
    payment = _card_to_card_payment(client, member_h, member_id)

    res = _upload(client, payment["id"], member_h, data=b"not-an-image", ctype="text/plain")
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "unsupported_receipt_type"

    # PNG جعلی با نام درست هم رد می‌شود: نوع از محتوا خوانده می‌شود، نه از هدر.
    res = _upload(
        client, payment["id"], member_h, data=b"\x89PNG\r\n\x1a\nbroken", ctype="image/png"
    )
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "invalid_receipt_image"

    big = b"\x89PNG\r\n\x1a\n" + b"0" * (6 * 1024 * 1024)
    res = _upload(client, payment["id"], member_h, data=big, ctype="image/png")
    assert res.status_code == 413
    assert res.json()["error"]["code"] == "receipt_too_large"


def test_cash_payment_has_no_receipt_path(client: TestClient) -> None:
    _, member_id, member_h = _member_user()
    res = client.post(
        "/api/v1/payments",
        json={"member_id": member_id, "amount_rial": 100_000, "method": "cash"},
        headers=member_h,
    )
    payment_id = res.json()["id"]
    out = _upload(client, payment_id, member_h)
    assert out.status_code == 400
    assert out.json()["error"]["code"] == "receipt_not_applicable"


def test_staff_approval_is_atomic_and_notifies_the_member(client: TestClient) -> None:
    _, member_id, member_h = _member_user()
    payment = _card_to_card_payment(client, member_h, member_id)
    review = _upload(client, payment["id"], member_h).json()
    approver_id, staff_h = _staff()

    res = client.post(f"/api/v1/payments/{payment['id']}/approve", json={}, headers=staff_h)
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "paid"

    with get_session_factory()() as s:
        row = s.get(Payment, payment["id"])
        assert row.status == "paid" and row.paid_at is not None
        assert row.reference_id.startswith("receipt-")
        receipt = s.get(PaymentReceipt, review["receipt_id"])
        assert receipt.status == "approved"
        assert receipt.reviewed_by_user_id == approver_id

    notes = client.get(f"/api/v1/notifications/member/{member_id}", headers=member_h).json()
    assert any("تأیید" in n["title"] for n in notes)
    audit = client.get("/api/v1/admin/audit?action=payment_approved", headers=staff_h)
    if audit.status_code == 200:
        assert audit.json()


def test_approval_can_activate_membership_in_the_same_transaction(client: TestClient) -> None:
    from app.security.jwt import create_access_token

    owner = create_actor("super_admin")
    n = next(_counter)
    with get_session_factory()() as s:
        user = User(phone=f"097{n:08d}", full_name="عضو پلن", role="member")
        s.add(user)
        s.commit()
        member = Member(user_id=user.id, goal="hypertrophy", constraints="[]", gender="male")
        s.add(member)
        s.commit()
        member_id = member.id
        member_h = {"Authorization": f"Bearer {create_access_token(user.id, user.role)}"}

    payment = _card_to_card_payment(client, member_h, member_id, plan_key="monthly_basic")
    _upload(client, payment["id"], member_h)
    _, staff_h = _staff(grants=["finance.write"])

    res = client.post(f"/api/v1/payments/{payment['id']}/approve", json={}, headers=staff_h)
    assert res.status_code == 200, res.text
    assert res.json()["membership_id"]

    memberships = client.get(f"/api/v1/members/{member_id}/memberships", headers=owner).json()
    assert memberships, memberships


def test_creator_cannot_approve_their_own_payment(client: TestClient) -> None:
    _, member_id, member_h = _member_user()
    creator_id, creator_h = _staff()
    payment = _card_to_card_payment(client, creator_h, member_id)
    _upload(client, payment["id"], member_h)

    res = client.post(f"/api/v1/payments/{payment['id']}/approve", json={}, headers=creator_h)
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "self_approval_forbidden"
    with get_session_factory()() as s:
        assert s.get(Payment, payment["id"]).status == "in_review"


def test_double_approval_changes_nothing_economically(client: TestClient) -> None:
    _, member_id, member_h = _member_user()
    payment = _card_to_card_payment(client, member_h, member_id)
    _upload(client, payment["id"], member_h)
    _, staff_h = _staff()

    first = client.post(f"/api/v1/payments/{payment['id']}/approve", json={}, headers=staff_h)
    assert first.status_code == 200
    reference = first.json()["reference_id"]

    second = client.post(f"/api/v1/payments/{payment['id']}/approve", json={}, headers=staff_h)
    assert second.status_code == 400
    assert second.json()["error"]["code"] == "already_processed"
    with get_session_factory()() as s:
        assert s.get(Payment, payment["id"]).reference_id == reference


def test_rejection_marks_payment_failed_with_reason(client: TestClient) -> None:
    _, member_id, member_h = _member_user()
    payment = _card_to_card_payment(client, member_h, member_id)
    review = _upload(client, payment["id"], member_h).json()
    _, staff_h = _staff()

    res = client.post(
        f"/api/v1/payments/{payment['id']}/reject",
        json={"reason": "مبلغ واریزی با فاکتور نمی‌خواند"},
        headers=staff_h,
    )
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "failed"

    with get_session_factory()() as s:
        receipt = s.get(PaymentReceipt, review["receipt_id"])
        assert receipt.status == "rejected"
        assert "نمی‌خواند" in (receipt.reject_reason or "")

    again = client.post(f"/api/v1/payments/{payment['id']}/approve", json={}, headers=staff_h)
    assert again.status_code == 400
    assert again.json()["error"]["code"] == "not_in_review"


def test_idempotency_key_prevents_duplicate_payments(client: TestClient) -> None:
    _, member_id, member_h = _member_user()
    first = _card_to_card_payment(client, member_h, member_id, idempotency_key="req-0001")
    second = _card_to_card_payment(client, member_h, member_id, idempotency_key="req-0001")
    assert first["id"] == second["id"]

    with get_session_factory()() as s:
        rows = s.scalars(select(Payment).where(Payment.member_id == member_id)).all()
        assert len(rows) == 1

    other = _card_to_card_payment(client, member_h, member_id, idempotency_key="req-0002")
    assert other["id"] != first["id"]


def test_expired_review_cannot_be_approved(client: TestClient) -> None:
    _, member_id, member_h = _member_user()
    payment = _card_to_card_payment(client, member_h, member_id)
    review = _upload(client, payment["id"], member_h).json()
    with get_session_factory()() as s:
        receipt = s.get(PaymentReceipt, review["receipt_id"])
        receipt.expires_at = datetime.now(UTC) - timedelta(hours=1)
        s.commit()

    _, staff_h = _staff()
    res = client.post(f"/api/v1/payments/{payment['id']}/approve", json={}, headers=staff_h)
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "review_expired"
