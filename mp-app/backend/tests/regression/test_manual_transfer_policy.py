"""M113-1: pure state policy; does not test an integrated payment workflow."""

from datetime import UTC, datetime, timedelta, timezone

import pytest

from modules.payments.manual_transfer_policy import (
    TransferAction as A,
)
from modules.payments.manual_transfer_policy import (
    TransferPolicyError,
    next_transfer_state,
)
from modules.payments.manual_transfer_policy import (
    TransferState as S,
)

NOW = datetime(2026, 11, 18, 12, tzinfo=UTC)
DEADLINE = NOW + timedelta(hours=1)


def decide(state, action, **kwargs):
    options = {"now": NOW, "deadline": DEADLINE, **kwargs}
    return next_transfer_state(state, action, **options)


@pytest.mark.parametrize("state", [S.AWAITING_PROOF, S.REJECTED])
def test_submit_before_deadline(state):
    assert decide(state, A.SUBMIT) is S.PENDING_REVIEW


@pytest.mark.parametrize("state", [S.PENDING_REVIEW, S.APPROVED, S.EXPIRED, S.CANCELLED])
def test_cannot_submit_reviewed_or_terminal(state):
    with pytest.raises(TransferPolicyError):
        decide(state, A.SUBMIT)


def test_submit_reject_resubmit_approve():
    state = decide(S.AWAITING_PROOF, A.SUBMIT)
    state = decide(state, A.REJECT, rejection_reason="شماره پیگیری خوانا نیست")
    state = decide(state, A.SUBMIT)
    state = decide(
        state,
        A.APPROVE,
        bank_verified=True,
        expected_rial=100_000,
        received_rial=100_000,
        bank_reference="bank-ref-01",
    )
    assert state is S.APPROVED
    with pytest.raises(TransferPolicyError):
        decide(
            state,
            A.APPROVE,
            bank_verified=True,
            expected_rial=100_000,
            received_rial=100_000,
            bank_reference="bank-ref-01",
        )


@pytest.mark.parametrize("now", [DEADLINE, DEADLINE + timedelta(microseconds=1)])
def test_deadline_is_exclusive_for_submit(now):
    with pytest.raises(TransferPolicyError):
        decide(S.AWAITING_PROOF, A.SUBMIT, now=now)
    assert decide(S.AWAITING_PROOF, A.EXPIRE, now=now) is S.EXPIRED


def test_before_deadline_does_not_expire():
    with pytest.raises(TransferPolicyError):
        decide(S.AWAITING_PROOF, A.EXPIRE, now=DEADLINE - timedelta(microseconds=1))


@pytest.mark.parametrize("action", [A.EXPIRE, A.CANCEL])
def test_receipt_in_review_cannot_be_expired_or_cancelled(action):
    with pytest.raises(TransferPolicyError):
        decide(S.PENDING_REVIEW, action, now=DEADLINE)


@pytest.mark.parametrize("state", [S.APPROVED, S.EXPIRED, S.CANCELLED])
@pytest.mark.parametrize("action", list(A))
def test_terminal_states_never_transition(state, action):
    with pytest.raises(TransferPolicyError):
        decide(
            state,
            action,
            now=DEADLINE,
            rejection_reason="reason",
            bank_verified=True,
            expected_rial=1,
            received_rial=1,
            bank_reference="ref",
        )


@pytest.mark.parametrize("action", list(A))
def test_closed_order_never_transitions(action):
    with pytest.raises(TransferPolicyError):
        decide(
            S.PENDING_REVIEW if action in (A.APPROVE, A.REJECT) else S.AWAITING_PROOF,
            action,
            order_open=False,
            now=DEADLINE,
            bank_verified=True,
            expected_rial=1,
            received_rial=1,
            bank_reference="ref",
            rejection_reason="reason",
        )


@pytest.mark.parametrize(
    "overrides",
    [
        {"bank_verified": False},
        {"bank_verified": 1},
        {"expected_rial": 0},
        {"expected_rial": True},
        {"expected_rial": 1.0},
        {"received_rial": 99},
        {"received_rial": 101},
        {"received_rial": None},
        {"bank_reference": "  "},
        {"bank_reference": "x" * 81},
        {"bank_reference": None},
    ],
)
def test_approval_fails_closed_on_incomplete_verification(overrides):
    args = {
        "bank_verified": True,
        "expected_rial": 100,
        "received_rial": 100,
        "bank_reference": "valid",
        **overrides,
    }
    with pytest.raises(TransferPolicyError):
        decide(S.PENDING_REVIEW, A.APPROVE, **args)


def test_review_after_deadline_is_allowed_but_reupload_is_not():
    later = DEADLINE + timedelta(days=1)
    assert (
        decide(
            S.PENDING_REVIEW,
            A.APPROVE,
            now=later,
            bank_verified=True,
            expected_rial=1,
            received_rial=1,
            bank_reference="verified",
        )
        is S.APPROVED
    )
    rejected = decide(S.PENDING_REVIEW, A.REJECT, now=later, rejection_reason="invalid")
    with pytest.raises(TransferPolicyError):
        decide(rejected, A.SUBMIT, now=later)


@pytest.mark.parametrize("reason", ["", "   ", "x" * 501, None])
def test_rejection_requires_bounded_reason(reason):
    with pytest.raises(TransferPolicyError):
        decide(S.PENDING_REVIEW, A.REJECT, rejection_reason=reason)


@pytest.mark.parametrize("bad", [datetime(2026, 1, 1), None, "2026-01-01"])
def test_naive_or_invalid_timestamps_rejected(bad):
    with pytest.raises(TransferPolicyError):
        decide(S.AWAITING_PROOF, A.SUBMIT, now=bad)
    with pytest.raises(TransferPolicyError):
        decide(S.AWAITING_PROOF, A.SUBMIT, deadline=bad)


def test_aware_timestamps_compare_by_instant():
    same_deadline = DEADLINE.astimezone(timezone(timedelta(hours=3, minutes=30)))
    with pytest.raises(TransferPolicyError):
        decide(S.AWAITING_PROOF, A.SUBMIT, now=same_deadline)


@pytest.mark.parametrize(
    "state,action", [("pending_review", A.APPROVE), (S.PENDING_REVIEW, "approve")]
)
def test_untyped_state_or_action_rejected(state, action):
    with pytest.raises(TransferPolicyError):
        decide(state, action)
