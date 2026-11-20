"""QF-06 — فیش خصوصی هزینه.

# قرارداد

| مورد | قاعده |
|---|---|
| آپلود | `finance.write`؛ فقط تصویر واقعی (محتوا، نه هدر)؛ یک فایل برای هر هزینه |
| خواندن | `finance.read`؛ بدون مجوز ۴۰۳؛ هرگز از مسیر عمومی سرو نمی‌شود |
| ذخیره | نام تصادفی، مجوز `0600`، بیرون از پوشهٔ استاتیک |
| حذف نرم | فایل پاک نمی‌شود (ممیزی) |

# آنچه تست نمی‌کند
- ذخیرهٔ ابری یا رمزنگاری در حالت استراحت (خارج از این برش).
"""

from __future__ import annotations

import io
import os
import stat
from datetime import date

from fastapi.testclient import TestClient
from PIL import Image

from db.base import get_session_factory
from tests.integration._actors import create_actor


def _png(size: tuple[int, int] = (8, 8)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, (0, 184, 106)).save(buf, format="PNG")
    return buf.getvalue()


def _expense(client: TestClient, headers: dict) -> int:
    res = client.post(
        "/api/v1/expenses",
        json={
            "amount_rial": 12_000_000,
            "category": "rent",
            "spent_on": date(2026, 3, 15).isoformat(),
            "payee": "مالک",
            "note": "فیش تست",
        },
        headers=headers,
    )
    assert res.status_code == 200, res.text
    return res.json()["id"]


def _upload(client: TestClient, headers: dict, expense_id: int, data: bytes, mime: str):
    return client.post(
        f"/api/v1/expenses/{expense_id}/receipt",
        files={"file": ("fish.png", data, mime)},
        headers=headers,
    )


def test_writer_uploads_real_png_and_reader_downloads_it(client: TestClient) -> None:
    writer = create_actor("manager", ["finance.write", "finance.read"])
    eid = _expense(client, writer)
    data = _png()

    up = _upload(client, writer, eid, data, "image/png")
    assert up.status_code == 201, up.text
    assert up.json()["mime"] == "image/png"
    assert up.json()["size_bytes"] == len(data)

    reader = create_actor("manager", ["finance.read"])
    got = client.get(f"/api/v1/expenses/{eid}/receipt", headers=reader)
    assert got.status_code == 200, got.text
    assert got.content == data
    assert got.headers["content-type"] == "image/png"
    assert "no-store" in got.headers.get("cache-control", "")


def test_stored_file_is_private_and_random_named(client: TestClient) -> None:
    writer = create_actor("manager", ["finance.write", "finance.read"])
    eid = _expense(client, writer)
    _upload(client, writer, eid, _png(), "image/png")
    from db.models import ExpenseReceipt

    with get_session_factory()() as s:
        row = s.query(ExpenseReceipt).filter(ExpenseReceipt.expense_id == eid).one()
        path = row.stored_path
    assert os.path.isfile(path)
    assert stat.S_IMODE(os.stat(path).st_mode) == 0o600
    assert "exp-" in os.path.basename(path)
    assert "/static" not in path


def test_second_receipt_for_same_expense_is_rejected(client: TestClient) -> None:
    writer = create_actor("manager", ["finance.write", "finance.read"])
    eid = _expense(client, writer)
    assert _upload(client, writer, eid, _png(), "image/png").status_code == 201
    again = _upload(client, writer, eid, _png(), "image/png")
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "receipt_exists"


def test_non_image_and_mismatched_type_are_rejected(client: TestClient) -> None:
    writer = create_actor("manager", ["finance.write", "finance.read"])
    eid = _expense(client, writer)
    fake = _upload(client, writer, eid, b"<html>not an image</html>", "image/png")
    assert fake.status_code == 422
    assert fake.json()["error"]["code"] == "invalid_receipt_image"

    mismatch = _upload(client, writer, eid, _png(), "image/jpeg")
    assert mismatch.status_code == 422
    assert mismatch.json()["error"]["code"] == "receipt_type_mismatch"

    pdf = _upload(client, writer, eid, b"%PDF-1.4", "application/pdf")
    assert pdf.status_code == 422
    assert pdf.json()["error"]["code"] == "unsupported_receipt_type"


def test_permissions_are_split_and_fail_closed(client: TestClient) -> None:
    writer = create_actor("manager", ["finance.write", "finance.read"])
    eid = _expense(client, writer)
    reader_only = create_actor("manager", ["finance.read"])
    writer_only = create_actor("manager", ["finance.write"])
    nobody = create_actor("manager")

    assert _upload(client, reader_only, eid, _png(), "image/png").status_code == 403
    assert _upload(client, nobody, eid, _png(), "image/png").status_code == 403
    assert client.get(f"/api/v1/expenses/{eid}/receipt", headers=writer_only).status_code == 403
    assert client.get(f"/api/v1/expenses/{eid}/receipt", headers=nobody).status_code == 403


def test_missing_expense_and_missing_receipt_are_404(client: TestClient) -> None:
    writer = create_actor("manager", ["finance.write", "finance.read"])
    assert _upload(client, writer, 999_999, _png(), "image/png").status_code == 404
    eid = _expense(client, writer)
    assert client.get(f"/api/v1/expenses/{eid}/receipt", headers=writer).status_code == 404


def test_soft_deleted_expense_keeps_file_and_refuses_new_upload(client: TestClient) -> None:
    writer = create_actor("manager", ["finance.write", "finance.read"])
    eid = _expense(client, writer)
    _upload(client, writer, eid, _png(), "image/png")
    from db.models import ExpenseReceipt

    with get_session_factory()() as s:
        path = s.query(ExpenseReceipt).filter(ExpenseReceipt.expense_id == eid).one().stored_path
    d = client.request(
        "DELETE",
        f"/api/v1/expenses/{eid}",
        json={"reason": "ورود تکراری"},
        headers=writer,
    )
    assert d.status_code == 200, d.text
    assert os.path.isfile(path), "حذف نرم نباید فایل ممیزی را پاک کند"
    # هزینهٔ حذف‌شده فیش تازه نمی‌پذیرد
    late = _upload(client, writer, eid, _png(), "image/png")
    assert late.status_code == 400
    assert late.json()["error"]["code"] == "expense_deleted"
