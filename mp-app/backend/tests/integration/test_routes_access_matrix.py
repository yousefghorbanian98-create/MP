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
    """نگاشت (method, path) → سیاست مؤثر، با همان تابع مولد artifact (WP 0.2).

    تابع مولد در `scripts/export_routes.py` است؛ این تست تازگی artifact را نسبت به
    مولد می‌سنجد. ادعای «مشاهده‌شده == اعلام‌شده» را گیت زندهٔ ماتریس
    (`probe_contract.py matrix` + ارزیاب WP 0.2) می‌سنجد، نه این تست.
    """
    import importlib.util
    import re

    from app.main import create_app
    from app.security.route_policy import declared_scopes

    spec = importlib.util.spec_from_file_location(
        "export_routes", Path(__file__).resolve().parents[2] / "scripts" / "export_routes.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    access: dict[tuple[str, str], dict] = {}
    for prefix, route in _walk(create_app().routes):
        path = prefix + route.path
        guards = _guards(route.dependant)
        sample = re.sub(r"\{[^}]+\}", "1", path)
        for method in sorted(route.methods):
            scopes = declared_scopes(method, path)
            access[(method, path)] = {
                "guards": guards,
                "scopes": sorted(scopes),
                **mod.effective_access(guards, scopes, method, sample),
            }
    return access


def test_routes_artifact_records_access_matrix() -> None:
    artifact = Path(__file__).resolve().parents[2] / "api" / "routes.json"
    stored = json.loads(artifact.read_text(encoding="utf-8"))["operations"]
    expected = _expected_access()

    for op in stored:
        key = (op["method"], op["path"])
        for field in ("guards", "scopes", "roles", "always_roles", "anonymous"):
            assert field in op, (
                f"artifact برای {key} فیلد {field} ندارد — export_routes.py را اجرا کنید"
            )
        for field in ("guards", "scopes", "roles", "always_roles", "anonymous"):
            assert op[field] == expected[key][field], (
                f"{field} برای {key} در artifact کهنه است: {op[field]} ≠ {expected[key][field]}"
            )

    assert len(stored) == len(expected), "تعداد operationهای artifact با اپ برابر نیست"


def test_public_routes_are_open_to_every_role() -> None:
    """مسیر بدون guard برای همهٔ نقش‌ها و anonymous باز است (مگر توکن در بدنه باشد)."""
    artifact = Path(__file__).resolve().parents[2] / "api" / "routes.json"
    stored = json.loads(artifact.read_text(encoding="utf-8"))["operations"]
    roles = ["member", "coach", "reception", "manager", "admin", "super_admin"]
    for op in stored:
        if not op["guards"]:
            assert op["roles"] == roles, f"{op['method']} {op['path']}: عمومی ولی roles ناقص"
            if "body_credential" in op["scopes"]:
                assert op["always_roles"] == [] and op["anonymous"] == "may"
            else:
                assert op["always_roles"] == roles and op["anonymous"] == "always"
        else:
            assert set(op["always_roles"]) <= set(op["roles"]), (
                f"{op['method']} {op['path']}: always ⊄ roles"
            )
            if "metrics_token" not in op["guards"]:
                assert op["roles"], (
                    f"{op['method']} {op['path']} guard دارد ولی هیچ نقشی مجاز نیست — "
                    "یا policy جا افتاده یا guard اشتباه است"
                )
