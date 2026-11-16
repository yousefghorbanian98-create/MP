"""M61/D1 — «ثبت چهره» در اپ عضو همیشه ۴۰۳ می‌گرفت.

اثبات باگ (پیش از رفع):

    curl -X POST /api/v1/face/enroll  (توکن member)
    → 403 {"code":"forbidden","message":"نقش member برای POST /api/v1/face/enroll مجاز نیست"}

دلیل: در `security/rbac.py` برای نقش member فقط
`("member", "/api/v1/face/enroll/*", "DELETE")` وجود داشت — هیچ POST.
یعنی دکمهٔ اپ عضوی که در `checkin_page.dart` رندر می‌شد، از روز اول مرده بود.

این فایل چهار چیز را قفل می‌کند:
  ۱) عضو **بدون** رضایت هنوز ۴۰۳ می‌گیرد (امنیت بیومتریک تضعیف نشد)
  ۲) عضو **با** رضایت می‌تواند چهرهٔ خودش را ثبت کند (دکمه واقعاً کار می‌کند)
  ۳) عضو نمی‌تواند برای عضو دیگر ثبت کند (مالکیت)
  ۴) وضعیت رضایت از مسیر خودش خوانده می‌شود، تا UI بداند دکمه را فعال کند
"""

import base64
import itertools

_phone = itertools.count(500)


def _member_with_token(client, auth):
    coach = auth("coach")
    n = next(_phone)
    r = client.post(
        "/api/v1/members",
        json={"phone": f"09{123000000 + n:09d}", "full_name": "عضو دکمهٔ چهره", "gender": "male"},
        headers=coach,
    )
    # خطای ساخت عضو را صریح نشان بده — نسخهٔ اول `.json()` خالی می‌گرفت و
    # خطا به شکل KeyError نامفهوم ظاهر می‌شد.
    assert r.status_code in (200, 201), r.text
    member = r.json()
    from app.security.jwt import create_access_token

    own = {"Authorization": f"Bearer {create_access_token(member['user_id'], 'member')}"}
    return member, own


def test_member_without_consent_still_gets_403(client, auth):
    """بازکردن مسیر نباید گیت رضایت را بردارد."""
    member, own = _member_with_token(client, auth)
    emb = base64.b64encode(b"\x01" * 128).decode()

    r = client.post(
        "/api/v1/face/enroll", json={"member_id": member["id"], "embedding_b64": emb}, headers=own
    )

    assert r.status_code == 403, r.text
    assert "consent" in r.text.lower() or "رضایت" in r.text


def test_member_with_consent_can_enroll_his_own_face(client, auth):
    """دکمهٔ «ثبت چهره» در اپ عضو واقعاً کار می‌کند."""
    member, own = _member_with_token(client, auth)
    client.post("/api/v1/face/consent", json={"member_id": member["id"]}, headers=own)
    emb = base64.b64encode(b"\x02" * 128).decode()

    r = client.post(
        "/api/v1/face/enroll", json={"member_id": member["id"], "embedding_b64": emb}, headers=own
    )

    assert r.status_code == 200, r.text
    assert r.json()["member_id"] == member["id"]


def test_member_cannot_enroll_for_another_member(client, auth):
    """بازکردن POST نباید به عضو اجازهٔ دست‌کاری چهرهٔ دیگری بدهد."""
    member_a, own_a = _member_with_token(client, auth)
    member_b, _ = _member_with_token(client, auth)
    client.post("/api/v1/face/consent", json={"member_id": member_a["id"]}, headers=own_a)
    emb = base64.b64encode(b"\x03" * 128).decode()

    r = client.post(
        "/api/v1/face/enroll",
        json={"member_id": member_b["id"], "embedding_b64": emb},
        headers=own_a,
    )

    assert r.status_code == 403, r.text


def test_my_face_consent_reports_state_for_the_ui_gate(client, auth):
    """UI باید بداند دکمه را فعال کند یا راهنمای رضایت نشان دهد."""
    member, own = _member_with_token(client, auth)

    before = client.get("/api/v1/members/me/face-consent", headers=own)
    assert before.status_code == 200, before.text
    assert before.json()["consent"] is False
    assert before.json()["enrolled"] is False
    assert before.json()["member_id"] == member["id"]

    client.post("/api/v1/face/consent", json={"member_id": member["id"]}, headers=own)
    emb = base64.b64encode(b"\x04" * 128).decode()
    client.post(
        "/api/v1/face/enroll", json={"member_id": member["id"], "embedding_b64": emb}, headers=own
    )

    after = client.get("/api/v1/members/me/face-consent", headers=own).json()
    assert after["consent"] is True
    assert after["enrolled"] is True
    # هیچ دادهٔ بیومتریکی برنمی‌گردد — فقط بولین
    assert set(after) == {"member_id", "consent", "policy_version", "enrolled"}
