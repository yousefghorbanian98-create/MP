"""فاز ۷ — جاروی IDOR روی همهٔ مسیرهای GET با `{member_id}` (QF-13..18).

# چرا این تست، نه هجده تست دستی

فهرست مسیرها از **قرارداد واقعی** (`api/routes.json`) خوانده می‌شود، نه از یک
لیست دستی که کهنه می‌شود. برای هر مسیر GET که `{member_id}` دارد، با توکن
عضوِ *دیگر* فراخوانی می‌کنیم و یکی از این دو را می‌پذیریم:

- کد مسدودکننده (400/403/404/409/422) — «رد»؛
- ۲۰۰ که هیچ دادهٔ عضو هدف در آن نباشد (بدنهٔ خالی/خودِ عضو).

اگر بدنه ۲۰۰ شامل شناسه یا تلفن یا نام عضو هدف باشد، تست شکست می‌خورد — یعنی
همان شکاف IDOR. مسیرهایی که در ادامه فاز ۷ مجاز می‌شوند (مثل گزارش محرمانه برای
coach) از این جارو بیرون‌اند چون نقش `member` در artifact آن‌ها نیست.

# آنچه این تست ثابت نمی‌کند
- مسیرهای POST/PATCH/DELETE با بدنهٔ عضو دیگر (آن‌ها در تست‌های هر ماژول‌اند).
- UI و کلاینت Flutter (اجرا نشده — `BLOCKED`).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from db.base import get_session_factory
from db.models import Member, User

ARTIFACT = Path(__file__).resolve().parents[2] / "api" / "routes.json"
BLOCKING = {400, 401, 403, 404, 409, 422}


def _member_operation_paths() -> list[str]:
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    out = []
    for op in data["operations"]:
        if op["method"] != "GET" or "{member_id}" not in op["path"]:
            continue
        if "member" not in op["roles"]:
            continue
        out.append(op["path"])
    return sorted(set(out))


def _new_member(phone: str, name: str, gender: str = "male") -> tuple[int, int, dict]:
    from app.security.jwt import create_access_token

    with get_session_factory()() as s:
        user = User(phone=phone, full_name=name, role="member")
        s.add(user)
        s.commit()
        member = Member(user_id=user.id, goal="hypertrophy", constraints="[]", gender=gender)
        s.add(member)
        s.commit()
        token = create_access_token(user.id, user.role)
        return user.id, member.id, {"Authorization": f"Bearer {token}"}


def _leaks(payload: object, member_id: int, phone: str, name: str) -> bool:
    text = json.dumps(payload, ensure_ascii=False)
    return (
        phone in text
        or name in text
        or f'"member_id": {member_id}' in text
        or f'Id": {member_id}' in text
    )


@pytest.mark.parametrize("template", _member_operation_paths())
def test_member_cannot_read_another_members_surface(client: TestClient, template: str) -> None:
    _, victim_id, _ = _new_member("09610000001", "عضو-هدف")
    _, _, attacker_h = _new_member("09610000002", "عضو-مهاجم")

    path = template.replace("{member_id}", str(victim_id))
    res = client.get(path, headers=attacker_h)

    if res.status_code == 200:
        body = res.json()
        assert not _leaks(body, victim_id, "09610000001", "عضو-هدف"), (
            f"{path} دادهٔ عضو دیگر را به عضو مهاجم داد: {str(body)[:300]}"
        )
    else:
        assert res.status_code in BLOCKING, f"{path} → {res.status_code} {res.text[:200]}"


def test_the_sweep_harness_really_detects_a_leak() -> None:
    """ضدِ سبزیِ توخالی: ابزار تشخیص باید روی نمونهٔ آلوده قرمز شود."""
    assert _leaks({"member_id": 5}, 5, "0912", "عضو") is True
    assert _leaks({"phone": "09120000001"}, 99, "09120000001", "کسی") is True
    assert _leaks({"full_name": "عضو-هدف"}, 5, "0912", "عضو-هدف") is True
    assert _leaks({"member_id": 6}, 5, "0912", "عضو") is False


def test_own_member_still_reads_own_data(client: TestClient) -> None:
    """اگر همه‌چیز بسته بود، جارو بی‌معنا سبز می‌شد؛ خواندن دادهٔ خود باید ۲۰۰ بدهد."""
    _, member_id, headers = _new_member("09610000003", "عضو-خود")
    res = client.get(f"/api/v1/members/{member_id}", headers=headers)
    assert res.status_code == 200, res.text
    assert res.json().get("id") == member_id
