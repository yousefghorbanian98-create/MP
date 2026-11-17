"""سرویس چهره، رضایت بیومتریک و چک‌این."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import ForbiddenError, NotFoundError
from db.models import BiometricConsent, CheckIn, FaceTemplate, Member, Membership


def _active_consent(db: Session, member_id: int) -> BiometricConsent | None:
    return db.scalar(
        select(BiometricConsent)
        .where(BiometricConsent.member_id == member_id, BiometricConsent.revoked_at.is_(None))
        .order_by(BiometricConsent.granted_at.desc(), BiometricConsent.id.desc())
        .limit(1)
    )


def has_active_consent(db: Session, user) -> dict:
    """Return only the current user's consent/enrollment state, never biometric data."""
    from app.security.ownership import get_own_member

    member = get_own_member(db, user)
    if member is None:
        raise NotFoundError("پروفایل عضو یافت نشد")
    consent = _active_consent(db, member.id)
    enrolled = (
        db.scalar(select(FaceTemplate.id).where(FaceTemplate.member_id == member.id)) is not None
    )
    return {
        "member_id": member.id,
        "consent": consent is not None,
        "policy_version": consent.policy_version if consent else None,
        "enrolled": enrolled,
    }


def grant_consent(db: Session, member_id: int, policy_version: str, user=None) -> BiometricConsent:
    """Record explicit, versioned consent; an active grant is idempotent."""
    from app.security.ownership import ensure_member_scope

    ensure_member_scope(db, user, member_id)
    if db.get(Member, member_id) is None:
        raise NotFoundError("عضو یافت نشد")
    existing = _active_consent(db, member_id)
    if existing is not None and existing.policy_version == policy_version:
        return existing
    if existing is not None:
        existing.revoked_at = datetime.now(UTC)
    consent = BiometricConsent(member_id=member_id, policy_version=policy_version)
    db.add(consent)
    db.flush()
    from modules.admin.service import audit

    audit(
        db,
        getattr(user, "id", None),
        "biometric_consent_granted",
        "biometric_consent",
        consent.id,
        {"member_id": member_id, "policy_version": policy_version},
    )
    db.refresh(consent)
    return consent


def revoke_consent(db: Session, member_id: int, user=None) -> dict:
    """Revoke current consent and delete the encrypted template in the same transaction."""
    from app.security.ownership import ensure_member_scope

    ensure_member_scope(db, user, member_id)
    if db.get(Member, member_id) is None:
        raise NotFoundError("عضو یافت نشد")
    consent = _active_consent(db, member_id)
    if consent is not None:
        consent.revoked_at = datetime.now(UTC)
    template = db.scalar(select(FaceTemplate).where(FaceTemplate.member_id == member_id))
    if template is not None:
        db.delete(template)
    db.flush()
    from modules.admin.service import audit

    actor_id = getattr(user, "id", None)
    audit(
        db,
        actor_id,
        "biometric_consent_revoked",
        "member",
        member_id,
        {"face_deleted": template is not None},
        commit=False,
    )
    if template is not None:
        audit(
            db,
            actor_id,
            "face_deleted",
            "face_template",
            template.id,
            {"member_id": member_id},
            commit=False,
        )
    db.commit()
    return {"status": "consent_revoked", "face_deleted": template is not None}


def _has_active_consent(db: Session, member_id: int) -> bool:
    return _active_consent(db, member_id) is not None


def enroll_face(db: Session, member_id: int, embedding: bytes, user=None) -> FaceTemplate:
    """Encrypt and upsert an embedding only after ownership and active consent checks."""
    from app.security.ownership import ensure_member_scope
    from security.crypto import FaceEmbeddingCipher

    ensure_member_scope(db, user, member_id)
    member = db.get(Member, member_id)
    if member is None:
        raise NotFoundError("عضو یافت نشد")
    if not _has_active_consent(db, member_id):
        raise ForbiddenError("ثبت چهره نیازمند رضایت فعال است (consent required)")
    encrypted = FaceEmbeddingCipher().encrypt(embedding)
    existing = db.scalar(select(FaceTemplate).where(FaceTemplate.member_id == member_id))
    if existing is not None:
        existing.embedding_encrypted = encrypted
        ft = existing
        action = "face_template_updated"
    else:
        ft = FaceTemplate(
            member_id=member_id,
            embedding_encrypted=encrypted,
            branch_id=member.branch_id,
        )
        db.add(ft)
        action = "face_enrolled"
    db.flush()
    from modules.admin.service import audit

    audit(db, getattr(user, "id", None), action, "face_template", ft.id, {"member_id": member_id})
    db.refresh(ft)
    return ft


def delete_face(db: Session, member_id: int, user=None) -> dict:
    """حذف قطعی چهره (حق حذف — US-108)."""
    from app.security.ownership import ensure_member_scope

    ensure_member_scope(db, user, member_id)
    if db.get(Member, member_id) is None:
        raise NotFoundError("عضو یافت نشد")
    ft = db.scalar(select(FaceTemplate).where(FaceTemplate.member_id == member_id))
    if ft is not None:
        template_id = ft.id
        db.delete(ft)
        db.flush()
        from modules.admin.service import audit

        audit(
            db,
            getattr(user, "id", None),
            "face_deleted",
            "face_template",
            template_id,
            {"member_id": member_id},
        )
    return {"status": "face_deleted"}


def match_face(db: Session, probe_embedding: bytes, candidate_member_id: int) -> bool:
    """تطبیق سادهٔ embedding (فاصلهٔ اقلیدسی) — منطق نهایی liveness در M15/گیت."""
    from security.crypto import FaceEmbeddingCipher

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


def _check_in(
    db: Session,
    member_id: int,
    method: str,
    result: str = "ok",
    denial_reason: str = "",
    user=None,
    qr_jti_hash: str | None = None,
) -> CheckIn:
    """ثبت چک‌این (US-106) — ورود فقط با اشتراک فعال."""
    from app.security.ownership import ensure_member_scope

    ensure_member_scope(db, user, member_id)
    member = db.get(Member, member_id)
    if member is None:
        raise NotFoundError("عضو یافت نشد")
    if result == "ok":
        now = datetime.now(UTC)
        memberships = db.scalars(
            select(Membership).where(
                Membership.member_id == member_id, Membership.status == "active"
            )
        )
        has_current_membership = any(
            _aware(membership.started_at) <= now < _aware(membership.expires_at)
            for membership in memberships
        )
        if not has_current_membership:
            result, denial_reason = "denied", "membership_expired"
    ci = CheckIn(
        member_id=member_id,
        method=method,
        result=result,
        denial_reason=denial_reason,
        qr_jti_hash=qr_jti_hash,
        branch_id=member.branch_id,
    )
    db.add(ci)
    db.commit()
    db.refresh(ci)
    from app.metrics import metrics

    metrics.inc("mp_checkins_total", method=method, result=result)
    return ci


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def check_in(
    db: Session,
    member_id: int,
    method: str,
    result: str = "ok",
    denial_reason: str = "",
    user=None,
    qr_jti_hash: str | None = None,
) -> CheckIn:
    """Record a check-in and observe its end-to-end service duration."""
    from app.metrics import Timer

    with Timer("mp_checkin_duration_seconds", method=method):
        return _check_in(
            db,
            member_id,
            method,
            result=result,
            denial_reason=denial_reason,
            user=user,
            qr_jti_hash=qr_jti_hash,
        )
