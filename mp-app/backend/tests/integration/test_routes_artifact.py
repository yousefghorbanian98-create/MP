"""تازگی artifact مسیرهای API (پشتوانهٔ گیت «هیچ مسیر دکوراتیو»).

گیت فرانت `tests/apiCoverage.test.ts` فهرست مسیرها را از
`api/routes.json` می‌خواند (جابِ studio در CI پایتون ندارد). اگر آن فایل
کهنه بماند، گیت می‌تواند مسیر جدیدی را نبیند و سبز بماند — یعنی دروغ.
این تست همان درِ پشتی را می‌بندد.
"""

from __future__ import annotations

import json
from pathlib import Path


def test_routes_artifact_is_fresh() -> None:
    from app.main import create_app

    artifact = Path(__file__).resolve().parents[2] / "api" / "routes.json"
    assert artifact.is_file(), "api/routes.json نیست — scripts/export_routes.py را اجرا کنید"
    stored_artifact = json.loads(artifact.read_text(encoding="utf-8"))
    spec = create_app().openapi()

    stored_paths = stored_artifact["paths"]
    actual_paths = sorted(spec["paths"])
    added = sorted(set(actual_paths) - set(stored_paths))
    removed = sorted(set(stored_paths) - set(actual_paths))
    assert not added, f"مسیرهای جدید در artifact نیستند: {added} — export_routes.py را اجرا کنید"
    assert not removed, f"مسیرهای حذف‌شده در artifact مانده‌اند: {removed}"
    assert stored_paths == actual_paths

    expected_operations = [
        {
            "method": method.upper(),
            "path": path,
            "operationId": operation.get("operationId"),
            "tags": operation.get("tags", []),
        }
        for path in sorted(spec["paths"])
        for method, operation in sorted(spec["paths"][path].items())
        if method.lower() in {"get", "post", "put", "patch", "delete"}
    ]
    stored_operations = stored_artifact.get("operations")
    assert isinstance(stored_operations, list), (
        "api/routes.json باید عملیات method/path را هم نگه دارد — export_routes.py را اجرا کنید"
    )
    assert stored_operations == expected_operations, (
        "عملیات API در api/routes.json کهنه یا به‌ترتیب ناپایدارند — export_routes.py را اجرا کنید"
    )
    operation_keys = [(item["method"], item["path"]) for item in stored_operations]
    assert len(operation_keys) == len(set(operation_keys)), "عملیات تکراری در api/routes.json"
