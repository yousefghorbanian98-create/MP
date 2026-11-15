"""سرویس membership — عضو، پروفایل، اشتراک (منطق تجاری فقط اینجا)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import ApiError, ConflictError, NotFoundError
from db.models import Member, Membership, User


def create_member(
    db: Session,
    phone: str,
    full_name: str,
    goal: str = "",
    gender: str = "unknown",
    height_cm: int | None = None,
    constraints: str = "[]",
) -> Member:
    existing = db.scalar(select(User).where(User.phone == phone))
    if existing is not None:
        raise ConflictError("این شماره قبلاً ثبت شده است")
    user = User(phone=phone, full_name=full_name, role="member")
    db.add(user)
    db.flush()
    member = Member(
        user_id=user.id,
        goal=goal,
        gender=gender,
        height_cm=height_cm,
        constraints=constraints,
        branch_id=1,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    from cache.keys import invalidate_member_caches
    from cache.store import get_cache

    invalidate_member_caches(get_cache())
    return member


def get_member(db: Session, member_id: int, user=None) -> Member:
    from app.security.ownership import ensure_member_scope

    ensure_member_scope(db, user, member_id)  # قبل از کش — کش نباید مالکیت را دور بزند
    from cache.keys import member_profile_key
    from cache.store import get_cache
    from modules.membership.repository import MemberRepository

    cache = get_cache()
    cached = cache.get(member_profile_key(member_id))
    if cached is not None:
        from db.models import Member as MemberModel

        return db.get(MemberModel, cached["id"])
    member = MemberRepository(db).get(member_id)
    if member is None:
        raise NotFoundError("عضو یافت نشد")
    cache.set(
        member_profile_key(member_id),
        {"id": member.id, "goal": member.goal},
        ttl=30,
    )
    return member


def list_members(db: Session, offset: int = 0, limit: int = 50, user=None, gender: str | None = None) -> list[Member]:
    from app.security.ownership import ensure_member_scope, get_own_member
    from cache.keys import members_list_key
    from cache.store import get_cache
    from db.models import Member as MemberModel
    from modules.membership.repository import MemberRepository

    if user is not None and user.role == "member":
        ensure_member_scope(
            db, user, get_own_member(db, user).id if get_own_member(db, user) else -1
        )
        own = get_own_member(db, user)
        return [own] if own else []
    cache = get_cache()
    key = members_list_key(offset, limit) + (f":{gender}" if gender else "")
    cached = cache.get(key)
    if cached is not None:
        return [db.get(MemberModel, mid) for mid in cached]
    members = MemberRepository(db).list(offset=offset, limit=limit, gender=gender)
    cache.set(key, [m.id for m in members], ttl=30)
    return members


def update_member(db: Session, member_id: int, user=None, **fields) -> Member:
    member = get_member(db, member_id, user=user)
    for key, value in fields.items():
        if value is not None and hasattr(member, key):
            setattr(member, key, value)
    db.commit()
    db.refresh(member)
    from cache.keys import invalidate_member_caches
    from cache.store import get_cache

    invalidate_member_caches(get_cache(), member.id)
    return member


def create_membership(
    db: Session,
    member_id: int,
    plan_name: str,
    duration_days: int,
    price_rial: int,
) -> Membership:
    member = get_member(db, member_id)
    now = datetime.now(UTC)
    # اگر اشتراک فعالی هست، از پایان همان ادامه می‌یابد (تمدید)
    active = db.scalar(
        select(Membership)
        .where(Membership.member_id == member.id, Membership.status == "active")
        .order_by(Membership.expires_at.desc())
        .limit(1)
    )
    start = active.expires_at if active and _aware(active.expires_at) > now else now
    if active and _aware(active.expires_at) > now:
        active.status = "cancelled"  # ادغام تمدید در اشتراک جدید
    ms = Membership(
        member_id=member.id,
        plan_name=plan_name,
        started_at=start,
        expires_at=start + timedelta(days=duration_days),
        status="active",
        price_rial=price_rial,
        branch_id=member.branch_id,
    )
    db.add(ms)
    db.commit()
    db.refresh(ms)
    return ms


def get_active_membership(db: Session, member_id: int) -> Membership | None:
    from modules.membership.repository import MembershipRepository

    return MembershipRepository(db).active_for_member(member_id)


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def create_membership_from_plan(db: Session, member_id: int, plan_key: str) -> dict:
    """خرید/تمدید از روی پلن جنسیت‌محور (M41-c2) — مدت/قیمت از motor + reason."""
    from engine.gender_plans import resolve_plan

    member = get_member(db, member_id)
    if member.gender not in ("male", "female"):
        raise ApiError(
            "جنسیت عضو ثبت نشده — ابتدا ثبت‌نام را کامل کنید (داده ناشناخته است نه صفر)",
            code="missing_gender",
        )
    try:
        resolution = resolve_plan(plan_key=plan_key, gender=member.gender)
    except KeyError as exc:
        raise ApiError(f"پلن «{plan_key}» تعریف نشده", code="unknown_plan") from exc
    ms = create_membership(
        db,
        member_id=member.id,
        plan_name=resolution["plan_name"],
        duration_days=resolution["duration_days"],
        price_rial=resolution["price_rial"],
    )
    return {"membership": ms, "invoice": {**resolution, "membership_id": ms.id}}


def membership_invoice(db: Session, membership_id: int) -> dict:
    """صورتحساب/تاریخچه با reason سیاست (M41-c3) — بدون ادعای علمی/فروش."""
    from db.models import Membership
    from engine.gender_plans import PLAN_POLICY_VERSION

    ms = db.get(Membership, membership_id)
    if ms is None:
        raise ApiError("اشتراک یافت نشد", code="not_found")
    member = db.get(Member, ms.member_id)
    duration = (_aware(ms.expires_at) - _aware(ms.started_at)).days
    return {
        "membership_id": ms.id,
        "member_id": ms.member_id,
        "plan_name": ms.plan_name,
        "started_at": ms.started_at.isoformat(),
        "expires_at": ms.expires_at.isoformat(),
        "duration_days": duration,
        "price_rial": ms.price_rial,
        "status": ms.status,
        "gender": member.gender if member else None,
        "policy_note": (
            "قیمت و مدت طبق سیاست نسخه‌دار باشگاه ثبت شده است (تصمیم مالک) — "
            "در پلن‌های بانوان، ماه ۳۷ روز (۳۰+۷ جبران هفتهٔ قاعدگی) محاسبه می‌شود"
        ),
        "policy_version": PLAN_POLICY_VERSION,
    }
