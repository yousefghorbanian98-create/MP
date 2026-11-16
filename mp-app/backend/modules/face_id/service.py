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


def grant_consent(
    db: Session, member_id: int, policy_version: str = "v1", user=None
) -> BiometricConsent:
    from app.security.ownership import ensure_member_scope

    ensure_member_scope(db, user, member_id)
    if db.get(Member, member_id) is None:
        raise NotFoundError("عضو یافت نشد")
    c = BiometricConsent(member_id=member_id, policy_version=policy_version)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def revoke_consent(db: Session, member_id: int, user=None) -> dict:
    """پس‌گرفتن رضایت = حذف قطعی چهره (US-108)."""
    from app.security.ownership import ensure_member_scope

    ensure_member_scope(db, user, member_id)
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


def has_active_consent(db: Session, user=None) -> dict:
    """وضعیت رضایت + ثبت چهرهٔ **خودِ** کاربر — برای گیت UI در اپ عضو (M61/D1).

    برمی‌گرداند: `member_id`، `consent`، `enrolled`، `policy_version`.
    هیچ‌جا تصویر یا embedding برنمی‌گردد؛ فقط بولین‌ها.
    """
    from db.models import FaceTemplate, Member

    member = db.scalar(select(Member).where(Member.user_id == user.id)) if user else None
    if member is None:
        raise NotFoundError("عضو یافت نشد")
    consent = db.scalar(
        select(BiometricConsent)
        .where(BiometricConsent.member_id == member.id, BiometricConsent.revoked_at.is_(None))
        .order_by(BiometricConsent.id.desc())
    )
    enrolled = (
        db.scalar(select(FaceTemplate).where(FaceTemplate.member_id == member.id)) is not None
    )
    return {
        "member_id": member.id,
        "consent": consent is not None,
        "policy_version": consent.policy_version if consent else None,
        "enrolled": enrolled,
    }


def enroll_face(db: Session, member_id: int, embedding: bytes, user=None) -> FaceTemplate:
    """ثبت چهره — فقط با رضایت صریح و embedding رمزنگاری‌شده."""
    from app.security.ownership import ensure_member_scope

    ensure_member_scope(db, user, member_id)
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
    from modules.admin.service import audit

    audit(db, None, "face_enrolled", "face_template", ft.id, {"member_id": member_id})
    return ft


def delete_face(db: Session, member_id: int, user=None) -> dict:
    """حذف قطعی چهره (حق حذف — US-108)."""
    from app.security.ownership import ensure_member_scope

    ensure_member_scope(db, user, member_id)
    ft = db.scalar(select(FaceTemplate).where(FaceTemplate.member_id == member_id))
    if ft is not None:
        db.delete(ft)
        db.commit()
        from modules.admin.service import audit

        audit(db, None, "face_deleted", "face_template", None, {"member_id": member_id})
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
    db: Session, member_id: int, method: str, result: str = "ok", denial_reason: str = "", user=None
) -> CheckIn:
    """ثبت چک‌این (US-106) — ورود فقط با اشتراک فعال."""
    from app.security.ownership import ensure_member_scope

    ensure_member_scope(db, user, member_id)
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
    from app.metrics import metrics

    metrics.inc("mp_checkins_total", method=method, result=result)
    return ci


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
