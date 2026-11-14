"""سرویس face_id — ثبت/حذف چهره (رمزنگاری)، رضایت، چک‌این.

قاعده (NFR-3): فقط embedding رمزنگاری‌شده ذخیره می‌شود؛ تصویر خام هرگز.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import ForbiddenError, NotFoundError
from db.models import BiometricConsent, CheckIn, FaceTemplate, Member, Membership
from security.crypto import FaceEmbeddingCipher


def grant_consent(db: Session, member_id: int, policy_version: str = "v1") -> BiometricConsent:
    if db.get(Member, member_id) is None:
        raise NotFoundError("عضو یافت نشد")
    c = BiometricConsent(member_id=member_id, policy_version=policy_version)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def revoke_consent(db: Session, member_id: int) -> dict:
    """پس‌گرفتن رضایت = حذف قطعی چهره (US-108)."""
    delete_face(db, member_id)
    for c in db.scalars(
        select(BiometricConsent).where(
            BiometricConsent.member_id == member_id, BiometricConsent.revoked_at.is_(None)
        )
    ):
        c.revoked_at = datetime.now(UTC)
    db.commit()
    return {"status": "consent_revoked", "face_deleted": True}


def _has_active_consent(db: Session, member_id: int) -> bool:
    return (
        db.scalar(
            select(BiometricConsent).where(
                BiometricConsent.member_id == member_id, BiometricConsent.revoked_at.is_(None)
            )
        )
        is not None
    )


def enroll_face(db: Session, member_id: int, embedding: bytes) -> FaceTemplate:
    """ثبت چهره — فقط با رضایت صریح و embedding رمزنگاری‌شده."""
    if db.get(Member, member_id) is None:
        raise NotFoundError("عضو یافت نشد")
    if not _has_active_consent(db, member_id):
        raise ForbiddenError("ثبت چهره بدون رضایت صریح ممکن نیست (US-108)")
    cipher = FaceEmbeddingCipher()
    encrypted = cipher.encrypt(embedding)
    existing = db.scalar(select(FaceTemplate).where(FaceTemplate.member_id == member_id))
    if existing is not None:
        existing.embedding_encrypted = encrypted
        db.commit()
        db.refresh(existing)
        return existing
    ft = FaceTemplate(member_id=member_id, embedding_encrypted=encrypted, branch_id=1)
    db.add(ft)
    db.commit()
    db.refresh(ft)
    return ft


def delete_face(db: Session, member_id: int) -> dict:
    """حذف قطعی چهره (حق حذف — US-108)."""
    ft = db.scalar(select(FaceTemplate).where(FaceTemplate.member_id == member_id))
    if ft is not None:
        db.delete(ft)
        db.commit()
    return {"status": "face_deleted"}


def match_face(db: Session, probe_embedding: bytes, candidate_member_id: int) -> bool:
    """تطبیق سادهٔ embedding (فاصلهٔ اقلیدسی) — منطق نهایی liveness در M15/گیت."""
    ft = db.scalar(select(FaceTemplate).where(FaceTemplate.member_id == candidate_member_id))
    if ft is None:
        return False
    cipher = FaceEmbeddingCipher()
    stored = cipher.decrypt(ft.embedding_encrypted)
    return _distance(stored, probe_embedding) < 0.6


def _distance(a: bytes, b: bytes) -> float:
    if len(a) != len(b):
        return 2.0
    return sum((x - y) ** 2 for x, y in zip(a, b, strict=False)) ** 0.5 / max(len(a), 1) ** 0.5


def check_in(
    db: Session, member_id: int, method: str, result: str = "ok", denial_reason: str = ""
) -> CheckIn:
    """ثبت چک‌این (US-106) — ورود فقط با اشتراک فعال."""
    if db.get(Member, member_id) is None:
        raise NotFoundError("عضو یافت نشد")
    if result == "ok":
        now = datetime.now(UTC)
        active = db.scalar(
            select(Membership).where(
                Membership.member_id == member_id, Membership.status == "active"
            )
        )
        if active is None or _aware(active.expires_at) <= now:
            result, denial_reason = "denied", "membership_expired"
    ci = CheckIn(
        member_id=member_id,
        method=method,
        result=result,
        denial_reason=denial_reason,
        branch_id=1,
    )
    db.add(ci)
    db.commit()
    db.refresh(ci)
    return ci


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
