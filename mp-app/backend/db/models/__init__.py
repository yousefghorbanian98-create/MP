"""ثبت همهٔ مدل‌ها — import این ماژول کل metadata را کامل می‌کند."""

from db.models.admin import AuditLog, Campaign, FeatureFlag, Offer
from db.models.ai import RuleRun
from db.models.assessment import Assessment14Domain, DomainScore, JacksonPollockMeasurement
from db.models.auth import OtpCode, RefreshToken, User
from db.models.content import Exercise, FoodItem
from db.models.face_id import BiometricConsent, CheckIn, FaceTemplate
from db.models.membership import Member, Membership
from db.models.notification import Notification
from db.models.nutrition import MealItem, NutritionPlan
from db.models.payments import Payment, WalletTransaction
from db.models.programs import ProgramExercise, ProgramWeek, WorkoutProgram

__all__ = [
    "Assessment14Domain",
    "AuditLog",
    "BiometricConsent",
    "Campaign",
    "CheckIn",
    "DomainScore",
    "Exercise",
    "FaceTemplate",
    "FeatureFlag",
    "FoodItem",
    "JacksonPollockMeasurement",
    "MealItem",
    "Member",
    "Membership",
    "Notification",
    "NutritionPlan",
    "Offer",
    "OtpCode",
    "Payment",
    "ProgramExercise",
    "ProgramWeek",
    "RefreshToken",
    "RuleRun",
    "User",
    "WalletTransaction",
    "WorkoutProgram",
]
