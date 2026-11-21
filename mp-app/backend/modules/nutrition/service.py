"""سرویس nutrition — برنامهٔ تغذیه (اعداد فقط از موتور قواعد — G8)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clock import today_in_shop_zone
from app.errors import ApiError, NotFoundError
from db.models import MealItem, Member, NutritionPlan


def create_plan_from_engine(
    db: Session, member_id: int, engine_output: dict, coach_id: int | None = None
) -> NutritionPlan:
    if db.get(Member, member_id) is None:
        raise NotFoundError("عضو یافت نشد")
    plan = NutritionPlan(
        member_id=member_id,
        coach_id=coach_id,
        daily_kcal=engine_output["daily_kcal"],
        protein_g=engine_output["protein_g"],
        carbs_g=engine_output["carbs_g"],
        fat_g=engine_output["fat_g"],
        engine_version=engine_output.get("engine_version", ""),
        llm_explanation=engine_output.get("llm_explanation", ""),
        status="draft",
        branch_id=1,
    )
    db.add(plan)
    db.flush()
    for item in engine_output.get("meals", []):
        db.add(
            MealItem(
                plan_id=plan.id,
                food_id=item["food_id"],
                meal_slot=item["meal_slot"],
                grams=item["grams"],
                order=item.get("order", 0),
            )
        )
    db.commit()
    db.refresh(plan)
    return plan


def approve_plan(db: Session, plan_id: int, coach_id: int) -> NutritionPlan:
    plan = db.get(NutritionPlan, plan_id)
    if plan is None:
        raise NotFoundError("برنامهٔ تغذیه یافت نشد")
    if plan.status != "draft":
        raise ApiError("فقط برنامهٔ draft قابل تأیید است", code="invalid_status")
    plan.status = "approved"
    plan.coach_id = coach_id
    db.commit()
    db.refresh(plan)
    return plan


def list_member_plans(db: Session, member_id: int, user=None) -> list[NutritionPlan]:
    from app.security.ownership import ensure_member_scope

    ensure_member_scope(db, user, member_id)
    return list(
        db.scalars(
            select(NutritionPlan)
            .where(NutritionPlan.member_id == member_id)
            .order_by(NutritionPlan.id.desc())
        )
    )


# ── G5 — ثبت غذای روزانه (food-logging-1.0) [finn] ──

FOOD_LOG_VERSION = "food-logging-1.0"
VALID_SLOTS = ("breakfast", "lunch", "dinner", "snack")

# نام‌هایی که وزنشان «پیش از پخت» است. ۲۵۰ گرم برنج خشک ≈ ۹۰۰ کالری،
# ولی کاربر معمولاً «۲۵۰ گرم برنج پخته» در ذهن دارد (~۳۲۵ کالری).
# پنهان‌کردن این تفاوت، خطای ۵۰۰ کالری در روز است — پس صریح علامت می‌زنیم.
_DRY_OR_RAW_HINTS = ("(خشک)", "(خام)", "(نخود خشک)")


def is_dry_or_raw(name_fa: str) -> bool:
    """آیا اعداد این ماده برای وزن **خشک/خام** است؟"""
    return any(h in name_fa for h in _DRY_OR_RAW_HINTS)


def _food_macros(food, grams: float) -> dict:
    """درشت‌مغذی‌های یک وعده از جدول غذایی — همان لحظه، نه ذخیره‌شده.

    اگر مقادیر را در رکورد کپی می‌کردیم، اصلاح جدول غذایی هرگز به
    رکوردهای قدیمی نمی‌رسید.
    """
    f = grams / 100.0
    return {
        "kcal": round(food.kcal_per_100g * f, 1),
        "protein_g": round(food.protein_g_per_100g * f, 1),
        "carbs_g": round(food.carbs_g_per_100g * f, 1),
        "fat_g": round(food.fat_g_per_100g * f, 1),
    }


def log_food(
    db: Session,
    *,
    member_id: int,
    entries: list[dict],
    user=None,
) -> dict:
    """ثبت یک یا چند وعدهٔ واقعی. ورودی ناقص رد می‌شود، نه حدس زده."""
    from app.security.ownership import ensure_member_scope
    from db.models import FoodItem, FoodLog

    ensure_member_scope(db, user, member_id)
    rejected: list[dict] = []
    accepted: list[dict] = []

    for idx, entry in enumerate(entries):
        grams = entry.get("grams")
        food_id = entry.get("food_id")
        slot = entry.get("meal_slot") or "snack"
        day = entry.get("logged_for_date") or today_in_shop_zone().isoformat()  # F-28

        if food_id is None:
            rejected.append({"index": idx, "reason": "food_id لازم است"})
            continue
        if not grams or float(grams) <= 0:
            rejected.append({"index": idx, "reason": "گرم باید بزرگ‌تر از صفر باشد"})
            continue
        if slot not in VALID_SLOTS:
            rejected.append({"index": idx, "reason": f"وعدهٔ نامعتبر: {slot}"})
            continue
        if len(day) != 10 or day[4] != "-" or day[7] != "-":
            rejected.append({"index": idx, "reason": "تاریخ باید YYYY-MM-DD باشد"})
            continue
        food = db.get(FoodItem, int(food_id))
        if food is None:
            rejected.append({"index": idx, "reason": f"مادهٔ غذایی {food_id} در جدول نیست"})
            continue

        accepted.append(
            {
                "member_id": member_id,
                "food_id": food.id,
                "logged_for_date": day,
                "meal_slot": slot,
                "grams": float(grams),
                "source": entry.get("source", "member"),
                "notes": (entry.get("notes") or "").strip(),
                "branch_id": 1,
            }
        )

    for row in accepted:
        db.add(FoodLog(**row))
    db.commit()

    return {
        "logged": len(accepted),
        "rejected": rejected,
        "reason": (
            f"{len(accepted)} وعده ثبت شد" + (f"؛ {len(rejected)} ردیف رد شد" if rejected else "")
        ),
        "rule_version": FOOD_LOG_VERSION,
    }


def daily_summary(db: Session, *, member_id: int, day: str | None = None, user=None) -> dict:
    """جمع کالری و درشت‌مغذی‌های یک روز + مقایسه با برنامهٔ تأییدشده.

    اگر برنامه‌ای نباشد، `target` صفر می‌شود و `target_source="none"` —
    نه اینکه هدفی از هوا ساخته شود.
    """
    from app.security.ownership import ensure_member_scope
    from db.models import FoodItem, FoodLog

    ensure_member_scope(db, user, member_id)
    day = day or today_in_shop_zone().isoformat()  # F-28

    rows = list(
        db.scalars(
            select(FoodLog)
            .where(FoodLog.member_id == member_id, FoodLog.logged_for_date == day)
            .order_by(FoodLog.id)
        ).all()
    )
    food_ids = {r.food_id for r in rows}
    foods = (
        {f.id: f for f in db.scalars(select(FoodItem).where(FoodItem.id.in_(food_ids))).all()}
        if food_ids
        else {}
    )

    totals = {"kcal": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0}
    per_slot: dict[str, dict] = {
        s: {"kcal": 0.0, "protein_g": 0.0, "count": 0} for s in VALID_SLOTS
    }
    items = []
    for r in rows:
        food = foods.get(r.food_id)
        if food is None:
            # مادهٔ غذایی حذف شده — با WARN گزارش می‌شود، نه سکوت
            items.append(
                {
                    "id": r.id,
                    "food_id": r.food_id,
                    "name_fa": "نامعلوم (مادهٔ غذایی حذف شده)",
                    "grams": r.grams,
                    "meal_slot": r.meal_slot,
                    "kcal": 0.0,
                    "protein_g": 0.0,
                    "carbs_g": 0.0,
                    "fat_g": 0.0,
                    "warning": "food_missing",
                }
            )
            continue
        macros = _food_macros(food, r.grams)
        for k in totals:
            totals[k] += macros[k]
        slot = per_slot.setdefault(r.meal_slot, {"kcal": 0.0, "protein_g": 0.0, "count": 0})
        slot["kcal"] += macros["kcal"]
        slot["protein_g"] += macros["protein_g"]
        slot["count"] += 1
        items.append(
            {
                "id": r.id,
                "food_id": r.food_id,
                "name_fa": food.name_fa,
                "grams": r.grams,
                "meal_slot": r.meal_slot,
                "warning": (
                    "اعداد برای وزن خشک/خام است — اگر پخته وزن کرده‌اید، مقدار کمتری وارد کنید"
                    if is_dry_or_raw(food.name_fa)
                    else ""
                ),
                **macros,
            }
        )

    plan = db.scalar(
        select(NutritionPlan)
        .where(NutritionPlan.member_id == member_id, NutritionPlan.status == "approved")
        .order_by(NutritionPlan.id.desc())
    )
    if plan is not None:
        target = {
            "kcal": plan.daily_kcal,
            "protein_g": plan.protein_g,
            "carbs_g": plan.carbs_g,
            "fat_g": plan.fat_g,
        }
        target_source = "approved_plan"
        plan_id = plan.id
    else:
        target = {"kcal": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0}
        target_source = "none"
        plan_id = None

    return {
        "member_id": member_id,
        "date": day,
        "items": items,
        "totals": {k: round(v, 1) for k, v in totals.items()},
        "by_slot": {
            s: {
                "kcal": round(v["kcal"], 1),
                "protein_g": round(v["protein_g"], 1),
                "count": v["count"],
            }
            for s, v in per_slot.items()
        },
        "target": target,
        "target_source": target_source,
        "plan_id": plan_id,
        "data_state": "logged" if rows else "nothing_logged",
        "reason": (
            f"{len(items)} وعده در {day} ثبت شده"
            if rows
            else f"برای {day} هیچ وعده‌ای ثبت نشده — صفر یعنی «ثبت نشده»، نه «نخورده»"
        ),
        "rule_version": FOOD_LOG_VERSION,
    }


def search_foods(db: Session, *, query: str = "", limit: int = 30) -> list[dict]:
    """جستجوی نام فارسی/انگلیسی در جدول غذایی. فهرست خالی، فهرست خالی است."""
    from db.models import FoodItem

    stmt = select(FoodItem)
    q = (query or "").strip()
    if q:
        like = f"%{q}%"
        stmt = stmt.where(FoodItem.name_fa.like(like) | FoodItem.name_en.like(like))
    stmt = stmt.order_by(FoodItem.name_fa).limit(max(1, min(int(limit), 100)))
    return [
        {
            "id": f.id,
            "name_fa": f.name_fa,
            "category": f.category,
            "kcal_per_100g": f.kcal_per_100g,
            "protein_g_per_100g": f.protein_g_per_100g,
            "carbs_g_per_100g": f.carbs_g_per_100g,
            "fat_g_per_100g": f.fat_g_per_100g,
            "dry_or_raw": is_dry_or_raw(f.name_fa),
        }
        for f in db.scalars(stmt).all()
    ]


# ── G3 — تغذیهٔ سازگار (adaptive-nutrition-1.0) [finn] ──


def log_weight(db: Session, *, member_id: int, entries: list[dict], user=None) -> dict:
    """ثبت وزن روزانه. یک رکورد در روز: ثبت دوباره = به‌روزرسانی."""
    from app.security.ownership import ensure_member_scope
    from db.models import BodyWeightLog

    ensure_member_scope(db, user, member_id)
    rejected: list[dict] = []
    accepted = 0
    updated = 0

    for idx, e in enumerate(entries):
        day = e.get("logged_for_date")
        kg = e.get("weight_kg")
        if not day or len(str(day)) != 10:
            rejected.append({"index": idx, "reason": "تاریخ باید YYYY-MM-DD باشد"})
            continue
        if kg is None or not (20 <= float(kg) <= 400):
            rejected.append({"index": idx, "reason": "وزن باید بین ۲۰ و ۴۰۰ کیلوگرم باشد"})
            continue
        existing = db.scalar(
            select(BodyWeightLog).where(
                BodyWeightLog.member_id == member_id,
                BodyWeightLog.logged_for_date == str(day),
            )
        )
        if existing is not None:
            existing.weight_kg = float(kg)
            existing.source = e.get("source", "member")
            existing.notes = (e.get("notes") or "").strip()
            updated += 1
        else:
            db.add(
                BodyWeightLog(
                    member_id=member_id,
                    logged_for_date=str(day),
                    weight_kg=float(kg),
                    source=e.get("source", "member"),
                    notes=(e.get("notes") or "").strip(),
                    branch_id=1,
                )
            )
            accepted += 1
    db.commit()

    return {
        "logged": accepted,
        "updated": updated,
        "rejected": rejected,
        "reason": f"{accepted} وزن ثبت شد، {updated} به‌روزرسانی"
        + (f"؛ {len(rejected)} ردیف رد شد" if rejected else ""),
        "rule_version": FOOD_LOG_VERSION,
    }


def adaptive_nutrition_report(db: Session, *, member_id: int, user=None) -> dict:
    """G3 — TDEE واقعی + پیشنهاد اصلاح کالری، از دادهٔ ثبت‌شدهٔ خود عضو.

    سه منبع داده، هر سه از DB واقعی:
      وزن  ← body_weight_logs
      مصرف ← food_logs (فقط روزهای ثبت‌شده)
      هدف  ← آخرین برنامهٔ تغذیهٔ approved

    اگر هر کدام کم باشد، به‌جای حدس زدن صریح گفته می‌شود.
    """
    from app.security.ownership import ensure_member_scope
    from db.models import BodyWeightLog, FoodItem, FoodLog
    from engine.adaptive_nutrition import (
        estimate_tdee,
        suggest_calorie_adjustment,
    )

    ensure_member_scope(db, user, member_id)

    weight_rows = list(
        db.scalars(
            select(BodyWeightLog)
            .where(BodyWeightLog.member_id == member_id)
            .order_by(BodyWeightLog.logged_for_date)
        ).all()
    )
    weight_points = [(r.logged_for_date, r.weight_kg) for r in weight_rows]

    # مصرف روزانه از food_logs + جدول غذایی
    log_rows = list(db.scalars(select(FoodLog).where(FoodLog.member_id == member_id)).all())
    food_ids = {r.food_id for r in log_rows}
    foods = (
        {f.id: f for f in db.scalars(select(FoodItem).where(FoodItem.id.in_(food_ids))).all()}
        if food_ids
        else {}
    )
    intake: dict[str, float] = {}
    for r in log_rows:
        food = foods.get(r.food_id)
        if food is None:
            continue
        intake[r.logged_for_date] = intake.get(r.logged_for_date, 0.0) + (
            food.kcal_per_100g * (r.grams / 100.0)
        )

    plan = db.scalar(
        select(NutritionPlan)
        .where(NutritionPlan.member_id == member_id, NutritionPlan.status == "approved")
        .order_by(NutritionPlan.id.desc())
    )
    current_target = plan.daily_kcal if plan is not None else None

    est = estimate_tdee(
        weight_points=weight_points,
        intake_by_date=intake,
        current_target_kcal=current_target,
    )

    from db.models import Member

    member = db.get(Member, member_id)
    goal = (member.goal if member is not None else "") or "fitness"
    latest_weight = weight_points[-1][1] if weight_points else None

    adj = suggest_calorie_adjustment(
        tdee_kcal=est["tdee_kcal"],
        current_target_kcal=current_target,
        goal=goal,
        body_weight_kg=latest_weight,
        slope_kg_per_week=est["trend"]["slope_kg_per_week"],
    )

    return {
        "member_id": member_id,
        "goal": goal,
        "current_target_kcal": current_target,
        "plan_id": plan.id if plan is not None else None,
        "estimate": est,
        "suggestion": adj,
        "data_counts": {
            "weight_entries": len(weight_points),
            "intake_days": len([v for v in intake.values() if v > 0]),
        },
        "latest_weight_kg": latest_weight,
        "rule_version": "adaptive-nutrition-1.0",
    }
