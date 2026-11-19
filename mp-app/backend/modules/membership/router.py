"""روتر membership."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.deps import CurrentUser, DbSession, require_permission
from app.errors import ForbiddenError
from app.ids import Id
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
    user: CurrentUser,
    # سقف بالا لازم است، نه فقط ge=0: DAST (R18) نشان داد
    # `GET /members?offset=10**30` روی SQLite `OverflowError` می‌دهد ← ۵۰۰.
    offset: int = Query(0, ge=0, le=1_000_000),
    limit: int = Query(50, ge=1, le=200),
    gender: str | None = Query(
        None, pattern="^(male|female)$", description="فیلتر تفکیک جنسیت (M41-c1)"
    ),
):
    return service.list_members(db, offset=offset, limit=limit, user=user, gender=gender)


# ── پروفایل شخصی (کلاینت عضو) — ساخت/ویرایش واقعی [finn] ──


class MeUpdate(BaseModel):
    full_name: str | None = None
    goal: str | None = None
    gender: str | None = None
    height_cm: int | None = Field(default=None, ge=50, le=260)
    constraints: str | None = None


def _me_dict(m, u) -> dict:
    return {
        "id": m.id,
        "user_id": u.id,
        "full_name": u.full_name,
        "phone": u.phone,
        # M46-c2 — نقش واقعی، تا کلاینت مجبور نباشد «مدیر» را hardcode کند
        "role": getattr(u, "role", "member"),
        "goal": m.goal,
        "gender": m.gender,
        "height_cm": m.height_cm,
        "constraints": m.constraints,
    }


@router.get("/me", summary="پروفایل من (ساخت خودکار در اولین ورود)")
def get_me(db: DbSession, user: CurrentUser):
    from db.models import Member

    m = db.scalar(select(Member).where(Member.user_id == user.id))
    if m is None:
        m = Member(user_id=user.id, branch_id=1)
        db.add(m)
        db.commit()
        db.refresh(m)
    return _me_dict(m, user)


@router.get("/me/checkins", summary="تاریخچهٔ چک‌این‌های خود عضو (M80)")
def my_checkins(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0, le=1_000_000),
):
    """از شناسهٔ عضوِ متصل به نشست استفاده می‌کند؛ member_id از درخواست نمی‌گیرد."""
    if "member_id" in request.query_params:
        raise ForbiddenError("شناسهٔ عضو در مسیر تاریخچهٔ شخصی قابل‌ارسال نیست")
    return service.my_checkin_history(db, user, limit=limit, offset=offset)


@router.put("/me", summary="ویرایش پروفایل من (نام/هدف/جنس/قد/محدودیت‌ها)")
def update_me(payload: MeUpdate, db: DbSession, user: CurrentUser):
    from db.models import Member, User

    m = db.scalar(select(Member).where(Member.user_id == user.id))
    if m is None:
        m = Member(user_id=user.id, branch_id=1)
        db.add(m)
    if payload.full_name is not None:
        u = db.get(User, user.id)
        u.full_name = payload.full_name
    if payload.goal is not None:
        m.goal = payload.goal
    if payload.gender is not None:
        m.gender = payload.gender
    if payload.height_cm is not None:
        m.height_cm = payload.height_cm
    if payload.constraints is not None:
        m.constraints = payload.constraints
    db.commit()
    db.refresh(m)
    db.refresh(user)
    return _me_dict(m, user)


# ── M41: پلن جنسیت‌محور + صورتحساب [finn] ──


class PlanPurchaseIn(BaseModel):
    member_id: Id
    plan_key: str = Field(..., min_length=2, max_length=40)


@router.get(
    "/me/face-consent",
    summary="وضعیت رضایت بیومتریک من (M61/D1)",
)
def my_face_consent(db: DbSession, user: CurrentUser):
    """«آیا رضایت داده‌ام؟» — تا اپ بتواند دکمهٔ ثبت چهره را درست فعال کند.

    چرا لازم شد: اپ عضو دکمهٔ «ثبت چهره» را همیشه نشان می‌داد، در حالی که
    بدون رضایت ثبت‌شده سرور ۴۰۳ می‌دهد (`_has_active_consent`). یعنی دکمه
    هرگز کار نمی‌کرد و دلیلش هم دیده نمی‌شد. این مسیر مالکیت‌محور است:
    فقط رضایت خودِ کاربر را برمی‌گرداند، نه کسی دیگر.
    """
    from modules.face_id.service import has_active_consent

    return has_active_consent(db, user)


@router.get("/memberships/plans", summary="فهرست پلن‌های جنسیت‌محور (M41-c2)")
def list_plans(db: DbSession, user: CurrentUser):
    from engine.gender_plans import list_plans as _list

    return _list()


@router.post("/memberships/from-plan", summary="خرید/تمدید از روی پلن جنسیت‌محور (M41-c2)")
def create_from_plan(payload: PlanPurchaseIn, db: DbSession):
    return service.create_membership_from_plan(db, payload.member_id, payload.plan_key)


@router.get("/memberships/{membership_id}/invoice", summary="صورتحساب + reason سیاست (M41-c3)")
def get_invoice(membership_id: int, db: DbSession, user: CurrentUser):
    # QF-00 — `member` به `/members/*` GET دسترسی دارد؛ بدون فرستادن کاربر،
    # صورتحساب هر عضوی (شامل gender و price) خواندنی بود.
    return service.membership_invoice(db, membership_id, user=user)


@router.get("/{member_id}", response_model=MemberOut, summary="پروفایل عضو")
def get_member(member_id: int, db: DbSession, user: CurrentUser):
    return service.get_member(db, member_id, user=user)


@router.patch("/{member_id}", response_model=MemberOut, summary="ویرایش پروفایل (US-102)")
def update_member(member_id: int, payload: MemberUpdate, db: DbSession, user: CurrentUser):
    return service.update_member(db, member_id, user=user, **payload.model_dump(exclude_unset=True))


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
def member_memberships(member_id: int, db: DbSession, user: CurrentUser):
    from app.security.ownership import ensure_member_scope

    ensure_member_scope(db, user, member_id)

    from db.models import Membership

    return list(
        db.scalars(
            select(Membership)
            .where(Membership.member_id == member_id)
            .order_by(Membership.id.desc())
        )
    )
