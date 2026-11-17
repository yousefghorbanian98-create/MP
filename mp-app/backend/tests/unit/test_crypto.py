"""تست‌های رمزنگاری بیومتریک (FaceEmbeddingCipher — PyNaCl)."""

from __future__ import annotations

import base64
import os

import pytest

from security.crypto import BiometricCryptoError, FaceEmbeddingCipher


def test_encrypt_decrypt_roundtrip():
    cipher = FaceEmbeddingCipher(key=os.urandom(32))
    embedding = os.urandom(128)  # خروجی نمونهٔ SFace
    encrypted = cipher.encrypt(embedding)
    assert encrypted != embedding
    assert cipher.decrypt(encrypted) == embedding


def test_encrypted_output_not_plain():
    cipher = FaceEmbeddingCipher(key=os.urandom(32))
    embedding = b"A" * 64
    encrypted = cipher.encrypt(embedding)
    assert b"A" * 64 not in encrypted  # متن خام در ciphertext نیست


def test_wrong_key_fails_decrypt():
    c1 = FaceEmbeddingCipher(key=os.urandom(32))
    c2 = FaceEmbeddingCipher(key=os.urandom(32))
    encrypted = c1.encrypt(b"data" * 8)
    with pytest.raises(BiometricCryptoError):
        c2.decrypt(encrypted)


def test_tampered_ciphertext_fails():
    cipher = FaceEmbeddingCipher(key=os.urandom(32))
    encrypted = bytearray(cipher.encrypt(b"data" * 8))
    encrypted[-1] ^= 0xFF
    with pytest.raises(BiometricCryptoError):
        cipher.decrypt(bytes(encrypted))


def test_invalid_key_length_rejected():
    with pytest.raises(BiometricCryptoError):
        FaceEmbeddingCipher(key=b"short")


def test_empty_embedding_rejected():
    cipher = FaceEmbeddingCipher(key=os.urandom(32))
    with pytest.raises(BiometricCryptoError):
        cipher.encrypt(b"")


def test_dev_key_derivation_stable(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "biometric_key", "")
    monkeypatch.setattr(settings, "secret_key", "fixed-dev-secret")
    k1 = FaceEmbeddingCipher._derive_dev_key()
    k2 = FaceEmbeddingCipher._derive_dev_key()
    assert k1 == k2
    assert len(k1) == 32


def test_env_key_base64(monkeypatch):
    from app.config import settings

    key = os.urandom(32)
    monkeypatch.setattr(settings, "biometric_key", base64.b64encode(key).decode())
    assert FaceEmbeddingCipher._derive_dev_key() == key
