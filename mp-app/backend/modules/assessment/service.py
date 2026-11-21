"""سرویس assessment — ارزیابی ۱۴ دامنه + JP7 (فرمول استاندارد جکسون-پولاک)."""

from __future__ import annotations

import json
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import ApiError, NotFoundError
from app.metrics import metrics
from db.models import (
    Assessment14Domain,
    DomainScore,
    JacksonPollockMeasurement,
    LimbMeasurement,
    Member,
)

SKINFOLD_SITES = ["chest", "triceps", "subscapular", "suprailiac", "abdomen", "thigh", "calf"]

_log = logging.getLogger(__name__)


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


# ── G6 — روندنمای JP7 + تفسیر خودکار [finn] ──

JP7_TREND_VERSION = "jp7-trend-1.0"

# آستانهٔ تغییر مجموع چین‌ها. ۲ میلی‌متر کمتر از خطای اندازه‌گیری
# پوست‌چین با کالیپر است، پس کمتر از آن «تغییر» نامیده نمی‌شود.
JP7_SUM_CHANGE_MM = 2.0


def jp7_trend(db: Session, *, member_id: int, user=None) -> dict:
    """روند تغییر چین‌های پوستی + تفسیر خودکار (G6).

    ## چرا روی «مجموع چین خام» و نه درصد چربی
    `body_fat_pct` عمداً قفل است (E07/D-012): معادلهٔ جکسون-پولاک تا
    تأیید مرجع مستقل ذخیره نمی‌شود. اگر روند را روی درصد چربیِ ساختگی
    بسازیم، همان کار ممنوعه را در ظاهر دیگر انجام داده‌ایم. مجموع هفت چین
    یک عدد خام، قابل بازبینی و بی‌ادعاست.

    ## تفکیک مهم
    کاهش مجموع ⇒ کاهش بافت زیرجلدی (خبر خوب برای کاهش وزن).
    افزایش مجموع ⇒ افزایش بافت. ولی *کاهش* چین‌ها همراه با *افت قدرت*
    می‌تواند تحلیل عضله باشد — چون قدرت داده‌اش در دست نیست، این را
    نمی‌توان از JP7 تنها نتیجه گرفت؛ صریحاً گفته می‌شود.
    """
    import json

    from app.security.ownership import ensure_member_scope
    from db.models import JacksonPollockMeasurement

    ensure_member_scope(db, user, member_id)

    rows = list(
        db.scalars(
            select(JacksonPollockMeasurement)
            .where(JacksonPollockMeasurement.member_id == member_id)
            .order_by(JacksonPollockMeasurement.measured_at)
        ).all()
    )

    points = []
    for r in rows:
        try:
            folds = json.loads(r.skinfolds_mm)
        except (TypeError, ValueError):
            # WP 2.5 / F‑17: ردیف خراب حذف می‌شود، ولی بی‌صدا نیست — لاگ + شمارنده.
            _log.warning("JP7 row %s skipped: unreadable skinfolds_mm", r.id)
            metrics.inc("assessment_jp7_rows_skipped")
            continue
        total = sum(float(v) for v in folds.values())
        points.append(
            {
                "id": r.id,
                "measured_at": r.measured_at.isoformat() if r.measured_at else None,
                "sum_mm": round(total, 1),
                "sites": {k: float(v) for k, v in folds.items()},
                "body_fat_pct": r.body_fat_pct,  # None = قفل، صادقانه برمی‌گردد
            }
        )

    if len(points) < 2:
        return {
            "member_id": member_id,
            "measurements": points,
            "trend": None,
            "interpretation": {
                "status": "insufficient",
                "headline": "برای تفسیر روند حداقل دو اندازه‌گیری لازم است",
                "detail": (f"فقط {len(points)} اندازه‌گیری ثبت شده. یک نقطه، روند نیست."),
                "confidence": "insufficient",
            },
            "data_state": "insufficient_measurements",
            "body_fat_note": (
                "درصد چربی محاسبه نشده و نمایش داده نمی‌شود: معادله تا تأیید "
                "مرجع مستقل قفل است (D-012). روند از مجموع چین خام ساخته می‌شود."
            ),
            "rule_version": JP7_TREND_VERSION,
        }

    first, last = points[0], points[-1]
    delta_mm = round(last["sum_mm"] - first["sum_mm"], 1)
    days = 0
    if first["measured_at"] and last["measured_at"]:
        from datetime import datetime

        d0 = datetime.fromisoformat(first["measured_at"])
        d1 = datetime.fromisoformat(last["measured_at"])
        days = max(0, (d1 - d0).days)
    per_week = round(delta_mm / (days / 7), 2) if days >= 7 else None

    # تفسیر خودکار — با آستانهٔ خطای اندازه‌گیری
    if abs(delta_mm) < JP7_SUM_CHANGE_MM:
        status = "stable"
        headline = "تغییر معناداری در چین‌های پوستی نیست"
        detail = (
            f"اختلاف مجموع {delta_mm:+.1f} میلی‌متر است و کمتر از آستانهٔ "
            f"{JP7_SUM_CHANGE_MM:.0f} میلی‌متر (خطای اندازه‌گیری کالیپر) — "
            "به‌عنوان «بدون تغییر» تفسیر می‌شود."
        )
        confidence = "high" if days >= 28 else "medium"
    elif delta_mm < 0:
        status = "decreasing"
        headline = "بافت زیرجلدی کاهش یافته است"
        detail = (
            f"مجموع چین‌ها {abs(delta_mm):.1f} میلی‌متر کم شده"
            + (f" ({abs(per_week):.2f} میلی‌متر در هفته)" if per_week is not None else "")
            + ". این با کاهش چربی سازگار است — ولی کاهش چین همراه با افت قدرت "
            "می‌تواند تحلیل عضله باشد؛ قدرت/حجم را جدا بررسی کنید."
        )
        confidence = "high" if days >= 42 else "medium"
    else:
        status = "increasing"
        headline = "بافت زیرجلدی افزایش یافته است"
        detail = (
            f"مجموع چین‌ها {delta_mm:.1f} میلی‌متر بیشتر شده"
            + (f" ({per_week:.2f} میلی‌متر در هفته)" if per_week is not None else "")
            + ". در هدف افزایش حجم این تا حدی طبیعی است؛ اگر سرعتش بیشتر از "
            "حد انتظار است، کالری را بازبینی کنید."
        )
        confidence = "high" if days >= 42 else "medium"

    # کدام ناحیه بیشترین تغییر را داشت — قابل اقدام برای مربی
    site_deltas = {
        site: {
            "first_mm": first["sites"].get(site),
            "last_mm": last["sites"].get(site),
            "delta_mm": round((last["sites"].get(site) or 0) - (first["sites"].get(site) or 0), 1),
        }
        for site in sorted(set(first["sites"]) | set(last["sites"]))
    }
    biggest = max(site_deltas.items(), key=lambda kv: abs(kv[1]["delta_mm"]))

    return {
        "member_id": member_id,
        "measurements": points,
        "trend": {
            "first_at": first["measured_at"],
            "last_at": last["measured_at"],
            "span_days": days,
            "first_sum_mm": first["sum_mm"],
            "last_sum_mm": last["sum_mm"],
            "delta_mm": delta_mm,
            "delta_mm_per_week": per_week,
            "biggest_change_site": biggest[0],
            "biggest_change_mm": biggest[1]["delta_mm"],
        },
        "site_deltas": site_deltas,
        "interpretation": {
            "status": status,
            "headline": headline,
            "detail": detail,
            "confidence": confidence,
            "threshold_mm": JP7_SUM_CHANGE_MM,
            "suggestion": (
                f"بیشترین تغییر در «{biggest[0]}» ({biggest[1]['delta_mm']:+.1f} میلی‌متر) — "
                "همان ناحیه را در اندازه‌گیری بعدی با همان روش و همان کالیپر تکرار کنید"
                if abs(biggest[1]["delta_mm"]) >= JP7_SUM_CHANGE_MM
                else "برای دیدن تغییر واقعی، اندازه‌گیری بعدی را با همان روش تکرار کنید"
            ),
        },
        "data_state": "trend_available",
        "body_fat_note": (
            "درصد چربی محاسبه نشده و نمایش داده نمی‌شود: معادله تا تأیید "
            "مرجع مستقل قفل است (D-012). روند از مجموع چین خام ساخته می‌شود."
        ),
        "rule_version": JP7_TREND_VERSION,
    }


# ── M54-c1 — آنالیز سگمنتال آنتروپومتریک (D-024) ──

SEGMENTAL_REPORT_VERSION = "segmental-report-1.0"

LIMB_FIELDS = (
    "neck_cm",
    "chest_cm",
    "waist_cm",
    "hip_cm",
    "upper_arm_right_cm",
    "upper_arm_left_cm",
    "thigh_right_cm",
    "thigh_left_cm",
    "calf_right_cm",
    "calf_left_cm",
)


def record_limb_measurement(
    db: Session,
    *,
    member_id: int,
    values: dict,
    user=None,
    quality: str | None = None,
    notes: str = "",
) -> LimbMeasurement:
    """ثبت محیط‌های اندام. حداقل یک محیط لازم است — رکورد خالی معنا ندارد."""
    from app.errors import ApiError
    from app.security.ownership import ensure_member_scope
    from db.models import LimbMeasurement, Member

    ensure_member_scope(db, user, member_id)
    if db.get(Member, member_id) is None:
        raise NotFoundError("عضو یافت نشد")

    clean = {k: values.get(k) for k in LIMB_FIELDS}
    if all(v is None for v in clean.values()):
        raise ApiError("حداقل یک محیط اندام باید ثبت شود", code="no_measurement")
    for k, v in clean.items():
        if v is not None and (v <= 0 or v > 300):
            raise ApiError(f"مقدار {k} خارج از بازهٔ معقول است", code="out_of_range")

    row = LimbMeasurement(
        member_id=member_id,
        quality=quality,
        notes=notes or "",
        measured_by=getattr(user, "id", None),
        **clean,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def limb_dict(row: LimbMeasurement) -> dict:
    return {
        "id": row.id,
        "member_id": row.member_id,
        "measured_at": row.measured_at.isoformat() if row.measured_at else None,
        **{k: getattr(row, k) for k in LIMB_FIELDS},
        "quality": row.quality,
        "notes": row.notes,
    }


def segmental_report(db: Session, *, member_id: int, user=None) -> dict:
    """آخرین اندازه‌گیری + تحلیل + روند بین همهٔ اندازه‌گیری‌ها."""
    from app.security.ownership import ensure_member_scope
    from db.models import LimbMeasurement, Member
    from engine import segmental

    ensure_member_scope(db, user, member_id)
    member = db.get(Member, member_id)
    if member is None:
        raise NotFoundError("عضو یافت نشد")

    rows = list(
        db.scalars(
            select(LimbMeasurement)
            .where(LimbMeasurement.member_id == member_id)
            .order_by(LimbMeasurement.measured_at.asc(), LimbMeasurement.id.asc())
        ).all()
    )

    if not rows:
        return {
            "member_id": member_id,
            "latest": None,
            "analysis": None,
            "trend": None,
            "measurements_count": 0,
            "reason": "هیچ اندازه‌گیری محیط اندامی برای این عضو ثبت نشده است",
            "note": "برای نمایش تحلیل، حداقل یک اندازه‌گیری محیطی لازم است",
            "rule_version": SEGMENTAL_REPORT_VERSION,
        }

    latest = rows[-1]
    points = [
        {
            "measured_at": r.measured_at,
            **{k: getattr(r, k) for k in LIMB_FIELDS},
        }
        for r in rows
    ]
    analysis = segmental.analyze(
        {k: getattr(latest, k) for k in LIMB_FIELDS},
        height_cm=member.height_cm,
        gender=member.gender,
    )
    return {
        "member_id": member_id,
        "latest": limb_dict(latest),
        "analysis": analysis,
        "trend": segmental.trend(points),
        "measurements_count": len(rows),
        "reason": "تحلیل بر پایهٔ آخرین اندازه‌گیری",
        "note": analysis["note"],
        "rule_version": SEGMENTAL_REPORT_VERSION,
    }
