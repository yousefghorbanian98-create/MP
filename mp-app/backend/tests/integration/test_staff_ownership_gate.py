"""STAFF-01(ب) — گیتِ *اجراییِ* نقش/مالکیت روی همان ماتریس SEC-01.

# چرا این فایل وجود دارد

ماتریس SEC-01 (`evidence/2026-11-27/SEC-01/rbac-matrix.txt`, ۹۷۸ ردیف) و
artifact `api/routes.json` (۱۶۳ operation) **یک** ماتریس‌اند: هر ردیف جدول از
همان `access_matrix(app)` می‌آید که `test_routes_access_matrix.py` و
`test_routes_artifact.py` تازگی‌اش را نسبت به کد تضمین می‌کنند. پس ماتریس
SEC-01 «جدولِ ایستا» نیست و **قابل تبدیل** است؛ ماتریس دومی ساخته نمی‌شود.

اما آن تست‌ها فقط *اعلام* سیاست را می‌سنجند: می‌گویند `enforce("member",
…, "GET")` چه جوابی می‌دهد، نه این‌که درخواست واقعی چه کدی برمی‌گرداند.
یعنی می‌شد قاعده‌ای در policy باز شود و هیچ درخواستی آزموده نشود. این فایل
همان شکاف را می‌بندد:

1. **انتخابِ ثابت از artifact** — فهرست مسیرهای staff از `api/routes.json`
   می‌آید، نه از policy زنده؛ پس باز‌کردنِ یک مسیر staff به روی member
   فهرست را «کوچک» نمی‌کند، بلکه موجی از ۴۰۳های شکست‌خورده می‌سازد.
2. **۴۰۳ واقعی برای نقش غیرمجاز** — برای هر مسیر staff (GET، نه member،
   نه عمومی) با توکن `member` یک درخواست HTTP واقعی می‌شود و کد باید ۴۰۳
   باشد؛ ۲۰۰/۲۰۴ یعنی نشت.
3. **هم‌خوانی انتخاب با اپ زنده** — مجموعهٔ مسیرهای staff در اپ زنده باید با
   artifact یکی باشد؛ یک staff route تازه در router بدون قاعدهٔ نقش این‌جا
   (و در `test_routes_access_matrix.py`) قرمز می‌شود.

# این فایل چه چیزی را اثبات نمی‌کند

- کنترل مالکیت *سطری/داده‌ای* (member فقط ردیف خودش) داخل service است؛ این
  گیت سطح route/policy را می‌سنجد.
- مسیرهای عمومی: مجازبودنشان با `scripts/route_guard_gate.py` (فهرست
  PUBLIC با دلیل) سنجیده می‌شود، نه این‌جا.
"""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import pytest

_BACKEND = Path(__file__).resolve().parents[2]
_ARTIFACT = _BACKEND / "api" / "routes.json"
_SCRIPT = _BACKEND / "scripts" / "export_routes.py"

# اعتبارنامهٔ ماشین (بدون نقش انسانی) — هر ورودی دلیل دارد و فهرست بسته است.
MACHINE_TOKEN_ONLY: dict[str, str] = {
    "GET /api/v1/metrics": "metrics_token؛ نقش انسانی ندارد — پوشش: test_wp13_metrics_auth.py",
}


def _live_matrix() -> dict[tuple[str, str], dict]:
    spec = importlib.util.spec_from_file_location("export_routes", _SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    from app.main import create_app

    return module.access_matrix(create_app())


def _is_staff(access: dict) -> bool:
    return (
        access["anonymous"] == "never" and bool(access["roles"]) and "member" not in access["roles"]
    )


def _artifact_operations() -> list[dict]:
    return json.loads(_ARTIFACT.read_text(encoding="utf-8"))["operations"]


def _artifact_staff_gets() -> list[str]:
    """فهرست ثابت (snapshot) مسیرهای staff-only GET — از artifact، نه policy."""
    return sorted(
        op["path"] for op in _artifact_operations() if op["method"] == "GET" and _is_staff(op)
    )


_STAFF_GETS = _artifact_staff_gets()


def test_selection_is_not_empty():
    """گیت نباید بی‌صدا خالی شود؛ خالی‌بودن یعنی تست هیچ‌چیز را نمی‌سنجد."""
    assert len(_STAFF_GETS) >= 20, (
        f"فقط {len(_STAFF_GETS)} مسیر staff در artifact — الگو را بررسی کنید"
    )


def test_live_selection_matches_artifact(matrix_cache):
    """مجموعهٔ staff در اپ زنده == artifact (route تازهٔ بدون قاعدهٔ نقش ⇒ قرمز)."""
    live = sorted(
        path
        for (method, path), access in matrix_cache.items()
        if method == "GET" and _is_staff(access)
    )
    assert live == _STAFF_GETS, (
        "مسیرهای staff بین اپ زنده و artifact نمی‌خوانند: "
        f"اضافه(زنده)={sorted(set(live) - set(_STAFF_GETS))} "
        f"کم(زنده)={sorted(set(_STAFF_GETS) - set(live))}"
    )


def test_every_token_only_operation_has_a_role(matrix_cache):
    """مسیر تازهٔ staff بدون قاعدهٔ نقش ⇒ قرمز (همان الگوی staffRouteMap)."""
    missing = sorted(
        f"{method} {path}"
        for (method, path), access in matrix_cache.items()
        if access["anonymous"] == "never"
        and not access["roles"]
        and f"{method} {path}" not in MACHINE_TOKEN_ONLY
    )
    assert not missing, (
        "این operationها توکن لازم دارند ولی هیچ نقشی از policy عبور نمی‌کند "
        f"(قاعدهٔ نقش در security/rbac.py نیست): {missing}"
    )


def test_machine_token_exemptions_are_exactly_the_documented_set(matrix_cache):
    """استثنای «بدون نقش» کور نیست: هرگز بیش از فهرست مستند بالا نیست."""
    roleless = {
        f"{method} {path}"
        for (method, path), access in matrix_cache.items()
        if access["anonymous"] == "never" and not access["roles"]
    }
    assert roleless == set(MACHINE_TOKEN_ONLY), (
        "بی‌نقش‌ها با فهرست مستند نمی‌خوانند: "
        f"اضافه={sorted(roleless - set(MACHINE_TOKEN_ONLY))} "
        f"کم={sorted(set(MACHINE_TOKEN_ONLY) - roleless)}"
    )


@pytest.fixture(scope="module")
def matrix_cache() -> dict[tuple[str, str], dict]:
    return _live_matrix()


@pytest.mark.parametrize(
    "path", _STAFF_GETS, ids=lambda value: re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-")
)
def test_member_gets_403_on_staff_route(client, auth, path):
    """نقش غیرمجاز روی مسیر staff باید ۴۰۳ بگیرد — نه ۲۰۰، نه ۵۰۰."""
    url = re.sub(r"\{[^}]+\}", "1", path)
    response = client.get(url, headers=auth("member"))
    assert response.status_code == 403, (
        f"GET {path} با نقش member باید ۴۰۳ بدهد، داد {response.status_code}: {response.text[:200]}"
    )
