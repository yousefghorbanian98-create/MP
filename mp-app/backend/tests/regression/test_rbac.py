"""تست‌های RBAC (M08) — ماتریس نقش/اجازه با casbin."""

from __future__ import annotations

import pytest

from security.rbac import POLICIES, enforce, get_enforcer

MATRIX = [
    # (role, path, method, expected)
    ("member", "/api/v1/members/3", "GET", True),
    ("member", "/api/v1/members", "POST", False),
    ("member", "/api/v1/members/3", "PATCH", False),
    ("member", "/api/v1/auth/logout-all", "POST", True),
    ("member", "/api/v1/notifications/5/read", "POST", True),
    ("member", "/api/v1/programs/2", "GET", True),
    ("member", "/api/v1/programs/2/approve", "POST", False),
    ("member", "/api/v1/admin/flags", "PUT", False),
    ("member", "/api/v1/admin/audit", "GET", False),
    ("coach", "/api/v1/programs/2/approve", "POST", True),
    ("coach", "/api/v1/programs/2/reject", "POST", True),
    ("coach", "/api/v1/assessments", "POST", True),
    ("coach", "/api/v1/assessments/jp7", "POST", True),
    ("coach", "/api/v1/members", "GET", True),
    ("coach", "/api/v1/payments/1/verify", "POST", False),
    ("coach", "/api/v1/admin/flags", "PUT", False),
    ("coach", "/api/v1/nutrition/plans", "POST", True),
    ("reception", "/api/v1/members", "POST", True),
    ("reception", "/api/v1/payments/1/verify", "POST", True),
    ("reception", "/api/v1/payments/wallet/charge", "POST", True),
    ("reception", "/api/v1/face/checkin", "POST", True),
    ("reception", "/api/v1/programs/2/approve", "POST", False),
    ("reception", "/api/v1/admin/audit", "GET", False),
    ("manager", "/api/v1/admin/flags", "PUT", True),
    ("manager", "/api/v1/admin/audit", "GET", True),
    ("manager", "/api/v1/payments", "GET", True),
    ("manager", "/api/v1/whatever", "DELETE", True),
    # M43-c3 (D-004) — معناشناسی یکپارچه‌شدهٔ casbin:
    ("member", "/api/v1/ai/program/generate", "POST", True),  # فرم ورودی عضو (باگ REA فیکس شد)
    ("member", "/api/v1/population/gate-check", "POST", True),  # فرم ورودی عضو (باگ REA فیکس شد)
    ("member", "/api/v1/classes/book", "POST", True),
    ("member", "/api/v1/classes", "POST", False),  # ایجاد کلاس = staff
    ("reception", "/api/v1/population/intake/next", "POST", True),
    ("reception", "/api/v1/classes/book", "POST", False),  # رزرو برای عضو/کادر، نه پذیرش
    ("coach", "/api/v1/reports/confidential/3", "GET", True),
    ("coach", "/api/v1/axis-assessments/4/review", "POST", False),  # بازبینی = manager/admin
    ("manager", "/api/v1/reports/confidential/3", "GET", False),  # ردِ صریح (DENIES)
    ("manager", "/api/v1/axis-assessments/4/review", "POST", True),
    ("super_admin", "/api/v1/reports/confidential/3", "GET", True),
]


@pytest.mark.parametrize("role,path,method,expected", MATRIX)
def test_permission_matrix(role, path, method, expected):
    assert enforce(role, path, method) is expected, f"{role} {method} {path}"


def test_unknown_role_denied():
    assert enforce("hacker", "/api/v1/members", "GET") is False
    assert enforce("", "/api/v1/members", "GET") is False


def test_policies_not_empty_and_manager_wildcard():
    assert len(POLICIES) > 10
    assert get_enforcer().enforce("manager", "/api/v1/x", "PUT") is True
