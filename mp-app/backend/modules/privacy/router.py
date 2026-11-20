"""روتر نگهداری داده (QF-28) — فقط مالک سیستم.

ادمین عادی هم این‌جا مجاز نیست: حذف دادهٔ ممیزی قابل‌بازگشت نیست و باید یک
مسئول مشخص داشته باشد. RBAC `admin` را مجاز می‌داند، پس این گارد لایهٔ دوم و
عامدانه است.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.deps import CurrentUser, DbSession, require_permission
from app.errors import ForbiddenError
from modules.privacy import retention

router = APIRouter(
    prefix="/admin/retention",
    tags=["privacy"],
    dependencies=[Depends(require_permission())],
)


def _require_owner(user: CurrentUser) -> None:
    if getattr(user, "role", None) != "super_admin":
        raise ForbiddenError("نگهداری داده فقط برای مالک سیستم مجاز است")


@router.get("", summary="پیش‌نمایش سیاست نگهداری و ردیف‌های منقضی (QF-28)")
def preview(db: DbSession, user: CurrentUser):
    _require_owner(user)
    return retention.preview(db)


@router.post("/run", summary="اجرای نگهداری و حذف ردیف‌های منقضی (QF-28)")
def run(db: DbSession, user: CurrentUser):
    _require_owner(user)
    return retention.run(db, commit=True)
