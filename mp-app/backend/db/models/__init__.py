"""ثبت همهٔ مدل‌ها — import این ماژول کل metadata را کامل می‌کند."""

from db.models.admin import AuditLog, Campaign, FeatureFlag, Offer
from db.models.ai import RuleRun
from db.models.assessment import (
    Assessment14Domain,
    AxisAssessment,
    AxisScore,
    DomainScore,
    FieldTestResult,
    JacksonPollockMeasurement,
    NormEntry,
)
from db.models.auth import OtpCode, RefreshToken, User
from db.models.classes import ClassBooking, GymClass
from db.models.content import (
    CatalogExercise,
    CatalogSource,
    Exercise,
    FoodItem,
    ProgressionLadder,
    ProgressionStep,
)
from db.models.face_id import BiometricConsent, CheckIn, FaceTemplate
from db.models.membership import Member, Membership
from db.models.notification import Notification
from db.models.nutrition import MealItem, NutritionPlan
from db.models.payments import Payment, WalletTransaction
from db.models.programs import ProgramExercise, ProgramWeek, SetFeedback, WorkoutProgram

__all__ = [
    "Assessment14Domain",
    "AuditLog",
    "AxisAssessment",
    "AxisScore",
    "BiometricConsent",
    "Campaign",
    "CatalogExercise",
    "CatalogSource",
    "ClassBooking",
    "CheckIn",
    "DomainScore",
    "Exercise",
    "FaceTemplate",
    "FieldTestResult",
    "FeatureFlag",
    "FoodItem",
    "GymClass",
    "JacksonPollockMeasurement",
    "MealItem",
    "Member",
    "Membership",
    "NormEntry",
    "Notification",
    "NutritionPlan",
    "Offer",
    "OtpCode",
    "Payment",
    "ProgramExercise",
    "ProgramWeek",
    "ProgressionLadder",
    "ProgressionStep",
    "RefreshToken",
    "RuleRun",
    "SetFeedback",
    "User",
    "WalletTransaction",
    "WorkoutProgram",
]
