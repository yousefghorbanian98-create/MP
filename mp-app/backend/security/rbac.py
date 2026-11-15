"""RBAC با casbin — ماتریس نقش/اجازه (python-casbin).

نقش‌ها: member، coach، reception، manager
قاعده: هیچ endpoint حساسی بدون guard نقش باز نمی‌ماند (M08).
"""

from __future__ import annotations

import casbin

MODEL_TEXT = """
[request_definition]
r = sub, obj, act

[policy_definition]
p = sub, obj, act

[role_definition]
g = _, _

[policy_effect]
e = some(where (p.eft == allow))

[matchers]
m = g(r.sub, p.sub) && keyMatch2(r.obj, p.obj) && (r.act == p.act || p.act == "*")
"""

# ماتریس اجازه‌ها (policy) — (نقش، الگوی مسیر، متد)
# نکتهٔ keyMatch2: فقط «/*» وایلدکارت است (به‌صورت /.* تفسیر می‌شود) — پس هر مسیر
# هم به‌صورت exact و هم با «/*» ثبت می‌شود.
# DENIES (D-004): ردِ صریح که بر allow اولویت دارد — برای حفظ معنای قدیمیِ
# guardهای ترکیبی (مثلاً «manager همه‌چیز به‌جز گزارش محرمانه»).
POLICIES: list[tuple[str, str, str]] = [
    # عضو: فقط دادهٔ خودش (کنترل مالکیت در service — لایهٔ ABAC بعدی)
    ("member", "/api/v1/auth/logout", "POST"),
    ("member", "/api/v1/auth/logout-all", "POST"),
    ("member", "/api/v1/auth/refresh", "POST"),
    ("member", "/api/v1/members/*", "GET"),
    ("member", "/api/v1/members/me", "PUT"),
    ("member", "/api/v1/face/consent", "POST"),
    ("member", "/api/v1/face/consent/revoke", "POST"),
    ("member", "/api/v1/face/enroll/*", "DELETE"),
    ("member", "/api/v1/face/checkin", "POST"),
    ("member", "/api/v1/face/privacy-notice", "GET"),
    ("member", "/api/v1/face/deep-status", "GET"),
    ("member", "/api/v1/face/qr-token", "GET"),
    ("member", "/api/v1/face/checkin-qr", "POST"),
    ("member", "/api/v1/face/checkins/*", "POST"),
    ("member", "/api/v1/notifications/*", "GET"),
    ("member", "/api/v1/notifications/*", "POST"),
    ("member", "/api/v1/programs/*", "GET"),
    ("member", "/api/v1/programs/set-feedback", "POST"),
    ("member", "/api/v1/assessments/*", "GET"),
    ("member", "/api/v1/assessments/limb", "POST"),
    ("member", "/api/v1/axis-assessments", "GET"),
    ("member", "/api/v1/axis-assessments/*", "GET"),
    ("member", "/api/v1/payments", "GET"),
    ("member", "/api/v1/payments/*", "GET"),
    ("member", "/api/v1/payments/wallet/pay", "POST"),
    ("member", "/api/v1/nutrition/*", "GET"),
    # G8 (M51-c1) — چت: عضو باید بتواند گفتگوی خودش را ببیند و پیام بدهد.
    # دامنهٔ دقیق، نه `*`: فقط زیرمسیرهای گفتگو. کنترل «کدام گفتگو»
    # در chat_service._load_conversation است (مالکیت بررسی می‌شود).
    ("member", "/api/v1/chat/conversations", "GET"),
    ("member", "/api/v1/chat/conversations", "POST"),
    ("member", "/api/v1/chat/conversations/*", "GET"),
    ("member", "/api/v1/chat/conversations/*", "POST"),
    # M43-c3 (D-004): مسیرهای مهاجرت‌داده‌شده از require_roles — عضو در فرم ورودی خودش
    # (باگ REA: نبود policy برای /ai و /population ← ۴۰۳ در مسیر ثبت‌نام واقعی)
    ("member", "/api/v1/ai/program/generate", "POST"),
    ("member", "/api/v1/ai/nutrition/generate", "POST"),
    ("member", "/api/v1/ai/suggest-weight", "POST"),
    ("member", "/api/v1/population/*", "*"),
    ("member", "/api/v1/classes/book", "POST"),
    ("member", "/api/v1/classes/cancel", "POST"),
    # مربی: ارزیابی/برنامه/اعضا (خواندن+نوشتن برنامه)
    ("coach", "/api/v1/members", "GET"),
    ("coach", "/api/v1/members", "POST"),
    ("coach", "/api/v1/members/*", "*"),
    ("coach", "/api/v1/members/memberships", "POST"),
    ("coach", "/api/v1/assessments", "GET"),
    ("coach", "/api/v1/assessments", "POST"),
    ("coach", "/api/v1/assessments/*", "*"),
    ("coach", "/api/v1/axis-assessments", "GET"),
    ("coach", "/api/v1/axis-assessments", "POST"),
    ("coach", "/api/v1/axis-assessments/*", "*"),
    ("coach", "/api/v1/programs", "GET"),
    ("reception", "/api/v1/programs", "GET"),
    ("coach", "/api/v1/admin/attendance", "GET"),
    ("coach", "/api/v1/admin/checkins", "GET"),
    ("coach", "/api/v1/programs/*", "*"),
    # M43-c3 (D-004): مسیرهای مهاجرت‌داده‌شده از require_roles
    ("coach", "/api/v1/ai/program/generate", "POST"),
    ("coach", "/api/v1/ai/nutrition/generate", "POST"),
    ("coach", "/api/v1/ai/suggest-weight", "POST"),
    ("coach", "/api/v1/population/*", "*"),
    ("coach", "/api/v1/classes", "POST"),
    ("coach", "/api/v1/classes/book", "POST"),
    ("coach", "/api/v1/classes/cancel", "POST"),
    ("coach", "/api/v1/reports/*", "*"),
    # M45: دادهٔ واقعی استودیو — حضور و خلاصهٔ اعضا برای مربی/مدیر/پذیرش/مالک
    ("coach", "/api/v1/admin/attendance", "GET"),
    ("coach", "/api/v1/admin/checkins", "GET"),
    ("coach", "/api/v1/admin/members-summary", "GET"),
    ("reception", "/api/v1/admin/attendance", "GET"),
    ("reception", "/api/v1/admin/checkins", "GET"),
    ("reception", "/api/v1/admin/members-summary", "GET"),
    ("coach", "/api/v1/nutrition/*", "*"),
    # G8 — مربی طرف گفتگو
    ("coach", "/api/v1/chat/conversations", "GET"),
    ("coach", "/api/v1/chat/conversations", "POST"),
    ("coach", "/api/v1/chat/conversations/*", "*"),
    ("coach", "/api/v1/nutrition/plans", "POST"),
    ("coach", "/api/v1/face/*", "*"),
    ("reception", "/api/v1/face/privacy-notice", "GET"),
    ("reception", "/api/v1/face/deep-status", "GET"),
    ("coach", "/api/v1/notifications/*", "*"),
    # پذیرش: ثبت‌نام/پرداخت/چک‌این
    ("reception", "/api/v1/members", "GET"),
    ("reception", "/api/v1/members", "POST"),
    ("reception", "/api/v1/members/*", "*"),
    ("reception", "/api/v1/members/memberships", "POST"),
    ("reception", "/api/v1/payments", "GET"),
    ("reception", "/api/v1/payments", "POST"),
    ("reception", "/api/v1/payments/*", "*"),
    ("reception", "/api/v1/face/checkin", "POST"),
    ("reception", "/api/v1/face/checkin-qr", "POST"),
    ("reception", "/api/v1/face/consent", "POST"),
    ("reception", "/api/v1/face/consent/revoke", "POST"),
    ("reception", "/api/v1/notifications/*", "*"),
    ("reception", "/api/v1/population/*", "*"),
    # مدیر: همه‌چیز
    ("manager", "/*", "*"),
    # ادمین سیستم: دسترسی کامل (هم‌ارز manager در casbin)
    ("admin", "/*", "*"),
    # مالک سیستم: دسترسی کامل (M39-c3 — شکاف policy پیدا شد: super_admin ثبت نشده بود)
    ("super_admin", "/*", "*"),
]

# ردِ صریح (D-004) — بر allow مقدم است؛ برای حفظ معنای قدیمیِ guardهای ترکیبی:
# - گزارش محرمانه فقط admin/coach (body-comp طبق قاعدهٔ کاربر فقط admin — manager هم رد)
# - بازبینی ارزیابی فقط manager/admin (coach نباید تأیید/رد کند)
DENIES: list[tuple[str, str, str]] = [
    ("manager", "/api/v1/reports/*", "*"),
    ("coach", "/api/v1/axis-assessments/:id/review", "POST"),
]


def _build_enforcer() -> casbin.Enforcer:
    model = casbin.model.Model()
    model.load_model_from_text(MODEL_TEXT)
    enforcer = casbin.Enforcer(model)
    for role, obj, act in POLICIES:
        enforcer.add_policy(role, obj, act)
    return enforcer


_enforcer: casbin.Enforcer | None = None


def get_enforcer() -> casbin.Enforcer:
    global _enforcer
    if _enforcer is None:
        _enforcer = _build_enforcer()
    return _enforcer


def enforce(role: str, path: str, method: str) -> bool:
    """بررسی اجازهٔ نقش برای مسیر/متد — DENIES (رد صریح) بر allow مقدم است (D-004)."""
    for deny_role, deny_obj, deny_act in DENIES:
        if (
            role == deny_role
            and (deny_act == "*" or deny_act == method)
            and casbin.util.key_match2(path, deny_obj)
        ):
            return False
    return bool(get_enforcer().enforce(role, path, method))
