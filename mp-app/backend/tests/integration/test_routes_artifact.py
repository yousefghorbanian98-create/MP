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
    stored = json.loads(artifact.read_text(encoding="utf-8"))["paths"]
    actual = sorted(create_app().openapi()["paths"])
    added = sorted(set(actual) - set(stored))
    removed = sorted(set(stored) - set(actual))
    assert not added, f"مسیرهای جدید در artifact نیستند: {added} — export_routes.py را اجرا کنید"
    assert not removed, f"مسیرهای حذف‌شده در artifact مانده‌اند: {removed}"
    assert stored == actual
