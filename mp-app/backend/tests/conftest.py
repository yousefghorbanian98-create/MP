"""فیکسچرهای مشترک pytest — session درون‌حافظه‌ای SQLite + سازنده‌های داده."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db import models  # noqa: E402,F401
from db.base import Base  # noqa: E402


@pytest.fixture()
def engine():
    eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=eng)
    yield eng
    Base.metadata.drop_all(bind=eng)
    eng.dispose()


@pytest.fixture()
def session(engine):
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    s = session_factory()
    yield s
    s.close()


@pytest.fixture()
def make_user(session):
    def _make(phone="09120000001", full_name="کاربر تست", role="member"):
        from db.models import User

        u = User(phone=phone, full_name=full_name, role=role)
        session.add(u)
        session.commit()
        return u

    return _make


@pytest.fixture()
def make_member(session, make_user):
    def _make(user=None, goal="hypertrophy", constraints="[]"):
        from db.models import Member

        user = user or make_user()
        m = Member(user_id=user.id, goal=goal, constraints=constraints)
        session.add(m)
        session.commit()
        return m

    return _make
