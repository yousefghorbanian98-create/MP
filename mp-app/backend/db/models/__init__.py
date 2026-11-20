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
from db.models.auth import (
    AdminPermission,
    OtpCode,
    PhoneChangeChallenge,
    RefreshToken,
    User,
)
from db.models.chat import Conversation, Message
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
from db.models.nutrition import BodyWeightLog, FoodLog, MealItem, NutritionPlan
from db.models.payments import Payment, PaymentReceipt, WalletTransaction
from db.models.programs import ProgramExercise, ProgramWeek, SetFeedback, WorkoutProgram
from db.models.segment import LimbMeasurement
from db.models.shop import (
    CartItem,
    ChangeRequest,
    Order,
    OrderItem,
    PaymentGatewayConfig,
    PriceBook,
    Product,
    ProductCategory,
    ProductVariant,
)

__all__ = [
    "AdminPermission",
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
    "BodyWeightLog",
    "Conversation",
    "Message",
    "LimbMeasurement",
    "FoodLog",
    "MealItem",
    "Member",
    "Membership",
    "NormEntry",
    "Notification",
    "NutritionPlan",
    "Offer",
    "OtpCode",
    "Payment",
    "PaymentReceipt",
    "PhoneChangeChallenge",
    "ProgramExercise",
    "ProgramWeek",
    "ProgressionLadder",
    "ProgressionStep",
    "CartItem",
    "ChangeRequest",
    "Order",
    "OrderItem",
    "PaymentGatewayConfig",
    "PriceBook",
    "Product",
    "ProductCategory",
    "ProductVariant",
    "RefreshToken",
    "RuleRun",
    "SetFeedback",
    "User",
    "WalletTransaction",
    "WorkoutProgram",
]
