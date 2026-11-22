"""WP 0.2 / F-12 — `api/routes.json` باید گاردهای **مؤثر** را اعلام کند.

چرا: فیلد `roles` قبلاً فقط casbin را منعکس می‌کرد. نتیجه: ۶۰۲ از ۱٬۱۴۱ سلول
ماتریس زنده (۱۶۳ عملیات × ۷ اصل) با اعلام قرارداد مخالف بود — مثلاً admin روی
`GET /admin/retention` اعلام‌شده مجاز بود ولی سرور ۴۰۳ می‌داد.

معنای فیلدها در artifact (تعریف کامل در `app/security/route_policy.py`):
- `roles`: نقش‌هایی که ممکن است از guardها عبور کنند (سقف).
- `always_roles`: نقش‌هایی که همیشه عبور می‌کنند (کف). `always ⊆ roles`.
- `anonymous`: `always` | `may` | `never` برای درخواست بدون توکن.
- `scopes`: قیدهای اعلامی که از برچسب guard درنمی‌آیند
  (`super_admin_only`, `owner_scope`, `body_credential`, `requires_bound_session`).

هر سلولی که «ممکن» است ولی «همیشه» نیست (grant برای admin/manager، مالکیت
سطری برای member) در گیت ماتریس زنده شرطی حساب می‌شود و دلیلش در `scopes`/`guards`
ثبت است؛ این تست ساختار و چند ادعای F-12 را قفل می‌کند.
"""

from __future__ import annotations

import json
from pathlib import Path

ROLES = ["member", "coach", "reception", "manager", "admin", "super_admin"]
ARTIFACT = Path(__file__).resolve().parents[2] / "api" / "routes.json"


def _ops() -> dict[tuple[str, str], dict]:
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))["operations"]
    return {(op["method"], op["path"]): op for op in data}


def test_every_operation_declares_always_may_and_anonymous() -> None:
    for key, op in _ops().items():
        for field in ("roles", "always_roles", "anonymous", "scopes"):
            assert field in op, (
                f"{key}: فیلد {field!r} در artifact نیست — export_routes.py را اجرا کنید"
            )
        assert set(op["always_roles"]) <= set(op["roles"]), f"{key}: always ⊄ roles"
        assert op["anonymous"] in ("always", "may", "never"), f"{key}: anonymous نامعتبر"


def test_f12_admin_is_not_declared_on_owner_only_routes() -> None:
    """F-12 ردیف ۱–۲: مالک‌سیستم‌بودن در بدنهٔ handler، نه در casbin."""
    ops = _ops()
    for key in [
        ("GET", "/api/v1/admin/retention"),
        ("POST", "/api/v1/admin/retention/run"),
        ("GET", "/api/v1/admin/users"),
        ("POST", "/api/v1/admin/users/{user_id}/role"),
        ("DELETE", "/api/v1/admin/users/{user_id}/role"),
    ]:
        op = ops[key]
        assert op["roles"] == ["super_admin"], f"{key}: roles={op['roles']} (باید فقط super_admin)"
        assert op["always_roles"] == ["super_admin"], f"{key}: always={op['always_roles']}"
        assert "super_admin_only" in op["scopes"], f"{key}: scope super_admin_only نیست"


def test_f12_grant_routes_keep_restricted_roles_conditional() -> None:
    """F-12 ردیف ۳ + QF-03: admin/manager فقط با ردیف مجوز فعال عبور می‌کنند."""
    op = _ops()[("POST", "/api/v1/expenses")]
    assert "manager" in op["roles"] and "manager" not in op["always_roles"]
    assert "admin" in op["roles"] and "admin" not in op["always_roles"]
    assert "super_admin" in op["always_roles"]
    assert "reception" not in op["roles"] or "reception" in op["always_roles"]


def test_f12_authenticated_routes_accept_every_role() -> None:
    """F-12 ردیف ۴: `authenticated` برای همهٔ نقش‌ها باز است، نه فقط casbin."""
    for key in [
        ("GET", "/api/v1/auth/sessions"),
        ("POST", "/api/v1/auth/logout-all"),
        ("POST", "/api/v1/auth/phone-change/request"),
    ]:
        op = _ops()[key]
        assert op["always_roles"] == ROLES, f"{key}: always={op['always_roles']}"
        assert op["roles"] == ROLES, f"{key}: roles={op['roles']}"


def test_f12_metrics_token_is_not_a_role_grant() -> None:
    """`/metrics` با توکن جدا است؛ هیچ نقش bearer به‌تنهایی عبور نمی‌کند."""
    op = _ops()[("GET", "/api/v1/metrics")]
    assert op["roles"] == [] and op["always_roles"] == []
    assert op["anonymous"] == "never"


def test_owner_scope_is_declared_for_member_row_routes() -> None:
    """member فقط دادهٔ خودش: `ensure_member_scope` در service ⇒ شرطی، نه همیشه."""
    op = _ops()[("GET", "/api/v1/members/{member_id}")]
    assert "owner_scope" in op["scopes"]
    assert "member" in op["roles"] and "member" not in op["always_roles"]


def test_public_routes_are_open_to_all_roles_and_anonymous() -> None:
    op = _ops()[("GET", "/health")]
    assert op["roles"] == ROLES and op["always_roles"] == ROLES
    assert op["anonymous"] == "always"


def test_body_credential_route_is_conditional_for_anonymous() -> None:
    """`/auth/refresh` بدون guard است ولی توکن را در بدنه می‌گیرد؛ 401 قابل‌انتظار است."""
    op = _ops()[("POST", "/api/v1/auth/refresh")]
    assert op["guards"] == []
    assert op["anonymous"] == "may"
    assert "body_credential" in op["scopes"]
