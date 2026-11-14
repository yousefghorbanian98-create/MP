"""سرویس assessment — ارزیابی ۱۴ دامنه + JP7 (فرمول استاندارد جکسون-پولاک)."""

from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import ApiError, NotFoundError
from db.models import Assessment14Domain, DomainScore, JacksonPollockMeasurement, Member

SKINFOLD_SITES = ["chest", "triceps", "subscapular", "suprailiac", "abdomen", "thigh", "calf"]


def create_assessment(
    db: Session,
    member_id: int,
    scores: list[dict],
    coach_id: int | None = None,
    notes: str = "",
) -> Assessment14Domain:
    """ثبت ارزیابی — scores: [{'domain': 1..14, 'score': 0..5, 'notes': ''}]."""
    if db.get(Member, member_id) is None:
        raise NotFoundError("عضو یافت نشد")
    domains = [s["domain"] for s in scores]
    if sorted(domains) != list(range(1, 15)):
        raise ApiError("ارزیابی باید دقیقاً ۱۴ دامنه (۱..۱۴) داشته باشد", code="invalid_domains")
    flags = []
    total = 0
    for s in scores:
        if not (0 <= s["score"] <= 5):
            raise ApiError("نمره باید بین ۰ تا ۵ باشد", code="invalid_score")
        total += s["score"]
        if s["score"] <= 1 and s["domain"] in (1, 2, 3):  # دامنه‌های سلامتی حیاتی
            flags.append(f"red_flag_domain_{s['domain']}")
    assessment = Assessment14Domain(
        member_id=member_id,
        coach_id=coach_id,
        total_score=total,
        flags=json.dumps(flags, ensure_ascii=False),
        notes=notes,
        branch_id=1,
    )
    db.add(assessment)
    db.flush()
    for s in scores:
        db.add(
            DomainScore(
                assessment_id=assessment.id,
                domain=s["domain"],
                score=s["score"],
                notes=s.get("notes", ""),
            )
        )
    db.commit()
    db.refresh(assessment)
    return assessment


def get_assessment(db: Session, assessment_id: int, user=None) -> Assessment14Domain:
    a = db.get(Assessment14Domain, assessment_id)
    if a is None:
        raise NotFoundError("ارزیابی یافت نشد")
    from app.security.ownership import ensure_record_scope

    ensure_record_scope(db, user, a)
    return a


def list_member_assessments(db: Session, member_id: int, user=None) -> list[Assessment14Domain]:
    from app.security.ownership import ensure_member_scope

    ensure_member_scope(db, user, member_id)
    return list(
        db.scalars(
            select(Assessment14Domain)
            .where(Assessment14Domain.member_id == member_id)
            .order_by(Assessment14Domain.id.desc())
        )
    )


def jp7_body_fat(skinfolds_mm: dict, age: int, gender: str) -> float:
    """قفل‌شده طبق E07/D-012 — فقط از مسیر ثبتیهٔ تأییدشده (equations.py)."""
    from modules.assessment.equations import LOCKED_VERSION
    from modules.assessment.equations import jp7_body_fat as _locked

    # عمداً بدون equation_id: همیشه قفل تا ثبت مرجع مستقل
    return _locked(skinfolds_mm, age, gender, equation_id=LOCKED_VERSION)


def record_jp7(
    db: Session,
    member_id: int,
    skinfolds_mm: dict,
    age: int,
    gender: str,
    measured_by: int | None = None,
    quality: str | None = None,
    method: str | None = None,
) -> JacksonPollockMeasurement:
    """ثبت اندازه‌گیری خام ۷ نقطه — محاسبهٔ درصد چربی قفل است (D-012).

    دادهٔ خام mm + کیفیت + روش + نسخهٔ معادله ذخیره می‌شود؛ body_fat_pct تا تأیید
    مرجع مستقل None می‌ماند (E02/E07 — مقادیر نامعلوم با صفر/ساختگی جایگزین نمی‌شوند).
    """
    from modules.assessment.equations import LOCKED_VERSION, validate_jp7_raw

    if db.get(Member, member_id) is None:
        raise NotFoundError("عضو یافت نشد")
    clean = validate_jp7_raw(skinfolds_mm, gender)  # اعتبارسنجی خام — بدون محاسبه
    m = JacksonPollockMeasurement(
        member_id=member_id,
        age=age,
        gender=gender,
        skinfolds_mm=json.dumps(clean, ensure_ascii=False),
        body_fat_pct=None,  # قفل: معادله تأیید نشده (E07)
        equation_version=LOCKED_VERSION,
        quality=quality,
        method=method,
        measured_by=measured_by,
        branch_id=1,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return m
