"""WP 3.2 / F‑26 — یک شکل پاکت خطا در کل API.

خطاهای HTTP که از خود Starlette می‌آیند (مسیر ناموجود ۴۰۴، متد نامجاز ۴۰۵) باید
همان `{"error": {code, message, details}}` پاکت پروژه را برگردانند، نه `{"detail": …}`.
"""

from __future__ import annotations


def _assert_envelope(body: dict, code: str) -> None:
    assert "detail" not in body, body
    assert set(body) == {"error"}, body
    err = body["error"]
    assert err["code"] == code
    assert isinstance(err["message"], str) and err["message"]
    assert err["details"] == []


def test_unknown_route_uses_project_envelope(client) -> None:
    resp = client.get("/api/v1/this-route-does-not-exist")
    assert resp.status_code == 404
    _assert_envelope(resp.json(), "not_found")


def test_method_not_allowed_uses_project_envelope(client) -> None:
    resp = client.post("/health")  # مسیر فقط GET دارد
    assert resp.status_code == 405
    _assert_envelope(resp.json(), "method_not_allowed")
