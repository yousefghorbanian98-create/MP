"""گیت inventory دسترسیِ هر operation در `api/routes.json` (QF-00).

# چرا این فایل وجود دارد

`test_routes_artifact.py` فقط method/path/operationId/tags را تازه نگه می‌دارد.
یعنی می‌شود یک endpoint جدید با guard اشتباه اضافه شود و artifact همچنان
«تازه» بماند؛ یا policy کاسبن عوض شود و هیچ‌کس متوجه نشود.

این تست همان شکاف را برای **لایهٔ احراز/مجوز درخواست** می‌بندد: برای هر
operation، فهرست guardهای واقعیِ درخت وابستگی و فهرست نقش‌هایی که
`security.rbac.enforce` (همان تابعی که در runtime صدا زده می‌شود) اجازه
می‌دهد، باید در artifact ثبت و با کد مساوی باشد.

# این تست چه چیزی را ثابت نمی‌کند

- کنترل مالکیت سطری (member فقط دادهٔ خودش) در service است؛ این artifact
  فقط سطح route/policy را می‌داند.
- اجرای واقعی درخواست، error handling، رقابت یا رفتار runtime را نمی‌سنجد.
- مسیرهای عمومی با `guards: []` مشخص می‌شوند؛ «عمومی‌بودن مجاز» همچنان
  با گیت مستقل `scripts/route_guard_gate.py` (فهرست PUBLIC با دلیل) سنجیده
  می‌شود و این تست جای آن نیست.
"""

from __future__ import annotations

import json
from pathlib import Path


def _guards(dependant, out: list[str] | None = None) -> list[str]:
    out = out if out is not None else []
    kind = getattr(dependant.call, "__rbac__", None)
    if kind:
        out.append(kind)
    for dep in dependant.dependencies:
        _guards(dep, out)
    return sorted(out)


def _walk(routes, prefix: str = ""):
    from fastapi.routing import APIRoute

    for route in routes:
        if isinstance(route, APIRoute):
            yield prefix, route
            continue
        ctx = getattr(route, "include_context", None)
        sub = getattr(route, "original_router", None) or getattr(ctx, "included_router", None)
        if sub is not None:
            yield from _walk(sub.routes, prefix + (getattr(ctx, "prefix", "") or ""))


def _expected_access() -> dict[tuple[str, str], dict]:
    """نگاشت (method, path) → {guards, roles} از خود اپ و policy کاسبن."""
    import re

    from app.main import create_app
    from security.rbac import enforce

    roles = ["member", "coach", "reception", "manager", "admin", "super_admin"]
    access: dict[tuple[str, str], dict] = {}
    for prefix, route in _walk(create_app().routes):
        path = prefix + route.path
        guards = _guards(route.dependant)
        # کاسبن سطح-مسیر است؛ نمونهٔ پارامتر جایگزین می‌شود تا الگوهای
        # `keyMatch2` مثل `/payments/*/start` همان‌طور که در runtime تطبیق
        # می‌خورند سنجیده شوند.
        sample = re.sub(r"\{[^}]+\}", "1", path)
        for method in sorted(route.methods):
            access[(method, path)] = {
                "guards": guards,
                "roles": [] if not guards else [r for r in roles if enforce(r, sample, method)],
            }
    return access


def test_routes_artifact_records_access_matrix() -> None:
    artifact = Path(__file__).resolve().parents[2] / "api" / "routes.json"
    stored = json.loads(artifact.read_text(encoding="utf-8"))["operations"]
    expected = _expected_access()

    for op in stored:
        key = (op["method"], op["path"])
        assert "guards" in op and "roles" in op, (
            f"artifact برای {key} فیلد guards/roles ندارد — export_routes.py را اجرا کنید"
        )
        assert op["guards"] == expected[key]["guards"], (
            f"guardهای {key} در artifact کهنه‌اند: {op['guards']} ≠ {expected[key]['guards']}"
        )
        assert op["roles"] == expected[key]["roles"], (
            f"نقش‌های مجاز {key} در artifact کهنه‌اند: {op['roles']} ≠ {expected[key]['roles']}"
        )

    assert len(stored) == len(expected), "تعداد operationهای artifact با اپ برابر نیست"


def test_public_routes_have_no_role_claims() -> None:
    """مسیر بدون guard نباید فهرست نقش داشته باشد؛ وگرنه ادعای مجوز دروغ است."""
    artifact = Path(__file__).resolve().parents[2] / "api" / "routes.json"
    stored = json.loads(artifact.read_text(encoding="utf-8"))["operations"]
    for op in stored:
        if not op["guards"]:
            assert op["roles"] == [], (
                f"{op['method']} {op['path']} guard ندارد ولی نقش اعلام کرده است"
            )
        else:
            assert op["roles"], (
                f"{op['method']} {op['path']} guard دارد ولی هیچ نقشی مجاز نیست — "
                "یا policy جا افتاده یا guard اشتباه است"
            )
