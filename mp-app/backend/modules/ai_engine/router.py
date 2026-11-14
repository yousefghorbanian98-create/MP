"""روتر ai_engine — تولید برنامه/تغذیه از موتور قواعد قطعی (G8)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.deps import DbSession, require_permission
from modules.ai_engine import service
from modules.ai_engine.schemas import NutritionGenerateIn, ProgramGenerateIn
from modules.nutrition.schemas import PlanOut
from modules.programs.schemas import ProgramOut

router = APIRouter(prefix="/ai", tags=["ai-engine"], dependencies=[Depends(require_permission())])


@router.post(
    "/program/generate",
    response_model=ProgramOut,
    summary="تولید برنامه از موتور قواعد قطعی (G8 — M15)",
)
def generate_program(payload: ProgramGenerateIn, db: DbSession):
    return service.draft_program_with_explanation(
        db,
        member_id=payload.member_id,
        goal=payload.goal,
        level=payload.level,
        days_per_week=payload.days_per_week,
        weeks_count=payload.weeks_count,
        constraints=payload.constraints,
    )


@router.post(
    "/nutrition/generate",
    response_model=PlanOut,
    summary="تولید برنامهٔ غذایی از موتور قواعد قطعی (G8 — M15)",
)
def generate_nutrition(payload: NutritionGenerateIn, db: DbSession):
    return service.draft_nutrition_with_explanation(
        db,
        member_id=payload.member_id,
        weight_kg=payload.weight_kg,
        height_cm=payload.height_cm,
        age=payload.age,
        gender=payload.gender,
        activity=payload.activity,
        goal=payload.goal,
    )
