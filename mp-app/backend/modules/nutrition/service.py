"""سرویس nutrition — برنامهٔ تغذیه (اعداد فقط از موتور قواعد — G8)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

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
