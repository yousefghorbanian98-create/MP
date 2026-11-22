"""WP 3.5 / F‑09، F‑25 — گاردهای قراردادی سراسری (D‑16).

این تست‌ها روی HEAD سبزند: F‑09 و F‑25 در اندازه‌گیری فعلی بازتولید نشدند (ر.ک. D‑16).
هدف قفل‌کردنِ معیارهای کیت در CI است تا بازگشت احتمالی رگرسیون قرمز شود.
هیچ آستانه‌ای کاهش و هیچ تستی حذف یا skip نمی‌شود.
"""

from __future__ import annotations

import importlib
import pkgutil
import re
from typing import Annotated, get_args, get_origin

import pytest
from pydantic import BaseModel, TypeAdapter, ValidationError

import modules
from app.money import MAX_SAFE_RIAL, Rial

BAD_IDS = ["-1", "0", "-0", "-9223372036854775808"]
PATH_PARAM = re.compile(r"{(\w+)}")


# ---------- C1 (F‑25): هیچ مسیر با شناسهٔ بد 2xx نمی‌دهد ----------


def _numeric_param_routes(spec: dict):
    for path, ops in spec["paths"].items():
        if not PATH_PARAM.search(path):
            continue
        for method in ops:
            if method in ("get", "post", "put", "patch", "delete"):
                yield path, method.upper()


def test_no_2xx_for_out_of_range_path_ids(client, auth):
    spec = client.get("/openapi.json").json()
    headers = auth("super_admin", grants=["finance.read", "finance.write"])
    offenders = []
    checked = 0
    for path, method in _numeric_param_routes(spec):
        for bad in BAD_IDS:
            concrete = path
            for name in PATH_PARAM.findall(path):
                concrete = concrete.replace("{" + name + "}", bad)
            body = {} if method in ("POST", "PUT", "PATCH") else None
            resp = client.request(method, concrete, headers=headers, json=body)
            checked += 1
            if 200 <= resp.status_code < 300:
                offenders.append((method, path, bad, resp.status_code))
    assert checked > 0, "هیچ مسیر پارامتری پیدا نشد؛ ماتریس خالی است"
    assert offenders == [], f"پاسخ 2xx برای شناسهٔ بد: {offenders}"


# ---------- C2 (F‑09): مرزهای پولی ----------

ADAPTER = TypeAdapter(Annotated[Rial, None])


@pytest.mark.parametrize("value", [2**53, 2**53 + 1, 10**18])
def test_rial_rejects_values_above_safe_integer(value):
    with pytest.raises(ValidationError):
        ADAPTER.validate_python(value)


@pytest.mark.parametrize("value", ["1500000", 1500000.0, True])
def test_rial_rejects_coercible_non_int(value):
    with pytest.raises(ValidationError):
        ADAPTER.validate_python(value)


def test_rial_accepts_normal_amount_and_bound():
    assert ADAPTER.validate_python(1500000) == 1500000
    assert ADAPTER.validate_python(MAX_SAFE_RIAL) == MAX_SAFE_RIAL


def _collect_constraints(annotation, out: list) -> None:
    """قیدهای Annotated را حتی داخل Optional/Union جمع می‌کند."""
    if get_origin(annotation) is Annotated:
        for meta in annotation.__metadata__:
            out.append(meta)
            # Field(...) داخل Annotated یک FieldInfo است که قیدها را در metadata خودش دارد.
            out.extend(getattr(meta, "metadata", []) or [])
    for arg in get_args(annotation):
        _collect_constraints(arg, out)


def _is_rial(field) -> bool:
    """Pydantic قیدهای Rial را گاهی در annotation (Optional) و گاهی در metadata می‌گذارد."""
    constraints = list(field.metadata)
    _collect_constraints(field.annotation, constraints)
    strict = any(getattr(m, "strict", False) is True for m in constraints)
    upper = [getattr(m, "le", None) for m in constraints if hasattr(m, "le")]
    return strict and MAX_SAFE_RIAL in upper


def test_every_input_money_field_uses_rial():
    checked = []
    for info in pkgutil.walk_packages(modules.__path__, modules.__name__ + "."):
        if not info.name.endswith(".schemas"):
            continue
        mod = importlib.import_module(info.name)
        for name, cls in vars(mod).items():
            if not (
                isinstance(cls, type)
                and issubclass(cls, BaseModel)
                and cls.__module__ == mod.__name__
            ):
                continue
            if name.endswith("Out"):
                continue
            for field_name in ("amount_rial", "price_rial"):
                field = cls.model_fields.get(field_name)
                if field is None:
                    continue
                checked.append(f"{info.name}.{name}.{field_name}")
                assert _is_rial(field), (
                    f"{info.name}.{name}.{field_name} قید Rial (strict + le) ندارد"
                )
    assert checked, "هیچ فیلد پولیِ ورودی پیدا نشد؛ گارد خالی است"
