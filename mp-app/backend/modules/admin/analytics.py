"""تحلیل‌های مدیریتی ادمین (M42-c1) — لیدربوردها از دادهٔ واقعی DB.

هر رتبه با method صریح برمی‌گردد؛ اعضای بدون داده اصلاً در فهرست نمی‌آیند
(«داده ناشناخته است نه صفر» — E05). هیچ عددی از LLM نمی‌آید (E04).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from db.models import AxisAssessment, AxisScore, CheckIn, Member, Payment, User

ANALYTICS_VERSION = "admin-analytics-1.0"
DEFAULT_WINDOW_DAYS = 30


def _member_names(db: Session, ids: list[int]) -> dict[int, str]:
    if not ids:
        return {}
    rows = db.execute(select(User.id, User.full_name).where(User.id.in_(ids))).all()
    return dict(rows)


def top_athletes(db: Session, *, limit: int = 10) -> list[dict]:
    """بهترین ورزشکارها: میانگین نمرهٔ محورهای موجود در آخرین ارزیابی هر عضو.

    نمرهٔ missing (None) در میانگین لحاظ نمی‌شود؛ عضو بدون ارزیابی حذف می‌شود.
    """
    latest_ids = db.execute(
        select(func.max(AxisAssessment.id)).group_by(AxisAssessment.member_id)
    ).scalars().all()
    if not latest_ids:
        return []
    rows = db.execute(
        select(
            AxisAssessment.member_id,
            func.avg(AxisScore.score),
            func.count(AxisScore.id),
        )
        .join(AxisScore, AxisScore.assessment_id == AxisAssessment.id)
        .where(
            AxisAssessment.id.in_(latest_ids),
            AxisScore.score.is_not(None),
        )
        .group_by(AxisAssessment.member_id)
        .order_by(func.avg(AxisScore.score).desc())
        .limit(limit)
    ).all()
    names = _member_names(db, [r[0] for r in rows])
    return [
        {
            "member_id": mid,
            "full_name": names.get(mid, ""),
            "avg_axis_score": round(float(avg), 1),
            "axes_counted": int(cnt),
            "method": "میانگین نمرهٔ محورهای موجود در آخرین ارزیابی ۱۴ محوره",
        }
        for mid, avg, cnt in rows
    ]


def top_spenders(db: Session, *, limit: int = 10, window_days: int | None = None) -> list[dict]:
    """بیشترین هزینه: جمع پرداخت‌های paid — در صورت window، فقط بازهٔ اخیر."""
    stmt = (
        select(
            Payment.member_id,
            func.sum(Payment.amount_rial),
            func.count(Payment.id),
            func.max(Payment.paid_at),
        )
        .where(Payment.status == "paid")
    )
    if window_days is not None:
        stmt = stmt.where(Payment.paid_at >= datetime.now(UTC) - timedelta(days=window_days))
    rows = db.execute(
        stmt.group_by(Payment.member_id)
        .order_by(func.sum(Payment.amount_rial).desc())
        .limit(limit)
    ).all()
    names = _member_names(db, [r[0] for r in rows])
    return [
        {
            "member_id": mid,
            "full_name": names.get(mid, ""),
            "total_paid_rial": int(total),
            "payments_count": int(cnt),
            "last_paid_at": last.isoformat() if last else None,
            "method": (
                f"جمع پرداخت‌های paid در {window_days} روز اخیر"
                if window_days
                else "جمع همهٔ پرداخت‌های paid"
            ),
        }
        for mid, total, cnt, last in rows
    ]


def most_visits(db: Session, *, limit: int = 10, window_days: int = DEFAULT_WINDOW_DAYS) -> list[dict]:
    """بیشترین مراجعه: چک‌این‌های ok در بازه + تعداد روزهای متمایز (حضور منظم)."""
    since = datetime.now(UTC) - timedelta(days=window_days)
    rows = db.execute(
        select(
            CheckIn.member_id,
            func.count(CheckIn.id),
            func.count(func.date(CheckIn.created_at)),
        )
        .where(CheckIn.result == "ok", CheckIn.created_at >= since)
        .group_by(CheckIn.member_id)
        .order_by(func.count(CheckIn.id).desc())
        .limit(limit)
    ).all()
    names = _member_names(db, [r[0] for r in rows])
    return [
        {
            "member_id": mid,
            "full_name": names.get(mid, ""),
            "visits": int(visits),
            "distinct_days": int(days),
            "method": f"چک‌این‌های موفق {window_days} روز اخیر (تعداد مراجعه و روزهای متمایز)",
        }
        for mid, visits, days in rows
    ]


def most_time(db: Session, *, limit: int = 10, window_days: int = DEFAULT_WINDOW_DAYS) -> list[dict]:
    """بیشترین تایم باشگاه: مجموع دقیقهٔ جلسات بسته‌شده (خروج ثبت‌شده).

    جلسات باز (بدون خروج) دقیقه ندارند — «نامعلوم» است نه صفر؛ شمارش‌شان جدا برمی‌گردد.
    محاسبه در پایتون (سازگار با SQLite و Postgres — بدون توابع گویش‌محور).
    """
    since = datetime.now(UTC) - timedelta(days=window_days)
    sessions = db.execute(
        select(CheckIn.member_id, CheckIn.created_at, CheckIn.checked_out_at, CheckIn.id)
        .where(
            CheckIn.result == "ok",
            CheckIn.created_at >= since,
            CheckIn.checked_out_at.is_not(None),
        )
    ).all()
    totals: dict[int, dict] = {}
    for mid, started, ended, _cid in sessions:
        entry = totals.setdefault(mid, {"minutes": 0.0, "closed": 0})
        start = started if started.tzinfo else started.replace(tzinfo=UTC)
        end = ended if ended.tzinfo else ended.replace(tzinfo=UTC)
        entry["minutes"] += (end - start).total_seconds() / 60.0
        entry["closed"] += 1
    open_rows = db.execute(
        select(CheckIn.member_id, func.count(CheckIn.id))
        .where(
            CheckIn.result == "ok",
            CheckIn.created_at >= since,
            CheckIn.checked_out_at.is_(None),
        )
        .group_by(CheckIn.member_id)
    ).all()
    open_by_member = dict(open_rows)
    ranked = sorted(totals.items(), key=lambda kv: kv[1]["minutes"], reverse=True)[:limit]
    names = _member_names(db, [mid for mid, _ in ranked])
    return [
        {
            "member_id": mid,
            "full_name": names.get(mid, ""),
            "total_minutes": int(data["minutes"]),
            "closed_sessions": int(data["closed"]),
            "open_sessions": int(open_by_member.get(mid, 0)),
            "method": (
                f"مجموع دقیقهٔ جلسات بسته‌شده (ورود تا خروج ثبت‌شده) در {window_days} روز اخیر — "
                "جلسات باز دقیقه ندارند (نامعلوم ≠ صفر)"
            ),
        }
        for mid, data in ranked
    ]


def leaderboards(db: Session, *, limit: int = 10, window_days: int = DEFAULT_WINDOW_DAYS) -> dict:
    return {
        "top_athletes": top_athletes(db, limit=limit),
        "top_spenders": top_spenders(db, limit=limit, window_days=window_days),
        "most_visits": most_visits(db, limit=limit, window_days=window_days),
        "most_time": most_time(db, limit=limit, window_days=window_days),
        "window_days": window_days,
        "rule_version": ANALYTICS_VERSION,
        "generated_at": datetime.now(UTC).isoformat(),
    }


def collect_member_facts(db: Session, *, window_days: int = DEFAULT_WINDOW_DAYS) -> dict[int, dict]:
    """واقعیت‌های ریسک ریزش هر عضو از DB — هر مقدار ممکن است None (ناشناخته)."""
    from db.models import Membership, SetFeedback, WorkoutProgram

    now = datetime.now(UTC)
    since30 = now - timedelta(days=window_days)
    since60 = now - timedelta(days=2 * window_days)
    facts: dict[int, dict] = {}

    def entry(mid: int) -> dict:
        return facts.setdefault(mid, {
            "last_checkin_days_ago": None,
            "days_to_expiry": None,
            "overdue_payments": None,
            "visits_30d": None,
            "visits_prev_30d": None,
            "has_active_program": None,
            "days_since_feedback": None,
        })

    # همهٔ اعضا حاضرند — حتی بدون هیچ سیگنالی (unknown ≠ نبود در فهرست)
    for mid, in db.execute(select(Member.id)).all():
        entry(mid)

    for mid, created in db.execute(
        select(CheckIn.member_id, func.max(CheckIn.created_at)).where(CheckIn.result == "ok").group_by(CheckIn.member_id)
    ).all():
        ts = created if created.tzinfo else created.replace(tzinfo=UTC)
        entry(mid)["last_checkin_days_ago"] = (now - ts).days

    for mid, count in db.execute(
        select(CheckIn.member_id, func.count(CheckIn.id))
        .where(CheckIn.result == "ok", CheckIn.created_at >= since30)
        .group_by(CheckIn.member_id)
    ).all():
        entry(mid)["visits_30d"] = int(count)

    for mid, count in db.execute(
        select(CheckIn.member_id, func.count(CheckIn.id))
        .where(CheckIn.result == "ok", CheckIn.created_at >= since60, CheckIn.created_at < since30)
        .group_by(CheckIn.member_id)
    ).all():
        entry(mid)["visits_prev_30d"] = int(count)

    for mid, expires in db.execute(
        select(Membership.member_id, func.max(Membership.expires_at)).group_by(Membership.member_id)
    ).all():
        ts = expires if expires.tzinfo else expires.replace(tzinfo=UTC)
        entry(mid)["days_to_expiry"] = (ts - now).days

    for mid, count in db.execute(
        select(Payment.member_id, func.count(Payment.id))
        .where(Payment.status == "pending")
        .group_by(Payment.member_id)
    ).all():
        entry(mid)["overdue_payments"] = int(count)

    for mid, in db.execute(
        select(WorkoutProgram.member_id).where(WorkoutProgram.status == "approved").distinct()
    ).all():
        entry(mid)["has_active_program"] = True

    for mid, last in db.execute(
        select(SetFeedback.member_id, func.max(SetFeedback.created_at)).group_by(SetFeedback.member_id)
    ).all():
        ts = last if last.tzinfo else last.replace(tzinfo=UTC)
        entry(mid)["days_since_feedback"] = (now - ts).days

    return facts


def churn_risk(db: Session, *, limit: int = 20, window_days: int = DEFAULT_WINDOW_DAYS) -> dict:
    from engine.churn_risk import CHURN_VERSION, rank_members

    ranked = rank_members(collect_member_facts(db, window_days=window_days))
    names = _member_names(db, [row["member_id"] for row in ranked[:limit]])
    return {
        "risk_rows": [{**row, "full_name": names.get(row["member_id"], "")} for row in ranked[:limit]],
        "window_days": window_days,
        "rule_version": CHURN_VERSION,
        "generated_at": datetime.now(UTC).isoformat(),
    }
