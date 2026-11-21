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
from db.models.finance import Expense, ExpenseReceipt, ExpenseRevision, ReportRun
from db.models.membership import Member, Membership
from db.models.notification import Notification
from db.models.nutrition import BodyWeightLog, FoodLog, MealItem, NutritionPlan
from db.models.outbox import InboxMessage, OutboxDeadLetter, OutboxEvent
from db.models.payments import Coupon, LedgerEntry, Payment, PaymentReceipt, WalletTransaction
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
from db.models.worker import WorkerHeartbeat

__all__ = [
    "AdminPermission",
    "Assessment14Domain",
    "AuditLog",
    "AxisAssessment",
    "AxisScore",
    "BiometricConsent",
    "BodyWeightLog",
    "Campaign",
    "CartItem",
    "CatalogExercise",
    "CatalogSource",
    "ChangeRequest",
    "CheckIn",
    "ClassBooking",
    "Conversation",
    "Coupon",
    "DomainScore",
    "Exercise",
    "Expense",
    "ExpenseReceipt",
    "ExpenseRevision",
    "FaceTemplate",
    "FeatureFlag",
    "FieldTestResult",
    "FoodItem",
    "FoodLog",
    "GymClass",
    "InboxMessage",
    "JacksonPollockMeasurement",
    "LedgerEntry",
    "LimbMeasurement",
    "MealItem",
    "Member",
    "Membership",
    "Message",
    "NormEntry",
    "Notification",
    "NutritionPlan",
    "Offer",
    "Order",
    "OrderItem",
    "OtpCode",
    "OutboxDeadLetter",
    "OutboxEvent",
    "Payment",
    "PaymentGatewayConfig",
    "PaymentReceipt",
    "PhoneChangeChallenge",
    "PriceBook",
    "Product",
    "ProductCategory",
    "ProductVariant",
    "ProgramExercise",
    "ProgramWeek",
    "ProgressionLadder",
    "ProgressionStep",
    "RefreshToken",
    "ReportRun",
    "RuleRun",
    "SetFeedback",
    "User",
    "WalletTransaction",
    "WorkerHeartbeat",
    "WorkoutProgram",
]
