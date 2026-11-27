# Route / ownership cross-check for the member account slice

This is source-level context for the local tests, not independent security acceptance.

- Studio `fetchMe()` calls `GET /api/v1/members/me`; backend `_me_dict` returns `Member.id`, `User.id`, role, profile and JSON-string constraints. The UI gates the next request on `role === "member"` and positive `Member.id`.
- Studio `fetchMemberMemberships(memberId)` calls `GET /api/v1/members/{memberId}/memberships`; the existing backend route calls `ensure_member_scope(db, user, member_id)` before reading rows.
- The backend integration test with temporary SQLite/TestClient asserts that a member's `/members/me` ID is their member profile ID; own membership history returns the created membership; existing member A → B history access remains HTTP 403. No backend authorization policy was changed.
- The matching Studio component test uses synthetic responses and proves that user ID `41` is not substituted for server member ID `17`, the request carries the member bearer token, and history is not requested before a valid member profile is returned.
