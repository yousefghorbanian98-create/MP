"""منطق ارزیابی ۱۴ توانایی — ثبت آزمون، امتیازدهی، ماتریس (M36-c2).

زنجیرهٔ داده←قاعده←شاهد←تصمیم:
    آزمون خام ← نُرم مستند (norm_entries + منبع) ← engine.scoring ← engine.axis_map
    ← engine.axis_rules (تصمیم چهارگانه + دلیل)
«داده ناشناخته است نه صفر»: نمرهٔ نامعلوم = None + quality=missing.
"""

from __future__ import annotations

import json
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import ApiError, NotFoundError
from db.models.assessment import AxisAssessment, AxisScore, FieldTestResult, NormEntry
from db.models.membership import Member
from engine.axis_map import AXIS_MAP_VERSION, aggregate_axis_scores
from engine.axis_rules import AXES_FA, decide_axis
from engine.scoring import SCORE_VERSION, estimate_percentile


def _member_age_sex(member: Member) -> tuple[int, str]:
    """سن و جنس عضو برای نگاشت نُرم — هر کدام نامعلوم ← خطای صریح."""
    if member.birth_date is None:
        raise ApiError("تاریخ تولد عضو ثبت نشده — داده ناشناخته است نه صفر", code="missing_birthdate")
    today = date.today()
    age = today.year - member.birth_date.year - (
        (today.month, today.day) < (member.birth_date.month, member.birth_date.day)
    )
    gender = (member.gender or "").lower()
    if gender in ("male", "m", "مرد"):
        sex = "m"
    elif gender in ("female", "f", "زن"):
        sex = "f"
    else:
        raise ApiError("جنسیت عضو ثبت نشده — نگاشت نُرم ناممکن است", code="missing_gender")
    return age, sex


def _find_norm(db: Session, test_key: str, sex: str, age: int) -> NormEntry:
    """ردیف نُرم مناسب: دقیق جنس/سن ← all/همه‌سن ← خطای صریح."""
    row = db.scalars(
        select(NormEntry).where(
            NormEntry.test_key == test_key,
            NormEntry.sex == sex,
            NormEntry.age_min <= age,
            NormEntry.age_max >= age,
        )
    ).first()
    if row is None:
        row = db.scalars(
            select(NormEntry).where(
                NormEntry.test_key == test_key,
                NormEntry.sex == "all",
            )
        ).first()
    if row is None:
        raise ApiError(
            f"نُرم برای آزمون {test_key} با جنس {sex} و سن {age} موجود نیست",
            code="missing_norm",
        )
    return row


def create_assessment(
    db: Session,
    *,
    member_id: int,
    tests: list[dict],
    notes: str = "",
    user=None,
) -> dict:
    from app.security.ownership import ensure_member_scope

    ensure_member_scope(db, user, member_id)
    member = db.get(Member, member_id)
    if member is None:
        raise NotFoundError("عضو یافت نشد")
    age, sex = _member_age_sex(member)

    assessment = AxisAssessment(member_id=member_id, status="draft", notes=notes)
    if user is not None and getattr(user, "role", "") in ("coach", "manager", "admin"):
        assessment.coach_id = user.id
    db.add(assessment)
    db.flush()

    test_scores: dict[str, dict] = {}
    seen: set[str] = set()
    for item in tests:
        test_key = item["test_key"]
        if test_key in seen:
            raise ApiError(f"آزمون {test_key} تکراری است", code="duplicate_test")
        seen.add(test_key)
        norm = _find_norm(db, test_key, sex, age)
        if norm.method == "criterion":
            raw = item["raw_value"]
            if not 0 <= raw <= 100:
                raise ApiError(
                    f"امتیاز rubric {test_key} باید بین ۰ و ۱۰۰ باشد", code="invalid_raw"
                )
            percentile_val: float | None = None
            quality = "criterion"
            score_val = raw
        else:
            estimate = estimate_percentile(
                raw_value=item["raw_value"],
                percentiles={k: float(v) for k, v in json.loads(norm.percentiles).items()},
                direction=norm.direction,
            )
            percentile_val = estimate["percentile"]
            quality = estimate["quality"]
            score_val = estimate["percentile"]
        test_scores[test_key] = {"score": score_val, "quality": quality, "method": norm.method}
        db.add(
            FieldTestResult(
                assessment_id=assessment.id,
                test_key=test_key,
                raw_value=item["raw_value"],
                unit=norm.unit,
                percentile=percentile_val,
                quality=quality,
                rule_version=SCORE_VERSION,
                norm_source=norm.source,
                measured_by=getattr(user, "id", None),
                notes=item.get("notes", ""),
            )
        )

    axis_results = aggregate_axis_scores(test_scores)
    for axis, result in axis_results.items():
        db.add(
            AxisScore(
                assessment_id=assessment.id,
                axis=axis,
                score=result["score"],
                quality=result["quality"],
                rule_version=AXIS_MAP_VERSION,
            )
        )
    assessment.meta = json.dumps(
        {"age": age, "sex": sex, "score_engine": SCORE_VERSION, "axis_map": AXIS_MAP_VERSION},
        ensure_ascii=False,
    )
    assessment.status = "completed"
    db.commit()
    db.refresh(assessment)
    return get_matrix(db, assessment.id, user=user)


def _axis_rows(db: Session, assessment: AxisAssessment) -> list[dict]:
    rows = []
    for axis in sorted(AXES_FA):
        score_row = db.scalars(
            select(AxisScore).where(
                AxisScore.assessment_id == assessment.id, AxisScore.axis == axis
            )
        ).first()
        score = score_row.score if score_row else None
        quality = score_row.quality if score_row else "missing"
        if score is None:
            decision = {
                "state": "unknown",
                "reason": f"محور {axis} ({AXES_FA[axis]}) آزمون داده‌دار ندارد — نامعلوم، نه صفر",
            }
        else:
            decision = decide_axis(axis=axis, score=score)
        rows.append(
            {
                "axis": axis,
                "name_fa": AXES_FA[axis],
                "score": score,
                "quality": quality,
                "decision_state": decision["state"],
                "decision_reason": decision["reason"],
            }
        )
    return rows


def get_matrix(db: Session, assessment_id: int, user=None) -> dict:
    from app.security.ownership import ensure_record_scope

    assessment = db.get(AxisAssessment, assessment_id)
    if assessment is None:
        raise NotFoundError("ارزیابی یافت نشد")
    ensure_record_scope(db, user, assessment)
    axes = _axis_rows(db, assessment)
    summary: dict[str, int] = {}
    for row in axes:
        summary[row["decision_state"]] = summary.get(row["decision_state"], 0) + 1
    return {
        "assessment_id": assessment.id,
        "member_id": assessment.member_id,
        "status": assessment.status,
        "axes": axes,
        "summary": summary,
        "rule_versions": {"score": SCORE_VERSION, "axis_map": AXIS_MAP_VERSION, "decision": "axis-decision-1.0"},
    }


def list_member_history(db: Session, member_id: int, user=None) -> list[dict]:
    from app.security.ownership import ensure_member_scope

    ensure_member_scope(db, user, member_id)
    assessments = db.scalars(
        select(AxisAssessment)
        .where(AxisAssessment.member_id == member_id)
        .order_by(AxisAssessment.id.desc())
    ).all()
    return [
        {
            "assessment_id": a.id,
            "member_id": a.member_id,
            "status": a.status,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in assessments
    ]
