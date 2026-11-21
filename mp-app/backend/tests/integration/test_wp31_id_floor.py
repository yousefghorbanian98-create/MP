"""WP 3.1 / F‑25 — کف شناسه: `-1`، `0`، `-0` و INT64_MIN باید در **هر** مسیر پارامتری‌شناسه ۴xx با `invalid_id` بدهند.

ریشه: `id_guard._too_big` فقط سقف را می‌سنجد و با `isdigit()` مقادیر منفی را نمی‌بیند.
طرح: dependency سراسری `check_path_id_floor` که پس از مسیریابی، فقط پارامترهای `*_id` را می‌سنجد
(در مشخصهٔ OpenAPI همهٔ `*_id` از نوع integer هستند؛ پارامترهای رشته‌ای مثل `key` دست‌نخورده می‌مانند).

مسیرها از خود اپ (`app.openapi()`) خوانده می‌شوند — FastAPI 0.141 مسیرها را در `_IncludedRouter` نگه می‌دارد.
"""

from __future__ import annotations

import re

import pytest

BAD_VALUES = ["-1", "0", "-0", "-9223372036854775808"]
METHODS = ("get", "post", "put", "patch", "delete")
PARAM = re.compile(r"\{(\w+)\}")


def _operations():
    """(method, path_template, param_names) برای هر عملیات برنامه."""
    from app.main import create_app

    spec = create_app().openapi()
    out = []
    for path, item in spec["paths"].items():
        params = PARAM.findall(path)
        for m in METHODS:
            if m in item:
                out.append((m.upper(), path, params))
    return out


def _fill(path: str, params: list[str], id_value: str) -> str:
    url = path
    for p in params:
        url = url.replace("{" + p + "}", id_value if p.endswith("_id") else "x")
    return url


def test_every_id_operation_rejects_non_positive_ids(client) -> None:
    ops = [(m, p, ps) for m, p, ps in _operations() if any(x.endswith("_id") for x in ps)]
    assert ops, "هیچ عملیات پارامتری‌شناسه پیدا نشد (بررسی ناسالم)"
    failures = []
    for method, path, params in ops:
        for bad in BAD_VALUES:
            r = client.request(method, _fill(path, params, bad))
            body = r.json() if "json" in r.headers.get("content-type", "") else {}
            code = (body.get("error") or {}).get("code")
            if not (400 <= r.status_code < 500 and code == "invalid_id"):
                failures.append((method, path, bad, r.status_code, code))
    assert not failures, (
        f"{len(failures)} سلول ناموفق از {len(ops) * len(BAD_VALUES)}؛ نمونه: {failures[:5]}"
    )


@pytest.mark.parametrize("value", ["1", "42", "9007199254740991"])
def test_valid_ids_are_not_rejected_by_floor(client, value) -> None:
    r = client.get(f"/api/v1/members/{value}")
    code = (
        (r.json() or {}).get("error", {}).get("code")
        if "json" in r.headers.get("content-type", "")
        else None
    )
    assert code != "invalid_id"


def test_string_params_are_not_touched(client) -> None:
    ops = [(m, p, ps) for m, p, ps in _operations() if any(x in ("key", "job_key") for x in ps)]
    assert ops, "مسیر رشته‌ای برای آزمون پیدا نشد"
    method, path, params = ops[0]
    url = path
    for p in params:
        url = url.replace("{" + p + "}", "-1" if p in ("key", "job_key") else "x")
    r = client.request(method, url)
    code = (
        (r.json() or {}).get("error", {}).get("code")
        if "json" in r.headers.get("content-type", "")
        else None
    )
    assert code != "invalid_id"
