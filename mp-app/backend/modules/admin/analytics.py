"""تحلیل‌های مدیریتی ادمین (M42-c1) — لیدربوردها از دادهٔ واقعی DB.

هر رتبه با method صریح برمی‌گردد؛ اعضای بدون داده اصلاً در فهرست نمی‌آیند
(«داده ناشناخته است نه صفر» — E05). هیچ عددی از LLM نمی‌آید (E04).
"""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from db.models import (
    AxisAssessment,
    AxisScore,
    CheckIn,
    Member,
    Membership,
    Payment,
    User,
)

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
    latest_ids = (
        db.execute(select(func.max(AxisAssessment.id)).group_by(AxisAssessment.member_id))
        .scalars()
        .all()
    )
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
    stmt = select(
        Payment.member_id,
        func.sum(Payment.amount_rial),
        func.count(Payment.id),
        func.max(Payment.paid_at),
    ).where(Payment.status == "paid")
    if window_days is not None:
        stmt = stmt.where(Payment.paid_at >= datetime.now(UTC) - timedelta(days=window_days))
    rows = db.execute(
        stmt.group_by(Payment.member_id).order_by(func.sum(Payment.amount_rial).desc()).limit(limit)
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


def most_visits(
    db: Session, *, limit: int = 10, window_days: int = DEFAULT_WINDOW_DAYS
) -> list[dict]:
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


def most_time(
    db: Session, *, limit: int = 10, window_days: int = DEFAULT_WINDOW_DAYS
) -> list[dict]:
    """بیشترین تایم باشگاه: مجموع دقیقهٔ جلسات بسته‌شده (خروج ثبت‌شده).

    جلسات باز (بدون خروج) دقیقه ندارند — «نامعلوم» است نه صفر؛ شمارش‌شان جدا برمی‌گردد.
    محاسبه در پایتون (سازگار با SQLite و Postgres — بدون توابع گویش‌محور).
    """
    since = datetime.now(UTC) - timedelta(days=window_days)
    sessions = db.execute(
        select(CheckIn.member_id, CheckIn.created_at, CheckIn.checked_out_at, CheckIn.id).where(
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
        return facts.setdefault(
            mid,
            {
                "last_checkin_days_ago": None,
                "days_to_expiry": None,
                "overdue_payments": None,
                "visits_30d": None,
                "visits_prev_30d": None,
                "has_active_program": None,
                "days_since_feedback": None,
            },
        )

    # همهٔ اعضا حاضرند — حتی بدون هیچ سیگنالی (unknown ≠ نبود در فهرست)
    for (mid,) in db.execute(select(Member.id)).all():
        entry(mid)

    for mid, created in db.execute(
        select(CheckIn.member_id, func.max(CheckIn.created_at))
        .where(CheckIn.result == "ok")
        .group_by(CheckIn.member_id)
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

    for (mid,) in db.execute(
        select(WorkoutProgram.member_id).where(WorkoutProgram.status == "approved").distinct()
    ).all():
        entry(mid)["has_active_program"] = True

    for mid, last in db.execute(
        select(SetFeedback.member_id, func.max(SetFeedback.created_at)).group_by(
            SetFeedback.member_id
        )
    ).all():
        ts = last if last.tzinfo else last.replace(tzinfo=UTC)
        entry(mid)["days_since_feedback"] = (now - ts).days

    return facts


def churn_risk(db: Session, *, limit: int = 20, window_days: int = DEFAULT_WINDOW_DAYS) -> dict:
    from engine.churn_risk import CHURN_VERSION, rank_members

    ranked = rank_members(collect_member_facts(db, window_days=window_days))
    names = _member_names(db, [row["member_id"] for row in ranked[:limit]])
    return {
        "risk_rows": [
            {**row, "full_name": names.get(row["member_id"], "")} for row in ranked[:limit]
        ],
        "window_days": window_days,
        "rule_version": CHURN_VERSION,
        "generated_at": datetime.now(UTC).isoformat(),
    }


# ── M45: حضور و خلاصهٔ اعضا (دادهٔ واقعی برای استودیو) [finn] ──

ATTENDANCE_VERSION = "admin-attendance-1.0"
MEMBERS_SUMMARY_VERSION = "admin-members-summary-1.0"
EXPIRING_DAYS = 7


def attendance_summary(db: Session, *, window_days: int = DEFAULT_WINDOW_DAYS) -> dict:
    """خلاصهٔ حضور باشگاه در بازه — سری روزانه + جداکردن جلسات باز از بسته.

    «جلسهٔ باز دقیقه ندارد» (E05): در `total_minutes` شمرده نمی‌شود، ولی در
    `open_sessions` دیده می‌شود تا صفر جعلی ساخته نشود.
    """
    since = datetime.now(UTC) - timedelta(days=window_days)
    rows = db.execute(
        select(CheckIn.member_id, CheckIn.created_at, CheckIn.checked_out_at).where(
            CheckIn.result == "ok", CheckIn.created_at >= since
        )
    ).all()

    daily: dict[str, int] = {}
    total_minutes = 0.0
    closed = 0
    open_sessions = 0
    members: set[int] = set()
    for member_id, started, ended in rows:
        members.add(member_id)
        start = started if started.tzinfo else started.replace(tzinfo=UTC)
        daily[start.date().isoformat()] = daily.get(start.date().isoformat(), 0) + 1
        if ended is None:
            open_sessions += 1
        else:
            end = ended if ended.tzinfo else ended.replace(tzinfo=UTC)
            total_minutes += (end - start).total_seconds() / 60.0
            closed += 1

    series = [{"date": day, "count": daily[day]} for day in sorted(daily)]
    return {
        "window_days": window_days,
        "total_checkins": len(rows),
        "distinct_members": len(members),
        "closed_sessions": closed,
        "open_sessions": open_sessions,
        "total_minutes": int(total_minutes),
        "series": series,
        "rule_version": ATTENDANCE_VERSION,
        "generated_at": datetime.now(UTC).isoformat(),
    }


def members_summary(db: Session, *, limit: int = 200) -> dict:
    """خلاصهٔ اعضا برای جدول استودیو — نام، تلفن، هدف، وضعیت اشتراک، روز باقی‌مانده.

    وضعیت اشتراک از **آخرین** اشتراک عضو محاسبه می‌شود:
    - هیچ اشتراکی ← `unknown` (نه expired — E05)
    - `expires_at` گذشته یا status != active ← `expired`
    - تا EXPIRING_DAYS روز آینده ← `expiring`
    - وگرنه ← `active`
    """
    now = datetime.now(UTC)
    members = db.scalars(select(Member).order_by(Member.id).limit(limit)).all()
    if not members:
        return {
            "items": [],
            "rule_version": MEMBERS_SUMMARY_VERSION,
            "generated_at": now.isoformat(),
        }

    member_ids = [m.id for m in members]
    users = {
        row[0]: row
        for row in db.execute(
            select(User.id, User.full_name, User.phone, User.is_active).where(
                User.id.in_([m.user_id for m in members])
            )
        ).all()
    }

    latest: dict[int, Membership] = {}
    for ms in db.scalars(
        select(Membership)
        .where(Membership.member_id.in_(member_ids))
        .order_by(Membership.member_id, Membership.expires_at.desc())
    ).all():
        latest.setdefault(ms.member_id, ms)

    items = []
    for m in members:
        user_row = users.get(m.user_id)
        full_name = user_row[0] if user_row else ""
        phone = user_row[1] if user_row else ""
        ms = latest.get(m.id)
        if ms is None:
            status = "unknown"
            days_left = None
            expires_at = None
        else:
            expires = ms.expires_at if ms.expires_at.tzinfo else ms.expires_at.replace(tzinfo=UTC)
            # سقف نه کف: ۲٫۹ روز باقی‌مانده باید «۳ روز» گزارش شود، نه «۲ روز»
            # (timedelta.days کف می‌گیرد و یک روز کامل کم‌نمایی می‌کند)
            remaining = (expires - now).total_seconds()
            days_left = math.ceil(remaining / 86400)
            expires_at = expires.isoformat()
            if ms.status != "active" or days_left < 0:
                status = "expired"
            elif days_left <= EXPIRING_DAYS:
                status = "expiring"
            else:
                status = "active"
        items.append(
            {
                "member_id": m.id,
                "user_id": m.user_id,
                "full_name": full_name,
                "phone": phone,
                "goal": m.goal,
                "gender": m.gender,
                "membership_id": ms.id if ms else None,
                "plan_name": ms.plan_name if ms else None,
                "status": status,
                "days_left": days_left,
                "expires_at": expires_at,
                "is_active": bool(user_row[2]) if user_row else True,
            }
        )
    return {
        "items": items,
        "rule_version": MEMBERS_SUMMARY_VERSION,
        "expiring_days": EXPIRING_DAYS,
        "unknown_status_meaning": "عضو هیچ اشتراکی ندارد — نامعلوم، نه منقضی",
        "generated_at": now.isoformat(),
    }


CHECKIN_FEED_VERSION = "admin-checkin-feed-1.0"


def recent_checkins(db: Session, *, limit: int = 50) -> dict:
    """جریان ورودهای اخیر — جدیدترین اول، شامل ورودهای ردشده با دلیل.

    ورود رد‌شده پنهان نمی‌شود: گزارش ناقص بدتر از گزارش ناخوشایند است.
    """
    rows = db.execute(
        select(
            CheckIn.id,
            CheckIn.member_id,
            CheckIn.method,
            CheckIn.result,
            CheckIn.denial_reason,
            CheckIn.created_at,
            CheckIn.checked_out_at,
        )
        .order_by(CheckIn.created_at.desc(), CheckIn.id.desc())
        .limit(limit)
    ).all()
    ids = list({r[1] for r in rows})
    names: dict[int, str] = {}
    if ids:
        names = dict(
            db.execute(
                select(Member.id, User.full_name)
                .join(User, User.id == Member.user_id)
                .where(Member.id.in_(ids))
            ).all()
        )
    items = [
        {
            "checkin_id": cid,
            "member_id": mid,
            "member_name": names.get(mid, ""),
            "method": method,
            "result": result,
            "denial_reason": reason or "",
            "checked_in_at": created.isoformat() if created else None,
            "checked_out_at": checkout.isoformat() if checkout else None,
            "is_open": checkout is None and result == "ok",
        }
        for cid, mid, method, result, reason, created, checkout in rows
    ]
    return {
        "items": items,
        "rule_version": CHECKIN_FEED_VERSION,
        "generated_at": datetime.now(UTC).isoformat(),
    }
