"""تست متن حریم خصوصی بیومتریک (M31)."""

from __future__ import annotations

import itertools

import pytest
from fastapi.testclient import TestClient

from app.config import settings

from ._actors import create_actor

_counter = itertools.count(910001)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/fp.db")
    from db.base import init_db, reset_engine

    reset_engine()
    init_db()
    limiter.reset()
    from cache.store import InMemoryCache, reset_cache

    reset_cache(InMemoryCache())
    app = __import__("app.main", fromlist=["create_app"]).create_app()
    with TestClient(app) as c:
        yield c
    reset_engine()


@pytest.fixture()
def auth():
    """هدر کاربر تازه؛ `grants` مجوزهای شخصی فاز ۵ را هم می‌سازد."""

    def _auth(role: str = "member", grants: list[str] | None = None) -> dict:
        return create_actor(role, grants)

    return _auth


def test_privacy_notice_versioned_and_readable(client, auth):
    h = auth("member")
    r = client.get("/api/v1/face/privacy-notice", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["version"].startswith("faceid-privacy-")
    assert any("رضایت" in s["text"] or "رضایت" in s["heading"] for s in body["sections"])
    assert any("حذف" in s["text"] for s in body["sections"])  # حق حذف صریح


def test_production_requires_a_dedicated_biometric_key(monkeypatch):
    """باگ امنیتی: در production بدون MP_BIOMETRIC_KEY، کلید از secret مشتق می‌شد.

    یعنی رمزنگاری‌ای که فقط ظاهرش رمزنگاری بود: هر کسی که به secret_key
    دسترسی داشت (همان فایل تنظیمات) می‌توانست embedding چهره را بگشاید،
    و مهاجرت کلید هرگز اجباری نمی‌شد. باید صریح بشکند، نه بی‌صدا.
    """
    from app.config import settings
    from security.crypto import BiometricCryptoError, FaceEmbeddingCipher

    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "biometric_key", "")
    with pytest.raises(BiometricCryptoError) as exc:
        FaceEmbeddingCipher()
    assert "MP_BIOMETRIC_KEY" in str(exc.value)


def test_production_accepts_a_real_32_byte_key(monkeypatch):
    import base64

    from app.config import settings
    from security.crypto import FaceEmbeddingCipher

    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "biometric_key", base64.b64encode(b"k" * 32).decode())
    cipher = FaceEmbeddingCipher()
    assert cipher.decrypt(cipher.encrypt(b"embedding")) == b"embedding"


def test_rejected_key_length_still_fails():
    from security.crypto import BiometricCryptoError, FaceEmbeddingCipher

    with pytest.raises(BiometricCryptoError):
        FaceEmbeddingCipher(key=b"short")
