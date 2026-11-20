"""سازندهٔ کاربر/هدر برای تست‌های یکپارچه — تک‌منبع، تا هر فایل کپی خودش را نسازد.

فاز ۵ (QF-03): مجوز شخصی (`grants`) بخشی از هویت actor است؛ تستی که پول جابه‌جا
می‌کند باید صریحاً همان مجوز را بدهد، نه این‌که با نقش `manager` فرض کند باز است.
"""

from __future__ import annotations

import itertools

_counter = itertools.count(10_000)


def create_actor(role: str = "manager", grants: list[str] | None = None) -> dict:
    """کاربر تازه با نقش دلخواه + هدر `Authorization`؛ `grants` مجوزهای فعال او."""
    from app.security.jwt import create_access_token
    from db.base import get_session_factory
    from db.models import AdminPermission, User

    n = next(_counter)
    with get_session_factory()() as s:
        u = User(phone=f"09{n:09d}", full_name=f"{role}-{n}", role=role)
        s.add(u)
        s.commit()
        for permission in grants or []:
            s.add(AdminPermission(user_id=u.id, permission=permission, note="test fixture"))
        if grants:
            s.commit()
        token = create_access_token(u.id, u.role)
    return {"Authorization": f"Bearer {token}"}
