"""تجمیع روترهای /api/v1 — قرارداد نسخه‌دار."""

from __future__ import annotations

from fastapi import APIRouter

from api.v1.monitoring import router as monitoring_router
from modules.admin.router import router as admin_router
from modules.ai.router import router as ai_router
from modules.ai_engine.router import router as ai_engine_router
from modules.assessment.router import router as assessment_router
from modules.auth.router import router as auth_router
from modules.axis_assessment.router import router as axis_assessment_router
from modules.classes.router import router as classes_router
from modules.exercises.router import router as library_router
from modules.expenses.router import router as expenses_router
from modules.face_id.router import router as face_router
from modules.membership.router import router as members_router
from modules.notification.chat_router import router as chat_router
from modules.notification.router import router as notifications_router
from modules.nutrition.router import router as nutrition_router
from modules.payments.router import payments_return_router
from modules.payments.router import router as payments_router
from modules.population.router import router as population_router
from modules.programs.router import router as programs_router
from modules.reporting.router import router as reporting_router
from modules.shop.router import router as shop_router
from modules.updates.router import router as updates_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(classes_router)
api_router.include_router(library_router)
api_router.include_router(members_router)
api_router.include_router(payments_router)
api_router.include_router(expenses_router)
# بازگشت مرورگر از بانک — عمداً بیرونِ require_permission (توضیح در router.py)
api_router.include_router(payments_return_router)
api_router.include_router(assessment_router)
api_router.include_router(axis_assessment_router)
api_router.include_router(programs_router)
api_router.include_router(reporting_router)
api_router.include_router(population_router)
api_router.include_router(nutrition_router)
api_router.include_router(face_router)
api_router.include_router(notifications_router)
api_router.include_router(chat_router)
api_router.include_router(admin_router)
api_router.include_router(shop_router)
api_router.include_router(ai_router)
api_router.include_router(monitoring_router)
api_router.include_router(ai_engine_router)
api_router.include_router(updates_router)
