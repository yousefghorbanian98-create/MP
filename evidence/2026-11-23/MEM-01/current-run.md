# MEM-01 follow-up — member shell plus account/API slice

**Status: `PARTIAL / NOT_ACCEPTED`; canonical checkboxes remain open.** This is source and synthetic/local test evidence on a dirty worktree, not full product, browser, or release acceptance.

- Branch: `arena/5e0f64cf-mp`; baseline `HEAD`=`5828c94c9d875fa5a4c58740611bf800324649f8`. Studio/backend tests and product page source were modified after this baseline; it is not the tested source SHA and there is no clean-commit evidence.
- The earlier shell-only run is superseded for current behavior by this follow-up. Historical route/auth run outputs remain at [`focused-studio-tests.txt`](focused-studio-tests.txt) and [`headless-smoke.txt`](headless-smoke.txt).

## Product/source slice

- `/member` now contains an API-backed member account: authenticated `GET /api/v1/members/me`, then (only after a valid `role=member` profile) authenticated `GET /api/v1/members/{Member.id}/memberships`. The UI uses the server's member-profile ID, not `User.id`; no client-selected ID, local fixture fallback, or staff membership-summary table is used.
- Profile fields and constraints are rendered from the API. Known constraint codes have Persian labels; unknown/malformed values remain visible rather than silently becoming “none”. Membership history distinguishes active, expiring, expired, cancelled, and unknown; an empty list is explicitly not “expired”. Active rows are checked against the exact expiry instant.
- ISO timestamps carrying no timezone offset are interpreted as UTC (membership creation is UTC; SQLite may serialize a naive value), then formatted using the Persian calendar and `Asia/Tehran`.
- `useApi` supplies explicit loading, error/session-expired states and retry. A role mismatch or invalid profile ID fails closed before history is requested.
- `/member/today` deliberately remains a no-fabricated-program placeholder. Staff routes and navigation/auth behavior are unchanged by this account rendering.

## Verification on this worktree

- Focused Studio: **5 files / 33 tests passed**; includes API path/token/ID guard, account states, OTP-to-member-home integration with stubbed `fetch`, and navigation/auth regression. See [`member-account-focused-studio.txt`](member-account-focused-studio.txt).
- Full Studio: **54 files passed, 2 skipped; 379 passed, 10 skipped; exit 0**. Existing JSDOM `getComputedStyle`, React `act(...)` and Recharts warnings remain; skips are not passes. The tool output was warning-heavy and truncated; see the result summary [`member-account-studio-full-summary.txt`](member-account-studio-full-summary.txt).
- `npm run build`: **PASS**, `tsc -b` plus Vite `5.4.21`, `4048` modules; see [`member-account-build.txt`](member-account-build.txt).
- Changed-file ESLint, touched-test Ruff, final `git diff --check` and `git diff --cached --check`: **PASS**; see [`member-account-quality-gates.txt`](member-account-quality-gates.txt). Documentation gate after the handoff/tracker update: **38 Markdown, 607 local links, 15 Mermaid**; [`member-account-docs-gate.txt`](member-account-docs-gate.txt).
- Backend `test_m46_whoami.py` + `test_ownership.py`: **9 passed, 1 Starlette/httpx deprecation warning** using temporary SQLite/TestClient; own `/members/me` and membership response are asserted, and A→B history denial remains. See [`member-account-backend-tests.txt`](member-account-backend-tests.txt) and [`member-account-routes-and-ownership.md`](member-account-routes-and-ownership.md).

## Acceptance boundaries

- The UI-level tests use stubbed `fetch`; backend tests use a separate synthetic TestClient. There was no live Studio-to-running-backend user session in this run.
- No Chromium/browser, physical Android, OS/device matrix, manual screen-reader/contrast review, real OTP/SMS, reviewer sign-off, or full PWA journey was run. The prior Chromium attempt stopped before page creation because `libnspr4.so` was missing; that is not a product pass/fail.
- `MEM-01=PARTIAL/NOT_ACCEPTED` remains open. This implementation overlaps account/history `MEM-02` / canonical `PWA-31`, now recorded as `PARTIAL/NOT_ACCEPTED`; this run does not accept it or close a checkbox. `MEM-03…MEM-16`, then `STAFF-01`, remain in sequence.
- `INV-02/03` and `SEC-01` remain `PARTIAL/NOT_ACCEPTED`; `PWA-01=PROPOSED/NOT_RUN`; release remains `NO-GO`. PR #30 must not be merged. No commit/push was made. Existing private receipts and unrelated untracked paths were not bulk-staged or cleaned.
