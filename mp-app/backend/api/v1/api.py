"""تجمیع روترهای /api/v1 — قرارداد نسخه‌دار."""

from __future__ import annotations

from fastapi import APIRouter

from api.v1.monitoring import router as monitoring_router
from modules.admin.router import router as admin_router
from modules.assessment.router import router as assessment_router
from modules.auth.router import router as auth_router
from modules.face_id.router import router as face_router
from modules.membership.router import router as members_router
from modules.notification.router import router as notifications_router
from modules.nutrition.router import router as nutrition_router
from modules.payments.router import router as payments_router
from modules.programs.router import router as programs_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(members_router)
api_router.include_router(payments_router)
api_router.include_router(assessment_router)
api_router.include_router(programs_router)
api_router.include_router(nutrition_router)
api_router.include_router(face_router)
api_router.include_router(notifications_router)
api_router.include_router(admin_router)
api_router.include_router(monitoring_router)
