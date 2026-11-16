"""روتر کلاس/رزرو (M27)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.deps import CurrentUser, DbSession, require_permission
from modules.classes import service

router = APIRouter(prefix="/classes", tags=["classes"])


class ClassIn(BaseModel):
    name: str
    capacity: int = Field(..., ge=1, le=200)
    schedule_text: str = ""
    coach_id: int | None = None


class BookIn(BaseModel):
    class_id: int
    member_id: int


@router.get(
    "",
    summary="لیست کلاس‌ها با ظرفیت/لیست انتظار",
    dependencies=[Depends(require_permission())],
)
def list_classes(user: CurrentUser, db: DbSession):
    # M60/R2 — این مسیر تا امروز **بدون هیچ احراز هویتی** کل جدول کلاس‌ها را
    # با شمارش رزروها برمی‌گرداند؛ یک dump عمومی از دادهٔ عملیاتی باشگاه.
    # `GET /api/v1/classes` بدون توکن ۲۰۰ می‌داد (تأییدشده با TestClient).
    # دو مصرف‌کنندهٔ واقعی (کلاینت فلاتر و ScheduleTimeline استودیو) هر دو
    # توکن می‌فرستند، پس بستنش چیزی را نمی‌شکند.
    return service.list_classes(db)


@router.post(
    "",
    summary="ایجاد کلاس (staff)",
    dependencies=[Depends(require_permission())],
)
def create_class(payload: ClassIn, db: DbSession):
    c = service.create_class(
        db,
        name=payload.name,
        capacity=payload.capacity,
        schedule_text=payload.schedule_text,
        coach_id=payload.coach_id,
    )
    return {"id": c.id, "name": c.name, "capacity": c.capacity}


@router.post(
    "/book",
    summary="رزرو کلاس (confirmed/waitlisted)",
    dependencies=[Depends(require_permission())],
)
def book(payload: BookIn, db: DbSession):
    b = service.book(db, class_id=payload.class_id, member_id=payload.member_id)
    return {"id": b.id, "status": b.status}


@router.post(
    "/cancel",
    summary="لغو رزرو + ارتقای لیست انتظار",
    dependencies=[Depends(require_permission())],
)
def cancel(payload: BookIn, db: DbSession):
    b = service.cancel(db, class_id=payload.class_id, member_id=payload.member_id)
    return {"id": b.id, "status": b.status}
