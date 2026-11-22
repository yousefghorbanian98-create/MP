"""WP 3.3 / F-14 — gateway-return برای پرداخت ناموجود باید 404 بدهد، نه 200.

یافتهٔ محلی (HEAD قبل از اصلاح): شناسه‌های نامعتبر (-1، 0، -0، INT64_MIN) از قبل با
422 `invalid_id` رد می‌شوند (id_guard) و **بازتولید نشدند**؛ خطای واقعی شناسهٔ معتبرِ
ناموجود است (999999999) که HTML «یافت نشد» را با HTTP 200 برمی‌گرداند.
محدوده (D‑15): فقط «یافت نشد» ⇒ 404. سایر شکست‌های callback (امضا، authority) بدون تغییر 200.
"""

from __future__ import annotations

import pytest

from app.errors import ApiError


def _get(client, pid):
    return client.get(
        f"/api/v1/payments/{pid}/gateway-return", params={"Authority": "x", "token": "y"}
    )


def test_missing_valid_payment_id_returns_404(client):
    resp = _get(client, "999999999")
    assert resp.status_code == 404, resp.status_code
    assert "text/html" in resp.headers.get("content-type", "")


@pytest.mark.parametrize("pid", ["-1", "0", "-0", "-9223372036854775808"])
def test_out_of_range_ids_are_rejected_not_200(client, pid):
    # guard، نه رفع: این مقادیر در HEAD هم 422 بودند؛ قرارداد جلوی بازگشت 200 را می‌گیرد.
    resp = _get(client, pid)
    assert resp.status_code == 422, (pid, resp.status_code)


def test_other_callback_failures_keep_200(client, monkeypatch):
    from modules.payments import service

    def _bad_sig(*_a, **_k):
        raise ApiError("امضای callback نامعتبر است", code="bad_signature")

    monkeypatch.setattr(service, "verify_with_gateway", _bad_sig)
    resp = _get(client, "1")
    assert resp.status_code == 200
