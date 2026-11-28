"""STAFF-02 (PWA-41) — جست‌وجوی اعضا سمت سرور و منفیِ دسترسی مستقیم.

# چرا این فایل وجود دارد

جدول اعضای Studio پیش‌تر `GET /api/v1/admin/members-summary` را می‌گرفت و
جست‌وجوی نام/تلفن را **در مرورگر** روی همان ردیف‌های برگشته انجام می‌داد.
با بیشتر از `limit` عضو، عضوی که بیرون از صفحه بود هرگز پیدا نمی‌شد و
برچسب «N عضو» هم عدد صفحه را نشان می‌داد، نه نتیجهٔ واقعی جست‌وجو. این
تست قرارداد سمت سرور را قفل می‌کند: `q` روی نام/تلفن در SQL اعمال می‌شود،
`%`/`_` ورودی کاربر wildcard نمی‌شوند (escape)، و نقش غیرمجاز ۴۰۳ می‌گیرد.
"""

from __future__ import annotations

import itertools

import pytest

_phones = itertools.count(31_000)


def _member(client, staff_headers: dict, full_name: str) -> dict:
    n = next(_phones)
    response = client.post(
        "/api/v1/members",
        json={"phone": f"0912{n:07d}", "full_name": full_name, "gender": "male"},
        headers=staff_headers,
    )
    assert response.status_code == 200, response.text
    return response.json()


@pytest.fixture()
def roster(client, auth):
    staff = auth("manager")
    rows = [
        _member(client, staff, "نگار تمرین"),
        _member(client, staff, "سامان استقامت"),
        _member(client, staff, "پرهام قدرتی"),
    ]
    return staff, rows


def _names(client, headers: dict, query: str) -> list[str]:
    response = client.get("/api/v1/admin/members-summary", params={"q": query}, headers=headers)
    assert response.status_code == 200, response.text
    return [item["full_name"] for item in response.json()["items"]]


def test_search_by_name_is_server_side(client, roster):
    staff, _rows = roster
    assert _names(client, staff, "استقامت") == ["سامان استقامت"]


def test_search_by_phone_fragment(client, roster):
    staff, rows = roster
    phone = client.get("/api/v1/admin/members-summary", params={"q": rows[0]["id"]}, headers=staff)
    assert phone.status_code == 200  # شناسه عددی مسیر جست‌وجو نیست (نه نام، نه تلفن)
    found = client.get("/api/v1/admin/members-summary", params={"q": "0912"}, headers=staff)
    assert found.status_code == 200
    assert len(found.json()["items"]) >= 3


def test_wildcards_are_not_honoured(client, roster):
    """`%` ورودی کاربر wildcard نیست؛ وگرنه جست‌وجو همهٔ اعضا را برمی‌گرداند."""
    staff, _rows = roster
    assert _names(client, staff, "%") == []
    assert _names(client, staff, "_") == []


def test_unknown_query_returns_empty_not_everything(client, roster):
    staff, _rows = roster
    assert _names(client, staff, "هیچ‌کس-این‌نام-را-ندارد") == []


def test_blank_query_means_no_filter(client, roster):
    staff, _rows = roster
    response = client.get("/api/v1/admin/members-summary", params={"q": "   "}, headers=staff)
    assert response.status_code == 200
    assert len(response.json()["items"]) >= 3


def test_overlong_query_is_rejected(client, roster):
    staff, _rows = roster
    response = client.get("/api/v1/admin/members-summary", params={"q": "a" * 81}, headers=staff)
    assert response.status_code == 422, response.text


def test_member_role_cannot_call_the_staff_list(client, roster):
    from app.security.jwt import create_access_token

    _staff, rows = roster
    headers = {"Authorization": f"Bearer {create_access_token(rows[0]['user_id'], 'member')}"}
    response = client.get("/api/v1/admin/members-summary", headers=headers)
    assert response.status_code == 403, response.text
