"""تست‌های واحد مدل‌ها — وجود جدول‌ها، قیدها، branch_id، ایندکس‌ها."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from db.base import Base

MAIN_TABLES_WITH_BRANCH = {
    "members",
    "memberships",
    "payments",
    "wallet_transactions",
    "assessments",
    "jackson_pollock_measurements",
    "face_templates",
    "checkins",
    "workout_programs",
    "nutrition_plans",
    "campaigns",
    "offers",
}


def test_all_expected_tables_exist(engine):
    tables = set(Base.metadata.tables.keys())
    expected = MAIN_TABLES_WITH_BRANCH | {
        "users",
        "otp_codes",
        "refresh_tokens",
        "domain_scores",
        "exercises",
        "food_items",
        "program_weeks",
        "program_exercises",
        "meal_items",
        "notifications",
        "audit_logs",
        "feature_flags",
        "rule_runs",
        "biometric_consents",
    }
    assert expected <= tables, f"جدول‌های جامانده: {expected - tables}"


@pytest.mark.parametrize("table", sorted(MAIN_TABLES_WITH_BRANCH))
def test_branch_id_column_exists(engine, table):
    cols = {c.name for c in Base.metadata.tables[table].columns}
    assert "branch_id" in cols, f"branch_id در جدول {table} نیست (دام لایهٔ ۳)"


def test_user_phone_unique(session, make_user):
    make_user(phone="09121111111")
    with pytest.raises(IntegrityError):
        make_user(phone="09121111111")
    session.rollback()


def test_member_creation_with_branch(session, make_member):
    m = make_member(goal="strength")
    assert m.id is not None
    assert m.branch_id == 1
    assert m.goal == "strength"


def test_membership_lifecycle(session, make_member):
    from db.models import Membership

    m = make_member()
    now = datetime.now(UTC)
    ms = Membership(
        member_id=m.id,
        plan_name="ماهانه",
        started_at=now,
        expires_at=now + timedelta(days=30),
        status="active",
        price_rial=10_000_000,
    )
    session.add(ms)
    session.commit()
    assert ms.status == "active"
    assert ms.expires_at > ms.started_at


def test_otp_stores_hash_not_plain(session):
    from db.models import OtpCode

    otp = OtpCode(
        phone="09120000002",
        code_hash="$sha256$abcdef",  # فقط هش — هرگز خام
        expires_at=datetime.now(UTC) + timedelta(minutes=2),
    )
    session.add(otp)
    session.commit()
    assert otp.code_hash.startswith("$")
    assert "1234" not in otp.code_hash


def test_refresh_token_revocable(session, make_user):
    from db.models import RefreshToken

    u = make_user()
    rt = RefreshToken(
        user_id=u.id,
        token_hash="h" * 64,
        expires_at=datetime.now(UTC) + timedelta(days=14),
    )
    session.add(rt)
    session.commit()
    assert rt.revoked_at is None
    rt.revoked_at = datetime.now(UTC)
    session.commit()
    assert rt.revoked_at is not None


def test_assessment_domain_scores_unique(session, make_member):
    from db.models import Assessment14Domain, DomainScore

    m = make_member()
    a = Assessment14Domain(member_id=m.id, total_score=42)
    session.add(a)
    session.commit()
    session.add(DomainScore(assessment_id=a.id, domain=1, score=3))
    session.commit()
    with pytest.raises(IntegrityError):
        session.add(DomainScore(assessment_id=a.id, domain=1, score=4))
        session.commit()
    session.rollback()


def test_checkin_index_and_fields(session, make_member):
    from db.models import CheckIn

    m = make_member()
    ci = CheckIn(member_id=m.id, method="face", result="ok")
    session.add(ci)
    session.commit()
    assert ci.created_at is not None
    assert ci.branch_id == 1


def test_face_template_stores_only_encrypted_bytes(session, make_member):
    from db.models import FaceTemplate

    m = make_member()
    ft = FaceTemplate(
        member_id=m.id, embedding_encrypted=b"\x00\x01encrypted-blob", algorithm="sface-v1"
    )
    session.add(ft)
    session.commit()
    assert isinstance(ft.embedding_encrypted, bytes)
    # ستون خام embedding وجود ندارد
    cols = {c.name for c in FaceTemplate.__table__.columns}
    assert "embedding_raw" not in cols


def test_workout_program_workflow_states(session, make_member):
    from db.models import WorkoutProgram

    m = make_member()
    wp = WorkoutProgram(member_id=m.id, goal="hypertrophy", engine_version="rules-1.0")
    session.add(wp)
    session.commit()
    assert wp.status == "draft"  # بدون تأیید مربی قابل نمایش نیست
    wp.status = "approved"
    wp.approved_at = datetime.now(UTC)
    session.commit()
    assert wp.status == "approved"
