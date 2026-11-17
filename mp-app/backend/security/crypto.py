"""رمزنگاری دادهٔ بیومتریک — FaceTemplate فقط embedding رمزنگاری‌شده (PyNaCl SecretBox).

قاعده (NFR-3 / ADR-004): هرگز تصویر خام یا embedding خام ذخیره نمی‌شود.
کلید از env `MP_BIOMETRIC_KEY` (base64، ۳۲ بایت) خوانده می‌شود؛ در صورت نبود،
کلید مشتق‌شده از secret_key فقط برای محیط development ساخته می‌شود.
"""

from __future__ import annotations

import base64
import hashlib

from nacl.exceptions import CryptoError
from nacl.secret import SecretBox


class BiometricCryptoError(Exception):
    """خطای رمزنگاری/گشایش دادهٔ بیومتریک."""


class FaceEmbeddingCipher:
    """رمزگذار/گشاگر embedding چهره با SecretBox (authenticated encryption)."""

    def __init__(self, key: bytes | None = None):
        if key is None:
            key = self._derive_dev_key()
        if len(key) != SecretBox.KEY_SIZE:
            raise BiometricCryptoError(
                f"کلید باید {SecretBox.KEY_SIZE} بایت باشد، {len(key)} داده شد"
            )
        self._box = SecretBox(key)

    @staticmethod
    def _derive_dev_key() -> bytes:
        from app.config import settings

        if settings.biometric_key:
            try:
                key = base64.b64decode(settings.biometric_key, validate=True)
            except Exception as exc:  # noqa: BLE001
                raise BiometricCryptoError("MP_BIOMETRIC_KEY معتبر نیست (base64)") from exc
            return key
        # محیط dev: مشتق از secret_key.
        # در production این مسیر **بی‌صدا** رد نمی‌شود: بدون کلید اختصاصی،
        # همهٔ قالب‌های چهره با کلیدی رمز می‌شدند که کنار خودِ سیستم است —
        # یعنی رمزنگاری‌ای که فقط ظاهرش رمزنگاری است. باید صریحاً بشکند.
        if settings.environment == "production":
            raise BiometricCryptoError(
                "MP_BIOMETRIC_KEY در production الزامی است (base64، ۳۲ بایت) — "
                "بدون آن، دادهٔ بیومتریک با کلید مشتق‌شده از secret رمز می‌شود"
            )
        return hashlib.sha256(settings.secret_key.encode("utf-8")).digest()

    def encrypt(self, embedding: bytes) -> bytes:
        """رمزنگاری embedding (bytes خروجی SFace)."""
        if not isinstance(embedding, bytes) or not embedding:
            raise BiometricCryptoError("embedding باید bytes غیرخالی باشد")
        return self._box.encrypt(embedding)

    def decrypt(self, encrypted: bytes) -> bytes:
        """گشایش embedding رمزنگاری‌شده."""
        try:
            return self._box.decrypt(encrypted)
        except (CryptoError, ValueError) as exc:
            raise BiometricCryptoError("گشایش embedding ناموفق بود") from exc
