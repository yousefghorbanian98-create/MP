"""روتر nutrition."""

from __future__ import annotations

from fastapi import APIRouter

from app.deps import DbSession
from modules.nutrition import service
from modules.nutrition.schemas import PlanFromEngineIn, PlanOut

router = APIRouter(prefix="/nutrition", tags=["nutrition"])


@router.post("/plans", response_model=PlanOut, summary="ثبت برنامهٔ تغذیه از خروجی موتور (US-204)")
def create_plan(payload: PlanFromEngineIn, db: DbSession):
    return service.create_plan_from_engine(db, payload.member_id, payload.model_dump())


@router.post("/plans/{plan_id}/approve", response_model=PlanOut, summary="تأیید تغذیه توسط مربی")
def approve_plan(plan_id: int, db: DbSession):
    return service.approve_plan(db, plan_id, coach_id=0)  # M08: از JWT


@router.get(
    "/plans/member/{member_id}", response_model=list[PlanOut], summary="برنامه‌های تغذیهٔ عضو"
)
def list_member_plans(member_id: int, db: DbSession):
    return service.list_member_plans(db, member_id)
