"""برون‌بری فهرست مسیرهای API به `api/routes.json`.

چرا: گیت «هیچ مسیر دکوراتیو» در استودیو باید ثابت کند هر مسیر API
مصرف‌کننده دارد. اجرای پایتون از داخل Vitest ممکن نیست (جابِ studio در
CI پایتون ندارد)، پس فهرست به‌صورت artifact در ریپو نگه داشته می‌شود و
یک تست بک‌اند تازگی آن را تضمین می‌کند (`test_routes_artifact_fresh`).

اجرا: python scripts/export_routes.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

OUT = Path(__file__).resolve().parents[1] / "api" / "routes.json"


def collect() -> list[str]:
    from app.main import create_app

    return sorted(create_app().openapi()["paths"])


def main() -> int:
    paths = collect()
    OUT.write_text(
        json.dumps({"paths": paths}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    print(f"{len(paths)} مسیر در {OUT} نوشته شد")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
