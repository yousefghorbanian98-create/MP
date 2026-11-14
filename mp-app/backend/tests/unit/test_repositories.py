"""تست‌های لایهٔ Repository (M05)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from db.models import Member, Membership, Payment, User
from modules.assessment.repository import AssessmentRepository, Jp7Repository
from modules.membership.repository import MemberRepository, MembershipRepository
from modules.payments.repository import PaymentRepository, WalletRepository


def test_member_repository(session):
    repo = MemberRepository(session)
    user = User(phone="09120000010", full_name="x", role="member")
    session.add(user)
    session.flush()
    member = Member(user_id=user.id, goal="g")
    session.add(member)
    session.commit()
    assert repo.get(member.id) is not None
    assert repo.get_by_phone("09120000010") is not None
    assert repo.get(99999) is None
    assert len(repo.list()) >= 1


def test_membership_repository_active_and_history(session):
    user = User(phone="09120000011", full_name="x", role="member")
    session.add(user)
    session.flush()
    member = Member(user_id=user.id, goal="g")
    session.add(member)
    session.flush()
    now = datetime.now(UTC)
    ms = Membership(
        member_id=member.id,
        plan_name="m",
        started_at=now,
        expires_at=now + timedelta(days=5),
        status="active",
    )
    session.add(ms)
    session.commit()
    repo = MembershipRepository(session)
    assert repo.active_for_member(member.id) is not None
    assert repo.active_for_member(99999) is None
    assert len(repo.history(member.id)) == 1


def test_payment_repository_filters(session):
    user = User(phone="09120000012", full_name="x", role="member")
    session.add(user)
    session.flush()
    member = Member(user_id=user.id, goal="g")
    session.add(member)
    session.flush()
    session.add(Payment(member_id=member.id, amount_rial=1000, status="paid", branch_id=1))
    session.add(Payment(member_id=member.id, amount_rial=2000, status="pending", branch_id=1))
    session.commit()
    repo = PaymentRepository(session)
    assert len(repo.list(member_id=member.id)) == 2
    assert len(repo.list(member_id=member.id, status="paid")) == 1
    assert repo.get(1) is not None


def test_wallet_repository_balance(session):
    from db.models import WalletTransaction

    user = User(phone="09120000013", full_name="x", role="member")
    session.add(user)
    session.flush()
    member = Member(user_id=user.id, goal="g")
    session.add(member)
    session.flush()
    repo = WalletRepository(session)
    repo.add(WalletTransaction(member_id=member.id, amount_rial=5000, kind="credit"))
    assert sum(t.amount_rial for t in repo.entries(member.id)) == 5000


def test_assessment_repositories(session):
    user = User(phone="09120000014", full_name="x", role="member")
    session.add(user)
    session.flush()
    member = Member(user_id=user.id, goal="g")
    session.add(member)
    session.flush()
    from db.models import Assessment14Domain

    a = Assessment14Domain(member_id=member.id, total_score=30)
    session.add(a)
    session.commit()
    repo = AssessmentRepository(session)
    assert repo.get(a.id) is not None
    assert repo.latest(member.id) is not None
    assert len(repo.list_by_member(member.id)) == 1
    assert Jp7Repository(session).history(member.id) == []
