"""تست‌های M36-c1 — مدل‌های ارزیابی ۱۴ توانایی + RBAC."""

from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError

from db.models.assessment import AxisAssessment, AxisScore, FieldTestResult
from security.rbac import enforce


def test_axis_assessment_models_roundtrip(session, make_user, make_member):
    user = make_user()
    member = make_member(user=user)
    assessment = AxisAssessment(member_id=member.id, status="draft", meta='{"rules":"axis-decision-1.0"}')
    session.add(assessment)
    session.flush()
    session.add(AxisScore(assessment_id=assessment.id, axis=7, score=32.5, quality="interpolated",
                          rule_version="axis-test-map-1.0"))
    session.add(AxisScore(assessment_id=assessment.id, axis=12, score=None, quality="missing",
                          rule_version="axis-test-map-1.0"))
    session.add(FieldTestResult(assessment_id=assessment.id, test_key="pushup_1min", raw_value=23.5,
                                unit="reps", percentile=37.5, quality="interpolated",
                                rule_version="axis-score-1.0", norm_source="https://fitnessnorms.com/strength/push-ups/"))
    session.commit()

    got = session.get(AxisAssessment, assessment.id)
    assert got.status == "draft"
    assert len(got.scores) == 2
    assert len(got.tests) == 1
    unknown = [s for s in got.scores if s.axis == 12][0]
    assert unknown.score is None  # نامعلوم = None، نه صفر
    assert unknown.quality == "missing"


def test_axis_score_unique_per_axis(session, make_user, make_member):
    user = make_user()
    member = make_member(user=user)
    assessment = AxisAssessment(member_id=member.id)
    session.add(assessment)
    session.flush()
    session.add(AxisScore(assessment_id=assessment.id, axis=3, score=50.0, quality="exact"))
    session.commit()
    session.add(AxisScore(assessment_id=assessment.id, axis=3, score=60.0, quality="exact"))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_rbac_axis_assessments_matrix() -> None:
    assert enforce("coach", "/api/v1/axis-assessments", "POST")
    assert enforce("coach", "/api/v1/axis-assessments/5/matrix", "GET")
    assert enforce("manager", "/api/v1/axis-assessments", "POST")
    assert enforce("member", "/api/v1/axis-assessments/5/matrix", "GET")
    assert not enforce("member", "/api/v1/axis-assessments", "POST")
    assert not enforce("reception", "/api/v1/axis-assessments", "POST")
    assert not enforce("reception", "/api/v1/axis-assessments/5/matrix", "GET")
