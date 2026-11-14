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
POLICIES: list[tuple[str, str, str]] = [
    # عضو: فقط دادهٔ خودش (کنترل مالکیت در service — لایهٔ ABAC بعدی)
    ("member", "/api/v1/auth/logout", "POST"),
    ("member", "/api/v1/auth/logout-all", "POST"),
    ("member", "/api/v1/auth/refresh", "POST"),
    ("member", "/api/v1/members/*", "GET"),
    ("member", "/api/v1/face/consent", "POST"),
    ("member", "/api/v1/face/consent/revoke", "POST"),
    ("member", "/api/v1/face/enroll/*", "DELETE"),
    ("member", "/api/v1/face/checkin", "POST"),
    ("member", "/api/v1/notifications/*", "GET"),
    ("member", "/api/v1/notifications/*", "POST"),
    ("member", "/api/v1/programs/*", "GET"),
    ("member", "/api/v1/assessments/*", "GET"),
    ("member", "/api/v1/payments", "GET"),
    ("member", "/api/v1/payments/*", "GET"),
    ("member", "/api/v1/payments/wallet/pay", "POST"),
    ("member", "/api/v1/nutrition/*", "GET"),
    # مربی: ارزیابی/برنامه/اعضا (خواندن+نوشتن برنامه)
    ("coach", "/api/v1/members", "GET"),
    ("coach", "/api/v1/members", "POST"),
    ("coach", "/api/v1/members/*", "*"),
    ("coach", "/api/v1/members/memberships", "POST"),
    ("coach", "/api/v1/assessments", "GET"),
    ("coach", "/api/v1/assessments", "POST"),
    ("coach", "/api/v1/assessments/*", "*"),
    ("coach", "/api/v1/programs", "GET"),
    ("coach", "/api/v1/programs/*", "*"),
    ("coach", "/api/v1/nutrition/*", "*"),
    ("coach", "/api/v1/nutrition/plans", "POST"),
    ("coach", "/api/v1/face/*", "*"),
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
    ("reception", "/api/v1/face/consent", "POST"),
    ("reception", "/api/v1/face/consent/revoke", "POST"),
    ("reception", "/api/v1/notifications/*", "*"),
    # مدیر: همه‌چیز
    ("manager", "/*", "*"),
    # ادمین سیستم: دسترسی کامل (هم‌ارز manager در casbin)
    ("admin", "/*", "*"),
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
    """بررسی اجازهٔ نقش برای مسیر/متد."""
    return bool(get_enforcer().enforce(role, path, method))
