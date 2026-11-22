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
- `roles`: سقف نقش‌هایی که می‌توانند از guardها عبور کنند. برای `permission`
  از `security.rbac.enforce` (همان تابع runtime) می‌آید؛ برای `authenticated`
  همهٔ نقش‌ها؛ برای مسیر عمومی همهٔ نقش‌ها؛ برای `metrics_token` هیچ‌کدام.
- `always_roles`: کف — نقش‌هایی که همیشه عبور می‌کنند. `grant:*` نقش‌های
  محدودشده (admin/manager) را شرطی می‌کند و `owner_scope` همه را شرطی می‌کند.
- `anonymous`: `always` | `may` | `never` برای درخواست بدون توکن.
- `scopes`: قیدهای اعلامی از `app/security/route_policy.py`
  (`super_admin_only`, `owner_scope`, `body_credential`, `requires_bound_session`).

محدودیت صریح: این artifact اعلامیهٔ OpenAPI + سیاست سطح-route است. کنترل
مالکیت سطری (member فقط دادهٔ خودش) داخل service انجام می‌شود و این فایل
آن را اثبات نمی‌کند؛ رفتار runtime، errorها و رقابت هم همین‌طور.

اجرا: python scripts/export_routes.py
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

os.environ.setdefault("MP_ENVIRONMENT", "development")  # WP 1.2: ابزار فقط‌خواندنی مسیر/OpenAPI

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


def effective_access(guards: list[str], scopes: dict[str, str], method: str, sample: str) -> dict:
    """سیاست مؤثر یک operation — ترکیب برچسب guardها و قیدهای اعلامی `route_policy`.

    - `roles`: سقف (ممکن است عبور کند). `always_roles`: کف (همیشه عبور می‌کند).
    - `anonymous`: `always` | `may` | `never`.
    - guard ناشناخته ⇒ خطا (fail-closed)؛ هیچ نقشی به‌صورت پیش‌فرض اضافه نمی‌شود.
    """
    from app.security.grants import OWNER_ROLE, RESTRICTED_ROLES
    from security.rbac import enforce

    kinds = set(guards)
    grant_kinds = {g for g in kinds if g.startswith("grant:")}
    unknown = kinds - {"permission", "authenticated", "metrics_token"} - grant_kinds
    if unknown:
        raise ValueError(f"guard ناشناخته در {method} {sample}: {sorted(unknown)}")

    if "super_admin_only" in scopes:
        roles = [OWNER_ROLE]
        always = [OWNER_ROLE]
        anonymous = "never"
    elif not guards:
        roles = list(ROLES)
        if "body_credential" in scopes:
            always, anonymous = [], "may"
        else:
            always, anonymous = list(ROLES), "always"
    elif "metrics_token" in kinds:
        if kinds != {"metrics_token"}:
            raise ValueError(f"ترکیب نامعتبر metrics_token در {method} {sample}")
        roles, always, anonymous = [], [], "never"
    else:
        if "permission" in kinds:
            roles = [r for r in ROLES if enforce(r, sample, method)]
        else:
            # authenticated یا grant بدون casbin: همهٔ نقش‌ها سقف‌اند.
            roles = list(ROLES)
        # grant:* — نقش‌های محدودشده فقط با ردیف فعال؛ مالک همیشه.
        if grant_kinds:
            always = [r for r in roles if r == OWNER_ROLE or r not in RESTRICTED_ROLES]
        else:
            always = list(roles)
        # مالکیت سطری: نتیجه به داده بستگی دارد ⇒ هیچ نقشی «همیشه» نیست.
        if "owner_scope" in scopes:
            always = []
        anonymous = "never"
    return {"roles": roles, "always_roles": always, "anonymous": anonymous}


def access_matrix(app) -> dict[tuple[str, str], dict]:
    from app.security.route_policy import declared_scopes

    access: dict[tuple[str, str], dict] = {}
    for prefix, route in walk_routes(app.routes):
        path = prefix + route.path
        guards = guard_kinds(route.dependant)
        sample = re.sub(r"\{[^}]+\}", "1", path)
        for method in sorted(route.methods):
            scopes = declared_scopes(method, path)
            access[(method, path)] = {
                "guards": guards,
                "scopes": sorted(scopes),
                **effective_access(guards, scopes, method, sample),
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
