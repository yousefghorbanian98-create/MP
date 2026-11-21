"""آماده‌سازی دادهٔ S3c برای M39-c3: کاربر super_admin + عضو.

توکن هرگز روی stdout چاپ نمی‌شود (WP 1.4 / F-08)؛ اگر MP_SEED_TOKEN_FILE تنظیم باشد
توکن با مجوز 0600 در آن فایل نوشته می‌شود. stdout فقط member_id را می‌دهد.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import os  # noqa: E402

from app.security.jwt import create_access_token, create_refresh_token  # noqa: E402
from db.base import get_session_factory  # noqa: E402
from db.models import Member, RefreshToken, User  # noqa: E402

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
    _refresh, refresh_hash, expires = create_refresh_token()
    db.add(
        RefreshToken(
            user_id=user.id, token_hash=refresh_hash, expires_at=expires, device_info="seed"
        )
    )
    db.commit()
    token = create_access_token(
        user.id, user.role, session_id=refresh_hash, auth_version=user.auth_version
    )
    token_file = os.environ.get("MP_SEED_TOKEN_FILE")
    if token_file:
        fd = os.open(token_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(token)
    print(member.id)
