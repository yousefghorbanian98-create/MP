"""روتر جمعیت/ورودی پویا (M25)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.deps import require_permission
from modules.population.gates import POPULATION_PATHS, assert_generation_allowed
from modules.population.intake import next_questions

router = APIRouter(
    prefix="/population",
    tags=["programs"],
    # M43-c3 (D-004): casbin تنها مرجع مجوز — نقش‌ها در security/rbac.py
    dependencies=[Depends(require_permission())],
)


class GateCheckIn(BaseModel):
    path: str = Field(min_length=1, max_length=80)


class IntakeIn(BaseModel):
    goal: str
    constraints: list[str] = []
    answered_ids: list[str] = []


@router.get("/paths", summary="ماتریس وضعیت مسیرهای جمعیتی (E05)")
def paths():
    return POPULATION_PATHS


@router.post("/gate-check", summary="گیت صریح تولید — توقف خودکار برای مسیر غیرفعال")
def gate_check(payload: GateCheckIn):
    return assert_generation_allowed(payload.path)


@router.post("/intake/next", summary="سؤال‌های تکمیلی پویا (هدف‌محور)")
def intake_next(payload: IntakeIn):
    return {"questions": next_questions(payload.goal, payload.constraints, payload.answered_ids)}
