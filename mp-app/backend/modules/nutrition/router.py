"""روتر nutrition."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.deps import CurrentUser, DbSession, require_permission
from modules.nutrition import service
from modules.nutrition.schemas import (
    FoodLogIn,
    FoodLogOut,
    FoodSearchRow,
    PlanFromEngineIn,
    PlanOut,
)

router = APIRouter(
    prefix="/nutrition", tags=["nutrition"], dependencies=[Depends(require_permission())]
)


@router.post("/plans", response_model=PlanOut, summary="ثبت برنامهٔ تغذیه از خروجی موتور (US-204)")
def create_plan(payload: PlanFromEngineIn, db: DbSession):
    return service.create_plan_from_engine(db, payload.member_id, payload.model_dump())


@router.post("/plans/{plan_id}/approve", response_model=PlanOut, summary="تأیید تغذیه توسط مربی")
def approve_plan(plan_id: int, db: DbSession, user: CurrentUser):
    """M49-c1 — این endpoint قبلاً `coach_id=0` می‌فرستاد (کامنت «M08: از JWT»
    که هرگز انجام نشد). `users.id` هرگز صفر نیست، پس هر تأیید به
    «FOREIGN KEY constraint failed» می‌خورد: دکمهٔ تأیید در عمل کار نمی‌کرد.
    حالا مربی از توکن گرفته می‌شود."""
    return service.approve_plan(db, plan_id, coach_id=user.id)


@router.get(
    "/plans/member/{member_id}", response_model=list[PlanOut], summary="برنامه‌های تغذیهٔ عضو"
)
def list_member_plans(member_id: int, db: DbSession, user: CurrentUser):
    return service.list_member_plans(db, member_id, user=user)


# ── G5 — ثبت غذای روزانه [finn] ──


@router.get(
    "/foods",
    response_model=list[FoodSearchRow],
    summary="جستجوی جدول غذایی (دادهٔ آزاد MIT)",
)
def search_foods(db: DbSession, q: str = "", limit: int = 30):
    return service.search_foods(db, query=q, limit=limit)


@router.post(
    "/food-logs",
    response_model=FoodLogOut,
    summary="ثبت وعده‌های واقعی عضو (G5)",
)
def log_food(payload: FoodLogIn, db: DbSession, user: CurrentUser):
    entries = []
    for e in payload.entries:
        d = e.model_dump()
        d["logged_for_date"] = e.logged_for_date.isoformat() if e.logged_for_date else None
        entries.append(d)
    return service.log_food(db, member_id=payload.member_id, entries=entries, user=user)


@router.get(
    "/food-logs/member/{member_id}/daily",
    summary="جمع کالری/درشت‌مغذی یک روز + مقایسه با برنامهٔ تأییدشده (G5)",
)
def daily_summary(member_id: int, db: DbSession, user: CurrentUser, date: str | None = None):
    return service.daily_summary(db, member_id=member_id, day=date, user=user)
