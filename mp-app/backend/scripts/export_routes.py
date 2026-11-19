"""برون‌بری pathها، operationها و ماتریس دسترسیِ سطح-route به `api/routes.json`.

چرا: گیت «هیچ مسیر دکوراتیو» در استودیو مصرف مسیرها را می‌سنجد؛ method،
operationId و tagها نیز برای inventory/trace لازم‌اند. اجرای پایتون از Vitest
ممکن نیست (جابِ studio در CI پایتون ندارد)، پس artifact در repo نگه‌داری و
تازگی path، operation و ماتریس دسترسی آن با
`tests/integration/test_routes_artifact.py` و
`tests/integration/test_routes_access_matrix.py` تضمین می‌شود.

هر operation دو فیلد تازه هم دارد:

- `guards`: برچسب‌های `__rbac__` روی درخت وابستگی همان route
  (`permission` / `roles` / `authenticated`). فهرست خالی = مسیر عمومی.
- `roles`: نقش‌هایی که `security.rbac.enforce` — همان تابع runtime — برای
  همان method/الگوی مسیر اجازه می‌دهد (پارامترهای مسیر با نمونهٔ `1`
  جایگزین می‌شوند؛ کاسبن سطح-مسیر است، پس نتیجه به مقدار شناسه وابسته نیست).

محدودیت صریح: این artifact اعلامیهٔ OpenAPI + سیاست سطح-route است. کنترل
مالکیت سطری (member فقط دادهٔ خودش) داخل service انجام می‌شود و این فایل
آن را اثبات نمی‌کند؛ رفتار runtime، errorها و رقابت هم همین‌طور.

اجرا: python scripts/export_routes.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

OUT = Path(__file__).resolve().parents[1] / "api" / "routes.json"


HTTP_METHODS = {"get", "post", "put", "patch", "delete"}

# ترتیب ثابت تا artifact پایدار (deterministic) بماند.
ROLES = ("member", "coach", "reception", "manager", "admin", "super_admin")


def walk_routes(routes, prefix: str = ""):
    """پیمایش بازگشتی روترهای include‌شده (FastAPI 0.163 routeها را flatten نمی‌کند)."""
    from fastapi.routing import APIRoute

    for route in routes:
        if isinstance(route, APIRoute):
            yield prefix, route
            continue
        ctx = getattr(route, "include_context", None)
        sub = getattr(route, "original_router", None) or getattr(ctx, "included_router", None)
        if sub is not None:
            yield from walk_routes(sub.routes, prefix + (getattr(ctx, "prefix", "") or ""))


def guard_kinds(dependant, out: list[str] | None = None) -> list[str]:
    """برچسب‌های guard روی درخت وابستگی — بدون تکیه بر نام تابع (functools.wraps)."""
    out = out if out is not None else []
    kind = getattr(dependant.call, "__rbac__", None)
    if kind:
        out.append(kind)
    for dep in dependant.dependencies:
        guard_kinds(dep, out)
    return sorted(out)


def access_matrix(app) -> dict[tuple[str, str], dict]:
    from security.rbac import enforce

    access: dict[tuple[str, str], dict] = {}
    for prefix, route in walk_routes(app.routes):
        path = prefix + route.path
        guards = guard_kinds(route.dependant)
        sample = re.sub(r"\{[^}]+\}", "1", path)
        for method in sorted(route.methods):
            access[(method, path)] = {
                "guards": guards,
                "roles": [] if not guards else [r for r in ROLES if enforce(r, sample, method)],
            }
    return access


def collect() -> dict[str, list]:
    """Export path/operation/access declarations, not runtime/ownership claims."""
    from app.main import create_app

    app = create_app()
    paths = app.openapi()["paths"]
    access = access_matrix(app)
    operations = [
        {
            "method": method.upper(),
            "path": path,
            "operationId": operation.get("operationId"),
            "tags": operation.get("tags", []),
            **access[(method.upper(), path)],
        }
        for path in sorted(paths)
        for method, operation in sorted(paths[path].items())
        if method.lower() in HTTP_METHODS
    ]
    return {"paths": sorted(paths), "operations": operations}


def main() -> int:
    inventory = collect()
    OUT.write_text(json.dumps(inventory, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    operations = inventory["operations"]
    public = sum(1 for op in operations if not op["guards"])
    print(
        f"{len(inventory['paths'])} مسیر و {len(operations)} عملیات در {OUT} نوشته شد "
        f"({public} عملیات عمومیِ بدون guard، {len(operations) - public} عملیات با guard)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
