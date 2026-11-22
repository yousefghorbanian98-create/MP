"""B2 — WP 2.3 (F‑18)، WP 4.3 (F‑19)، WP 4.4 (F‑20)؛ معیارها در D‑14.

قرمز پیش از اصلاح:
- WP 2.3: پیش‌فرض WEB_CONCURRENCY در Dockerfile ۴ است (BD‑4 ⇒ ۱).
- WP 4.3: دو `await import("../lib/api")` در هندلرهای کلیک Shop.tsx.
- WP 4.4: export `updateProduct` هنوز در lib/api.ts است (BD‑2 ⇒ حذف).
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
STUDIO_SRC = ROOT / "mp-app/studio/src"
DOCKERFILES = (
    ROOT / "mp-app/backend/Dockerfile",
    ROOT / "mp-app/infra/Dockerfile.backend",
)


def test_web_concurrency_default_is_one_worker():
    """WP 2.3: SQLite تک‌فایل ⇒ پیش‌فرض یک ورکر (حساب ظرفیت در OPS-RUNBOOK)."""
    for path in DOCKERFILES:
        text = path.read_text(encoding="utf-8")
        match = re.search(r"WEB_CONCURRENCY:-(\d+)", text)
        assert match, f"no WEB_CONCURRENCY default in {path}"
        assert match.group(1) == "1", f"{path.name}: default {match.group(1)} != 1"


def test_no_dynamic_import_in_studio_handlers():
    """WP 4.3: grep ⇒ ۰ `await import(` در src/**."""
    hits = []
    for path in STUDIO_SRC.rglob("*.ts*"):
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if "await import(" in line:
                hits.append(f"{path.relative_to(ROOT)}:{lineno}")
    assert hits == [], f"dynamic imports remain: {hits}"


def test_shop_order_actions_are_statically_imported():
    """WP 4.3: fetchOrderReceipt و markOrderStatus از import ایستا می‌آیند."""
    text = (STUDIO_SRC / "pages/Shop.tsx").read_text(encoding="utf-8")
    header = text.split('} from "../lib/api";', 1)[0]
    assert "fetchOrderReceipt" in header
    assert "markOrderStatus" in header


def test_update_product_export_removed():
    """WP 4.4 (BD‑2): `updateProduct` کلاینت حذف شده است؛ کد زنده‌ای به آن ارجاع نمی‌دهد."""
    api = (STUDIO_SRC / "lib/api.ts").read_text(encoding="utf-8")
    assert "export const updateProduct" not in api
    for path in STUDIO_SRC.rglob("*.ts*"):
        assert "updateProduct" not in path.read_text(encoding="utf-8"), path
