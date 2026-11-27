# MEM-01 follow-up — API-backed member account slice

**Local result: `PARTIAL / NOT_ACCEPTED`.** This records a dirty-worktree implementation and synthetic/local verification only; no canonical acceptance checkbox is closed.

## Provenance and boundary

- Arena reference date: `2026-11-23 UTC`.
- Branch: `arena/5e0f64cf-mp`; baseline `HEAD` before edits: `5828c94c9d875fa5a4c58740611bf800324649f8`.
- Studio/backend source and tests were changed while the worktree already had unrelated staged and untracked entries. The baseline SHA is not the tested source SHA, and this is not clean-commit evidence.
- No production data, credentials, real member account, real SMS, or live production/staging service was used. Browser/device/headless execution was not repeated; the previously recorded Chromium launch blocker (`libnspr4.so` absent) remains an environment limitation, not a product result.

## Implementation

- `/member` now renders a `MemberAccount` slice; `/member/today` remains an explicit no-fabricated-program placeholder.
- The page calls the existing authenticated `GET /api/v1/members/me` first. Only when the response says `role=member` and contains a positive safe `Member.id` does it request `GET /api/v1/members/{Member.id}/memberships`. It deliberately uses the server's member-profile ID, not the user ID or a client-selected ID. There is no local/mock fallback.
- The account view shows the server profile, height/goal/gender, and member constraints. Known constraint codes are rendered in Persian; unknown/malformed values are retained rather than silently treated as empty.
- Membership rows are read from the existing membership response contract. Explicit cancellation and backend expiry remain distinct; an `active` row whose exact expiry instant has passed is shown expired even if an expiry job has not updated the row. Unknown/malformed status/time remains unknown. An empty list is explicitly not labelled expired.
- Timestamps with an explicit offset are respected. A timezone-naive ISO timestamp from this backend is interpreted as UTC (membership creation uses UTC; SQLite can drop the offset), then formatted with the Persian calendar and `Asia/Tehran`.
- Profile/history loading, retryable server errors, invalid profile IDs, role mismatch and session-expiry messaging are represented. The shared session client supplies bearer auth, refresh/retry and 401 handling.

## Verification performed

- Studio focused run: **5 files / 33 tests passed**; details in [`member-account-focused-studio.txt`](member-account-focused-studio.txt). This includes API-client path/token/ID-guard tests, component loading/error/retry/role-guard tests, Persian-date/status unit tests, member OTP-to-home integration with stubbed fetch, and existing auth/navigation regressions.
- Full Studio Vitest: **54 files passed, 2 skipped; 379 passed, 10 skipped; exit 0**. Details in [`member-account-studio-full-summary.txt`](member-account-studio-full-summary.txt). Existing JSDOM `getComputedStyle`, React `act(...)`, and Recharts warnings remain; skipped tests are not passes.
- Studio build/typecheck: **PASS**, `npm run build`, Vite `5.4.21`, `4048` modules; [`member-account-build.txt`](member-account-build.txt).
- Targeted ESLint on changed Studio files and Ruff on the two touched backend integration-test files: **PASS**; [`member-account-quality-gates.txt`](member-account-quality-gates.txt).
- Backend integration: `pytest -q tests/integration/test_m46_whoami.py tests/integration/test_ownership.py` → **9 passed, 1 Starlette/httpx deprecation warning**. SQLite/TestClient synthetic fixtures exercise the real route/service code: `/members/me` ID/role/constraints, own history response, and member A → member B denial. Log: [`member-account-backend-tests.txt`](member-account-backend-tests.txt).
- The frontend component and OTP/App flow used stubbed `fetch`; the backend tests used a separate TestClient. There was **no live Studio-to-running-backend end-to-end session** in this run.
- Documentation gate after the tracker/handoff update: **38 Markdown, 607 local links, 15 Mermaid**, handoff headings/README entrypoints/SVG XML passed. Final `git diff --check` and `git diff --cached --check` also passed; see [`member-account-docs-gate.txt`](member-account-docs-gate.txt).

## Acceptance still open

- Keep `MEM-01=PARTIAL/NOT_ACCEPTED`; shell/API-backed account progress is not full parent acceptance.
- This work overlaps account/history (`MEM-02` / canonical `PWA-31`), now recorded as `PARTIAL/NOT_ACCEPTED`; its canonical checkbox stays open and local fixtures/tests do not satisfy it. `MEM-03…MEM-16` and `STAFF-01` remain queued.
- No browser/physical Android or OS matrix, accessibility/screen-reader review, real backend account, real session/OTP delivery, reviewer sign-off or full PWA journey was accepted here. `INV-02/03`, `SEC-01`, `PWA-01`, release=`NO-GO` remain unchanged. PR #30 must not be merged.
- No commit or push was made. The pre-existing curated Git index and unrelated/private untracked files were not bulk-staged, cleaned, or rewritten as part of this slice.
