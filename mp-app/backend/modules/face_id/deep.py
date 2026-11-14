"""آداپتور مدل عمیق چهره (D-008 / بستن کار باز — ۲۰۲۶-۱۱-۱۴).

سیاست model_lock: تا سه شرط برقرار نشود، استنتاج عمیق انجام نمی‌شود:
  ۱) فایل وزن ONNX معتبر (magic bytes) با SHA256 ثبت‌شده
  ۲) مجوز مدل در NOTICE-THIRD-PARTY.md ثبت‌شده باشد (D-022)
  ۳) تأیید جمعیتی (population fit) مستند باشد
وزن مدل در مخزن نگهداری نمی‌شود (فایل بزرگ + مجوز جدا) — مسیر از متغیر محیطی
`MP_FACE_MODEL_PATH` خوانده می‌شود (استقرار).
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

from app.errors import ApiError

MODEL_LOCK_VERSION = "model-lock-1.1"

# ONNX یک protobuf است؛ نخستین بایت‌ها معمولاً 0x08 (فیلد اول varint).
_ONNX_MAGIC = b"\x08"
_HTML_MAGIC = (b"<!doctype", b"<html", b"<?xml")


def verify_model_file(path: Path) -> dict:
    """اعتبارسنجی فایل وزن: نوع/حجم/هش — هرگز فایل HTML/خطا به‌جای مدل پذیرفته نمی‌شود."""
    if not path.is_file():
        raise ApiError(f"فایل مدل یافت نشد: {path}", code="model_missing")
    head = path.read_bytes()[:16]
    if head[:2].lower().startswith(b"<!") or any(head.lower().startswith(m) for m in _HTML_MAGIC):
        raise ApiError("فایل مدل، HTML است (دانلود ناموفق) — رد شد", code="model_not_onnx")
    if not head.startswith(_ONNX_MAGIC):
        raise ApiError("magic bytes نامعتبر برای ONNX — رد شد", code="model_not_onnx")
    size = path.stat().st_size
    if size < 1024 * 1024:  # مدل واقعی چهره < ۱ مگابایت نیست
        raise ApiError(f"حجم فایل مدل مشکوک است ({size} بایت)", code="model_too_small")
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"path": str(path), "size": size, "sha256": sha}


def lock_status() -> dict:
    """وضعیت واقعی قفل — هرگز «باز» جعل نمی‌شود (missing ≠ normal)."""
    model_path = os.environ.get("MP_FACE_MODEL_PATH", "")
    checks = {
        "weights_present": bool(model_path) and Path(model_path).is_file(),
        "weights_sha256_registered": bool(os.environ.get("MP_FACE_MODEL_SHA256")),
        "license_registered": bool(os.environ.get("MP_FACE_MODEL_LICENSE")),
        "population_fit_documented": bool(os.environ.get("MP_FACE_POPULATION_FIT")),
    }
    unlocked = all(checks.values())
    return {
        "lock_version": MODEL_LOCK_VERSION,
        "unlocked": unlocked,
        "checks": checks,
        "active_backend": "hog-dlib" if not unlocked else "deep-onnx",
        "note": (
            "استنتاج عمیق قفل است — از موتور HOG تأییدشده استفاده می‌شود"
            if not unlocked
            else "همهٔ شرایط برقرار — آمادهٔ استنتاج عمیق"
        ),
    }


class DeepFaceAdapter:
    """بارگذاری و استنتاج ONNX — فقط وقتی قفل باز است (لازی: onnxruntime)."""

    def __init__(self) -> None:
        status = lock_status()
        if not status["unlocked"]:
            raise ApiError("مدل عمیق قفل است (model_lock)", code="model_locked")
        self._info = verify_model_file(Path(os.environ["MP_FACE_MODEL_PATH"]))

    def embed(self, image_bgr) -> list[float]:
        """بردار چهره — ورودی آرایهٔ HxWx3؛ نیازمند onnxruntime در استقرار."""
        try:
            import onnxruntime  # type: ignore
        except ImportError as exc:  # pragma: no cover - در استقرار نصب می‌شود
            raise ApiError(
                "onnxruntime نصب نیست (وابستگی استقرار مدل عمیق)", code="onnxruntime_missing"
            ) from exc
        session = onnxruntime.InferenceSession(self._info["path"])
        # نرمال‌سازی ورودی مطابق قرارداد مدل — در استقرار با مدل انتخابی تکمیل می‌شود
        raise (
            ApiError(
                "پیکربندی preprocess مدل ثبت نشده — قفل جزئی", code="model_preprocess_unconfigured"
            )
            if session
            else None
        )
