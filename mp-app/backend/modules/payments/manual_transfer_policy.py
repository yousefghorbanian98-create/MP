"""Pure policy for a future manual bank-transfer workflow.

Not connected to any API, storage or ledger.  This module only evaluates
transitions; transactional locking, authorization and bank reconciliation
must be enforced by the service that eventually calls it.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum


class TransferState(StrEnum):
    AWAITING_PROOF = "awaiting_proof"
    PENDING_REVIEW = "pending_review"
    REJECTED = "rejected"
    APPROVED = "approved"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class TransferAction(StrEnum):
    SUBMIT = "submit"
    APPROVE = "approve"
    REJECT = "reject"
    EXPIRE = "expire"
    CANCEL = "cancel"


class TransferPolicyError(ValueError):
    """An invalid or incomplete decision; callers must fail closed."""


def _aware(value: datetime) -> bool:
    return (
        isinstance(value, datetime) and value.tzinfo is not None and value.utcoffset() is not None
    )


def _positive_int(value: object) -> bool:
    return type(value) is int and value > 0


def next_transfer_state(
    state: TransferState,
    action: TransferAction,
    *,
    now: datetime,
    deadline: datetime,
    order_open: bool = True,
    bank_verified: bool = False,
    expected_rial: int | None = None,
    received_rial: int | None = None,
    bank_reference: str = "",
    rejection_reason: str = "",
) -> TransferState:
    """Evaluate one transition; money is never moved by this function.

    The caller supplies trusted server-side order values and a separately
    recorded authorized human bank attestation. Neither an image nor client
    input proves a bank transfer. Exact amount is mandatory: partial and excess
    payments remain for human reconciliation outside this policy.
    """
    if not isinstance(state, TransferState) or not isinstance(action, TransferAction):
        raise TransferPolicyError("invalid state or action")
    if not _aware(now) or not _aware(deadline):
        raise TransferPolicyError("timestamps must be timezone-aware")
    if type(order_open) is not bool or type(bank_verified) is not bool:
        raise TransferPolicyError("boolean inputs required")

    if action is TransferAction.SUBMIT:
        if state not in (TransferState.AWAITING_PROOF, TransferState.REJECTED):
            raise TransferPolicyError("receipt submission is not allowed in this state")
        if not order_open or now >= deadline:
            raise TransferPolicyError("order closed or receipt deadline reached")
        return TransferState.PENDING_REVIEW

    if action is TransferAction.APPROVE:
        if state is not TransferState.PENDING_REVIEW or not order_open:
            raise TransferPolicyError("receipt cannot be approved")
        if (
            not bank_verified
            or not _positive_int(expected_rial)
            or not _positive_int(received_rial)
            or received_rial != expected_rial
            or not isinstance(bank_reference, str)
            or not bank_reference.strip()
            or len(bank_reference.strip()) > 80
        ):
            raise TransferPolicyError("independent bank verification is incomplete")
        return TransferState.APPROVED

    if action is TransferAction.REJECT:
        if state is not TransferState.PENDING_REVIEW or not order_open:
            raise TransferPolicyError("receipt cannot be rejected")
        if not isinstance(rejection_reason, str) or not rejection_reason.strip():
            raise TransferPolicyError("rejection reason required")
        if len(rejection_reason.strip()) > 500:
            raise TransferPolicyError("rejection reason too long")
        return TransferState.REJECTED

    if action is TransferAction.EXPIRE:
        if state not in (TransferState.AWAITING_PROOF, TransferState.REJECTED):
            raise TransferPolicyError("receipt in review or terminal state cannot expire")
        if not order_open or now < deadline:
            raise TransferPolicyError("order closed or deadline not reached")
        return TransferState.EXPIRED

    if action is TransferAction.CANCEL:
        if state not in (TransferState.AWAITING_PROOF, TransferState.REJECTED):
            raise TransferPolicyError("receipt in review or terminal state cannot be cancelled")
        if not order_open:
            raise TransferPolicyError("order already closed")
        return TransferState.CANCELLED

    raise TransferPolicyError("unsupported action")
