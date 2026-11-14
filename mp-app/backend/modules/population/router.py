"""روتر جمعیت/ورودی پویا (M25)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.deps import require_roles
from modules.population.gates import POPULATION_PATHS, assert_generation_allowed
from modules.population.intake import next_questions

router = APIRouter(prefix="/population", tags=["programs"])


class IntakeIn(BaseModel):
    goal: str
    constraints: list[str] = []
    answered_ids: list[str] = []


@router.get("/paths", summary="ماتریس وضعیت مسیرهای جمعیتی (E05)")
def paths(_staff=Depends(require_roles("admin", "coach", "manager"))):
    return POPULATION_PATHS


@router.post("/gate-check", summary="گیت صریح تولید — توقف خودکار برای مسیر غیرفعال")
def gate_check(path: str, _staff=Depends(require_roles("admin", "coach", "manager"))):
    return assert_generation_allowed(path)


@router.post("/intake/next", summary="سؤال‌های تکمیلی پویا (هدف‌محور)")
def intake_next(payload: IntakeIn, _staff=Depends(require_roles("admin", "coach", "manager"))):
    return {"questions": next_questions(payload.goal, payload.constraints, payload.answered_ids)}
