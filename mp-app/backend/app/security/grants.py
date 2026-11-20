"""مجوز شخصی ادمین (QF-03) — «مالی به‌طور پیش‌فرض خاموش».

# چرا این لایه روی RBAC نشست

`security/rbac.py` نقش‌محور است و برای هر نقش یک «خط اول» می‌دهد. اما نقش
`admin`/`manager` نباید یعنیِ «همه‌چیز از جمله پول». این لایه مجوز **شخصی و
زمان‌دار** اضافه می‌کند: `super_admin` همیشه مجاز است (مالک سیستم)؛ نقش‌های
بالادستی (`admin`, `manager`) برای کلیدهای حساس باید ردیف فعال داشته باشند؛
بقیهٔ نقش‌ها زیر همان RBAC خودشان می‌مانند (پذیرش برای گرفتن پول مجاز است).

# قواعد fail-closed

- کلید ناشناخته هرگز مجاز نیست (`KNOWN_PERMISSIONS` تنها مرجع است).
- ردیف منقضی یا ابطال‌شده اثر ندارد، ولی حذف نمی‌شود (ممیزی).
- نبودِ ردیف = «نه»، نه «شاید».
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import CurrentUser, DbSession
from app.errors import ForbiddenError
from db.models import AdminPermission, User

OWNER_ROLE = "super_admin"

# نقش‌هایی که این لایه آن‌ها را محدود می‌کند؛ بقیه دست‌نخورده می‌مانند.
RESTRICTED_ROLES = frozenset({"admin", "manager"})

KNOWN_PERMISSIONS: dict[str, str] = {
    "finance.write": "تأیید دستی پرداخت، شارژ کیف‌پول و هر تغییر پولی",
    "finance.read": "دیدن گزارش‌های مالی تجمیعی",
    "reports.confidential": "دیدن گزارش محرمانهٔ سلامت عضو",
    "roles.manage": "اعطا/سلب نقش (افزون بر super_admin-only بودن مسیر)",
    "flags.write": "تغییر feature flag در production",
}


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def is_granted(db: Session, user_id: int, permission: str, now: datetime | None = None) -> bool:
    """آیا ردیف فعالی برای این کلید وجود دارد؟ کلید ناشناخته ← همیشه نه."""
    if permission not in KNOWN_PERMISSIONS:
        return False
    moment = now or datetime.now(UTC)
    rows = db.scalars(
        select(AdminPermission).where(
            AdminPermission.user_id == user_id,
            AdminPermission.permission == permission,
            AdminPermission.revoked_at.is_(None),
        )
    )
    for row in rows:
        expires = _aware(row.expires_at)
        if expires is None or expires > moment:
            return True
    return False


def allowed_for(user: User, db: Session, permission: str) -> bool:
    """تصمیم نهایی برای یک کاربر؛ مالک و نقش‌های خارج از دامنه آزادند."""
    if user.role == OWNER_ROLE:
        return True
    if user.role not in RESTRICTED_ROLES:
        return True
    return is_granted(db, user.id, permission)


def require_grant(permission: str):
    """guard FastAPI: کلید مجوز باید فعال باشد، وگرنه ۴۰۳ `permission_required`."""
    if permission not in KNOWN_PERMISSIONS:
        raise ValueError(f"کلید مجوز ناشناخته: {permission}")

    def _guard(user: CurrentUser, db: DbSession) -> User:
        if not allowed_for(user, db, permission):
            raise ForbiddenError(
                f"مجوز «{permission}» برای این حساب فعال نیست — فقط مالک سیستم می‌تواند اعطا کند",
                code="permission_required",
            )
        return user

    _guard.__rbac__ = f"grant:{permission}"  # type: ignore[attr-defined]
    _guard.__grant__ = permission  # type: ignore[attr-defined]
    return _guard


def effective_status(
    db: Session, user_id: int, permission: str, now: datetime | None = None
) -> str:
    """وضعیت مؤثر برای نمایش: active | expired | revoked | missing."""
    moment = now or datetime.now(UTC)
    rows = list(
        db.scalars(
            select(AdminPermission)
            .where(
                AdminPermission.user_id == user_id,
                AdminPermission.permission == permission,
            )
            .order_by(AdminPermission.id.desc())
        )
    )
    for row in rows:
        if row.revoked_at is not None:
            continue
        expires = _aware(row.expires_at)
        if expires is None or expires > moment:
            return "active"
        return "expired"
    return "revoked" if rows else "missing"
