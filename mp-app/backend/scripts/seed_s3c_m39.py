"""آماده‌سازی دادهٔ S3c برای M39-c3: کاربر super_admin + عضو + توکن (stdout: token|member_id)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.security.jwt import create_access_token  # noqa: E402
from db.base import get_session_factory  # noqa: E402
from db.models import Member, User  # noqa: E402

session_factory = get_session_factory()
with session_factory() as db:
    user = User(phone="09120000039", full_name="ادمین S3c", role="super_admin")
    db.add(user)
    db.flush()
    member = Member(
        user_id=user.id,
        gender="male",
        birth_date=None,
        height_cm=175,
        goal="hypertrophy",
    )
    db.add(member)
    db.commit()
    token = create_access_token(user.id, user.role)
    print(f"{token}|{member.id}")
