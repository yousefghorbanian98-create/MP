"""روتر membership."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.deps import DbSession, require_permission
from modules.membership import service
from modules.membership.schemas import (
    MemberCreate,
    MemberOut,
    MembershipCreate,
    MembershipOut,
    MemberUpdate,
)

router = APIRouter(
    prefix="/members", tags=["members"], dependencies=[Depends(require_permission())]
)


@router.post("", response_model=MemberOut, summary="ثبت‌نام عضو جدید (US-301)")
def create_member(payload: MemberCreate, db: DbSession):
    # نقش‌ها در M08 با casbin سخت‌گیرانه می‌شوند (RBAC)
    return service.create_member(
        db,
        phone=payload.phone,
        full_name=payload.full_name,
        goal=payload.goal,
        gender=payload.gender,
        height_cm=payload.height_cm,
        constraints=payload.constraints,
    )


@router.get("", response_model=list[MemberOut], summary="لیست اعضا (US-205)")
def list_members(
    db: DbSession,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    return service.list_members(db, offset=offset, limit=limit)


@router.get("/{member_id}", response_model=MemberOut, summary="پروفایل عضو")
def get_member(member_id: int, db: DbSession):
    return service.get_member(db, member_id)


@router.patch("/{member_id}", response_model=MemberOut, summary="ویرایش پروفایل (US-102)")
def update_member(member_id: int, payload: MemberUpdate, db: DbSession):
    return service.update_member(db, member_id, **payload.model_dump(exclude_unset=True))


@router.post(
    "/memberships",
    response_model=MembershipOut,
    summary="ایجاد/تمدید اشتراک (US-302)",
    include_in_schema=True,
)
def create_membership(payload: MembershipCreate, db: DbSession):
    return service.create_membership(
        db,
        member_id=payload.member_id,
        plan_name=payload.plan_name,
        duration_days=payload.duration_days,
        price_rial=payload.price_rial,
    )


@router.get(
    "/{member_id}/memberships",
    response_model=list[MembershipOut],
    summary="تاریخچهٔ اشتراک‌های عضو",
)
def member_memberships(member_id: int, db: DbSession):
    from sqlalchemy import select

    from db.models import Membership

    return list(
        db.scalars(
            select(Membership)
            .where(Membership.member_id == member_id)
            .order_by(Membership.id.desc())
        )
    )
