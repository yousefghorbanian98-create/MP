"""سرویس programs — گردش کاری برنامه (draft → تأیید/رد مربی).

قاعدهٔ G8: تولید اعداد (بار/ست/تکرار) فقط در ai_engine (M15) انجام می‌شود؛
این سرویس فقط مدیریت چرخهٔ وضعیت و ثبت تغییرات را انجام می‌دهد.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import ApiError, NotFoundError
from db.models import Member, ProgramExercise, ProgramWeek, WorkoutProgram


def get_program(db: Session, program_id: int, user=None) -> WorkoutProgram:
    p = db.get(WorkoutProgram, program_id)
    from app.security.ownership import ensure_record_scope

    ensure_record_scope(db, user, p)
    if p is None:
        raise NotFoundError("برنامه یافت نشد")
    return p


def list_member_programs(db: Session, member_id: int, user=None) -> list[WorkoutProgram]:
    from app.security.ownership import ensure_member_scope

    ensure_member_scope(db, user, member_id)
    return list(
        db.scalars(
            select(WorkoutProgram)
            .where(WorkoutProgram.member_id == member_id)
            .order_by(WorkoutProgram.id.desc())
        )
    )


def approve_program(db: Session, program_id: int, coach_id: int) -> WorkoutProgram:
    """تأیید مربی (US-203) — فقط draft قابل تأیید است."""
    p = get_program(db, program_id)
    if p.status != "draft":
        raise ApiError("فقط برنامهٔ draft قابل تأیید است", code="invalid_status")
    p.status = "approved"
    p.approved_at = datetime.now(UTC)
    p.approved_by = coach_id
    db.commit()
    db.refresh(p)
    from modules.admin.service import audit

    audit(db, coach_id, "program_approved", "workout_program", p.id, {})
    return p


def reject_program(db: Session, program_id: int, coach_id: int, reason: str) -> WorkoutProgram:
    p = get_program(db, program_id)
    if p.status != "draft":
        raise ApiError("فقط برنامهٔ draft قابل رد است", code="invalid_status")
    if not reason.strip():
        raise ApiError("دلیل رد الزامی است", code="reason_required")
    p.status = "rejected"
    p.reject_reason = reason
    p.approved_by = coach_id
    db.commit()
    db.refresh(p)
    from modules.admin.service import audit

    audit(db, coach_id, "program_rejected", "workout_program", p.id, {"reason": reason})
    return p


def create_program_from_engine_output(
    db: Session,
    member_id: int,
    engine_output: dict,
    coach_id: int | None = None,
) -> WorkoutProgram:
    """ثبت خروجی موتور قواعد به‌صورت برنامهٔ draft (توسط ai_engine/M15 فراخوانی می‌شود).

    ساختار engine_output: {'goal': str, 'engine_version': str, 'weeks': [
      {'week_number': 1, 'focus': str, 'exercises': [
        {'exercise_id': 1, 'day': 1, 'order': 0, 'sets': 3, 'reps': '8-12',
         'load_pct': 70, 'rest_seconds': 90, 'notes': ''}]}]}
    """
    # Q7 — غربالگری ایمنی پیش از ثبت برنامه.
    # برنامه‌ای که با محدودیت پزشکی عضو ناسازگار است باید در وضعیت
    # `flagged` ثبت شود تا مربی ببیند، نه بی‌صدا تأیید شود.
    import json as _json

    safety = _safety_gate(db, member_id, engine_output)

    program = WorkoutProgram(
        member_id=member_id,
        coach_id=coach_id,
        goal=engine_output.get("goal", ""),
        engine_version=engine_output.get("engine_version", ""),
        llm_explanation=engine_output.get("llm_explanation", ""),  # فقط متن — هرگز عدد (G8)
        status="draft",
        branch_id=1,
        safety_flags=_json.dumps(safety, ensure_ascii=False),
    )
    db.add(program)
    db.flush()

    # M46-c4 — پیش از درج حرکات، کاتالوگ را تضمین کن.
    # `program_exercises.exercise_id` یک FK واقعی است و LIBRARY موتور
    # هیچ seedی در DB نداشت؛ نتیجه ردیف یتیم (FK خاموش) یا ۵۰۰ (FK روشن).
    from engine.catalog_sync import ensure_exercises

    ensure_exercises(
        db,
        {
            ex["exercise_id"]
            for week in engine_output.get("weeks", [])
            for ex in week.get("exercises", [])
            if "exercise_id" in ex
        },
    )

    for week in engine_output.get("weeks", []):
        w = ProgramWeek(
            program_id=program.id,
            week_number=week["week_number"],
            focus=week.get("focus", ""),
        )
        db.add(w)
        db.flush()
        for ex in week.get("exercises", []):
            db.add(
                ProgramExercise(
                    week_id=w.id,
                    exercise_id=ex["exercise_id"],
                    day=ex["day"],
                    order=ex.get("order", 0),
                    sets=ex["sets"],
                    reps=ex["reps"],
                    load_pct=ex.get("load_pct", 0),
                    rest_seconds=ex.get("rest_seconds", 60),
                    notes=ex.get("notes", ""),
                )
            )
    db.commit()
    db.refresh(program)
    return program


def record_set_feedback(
    db: Session,
    *,
    member_id: int,
    program_id: int | None,
    entries: list[dict],
    user=None,
) -> dict:
    """ثبت بازخورد ست‌ها + پیشنهاد جلسهٔ بعد (G1 — M38-c2)."""
    from app.security.ownership import ensure_member_scope
    from db.models.programs import SetFeedback
    from engine.feedback_apply import apply_suggestions
    from engine.set_feedback import process_set_feedback as _process

    ensure_member_scope(db, user, member_id)

    # مهم: برنامه را **قبل از** درج ردیف‌ها حل می‌کنیم. قبلاً این حل بعد از
    # commit انجام می‌شد و وقتی club_id/program_id در درخواست نبود، هر ردیف با
    # program_id=None («بازخورد یتیم») ذخیره می‌شد — یعنی بازخورد هرگز به برنامه
    # وصل نمی‌شد و گزارش حجم آن را نمی‌دید. (باگ ۱۹)
    from db.models import WorkoutProgram

    program = None
    if program_id is not None:
        program = db.get(WorkoutProgram, program_id)
    else:
        program = db.scalar(
            select(WorkoutProgram)
            .where(WorkoutProgram.member_id == member_id)
            .order_by(WorkoutProgram.id.desc())
        )
    if program is not None:
        program_id = program.id

    for entry in entries:
        db.add(
            SetFeedback(
                member_id=member_id,
                program_id=program_id,
                movement_id=entry["movement_id"],
                weight=entry["weight"],
                target_reps=entry["target_reps"],
                reps_done=entry["reps_done"],
                rir=entry.get("rir"),
                soreness=entry.get("soreness"),
                notes=entry.get("notes", ""),
            )
        )
    db.commit()

    result = _process(entries=entries)

    # M48-c1 — G1 تا اینجا نیمه‌کاره بود: پیشنهاد ساخته می‌شد ولی هیچ ردیفی
    # در برنامه تغییر نمی‌کرد. اینجا پیشنهاد واقعاً روی هفتهٔ بعد اعمال می‌شود.
    # `program` بالاتر (پیش از درج) حل شده است.
    result["applied"] = apply_suggestions(db, program=program, suggestions=result["suggestions"])
    return result


PROGRAMS_SUMMARY_VERSION = "programs-summary-1.0"


def list_programs_summary(db, *, status: str | None = None, limit: int = 200) -> dict:
    """فهرست برنامه‌های باشگاه با نام عضو — برای صفحهٔ «برنامه‌ها» در استودیو.

    فقط برنامه‌های واقعی برمی‌گردند؛ فهرست خالی یعنی «برنامه‌ای ثبت نشده»،
    نه اینکه با داده‌ی نمایشی پر شود.
    """
    from sqlalchemy import select

    from db.models import Member, User, WorkoutProgram

    stmt = select(WorkoutProgram).order_by(WorkoutProgram.id.desc()).limit(limit)
    if status:
        stmt = stmt.where(WorkoutProgram.status == status)
    programs = db.scalars(stmt).all()

    member_ids = {p.member_id for p in programs}
    names: dict[int, str] = {}
    if member_ids:
        rows = db.execute(
            select(Member.id, User.full_name)
            .join(User, User.id == Member.user_id)
            .where(Member.id.in_(member_ids))
        ).all()
        names = dict(rows)

    items = [
        {
            "id": p.id,
            "member_id": p.member_id,
            "member_name": names.get(p.member_id, ""),
            "status": p.status,
            "goal": p.goal,
            "engine_version": p.engine_version,
            "weeks_count": len(p.weeks) if p.weeks is not None else 0,
            "llm_explanation": p.llm_explanation,
            "reject_reason": p.reject_reason,
            "approved_at": p.approved_at.isoformat() if p.approved_at else None,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "safety_flags": p.safety_flags or "{}",
        }
        for p in programs
    ]
    return {
        "items": items,
        "rule_version": PROGRAMS_SUMMARY_VERSION,
        "counts_by_status": {
            s: sum(1 for i in items if i["status"] == s) for s in {i["status"] for i in items}
        },
    }


# ── G2 — نشانگرهای حجم هفتگی (volume-landmarks-1.0) [finn] ──

VOLUME_REPORT_VERSION = "volume-report-1.0"


def weekly_volume_report(db, *, member_id: int, level: str = "intermediate") -> dict:
    """حجم هفتگی هر گروه عضلانی برای آخرین برنامهٔ عضو + وضعیت و پیشنهاد.

    منبع عدد، صریح اعلام می‌شود:
      * `planned`            — هیچ ستّی گزارش نشده؛ عدد از خود برنامه است
      * `reported_hard_sets` — از بازخورد واقعی؛ فقط ست‌های سخت شمرده می‌شوند

    این تفکیک مهم است چون «برنامه ۱۲ ست دارد» با «۱۲ ست سخت انجام شد» یکی نیست.
    """
    from db.models import Exercise, ProgramExercise, ProgramWeek, SetFeedback, WorkoutProgram
    from engine.feedback_apply import resolve_exercise_id
    from engine.volume import summarize_volume

    program = db.scalar(
        select(WorkoutProgram)
        .where(WorkoutProgram.member_id == member_id)
        .order_by(WorkoutProgram.id.desc())
    )
    if program is None:
        return {
            "member_id": member_id,
            "program_id": None,
            "level": level,
            "muscles": [],
            "reason": "برای این عضو هیچ برنامه‌ای ثبت نشده — گزارش حجم ساخته نمی‌شود",
            "rule_version": VOLUME_REPORT_VERSION,
        }

    weeks = list(db.scalars(select(ProgramWeek).where(ProgramWeek.program_id == program.id)).all())
    if not weeks:
        return {
            "member_id": member_id,
            "program_id": program.id,
            "level": level,
            "muscles": [],
            "reason": "برنامه هیچ هفته‌ای ندارد",
            "rule_version": VOLUME_REPORT_VERSION,
        }

    # هفتهٔ جاری = آخرین هفتهٔ موجود (مافوق واقعیت: هفته‌ها ۱..N)
    current_week = max(weeks, key=lambda w: w.week_number)
    rows = list(
        db.scalars(select(ProgramExercise).where(ProgramExercise.week_id == current_week.id)).all()
    )

    ex_ids = {r.exercise_id for r in rows}
    catalog = (
        {e.id: e for e in db.scalars(select(Exercise).where(Exercise.id.in_(ex_ids))).all()}
        if ex_ids
        else {}
    )

    # ست‌های برنامه‌ریزی‌شده به تفکیک گروه عضلانی
    planned_by_muscle: dict[str, int] = {}
    for row in rows:
        ex = catalog.get(row.exercise_id)
        group = ex.muscle_group if ex is not None else "full_body"
        planned_by_muscle[group] = planned_by_muscle.get(group, 0) + (row.sets or 0)

    # بازخوردهای همان برنامه ← نگاشت movement_id به گروه عضلانی
    feedback = list(
        db.scalars(select(SetFeedback).where(SetFeedback.program_id == program.id)).all()
    )
    feedback_by_muscle: dict[str, list[dict]] = {}
    for fb in feedback:
        ex_id = resolve_exercise_id(fb.movement_id)
        ex = catalog.get(ex_id) if ex_id is not None else None
        if ex is None and ex_id is not None:
            ex = db.get(Exercise, ex_id)
        group = ex.muscle_group if ex is not None else "full_body"
        feedback_by_muscle.setdefault(group, []).append({"rir": fb.rir, "soreness": fb.soreness})

    muscles = []
    for group, planned in sorted(planned_by_muscle.items()):
        muscles.append(
            summarize_volume(
                muscle=group,
                level=level,
                planned_sets=planned,
                feedback_rows=feedback_by_muscle.get(group, []),
            )
        )

    return {
        "member_id": member_id,
        "program_id": program.id,
        "week_number": current_week.week_number,
        "level": level,
        "muscles": muscles,
        "reason": (
            f"{len(muscles)} گروه عضلانی از هفتهٔ {current_week.week_number} برنامهٔ "
            f"#{program.id} بررسی شد — ست سخت = RIR ≤ ۳"
        ),
        "rule_version": VOLUME_REPORT_VERSION,
    }


# ── G13 — مدل آمادگی/خستگی برای یک برنامهٔ واقعی [finn] ──

READINESS_REPORT_VERSION = "readiness-report-1.0"


def readiness_report(db, *, member_id: int) -> dict:
    """امتیاز آمادگی عضو از بازخوردهای واقعی ثبت‌شده.

    داده‌ها همه از `SetFeedback` می‌آیند:
      * آخرین ست گزارش‌شده ← تکرار و RIR (سیگنال اصلی)
      * مجموع ست‌های گزارش‌شده در ۷ روز اخیر در برابر ۷ روز قبل ← پرش حجم
      * حداکثر درد عضلانی ثبت‌شده ← سیگنال درد

    هدف تکرار و RIR از خود برنامه (`ProgramExercise.reps` و `load_pct`)
    نمی‌آید چون RIR هدف در برنامه ذخیره نمی‌شود؛ به‌جایش از
    `target_reps` همان گزارش استفاده می‌شود — که دقیقاً همان چیزی است
    که عضو در جلسه دیده. این صادقانه‌تر از حدس زدن یک RIR هدف است.
    """
    from datetime import UTC, datetime, timedelta

    from db.models import SetFeedback, WorkoutProgram
    from engine.readiness import assess_readiness

    program = db.scalar(
        select(WorkoutProgram)
        .where(WorkoutProgram.member_id == member_id)
        .order_by(WorkoutProgram.id.desc())
    )
    if program is None:
        return {
            "member_id": member_id,
            "program_id": None,
            "readiness": None,
            "reason": "برای این عضو هیچ برنامه‌ای ثبت نشده — آمادگی سنجیده نمی‌شود",
            "rule_version": READINESS_REPORT_VERSION,
        }

    rows = list(
        db.scalars(
            select(SetFeedback)
            .where(SetFeedback.program_id == program.id)
            .order_by(SetFeedback.id.desc())
        ).all()
    )
    if not rows:
        return {
            "member_id": member_id,
            "program_id": program.id,
            "readiness": None,
            "reason": "هیچ بازخورد ستی برای این برنامه ثبت نشده — آمادگی سنجیده نمی‌شود",
            "rule_version": READINESS_REPORT_VERSION,
        }

    latest = rows[0]
    now = datetime.now(UTC)
    cutoff_recent = now - timedelta(days=7)
    cutoff_prev = now - timedelta(days=14)

    def _created(r):
        c = r.created_at
        if c is None:
            return None
        return c if c.tzinfo is not None else c.replace(tzinfo=UTC)

    recent_sets = 0
    prev_sets = 0
    for r in rows:
        c = _created(r)
        if c is None:
            continue
        if c >= cutoff_recent:
            recent_sets += 1
        elif c >= cutoff_prev:
            prev_sets += 1

    max_soreness = max((r.soreness or 0 for r in rows), default=0) or None

    result = assess_readiness(
        target_reps=int(latest.target_reps or 0),
        reps_done=int(latest.reps_done or 0),
        target_rir=None,  # RIR هدف در برنامه ذخیره نمی‌شود — صادقانه None
        actual_rir=latest.rir,
        soreness=max_soreness,
        this_week_sets=recent_sets,
        last_week_sets=prev_sets,
    )

    payload = result.to_dict()
    payload["actionable"] = result.recommendation == "deload" and result.volume_delta_sets < 0
    return {
        "member_id": member_id,
        "program_id": program.id,
        "readiness": payload,
        "data_counts": {
            "feedback_rows": len(rows),
            "sets_last_7_days": recent_sets,
            "sets_prior_7_days": prev_sets,
        },
        "reason": result.reason,
        "note": (
            "RIR هدف در برنامه ذخیره نمی‌شود، پس سیگنال «اختلاف RIR» نامعلوم می‌ماند "
            "و وزنش به بقیهٔ سیگنال‌ها توزیع می‌شود — نه اینکه صفر فرض شود."
        ),
        "rule_version": READINESS_REPORT_VERSION,
    }


# ── Q7 — غربالگری ایمنی ──


def _safety_gate(db: Session, member_id: int, engine_output: dict) -> dict:
    """بررسی ناسازگاری برنامه با محدودیت‌های پزشکی عضو.

    الگوهای حرکتی از حرکت‌های برنامه استخراج می‌شوند (`exercise_id` به
    نام حرکت نگاشت می‌شود) و با موتور ایمنی سنجیده می‌شوند. خروجی در
    `llm_explanation` نمی‌نشیند — آن فیلد فقط متن است؛ پرچم ایمنی جای
    جدا دارد.
    """
    import json

    from engine.safety import screen

    member = db.get(Member, member_id)
    if member is None:
        return {"status": "unknown", "reason": "عضو یافت نشد"}

    try:
        constraints = json.loads(member.constraints or "[]")
    except (ValueError, TypeError):
        constraints = []
    if not isinstance(constraints, list):
        constraints = []

    patterns: list[str] = []
    for week in engine_output.get("weeks", []) or []:
        for ex in week.get("exercises", []) or []:
            name = ex.get("movement") or ex.get("pattern") or ""
            if name:
                patterns.append(str(name))

    return screen(
        constraints=[str(c) for c in constraints],
        planned_patterns=patterns,
        age=None,  # سن در پروفایل عضو نگه‌داری نمی‌شود؛ ادعای بی‌پشتوانه نمی‌کنیم
        has_medical_clearance=None,
    )


# ── G7 — همگام‌سازی صف آفلاین با LWW ──

SYNC_VERSION = "sync-api-1.0"


def sync_set_feedback(db: Session, *, member_id: int, items: list[dict], user=None) -> dict:
    """دریافت صف آفلاین بازخورد ست و اعمال با حل تعارض LWW.

    `items` هر آیتم: `client_id` (کلید محلی دستگاه)، `device_id`،
    `updated_at`، و فیلدهای بازخورد. `client_id` به‌همراه `member_id` کلید
    رکورد است تا صف یک دستگاه، رکورد دستگاه دیگر را نشکند.
    """
    from datetime import datetime as _dt

    from app.security.ownership import ensure_member_scope
    from db.models import SetFeedback
    from engine.sync_lww import Versioned, resolve_batch

    ensure_member_scope(db, user, member_id)
    if db.get(Member, member_id) is None:
        raise NotFoundError("عضو یافت نشد")

    existing = list(db.scalars(select(SetFeedback).where(SetFeedback.member_id == member_id)).all())
    server_rows: dict[tuple[str, str], Versioned] = {}
    by_key: dict[str, SetFeedback] = {}
    for row in existing:
        key = f"{row.device_id or 'server'}:{row.client_id or row.id}"
        server_rows[("set_feedback", key)] = Versioned(
            entity="set_feedback",
            entity_key=key,
            updated_at=row.client_updated_at or row.created_at,
            device_id=row.device_id or "",
        )
        by_key[key] = row

    client_rows: list[Versioned] = []
    payloads: dict[str, dict] = {}
    for item in items:
        key = f"{item['device_id']}:{item['client_id']}"
        client_rows.append(
            Versioned(
                entity="set_feedback",
                entity_key=key,
                updated_at=item["updated_at"],
                device_id=item["device_id"],
                payload=item,
            )
        )
        payloads[key] = item

    outcome = resolve_batch(server_rows, client_rows)

    applied_ids: list[str] = []
    unchanged_ids: list[str] = []
    for result in outcome["results"]:
        key = result["entity_key"]
        if result["action"] == "conflict_resolved" and result["winner"] == "server":
            # تساوی کامل timestamp یعنی همان نوشتهٔ قبلی دوباره رسیده
            # (تلاش مجدد شبکه). اعمال دوباره بی‌اثر است ولی «applied»
            # شمردنش کاربر را گمراه می‌کند؛ جدا گزارش می‌شود.
            unchanged_ids.append(key)
            continue
        if result["winner"] != "client":
            continue
        data = payloads[key]
        stamp = _dt.fromisoformat(str(data["updated_at"]).replace("Z", "+00:00"))
        row = by_key.get(key)
        if row is None:
            row = SetFeedback(
                member_id=member_id,
                movement_id=str(data.get("movement_id", "")),
                weight=float(data.get("weight", 0)),
                target_reps=int(data.get("target_reps", 0)),
                reps_done=int(data.get("reps_done", 0)),
                rir=data.get("rir"),
                soreness=data.get("soreness"),
                notes=str(data.get("notes", "")),
                device_id=data["device_id"],
                client_id=str(data["client_id"]),
                client_updated_at=stamp,
                branch_id=1,
            )
            db.add(row)
        else:
            row.weight = float(data.get("weight", row.weight))
            row.reps_done = int(data.get("reps_done", row.reps_done))
            row.rir = data.get("rir", row.rir)
            row.soreness = data.get("soreness", row.soreness)
            row.client_updated_at = stamp
        applied_ids.append(key)

    if applied_ids:
        db.commit()

    if unchanged_ids:
        outcome["counts"]["unchanged"] = len(unchanged_ids)

    return {
        "member_id": member_id,
        **outcome,
        "applied_keys": applied_ids,
        "unchanged_keys": unchanged_ids,
        "note": (
            "نوشته‌هایی که سرور جدیدتر می‌داند رد می‌شوند و در پاسخ با "
            "action صریح گزارش می‌شوند — هیچ نوشته‌ای بی‌صدا دور ریخته نمی‌شود."
        ),
        "rule_version": SYNC_VERSION,
    }
