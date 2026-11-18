# M65 — SEC-02 QR check-in reproduction and regression

> Date: 2026-11-16 | Branch: `arena/4f336f66-mp` | All fixtures use synthetic accounts and a temporary SQLite database. No production data, credentials, or database were used.

## Result

**SEC-02 reproduced on the current checkout before the fix and corrected in the same loop.** The pre-fix regression file produced **5 failures**: a QR check-in returned `ok` for a member with no membership and for an expired membership; member B could redeem member A's QR; replaying the same QR created a second successful check-in; and a QR token was accepted as a staff access token. These are local API integration-test observations, not claims about a deployed environment.

The fix issues a dedicated two-minute `checkin_qr` token with a random `jti`, keeps access-token validation separate, checks member ownership and current membership, and stores only a SHA-256 digest of `jti` on the check-in. A unique database index makes redemption single-use under a concurrent race; duplicate use is returned as `409 qr_replayed`. Expired/malformed QR tokens are rejected. Reception remains an authorized scanner actor; member actors can redeem only their own QR.

## Evidence after the fix

- `pytest -q mp-app/backend/tests/integration/test_m65_qr_security.py mp-app/backend/tests/integration/test_m61_face_member_gate.py mp-app/backend/tests/integration/test_api_contract.py mp-app/backend/tests/integration/test_m45_checkin_feed.py mp-app/backend/tests/integration/test_m45_admin_attendance.py mp-app/backend/tests/unit/test_models.py` — **65 passed, 5 warnings** (8.46s). The warnings were upstream Starlette/httpx and deprecated HTTP 422 constant warnings; no test was skipped or threshold changed. The six M65 scenarios cover missing/expired membership, cross-member QR, replay, an expired QR token, and QR/access-token separation.
- `ruff check` on all changed backend files — **passed**.
- Alembic graph: `c5d6e7f8a9b0` is the sole head, directly after `b7c9d1e2f3a4`.
- On a disposable `/tmp` SQLite database only: `alembic upgrade head`, `downgrade -1`, `upgrade head` — **passed**. This did not touch a production or repository database.

## Change set

- `app/security/jwt.py`: dedicated QR signing/decoding and two-minute expiry.
- `modules/face_id/{router.py,service.py,schemas.py}`: typed request, member scope, expiry/entitlement enforcement, QR-only digest recording, replay error handling, and time-window membership validation.
- `db/models/face_id.py` + migration `db/migrations/versions/c5d6e7f8a9b0_m65_qr_replay_guard.py`: nullable `qr_jti_hash` and unique index (NULL for non-QR check-ins).
- `tests/integration/test_m65_qr_security.py`: permanent regression cases.

## Scope and limits

No full backend suite, Flutter/device scanner test, GitHub Actions run, push, release, deploy/rollback, or production migration was run. The scanner UI/device remains out of scope (M89 is still blocked); passing local API tests does not prove a physical-device E2E or production configuration. No authorization beyond the tested receptionist/member roles is inferred.
