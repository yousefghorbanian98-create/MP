"""برون‌بری pathها و operationهای OpenAPI به `api/routes.json`.

چرا: گیت «هیچ مسیر دکوراتیو» در استودیو مصرف مسیرها را می‌سنجد؛ method،
operationId و tagها نیز برای inventory/trace لازم‌اند. اجرای پایتون از Vitest
ممکن نیست (جابِ studio در CI پایتون ندارد)، پس artifact در repo نگه‌داری و
تازگی path و operation آن با `test_routes_artifact_is_fresh` تضمین می‌شود.
این artifact اعلامیهٔ OpenAPI است، نه مدرک runtime یا authorization.

اجرا: python scripts/export_routes.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

OUT = Path(__file__).resolve().parents[1] / "api" / "routes.json"


HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


def collect() -> dict[str, list]:
    """Export path and operation declarations, not runtime/authorization claims."""
    from app.main import create_app

    paths = create_app().openapi()["paths"]
    operations = [
        {
            "method": method.upper(),
            "path": path,
            "operationId": operation.get("operationId"),
            "tags": operation.get("tags", []),
        }
        for path in sorted(paths)
        for method, operation in sorted(paths[path].items())
        if method.lower() in HTTP_METHODS
    ]
    return {"paths": sorted(paths), "operations": operations}


def main() -> int:
    inventory = collect()
    OUT.write_text(json.dumps(inventory, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(
        f"{len(inventory['paths'])} مسیر و {len(inventory['operations'])} عملیات در {OUT} نوشته شد"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
