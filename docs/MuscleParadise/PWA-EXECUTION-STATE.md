# وضعیت اجرای PWA — دفتر چرخه‌ها و شواهد

CURRENT_BRANCH=arena/3c08bfbd-mp
MAIN_HEAD=ebebef3ad153277f0223c2011efc4f9a9c855654 (PR #30 MERGED 2026-11-27T16:49:20Z)
PR30=MERGED — the older OPEN/DRAFT statements below are history, not current state
BRANCH_BASE=ebebef3ad153277f0223c2011efc4f9a9c855654
LAST_KNOWN_EVIDENCE=evidence/2026-11-27/MEM-03/current-run.md و فایل‌های همین پوشه: digest-gate-before.txt، secret-scan-redacted.txt، guard-mutation-test.txt، gitleaks-policy-test.txt (local worktree on arena/3c08bfbd-mp; local test/live-contract passes only); evidence/2026-11-23/MEM-01/member-account-slice.md, evidence/2026-11-27/INV-02-v2, INV-03-v2, INV-02-v3, INV-03-v3, CROSSWALK-v2-v3-comparison.md, SEC-01/current-run.md, WEB-02…11/browser-*.txt, WEB-browser-run-summary.md are separate/historical

> **نوع سند:** دفتر اجراییِ افزایشی؛ نه ADR، نه مرجع مستقل برای تعریف acceptance، و نه ادعای QA/release. شناسه‌ها و معیارهای هر کارت از tracker و backlog canonical پیروی می‌کنند.
> **تاریخ مرجع:** ۲۰۲۶-۱۱-۲۳ UTC. این تاریخ با timestampهای GitHub آینده‌نما که در handoff ثبت شده‌اند تعارض دارد؛ آن تعارض حل‌نشده باقی می‌ماند.

## منابع canonical و تقدم

- **تصمیم محصول:** [ADR-006](adr/006-shared-react-pwa.md) و [ADR-007](adr/007-pwa-primary-release.md)، همراه [دفتر تصمیم‌های مالک](OWNER-DECISIONS.md).
- **پذیرش و ترتیب کارت‌ها:** [TODO اجرایی انتشار PWA](TODO-PWA-RELEASE-2026-11-23.fa.md) و [backlog canonical پنجاه parent](TODO-2026-11-16.md#pwa-ui-ux-full-backlog-2026-11-23).
- **خلاصهٔ نشست:** [SESSION_HANDOFF](SESSION_HANDOFF.md)؛ این فایل وضعیت بین چرخه‌ها را ثبت می‌کند و جایگزین آن دو صف نمی‌شود.
- **شواهد:** مسیرهای پالایش‌شدهٔ `../../evidence/<تاریخ-مرجع>/<ID>/`؛ تاریخ مرجع پوشه را با marker زمان واقعی اجرا (و محدودیت‌های آن) جدا ثبت کنید؛ هر نتیجه فقط به همان command، toolchain، checkout و SHA/worktree fingerprint تعلق دارد.

در تعارض، تصمیم scope با ADR/تصمیم مالک، متن acceptance با کارت canonical، رفتار با کد و تست همان مسیر، و status اجرایی با آخرین شاهد پالایش‌شده تعیین می‌شود. Snapshotهای تاریخی، دیاگرام‌ها، screenshotها، artifact package، mock، skipped test و CI روی SHA دیگر acceptance محصول را ثابت نمی‌کنند.

## Latest continuation — MEM-04 / PWA-33 today program on the real contract

```text
CURRENT_BRANCH=arena/3c08bfbd-mp
STATE_LAST_UPDATED=2026-11-27T19:05:00Z
MEM-04/PWA-33=PARTIAL/NOT_ACCEPTED (canonical checkbox open)
MEM04_ROUTE_ACCESS=member=yes — api/routes.json:3369-3385 · modules/programs/router.py:31-37 · app/security/ownership.py:23-29
SURFACE=/member/today now renders MemberTodayProgram on GET /programs/member/{id} + /readiness
NUMBERS=هر عدد یک منبع مکتوب دارد؛ هیچ محاسبه‌ای در کلاینت نیست؛ KPI/کالری/ادعای پزشکی ساخته نشد
EMPTY_STATE=بدون برنامهٔ approved → پیام تهی + شمارش در انتظار تأیید؛ readiness=null → فقط reason سرور
AUTHORIZATION_PROOF=۳ تست تازه: عضو A روی /programs/member/B، /readiness، /volume و /programs/{id} → 403
LOCAL_GATES=Studio ۴ تست تازه؛ کل ۳۹۹ pass/۱۵ skip؛ tsc/eslint/build پاک؛ backend ۹ pass؛ interaction map pass
CI=پاس روی tip 27ef138 (۱۲ check، شامل secret-scan و گیت digest در job docs)؛ REVIEWER/DEVICE=NOT_RUN؛ release=NO-GO
```

- قرارداد از قبل وجود داشت و چیزی ساخته نشد: `GET /api/v1/programs/member/{member_id}`، `/readiness`، `/volume` و `GET /api/v1/programs/{program_id}`.
- دو شکاف واقعی قرارداد که UI به‌جای حدس زدن، صریح می‌نویسد: برنامه **شمارهٔ نسخهٔ عددی** و **تاریخ شروع/پایان** ندارد؛ تنها نسخه `engine_version` و تنها تاریخ `approved_at` است. پس «امروز» از روی شمارهٔ هفته حدس زده نمی‌شود.
- `safety_flags = "{}"` یعنی غربالگری انجام نشده، نه «بی‌خطر»؛ همین جمله روی صفحه است و برنامهٔ با فلگ غیرخالی هشدار «پیش از اجرا با مربی مرور کنید» می‌گیرد.
- شاهد: [`MEM-04 current run`](../../evidence/2026-11-27/MEM-04/current-run.md) و [`route-access`](../../evidence/2026-11-27/MEM-04/route-access.txt).

## Latest continuation — MEM-03 / PWA-32 phone change, device sessions and late-response guard

```text
CURRENT_BRANCH=arena/3c08bfbd-mp
BRANCH_BASE=ebebef3ad153277f0223c2011efc4f9a9c855654 (merged PR #30)
STATE_LAST_UPDATED=2026-11-27T17:10:00Z
EVIDENCE_DATE_DIRS=2026-11-23, 2026-11-27
MEM-03/PWA-32=PARTIAL/NOT_ACCEPTED (canonical checkbox open)
PRODUCT_SURFACE=member home now exposes phone change, own device sessions and logout-all
LATE_RESPONSE_GUARD=covered by unit tests; a late confirm reply can no longer clear/revoke another account's session
LIVE_PHONE_CHANGE_CONTRACT=PASS locally: 1 file / 1 test against synthetic Uvicorn + SQLite with DevSmsProvider echo
CI_WORKFLOW=updated (dev-only OTP echo for the synthetic job + new live phone-change/logout-all step)
PUSHED=3170b6a80029102dafbc28128f2997ee0df5b3f7 (run 46043582882: seven green + secret-scan red); earlier e22d8db, a5e4517, 7deb122
CI_E22D8DB=seven jobs success (studio, backend, docs, live-contract, e2e-api, client-flutter, client-pinned); secret-scan failed
CI_A5E4517=same result; one client-pinned attempt on e22d8db failed in the Android compile step and passed on rerun (transient infra)
SECRET_SCAN=RED/REMEDIATED-IN-CODE (run 46044835110 @d71dbe0): 5 findings، همه `generic-api-key` روی digestهای source در crosswalk JSON؛ رفع با دو مسیر مجاز — پیشوند `sha256:` در generator و ۱۰ خط fingerprint دقیق؛ نتیجهٔ CI روی SHA بعدی هنوز دیده نشده
CROSSWALK_DIGEST_GATE=NEW: scripts/verify_crosswalk_digests.py — در job `docs`؛ پیش از بازتولید روی d71dbe0 قرمز بود (۶ خطا در ۲ artifact)، پس از بازتولید روی درخت تمیز در 9ea9a24 **PASS** (۲ artifact، ۶ منبع، tracked_dirty=false)
CROSSWALK_STALE=v1 artifactها به `*.STALE.{md,json}` تغییر نام دادند (git mv؛ محتوا دست‌نخورده) چون v1 byte-for-byte بازتولیدشدنی نیست
FINISH_PHONE_CHANGE_TEST=ADDED+PASS (3 tests)؛ با mutation تأیید شد که invariant را می‌گیرد
ADR_008=PROPOSED (retention/redaction for phone_change_challenges); owner must set the window
PR31=DRAFT/open، merge ممنوع
REAL_SMS/DEVICE/BROWSER/NOT_RUN; release=NO-GO
```

- Scope review first: the backend contract was already complete (`/auth/phone-change/*`, `/auth/sessions`, `/auth/logout-all`), so no endpoint was invented. The real gaps were member-facing (no phone-change entry or device management in `MemberShell`, and `logout-all` had no UI consumer) plus one untested client race.
- The race: a successful `confirm` reply arriving after another account signed in on the same browser used to call `signOut()`, which cleared that newer session and revoked its refresh token server-side. `PhoneChangeDialog` now captures a `SessionGuard` (account id from the token `sub`, which is not an authorization decision) before sending `confirm`; `clearSessionForAccount` returns `ended`, `different-account`, or `signed-out`, and only `ended` touches storage.
- Evidence: [`MEM-03 current run`](../../evidence/2026-11-27/MEM-03/current-run.md) with raw files `studio-focused-tests.txt` (6 files / 42 tests), `studio-full-tests.txt` (55 files pass / 4 skip; 392 pass / 15 skip), `studio-gates.txt` (tsc/eslint/build), `backend-focused-tests.txt` (18 passed), `live-contract-phone-change.raw.txt`, `api-request-log.txt`, `db-state-after-run.txt`.
- Limits: every HTTP result came from a local synthetic API with the development SMS provider; no real SMS, device, browser, screen-reader or human review was performed, and CI has not run for this branch. The live suite mutates the synthetic fixture's login number, so it must be the last consumer of that account in a job.
- CI on `e22d8db` (and on `a5e4517`): seven jobs green, including `live-contract`, which executed the new phone-change/logout-all step; `secret-scan` was red on this branch **and equally red on main at `ebebef3`** (run `46036816362`). The five hits are 64-hex `source_digests` values in the merged crosswalk evidence JSON, i.e. file SHA-256 digests, not credentials. Raw metadata: [`pr-ci-a5e4517.txt`](../../evidence/2026-11-27/MEM-03/pr-ci-a5e4517.txt).
- **Secret-scan fix (owner-approved, two allowed routes only):** (i) `scripts/crosswalk_v2.py` now writes every source digest as `sha256:<hex>`, so the `generic-api-key` key/value pattern no longer matches future artifacts; (ii) `.gitleaksignore` gained exactly **five** exact fingerprint lines for commit `ebebef3…`; the five `6593cb4b…` lines for the same findings already existed because a fingerprint is commit-scoped — both sets are anchored to [`secret-scan-redacted.txt`](../../evidence/2026-11-27/MEM-03/secret-scan-redacted.txt). Nothing was allowlisted by rule or path. The CI job now prints `Fingerprint` only and uploads `/tmp/gitleaks-findings.json` as an artifact, so the next failure is readable without log download. Only `File`/`RuleID`/`Line`/`Commit`/`Fingerprint` are ever published.
- **Digest gate (new):** `scripts/verify_crosswalk_digests.py` runs in the `docs` job and fails when a crosswalk artifact's recorded digest differs from the current source file, or when it was generated on a dirty tree. On `d71dbe0` it is **red** — `INV-02` and `INV-03` are stale on two sources (`api.ts`, `navigation.ts`) and carry `tracked_dirty=true`. Widening vs the owner's one-file report is recorded in [`digest-gate-before.txt`](../../evidence/2026-11-27/MEM-03/digest-gate-before.txt). Regenerated on a clean tree at `9ea9a24` (the fix commit): both artifacts now record `tracked_dirty=false`, `untracked=0` and `sha256:` digests, and the gate prints `Crosswalk digest gate passed: 2 artifact`. Note the generator refuses a dirty tracked tree with `exit 4`, so the two artifacts were generated into `/tmp/cw/*` on one clean tree and copied in — writing the first artifact in place would dirty the tree and block the second run.
- **v1 artifacts are now `*.STALE.*`:** the four `INV-02-v1`/`INV-03-v1` files were renamed with `git mv` (content byte-identical) because no v1 generator exists in the repo, so they can never be reproduced byte-for-byte; the gate therefore ignores `*.STALE.json`, and both `review.md` files say so.
- **New guard test:** three tests in `mp-app/studio/tests/session.test.ts` cover `finishPhoneChange`'s decision point — `different-account` (storage untouched, no `/auth/logout` call), `ended` (own refresh token revoked), `signed-out`. A deliberate mutation that hoists `logoutSession` above the guard fails two of them, so the test is not vacuous: [`guard-mutation-test.txt`](../../evidence/2026-11-27/MEM-03/guard-mutation-test.txt). Studio evidence this round: 24/24 in that file, full run 55 files passed / 4 skipped (395 passed / 15 skipped), `tsc -b`, `eslint .`, `npm run build` clean.
- **STATE rule (no exception):** any artifact whose digest/HEAD differs from current HEAD is either regenerated on a clean tree or renamed with `STALE`; digests are never produced from a dirty tree.
- Retention of the old/new phone numbers and code hashes inside `phone_change_challenges` is now an explicit [ADR-008 proposal](adr/008-phone-change-challenge-retention.md) (`Proposed`, not implemented); the retention window stays an owner decision.
- `MEM-01`, `MEM-02`/`PWA-30/31` stay `PARTIAL/NOT_ACCEPTED`; `INV-02/03`, `SEC-01` remain partial; `PWA-01=PROPOSED/NOT_RUN`; release=`NO-GO`. Next: run CI on this branch, then judge MEM-04 only from code and evidence on that SHA.

## Latest continuation — MEM-01 live member-account contract and identity-negative

```text
CURRENT_BRANCH=arena/5e0f64cf-mp
BASE_REMOTE_HEAD=9cdd96554108d8438fe906a82b233d68e21e0fd8
STATE_LAST_UPDATED=2026-11-27T15:41:18Z
EVIDENCE_DATE_DIRS=2026-11-23, 2026-11-27
NOTE: reference date 2026-11-23 is the program start date, not the STATE update date.
MEM-01=PARTIAL/NOT_ACCEPTED (canonical checkbox open)
LIVE_MEMBER_CONTRACT=PASS locally: 1 file / 4 tests / 0 skipped against synthetic local Uvicorn + SQLite
IDENTITY_NEGATIVE=PASS locally: 3 TestClient tests; User.id substitution and B-member read denied
TODAY_EMPTY_STATE_TEST=PASS (honest no-mock placeholder and non-member denial only)
CI_WORKFLOW=updated to seed isolated A/B members and execute the new live suite with a member fixture token
PUSH/REMOTE_CI=not yet verified for this follow-up at this record timestamp
PR30=OPEN/DRAFT/unmerged; release=NO-GO
INDEX_GUARD=60 unrelated pre-existing staged paths preserved; no receipt/untracked paths touched
```

- `fetchMe` and `fetchMemberMemberships` were already present in `src/lib/api.ts`; that file required no product change. The new live test checks `/members/me`, role/token identity, exact self-profile field allowlist, member history via server `Member.id`, rejection of the wrong `User.id`, unknown status, and the 23:30 UTC `Asia/Tehran` Persian-calendar boundary. Synthetic raw results: [`live-contract-member.txt`](../../evidence/2026-11-27/MEM-01/live-contract-member.txt) and [`identity-negative.txt`](../../evidence/2026-11-27/MEM-01/identity-negative.txt).
- Studio lint passed; the updated `memberAccountPage.test.tsx` passed 6/6, including the new honest no-mock `/member/today` state and non-member `AccessDenied` route test. The live member suite passed 4/4 against local Uvicorn + temporary SQLite; backend focused identity suite passed 3/3 (one existing Starlette/httpx deprecation warning). Touched-file Ruff/format and workflow YAML/shell syntax passed. Local docs gate passed 38 Markdown / 611 links / 15 Mermaid; project guide and interaction map passed (32 surfaces / 163 routes / 0 drift); `git diff --check` passed. Always verify push and GitHub CI against the exact final branch SHA; local passes do not imply remote CI.
- `/member/today` remains the existing static no-fabrication placeholder, not a data-backed page. Its test ensures no sample program or unconnected program API is used. There is no configured support destination or Today API in this slice, so a support link and API-error/retry UI remain unimplemented; this small test is not acceptance of the Today flow.
- Preserve `MEM-01` and `PWA-30/31` as `PARTIAL/NOT_ACCEPTED`; `INV-02/03` and `SEC-01` remain partial, `PWA-01=PROPOSED/NOT_RUN`, release=`NO-GO`. PR #30 must remain draft/unmerged. Next requested work: begin MEM-03 phone-change/OTP scope review; no such product flow is claimed complete here.

## Previous continuation snapshot — MEM-01 / member account API slice (reference date: 2026-11-23 UTC; before live-identity follow-up)

```text
CURRENT_BRANCH=arena/5e0f64cf-mp
HEAD_BEFORE_DIRTY_SOURCE_PATCH=5828c94c9d875fa5a4c58740611bf800324649f8
MEM-01=PARTIAL/NOT_ACCEPTED (canonical checkbox remains open)
MEM-02/PWA-31=local account/history implementation + synthetic evidence; PARTIAL/NOT_ACCEPTED; canonical checkbox stays open
MEM-03…MEM-16=NOT_STARTED in this slice
CODE_OR_TEST_CHANGED_THIS_CYCLE=yes
CODE_CHANGED=mp-app/studio/src/App.tsx; src/lib/api.ts; src/lib/memberAccount.ts; src/pages/MemberAccount.tsx
TEST_CHANGED=Studio api/auth/navigation/member-account tests; backend test_m46_whoami.py and test_ownership.py
BROWSER_AVAILABLE=no — libnspr4.so/libnss3.so missing (apt/npm verified)
BROWSER_ALTERNATIVE=live-contract (CI job) + backend TestClient flow
LIVE_CONTRACT=PASS — 1 file; 9 passed; local synthetic API; raw log evidence/2026-11-27/MEM-01/live-contract.raw.txt
PENDING_PUSH=no
PUSHED=7833508b2c8dde4d7cb3f86754af71aa6d47815c روی arena/5e0f64cf-mp (remote branch and evidence API verified)
MEM01_COMMIT_ALLOWLISTED_COUNT=40
STAGE_SLICE_COMMIT_ALLOWLISTED_COUNT=10
INTERACTION_MAP_FIX_ALLOWLISTED_COUNT=10
INDEX_ALLOWLISTED_COUNT=0 (no changed path from the allowlists remains staged; 60 unrelated staged paths remain untouched)
PR30_CHECKS_E06=FAIL: backend + Documentation links/handoff; failure report retained
PR30_CHECKS_7833508=PASS: all main and supplemental checks; e2e-api passed
INTERACTION_MAP_LOCAL=PASS after regeneration — 32 surfaces; 163 routes; 0 drift; 6 existing untested surfaces
BACKEND_CI_LOCAL_REPRO=PASS — 1338 passed; 2 skipped; 2 warnings; 91% total; GitHub failure details unavailable (EOF)
BROWSER_RUN_THIS_CYCLE=no — no Chromium/browser/device assertions in this cycle.
LOOP_STALLED=no
```

- **Implementation:** `/member` home now renders a data-backed account slice: authenticated `GET /members/me`, followed only for a valid `role=member` identity by `GET /members/{Member.id}/memberships`. It displays the server profile/constraints and own membership history; it does not use a client-selected ID or staff summary. Unknown status/data remain unknown, empty history is not “expired”, and naive backend ISO datetimes are treated as UTC before Persian-calendar/`Asia/Tehran` formatting. Loading/error/session-expiry and retry are explicit. `/member/today` remains a no-fabricated-program placeholder; shell/session navigation and staff role gate remain in place.
- **Synthetic Studio coverage:** focused run across `memberAccount.test.ts`, `memberAccountPage.test.tsx`, `api.test.ts`, `authFlow.test.tsx`, and `navigation.test.tsx`: **5 files / 33 passed** ([result](../../evidence/2026-11-23/MEM-01/member-account-focused-studio.txt)). It includes the member OTP-to-home screen with stubbed `fetch`, server `Member.id` rather than `User.id`, bearer header, no history request on invalid identity/role, loading, retry after 503, empty history, expiry/status and timezone cases. Full Studio: **54 files passed, 2 skipped; 379 passed, 10 skipped**; existing JSDOM `getComputedStyle`, React `act` and Recharts warnings persist, skips are not passes ([summary](../../evidence/2026-11-23/MEM-01/member-account-studio-full-summary.txt)).
- **Backend ownership / Studio / live contract:** targeted FastAPI TestClient tests with temporary SQLite cover `/members/me` ID/role/constraints, own membership response, and member A→B denial: **9 passed, 1 Starlette/httpx deprecation warning** ([current log](../../evidence/2026-11-27/MEM-01/backend-focused-tests.txt); earlier evidence in `2026-11-23/MEM-01/`). Studio focused account/auth/API/navigation suite reran at **5 files / 33 passed** ([log](../../evidence/2026-11-27/MEM-01/studio-focused-tests.txt)). Existing `liveContract.test.ts` ran against local Uvicorn + synthetic temporary SQLite and passed **1 file / 9 tests**, exit 0 ([raw](../../evidence/2026-11-27/MEM-01/live-contract.raw.txt)); synthetic fixture token value was not recorded. This validates existing API contracts, not the new account page's `/members/me` → owner-scoped history flow. Studio build (Vite 5.4.21, 4048 modules) and selected ESLint/Ruff passed in the earlier source run; current evidence: [`MEM-01 account slice`](../../evidence/2026-11-23/MEM-01/member-account-slice.md) and [`2026-11-27 live-contract run`](../../evidence/2026-11-27/MEM-01/current-run.md).
- **Browser/build limits:** `BROWSER_AVAILABLE=no — libnspr4.so/libnss3.so missing (apt/npm verified)`. No headless browser/device run in this follow-up; no real user account/data, SMS/OTP delivery, physical Android/OS, manual screen-reader/contrast review, independent reviewer or full member journey was accepted. Browser alternative: existing live-contract CI job + local synthetic API and backend TestClient flow.
- **Documentation / evidence:** docs gate after the final handoff/evidence update passed (**38 Markdown / 609 local links / 15 Mermaid**); current run and CI diagnostics are in `../../evidence/2026-11-27/MEM-01/`.
- **Evidence / release:** source was tested from baseline HEAD `5828c94c9d875fa5a4c58740611bf800324649f8`; MEM-01 commit `a7aa5b715de3da021934152b75e17ef67f6f19a5`, stage-slice helper commit `cdc989b198737e1d2235eaf570fb023e9306e264`, map/CI diagnostic commit `1afab65839b325b6a2013443f4d211f899e58c87`, and final status record `7833508b2c8dde4d7cb3f86754af71aa6d47815c` were pushed. GitHub API confirmed 7833508 as branch head and the evidence directory (15 entries). `gh pr checks 30` on e06a716 first failed backend/docs; after map refresh, `gh pr checks 30 --watch --interval 10` on 7833508 exited 0 and all main plus supplemental checks passed, including backend, docs and `e2e-api`. The map gate passes locally (32 surfaces/163 routes/0 drift/6 baseline untested); the remote backend log on the earlier failed run was unavailable (EOF), while local `coverage_run.sh` passed 1338 tests, 2 skipped, 2 warnings, 91% total. `PENDING_PUSH=no`; 60 unrelated staged entries remain untouched. Keep `MEM-01=PARTIAL/NOT_ACCEPTED`, canonical `PWA-30/31=PARTIAL/NOT_ACCEPTED`, `INV-02/03=PARTIAL/NOT_ACCEPTED`, `SEC-01=PARTIAL/NOT_ACCEPTED`, `PWA-01=PROPOSED/NOT_RUN`, release=`NO-GO`; do not check canonical boxes or merge PR #30. Preserve private receipts and unrelated files; no bulk staging.

## Historical run snapshot — headless WEB + SEC-01 + crosswalk delta (مرجع Arena: ۲۰۲۶-۱۱-۲۳ UTC)

```text
CURRENT_BRANCH=arena/5e0f64cf-mp
HEAD_AT_BROWSER_BUILD_AND_TESTS=5828c94c9d875fa5a4c58740611bf800324649f8
BROWSER_AVAILABLE=yes (headless Chromium only; no physical OS/device assertion)
WEB_CHECKED_BY_BROWSER=WEB-02…WEB-11 (separate evidence files; WEB-11 API backend unavailable)
CODE_OR_TEST_CHANGED_THIS_CYCLE=yes
CODE_CHANGED=scripts/crosswalk_v2.py
TEST_CHANGED=scripts/test_crosswalk_v2.py; mp-app/backend/tests/integration/test_ownership.py; mp-app/backend/tests/integration/test_phase5_admin_permissions.py; mp-app/backend/tests/integration/test_qf10_period_report.py
LOOP_STALLED=no
```

- **Build/browser:** `npm run build` (`tsc -b && vite build`) passed on the real Studio source tree; Vite 5.4.21 transformed 4046 modules. Headless Chromium `153.0.8010.0`, Playwright Core `1.65.1`, axe-core `4.14.1`. Browser results are under [`WEB-02…11`](../../evidence/2026-11-27/WEB-browser-run-summary.md), with individual `browser-<view>.txt` files. Authenticated-page data was synthetic; WEB-11 directly hit the local Vite preview.
- **Browser findings:** WEB-02 deep-link redirect/reload and history were observed; WEB-03 and WEB-05 have 569px document width at 390px viewport (mobile overflow); WEB-04 had zero axe violations, but `color-contrast` severity `serious` remained incomplete on 5 login / 43 analytics nodes; WEB-06 used reduced-motion emulation; WEB-07 Space selected `هفته`; WEB-08 root-scope worker/manifest/icon fetches passed (OS install not asserted); WEB-09 synthetic A/B found no `/api` or private marker in Cache Storage and logout cleared tokens; WEB-10 a same-URL `/sw.js` update waited, exposed the update button, activated and reloaded; WEB-11 deep-link returned SPA shell `200`, while `/api/v1/members/me` returned `500 text/plain`/empty due proxy `ECONNREFUSED 127.0.0.1:8000`. Full roll-up: `evidence/2026-11-27/WEB-browser-run-summary.md`; build log: `studio-build.txt`.
- **SEC-01 focused HTTP tests:** 26 passed, 0 failed, one Starlette/httpx deprecation warning. The slice includes exact A→B `403`, A→A positive `200`, new anonymous `401` checks for sensitive routes, and finance period grant expiry/revocation (`403 permission_required`; active grant `200`) with synthetic DB actors. This is not the full backend suite or all route×role×resource coverage. [`current-run.md`](../../evidence/2026-11-27/SEC-01/current-run.md).
- **Crosswalk same-HEAD comparison:** v2 member `16 PARTIAL_REVIEW / 1 GAP`, staff `12 PARTIAL_REVIEW`; 82 Studio API call-sites, 24 dynamic paths, 0 current manifest-shape misses. Same-file import mapping: 15 page records (`member=1`, `staff=12`, `shared=2`); edges `0/69/6`, ratios `0.0/5.75/3.0`. v3 member `13 PARTIAL_REVIEW / 4 GAP` (17 Flutter features, 141 server routes, 47 Studio paths); staff `11 PARTIAL_REVIEW / 1 GAP` (12/12 pages routed). The changed v2 script has four synthetic regression tests; all pass, including a no-route dynamic path becoming `DYNAMIC_UNCOVERED`. Full counts/deltas: [`crosswalk comparison`](../../evidence/2026-11-27/CROSSWALK-v2-v3-comparison.md).
- **Validation:** `scripts/test_crosswalk_v2.py` 4/4 ([raw](../../evidence/2026-11-27/crosswalk-v2-unittest.txt)); focused backend tests 26/26 ([raw](../../evidence/2026-11-27/SEC-01/pytest-focused.txt)); Studio Vitest 52 files passed / 2 skipped, 362 passed / 10 skipped; build passed (`studio-build.txt`); Ruff touched paths and `git diff --check` passed ([Ruff](../../evidence/2026-11-27/ruff-touched-python.txt)); docs gate 38 Markdown / 606 links / 15 Mermaid passed ([log](../../evidence/2026-11-27/docs-gate.txt)). Existing JSDOM/React `act`/Recharts and one backend deprecation warning remain; skips are not PASS.
- **Status / guardrails:** `PWA-01=PROPOSED/NOT_RUN`, `SEC-01=PARTIAL/NOT_ACCEPTED`, INV-02/03 remain partial/non-accepted, all relevant checkboxes stay open, release=`NO-GO`. Current repository HEAD during runs was `5828c94c9d875fa5a4c58740611bf800324649f8`; the worktree was dirty, so this is not clean-commit evidence. Commit/push are pending at this note; do not merge PR #30. Preserve pre-existing untracked files/receipts. After this report continue MEM-01…16 without routine confirmation.

## Historical snapshot — INV-02/03 v2 and SEC-01 matrix (۲۰۲۶-۱۱-۲۷ UTC)

- **شاخه و همگام‌سازی:** `CURRENT_BRANCH=arena/5e0f64cf-mp`; `origin/main=352781043ad2ba202d8b3b459df1ce7e3d914ef7`. پس از fetch، `git merge --no-edit origin/main` پاسخ `Already up to date` داد؛ تعارض صفر و main از قبل در ancestry شاخه بود. STATE checkpoint `f06f2a95305082e01e33b157396f0dfc0128613d` و package evidence `6593cb4bc7f42c9ada4ca7e499fe60124bf00703` روی همان شاخه push شدند. PR #29 با squash merge ادغام شد؛ عدم ancestry commitهای شاخه به‌تنهایی به معنی حذف محتوا از main نیست. PR #30 draft ساخته شد؛ گزارش checkهای SHA=`6593cb4...` ثبت شده و بعد از commit همین گزارش، checkها فقط به همان SHA پیشین تعلق دارند. تاریخچه rewrite نشد.
- **INV-02/03 v2:** [crosswalkهای خام](../../evidence/2026-11-27/INV-02/member-capability-crosswalk.md) و [کارکنان](../../evidence/2026-11-27/INV-03/staff-page-crosswalk.md) با `scripts/crosswalk_v2.py` روی SHA=`f06f2a95305082e01e33b157396f0dfc0128613d` اجرا شدند؛ هر دو worktree با tracked docs dirty و untracked بوده، product tracked source تغییر نداشت. v1 byte-for-byte در `INV-02-v1/` و `INV-03-v1/` حفظ شد. شمارش‌ها: member `PARTIAL_REVIEW=14/GAP=3`; staff `PARTIAL_REVIEW=12/GAP=0`.
- **حد v2:** Analytics در `adminApi.ts` و alias `ALL_STAFF` اکنون در output دیده می‌شوند. ولی `dynamic_sites=0` و هیچ `DYNAMIC_UNCOVERED` تولید نشد؛ regex در template interpolation قطع می‌شود و check-in نمونهٔ prompt در source فعلی وجود ندارد (Flutter route در scope scanner TS نیست). مرور دستی فقط در reviewهای جدا ثبت شد؛ rawها patch نشدند. هر دو crosswalk `PARTIAL/NOT_ACCEPTED` می‌مانند؛ تفکیک consumer عضو از پنل کارکنان دستی است؛ اشارهٔ تستی، اجرای تست یا مجوز نیست.
- **SEC-01 matrix:** [`rbac-matrix.txt`](../../evidence/2026-11-27/SEC-01/rbac-matrix.txt) همهٔ `163` operation / `141` path در `routes.json` را با شش نقش در تابع `security.rbac.enforce` سنجید؛ `978` تصمیم policy در همان SHA=`f06f2a9...`. این جدول static policy است، نه HTTP پاسخ، grant/owner scope یا anonymous matrix.
- **SEC-01 negative و full pytest:** سه TestClient integration تست منفی عضو A→B در `members`, `assessments`, `payments`, `chat`, `checkin` را پاس کردند (`3 passed/0 failed`, یک warning). کل suite در `mp-app/backend` روی `claimed_sha=tested_sha=f06f2a95305082e01e33b157396f0dfc0128613d` اجرا شد: `1336 passed, 2 skipped, 2 warnings`, exit `0`. گزارش‌ها در [`SEC-01`](../../evidence/2026-11-27/SEC-01/role-server-slice-v2.md) هستند. SEC-01 فقط `PARTIAL` است؛ ماتریس static جای test HTTP برای تمام route×role/resource را نمی‌گیرد و checkbox باز می‌ماند.
- **سابقه و گاردریل:** slice قدیمی `90 passed/2 warnings` در `evidence/2026-11-23/SEC-01/` مربوط به اجرای ثبت‌شده در `2026-11-23 UTC` روی SHA=`352781043ad2ba202d8b3b459df1ce7e3d914ef7` است؛ آن شاهد از run فعلی جداست. هیچ role/grant/API/DB/Flutter/native source تغییر نکرد. `PWA-01=PROPOSED/NOT_RUN`, checkboxهای INV/SEC باز و release `NO-GO` هستند.
- **گیت‌های مستندات:** `python3 scripts/docs_gate.py` پس از ثبت و stage خروجی‌ها PASS شد: ۳۸ Markdown، ۶۰۶ local links، ۱۵ Mermaid؛ `git diff --check` و `git diff --cached --check` نیز PASS. transcript در `evidence/2026-11-27/SEC-01/docs-gate.txt` و `diff-check.txt` است. این گیت‌ها فقط کیفیت مستندات را می‌سنجند، نه acceptance محصول.
- **PR #30 و CI:** آخرین head آزموده‌شده هنگام ثبت این snapshot=`3e49232d2118e8212a4d1ddea20fc982da5cd13a`. `gh pr checks 30` روی همان SHA `12 pass / 0 fail / 0 pending` داد؛ `mp-ci` pull_request=`45998409658`, push=`45998396424`, و `pwa00-doc-quality`=`45998409713` همگی `completed/success`. Gitleaks تست fixture synthetic و full-history scan هر دو pass؛ PWA-00 patch/apply/cmp نیز pass. CI اولیه روی `6593cb4...` `10/2` بود و علت/اصلاح مستند در `evidence/2026-11-27/SEC-01/pr-30-checks-review.md`; خلاصهٔ اجرا در `pr-30-checks-3e49232.txt`. تغییرات snapshot بعد از این head evidence/docs-only هستند و CI برای commit بعدی باید جداگانه بررسی شود؛ PR draft و ادغام‌نشده است.
- **گام بعدی:** مرور source/unit برای `WEB-01…WEB-11` ثبت شد، اما هیچ parent پذیرفته نشده و checkboxها بازند. تکمیل فقط با browser/OS/device و review مستقل برای معیارهای کارت ممکن است؛ تا نبود آن‌ها runtime gates=`BLOCKED/NOT_RUN` می‌مانند. صرف green CI status را بالا نمی‌برد؛ `PWA-01=PROPOSED/NOT_RUN`, crosswalkها `PARTIAL/NOT_ACCEPTED`, SEC-01 حداکثر `PARTIAL` و release=`NO-GO` باقی می‌مانند.

## Snapshot پیشین — بازنشانی اجرا پس از بررسی remote (۲۰۲۶-۱۱-۲۳ UTC)

- **شاخه/گراف مشاهده‌شده:** شاخهٔ فعال `arena/5e0f64cf-mp`؛ `HEAD=e0ae95f48bf8451bd59b972a92c55fed404e6a92`؛ `origin/arena/5e0f64cf-mp=3f26e1d6ea05920a23236b368abd4c4ee0580799`؛ `origin/main=352781043ad2ba202d8b3b459df1ce7e3d914ef7`. HEAD در هیچ remote-tracking ref مشاهده‌شده نیست؛ tip شاخهٔ مجاز و `origin/main` هر دو ancestor آن هستند؛ والدهای HEAD همان دو tip و tree آن عیناً با tree `origin/main` برابر است. این فقط اثبات ancestry/tree است، نه remote witness برای مستندات/evidence محلی.
- **Worktree تازه:** ۲۴ tracked تغییر، همه README/docs؛ index خالی؛ ۳۰۹ untracked پیش از افزودن snapshot جاری و ۳۱۰ شامل همان snapshot؛ صفر tracked diff زیر `mp-app/`. مسیرهای untracked، به‌ویژه receiptها، عمداً در transcript منتشر نشده‌اند و دست‌نخورده می‌مانند. fingerprint و شمارش sanitized در [`INV-01/current-snapshot.txt`](../../evidence/2026-11-23/INV-01/current-snapshot.txt).
- **معنای «STATE از صفر»:** این چرخه statusهای قبلی را خودکار به ارث نمی‌برد. محتوای موجود فقط در workspace محلی است؛ هیچ فایل/شاهدی از روی حافظه بازسازی یا به‌عنوان شاهد remote معرفی نمی‌شود. ثبت‌های قبلی حفظ‌اند، اما `DONE/PASS` مستنداتی هم تا اجرای دوبارهٔ gate مربوط در این چرخه فقط سابقه‌اند. checkboxهای canonical دست‌نخورده می‌مانند؛ status محصول/release ارتقا نمی‌یابد. cursor جاری از اولین مورد باز پس از snapshot، یعنی `INV-02`، ادامه می‌دهد.
- هیچ checkout/reset/clean/branch switch، stage انبوه، commit یا push در preflight انجام نشد؛ شاخهٔ نشست تغییر نمی‌کند. `PR #29` قبلاً `MERGED` است و دوباره ادغام نمی‌شود؛ release همچنان `NO-GO` است.
- **گاردریل ثابت:** یک PWA مشترک React در `mp-app/studio/`؛ Flutter/Android، Electron و همهٔ workflow/testهای native حفظ شوند؛ شش نقش و تک‌باشگاه، SQLite فعلی، کارت‌به‌کارت با تطبیق انسانی، Shop نمایش‌محور، QR با اعتبارسنجی server-side و بدون face recognition، فقط fixture ساختگی و UI کتابخانهٔ موجود.

## صف و وضعیت

| ترتیب | شناسه/گروه | وضعیت این دفتر | شاهد/یادداشت |
|---:|---|---|---|
| 1 | `DOC-01…DOC-04` | `DONE` در tracker پیشین | رجیستر تصمیم‌های باز و اصلاحات تاریخی ثبت شده‌اند؛ این دفتر status آن‌ها را دوباره ارزیابی نمی‌کند. |
| 2 | `DOC-05` — ردیابی تصمیم‌ها و مرز شاهد | `PASS — docs-only, local; remote-DONE pending` | Re-run در 2026-11-27 UTC (directory baseline `2026-11-23`) در `../../evidence/2026-11-23/DOC-05/docs-gates-reset-rerun.txt`: traceability ۲۴ سند، docs/guide/map/hygiene/diff و Mermaid syntax ۲۷/۲۷ PASS؛ هیچ پذیرش محصولی ادعا نشده. |
| 3 | `DOC-06` — عدم حدس در تصمیم‌های حساس | `PASS — مرزبندی مستنداتی محلی; Ruff blocker ثبت‌شده` | Re-run در `../../evidence/2026-11-23/DOC-06/current-cycle-backend-revalidation.txt`: ۳۴ تست synthetic پاس/۱ warning؛ Ruff check همان ۹ فایل ۹ finding و exit=1؛ format پاس؛ هیچ policy یا approval انسانی حدس/اجرا نشد. remote-DONE pending. |
| 4 | `INV-01` — snapshot غیرمخرب | `PASS local — snapshot only; remote-DONE pending` | [`current-snapshot.txt`](../../evidence/2026-11-23/INV-01/current-snapshot.txt): HEAD=`e0ae95f…` در remote شاخه نیست؛ tree با `origin/main` برابر؛ ۲۴ tracked docs change، index خالی، ۳۰۹ untracked پیش از self-record؛ ۰ tracked product diff. هیچ فایل private فهرست/باز نشد. |
| 5 | `INV-02` — crosswalk کامل عضو (`PWA-01`) | `PARTIAL — crosswalk draft / NOT_ACCEPTED` | Crosswalk ۲۱ ردیفی/۱۷ feature؛ v3 rerun=۶۰/۶۰ literal shape-match (`../../evidence/2026-11-23/INV-02/member-static-inventory-v3-rerun.txt`). Studio روی dirty worktree با tracked product-source diff=0: `npm ci`, lint, build PASS؛ ۵۲ فایل/۳۶۲ تست PASS و ۲ فایل/۱۰ test skip (`studio-current-cycle-validation.txt`). این clean-tree/provenance claim نیست: snapshot جاری ۱۱۷ untracked path entry زیر `mp-app` دارد (نام‌ها حذف، محتوا بررسی‌نشده؛ `../../evidence/2026-11-23/INV-06/local-state-sanitized.txt`). Flutter toolchain، browser/device و reviewer در این crosswalk اجرا نشدند؛ در snapshot آن زمان `/member` placeholder بود و برش حساب محلی بعدی به‌عنوان current-source crosswalk محسوب نمی‌شود. policy/safety blockers پابرجا؛ checkbox باز، canonical `PWA-01=PROPOSED/NOT_RUN`. |
| 6 | `INV-03` — crosswalk کارکنان | `PARTIAL — static route/API/role inventory / NOT_ACCEPTED` | Script rerun: ۱۲ Studio page، ۵۹ endpoint shape، map ۳۱ surface/۱۶۳ operation، state field ندارد و `members`/`analytics` test ref ندارند؛ DB owner/error/persistence و action behavior هنوز ناقص. شاهد جاری `../../evidence/2026-11-23/INV-03/staff-crosswalk-static-rerun.txt`; checkbox باز. |
| 7 | `INV-04…INV-09` — وضعیت چهارگانه و inventory/acceptance باقی‌مانده | `INV-04/05/06 PARTIAL — scoped slices verified; full cards open` | `../../evidence/2026-11-23/INV-04/member-status-slice.txt`; `../../evidence/2026-11-23/INV-05/dashboard-current-cycle-test.txt`; `../../evidence/2026-11-23/INV-06/dashboard-actor-data-slice.txt` (۳۴ backend tests/۲ warnings). Staff/data surfaces و field-level ownership gaps بازند؛ همهٔ checkboxes باز؛ next independent `INV-07` CI baseline capture for exact candidate. |
| 8 | `SEC-01…SEC-10` | `NOT_STARTED` در این چرخه | fixture و source محلی فقط؛ policy/independent review بیرونی جدا می‌ماند. |
| 9 | `WEB-01…WEB-11` | `PARTIAL/NOT_ACCEPTED` review slices؛ همهٔ checkboxes باز | مرورهای ترتیبی [WEB-01](../../evidence/2026-11-27/WEB-01/runtime-boundary-review.md)، [WEB-02](../../evidence/2026-11-27/WEB-02/deep-link-review.md) و [WEB-03…11](../../evidence/2026-11-27/WEB-03-11/queue-review.md). Electron/browser/Nginx runtime و device/OS/reviewer غایب، بنابراین parentها هنوز پذیرفته نیستند. |
| 10 | `MEM-01…MEM-16`, `STAFF-01…STAFF-08`, `QA-01…QA-09` | `MEM-01=PARTIAL/NOT_ACCEPTED`; account/history `MEM-02/PWA-31=PARTIAL/NOT_ACCEPTED`; later slices not started | [Current member slice](../../evidence/2026-11-23/MEM-01/current-run.md) connects profile/history source to existing API and has synthetic Studio + TestClient tests. No live UI→backend/browser/device/reviewer acceptance; canonical checkboxes remain open. Continue sequence by each acceptance/dependency. |
| 11 | `OPS-01…OPS-14`, `PRIV-01/02` | `NOT_STARTED` در این چرخه | محیط/اپراتور/مقصد واقعی یا reviewer غایب ⇒ `BLOCKED/UNKNOWN`، نه PASS. |

Statusهای product-parent از tracker تغییر نمی‌کنند مگر evidence مستقیم همان کارت روی candidate ثبت شود: `PWA-04`, `PWA-11` و `PWA-17` همچنان `PARTIAL`; `PWA-00` فقط ثبت تصمیم است. شواهد Nginx build‌شده با upstream ساختگی، unit/mock/headless یا CI روی commit دیگر هیچ‌یک این statusها را به acceptance کامل ارتقا نمی‌دهد.

## ثبت چرخه‌ها

### DOC-05 — ردیابی تصمیم‌ها

- **Acceptance canonical:** در اسناد جاری به ADR/TODO مربوط لینک شود؛ دیاگرام، screenshot، handoff package و Option 03 به‌صراحت طراحی/مرجع، نه شاهد پیاده‌سازی، باشند؛ اسناد تاریخی بی‌صدا حذف/بازنویسی نشوند.
- **دامنهٔ مرور:** tracker و backlog PWA، ADR-006/007، handoff، docs/architecture index، اسناد Option 03 و PWA تاریخی، برنامهٔ تولید، و crosswalkهای PWA/Motion که برای وضعیت جاری ارجاع می‌شوند. اسناد تاریخی با الحاقیهٔ تاریخ‌دار cross-link می‌شوند؛ متن snapshot و خود assetها حفظ می‌شوند.
- **وضعیت چرخهٔ صفر:** `PASS local — مستندات فقط; remote-DONE pending`. ۲۴ سند PWA/تصمیم/راهنما به ADR/TODO/tracker/state مربوط cross-link شدند؛ Option 03 و نمودارها/screenshotها مرجع طراحی، نه شاهد اجرای PWA، برچسب خوردند. متن تاریخی دست‌نخورده ماند و فقط الحاقیهٔ تاریخ‌دار افزوده شد.
- **Traceability audit:** [`traceability_audit.py`](../../evidence/2026-11-23/DOC-05/traceability_audit.py) فقط marker-presence را روی ۲۴ سند PASS گزارش کرد؛ مقصد لینک‌ها و Mermaid/SVG جداگانه با `docs_gate.py` سنجیده شدند. نخستین audit نبودن block تازهٔ handoff را یافت؛ پس از افزودن block دوباره PASS شد. خروجی نهایی پس از اصلاح handoff در `../../evidence/2026-11-23/DOC-05/doc-gates-after-handoff-fix.txt` است؛ اجرای پیشین با شکست marker در handoff حفظ شده است.
- **گیت‌های مستندات:** روی worktree dirty با `HEAD=e0ae95f48bf8451bd59b972a92c55fed404e6a92`: ۳۸ Markdown، ۶۰۵ لینک محلی، ۱۵ Mermaid؛ project-guide `--check`, interaction-map (۳۱ سطح/۱۶۳ مسیر/رانش صفر), hygiene و `git diff --check` همگی PASS. raw/fingerprint در `../../evidence/2026-11-23/DOC-05/doc-gates-after-handoff-fix.txt`؛ نتیجه فقط مستندات است، نه product QA.
- **Revalidation چرخهٔ صفر (local-only; run 2026-11-27 UTC):** `docs-gates-reset-rerun.txt` روی همان HEAD و worktree مستنداتی dirty: traceability ۲۴ سند PASS؛ `docs_gate.py` ۳۸ Markdown/۶۰۵ لینک/۱۵ Mermaid PASS؛ project-guide `--check`, interaction-map ۳۱/۱۶۳/drift=0، repo hygiene و `git diff --check` PASS؛ Mermaid syntax gate با Node `v22.22.3`, npm `10.9.8`, Mermaid `11.17.2`، ۲۷/۲۷ diagram PASS. نسخهٔ کامل command/output در `../../evidence/2026-11-23/DOC-05/docs-gates-reset-rerun.txt`. این gateها فقط مستندات‌اند.
- **نتیجهٔ پذیرش:** `PASS local — DOC-05 scope only`; تا commit/push و شاهد remote `DONE` نیست؛ هیچ implementation/browser/device/release claim.

### DOC-06 — تصمیم‌های حساس را حدس نزنید

- **Acceptance canonical:** نگهداری داده، مشاهده/حذف سلامت، تعریف سود/درآمد، تطبیق بانکی، مدت اعتبار QR و مجوزهای جزئی فقط از منبع مصوب اجرا شوند؛ جزئیات ناکافی ⇒ `BLOCKED/UNKNOWN`.
- **وضعیت چرخهٔ صفر:** `PASS local — ثبت no-guess boundary; Ruff failure disclosed; remote-DONE pending`؛ مواردی که نیاز به مالک، reviewer یا پذیرش کارت مستقل دارند صریحاً باز می‌مانند. این بسته نه approval حقوقی/مالی است و نه مجوز تغییر code policy.

| حوزه | منبع/شاهد مشاهده‌شده | حکم امن / وضعیت |
|---|---|---|
| Retention و حذف سلامت | `DATA-RETENTION.md` خودش را پیش‌نویس مهندسی می‌نامد؛ جدول ثابت ۳۶ماهه/سایر مدت‌ها مجوز حقوقی نیست. `modules/privacy/retention.py` فقط audit/inbox/read notifications/report runs را کد می‌کند؛ comment همان module و سربرگ `test_phase8_privacy.py` می‌گویند report runs حذف نمی‌شود، اما implementation قدیمی‌تر از ۷۳۰ روز را حذف می‌کند و fixture تست این ردیف را نمی‌آزماید. | تعارض سند/code/test و نبود review حقوقی/حریم (`OD-05=BLOCKED`)؛ policy واقعی نگهداری، right-to-erasure و دادهٔ سلامت `BLOCKED/UNKNOWN`. هیچ retention/delete تازه‌ای اجرا نشد. |
| مشاهده/حذف سلامت و بیومتریک | test privacy صریحاً حذف به درخواست عضو را خارج از scope می‌گذارد؛ کلید `reports.confidential` در code وجود دارد اما ماتریس کامل دسترسی/حذف نیست. عکس پیشرفت بدن در ADR-007 از scope انتشار اول خارج است و face recognition سروری نیز خارج scope است. | دسترسی/مدت/درخواست حذف دادهٔ سلامت تا review مجاز `BLOCKED`; سیاست بیومتریک قدیمی authority فعال نیست؛ هیچ مسیر face/health تازه‌ای فعال نشد. |
| تعریف درآمد/سود | `TODO-CLOUD-FINANCE-ACCESS.md` تعریف حسابدار برای درآمد شناسایی‌شده/هزینه/سود را باز می‌گذارد. `modules/reports/period.py` امروز paid/refunded/expenses را طبق کد جمع و `profit=net−expenses` می‌کند؛ UI `PeriodReportPanel` در `complete=false` سود را unknown می‌کند، اما این فرمول code behavior است نه accounting sign-off. | تعریف حسابداری/مالی رسمی `BLOCKED`; incomplete را سود قطعی/صفر نخوان؛ test fixture پذیرش حسابدار یا بانک نیست. |
| تطبیق بانکی | تصمیم محصول کارت‌به‌کارت با بررسی انسانی و منبع بانکی مستقل است؛ رسید به‌تنهایی proof واریز نیست. مقصد/منبع/ساعات/اپراتور عملیاتی در `OD-07=OPEN` هستند و live merchant در scope نیست. | تطبیق واقعی و فعال‌سازی مالی `BLOCKED` تا actor/مرجع مستقل مجاز؛ هیچ حساب/بانک/provider واقعی استفاده نشد. |
| TTL QR | source `create_checkin_qr_token` در `jwt.py` زمان `exp=now+2 minutes` می‌سازد و TODO canonical M65 دو دقیقه ثبت کرده است؛ Option 03 قدیمی `30s` را نادرست می‌گوید. integration tests expiration/replay/ownership را می‌آزمایند، نه TTL دقیق token تازه‌ساخته‌شده. | **رفتار فعلی source:** دو دقیقه؛ **مدت پذیرفته‌شدهٔ محصول:** `UNKNOWN/BLOCKED` تا `MEM-10`/QA. erratum تاریخی ثبت شد، کد تغییر نکرد. |
| مجوزهای جزئی | ADR-007/OQ-03 شش نقش را نگه می‌دارند؛ `grants.py`/`route_policy.py` و تست‌های مربوط بخشی از guardها را می‌پوشانند، نه inventory کامل route×role×permission×ownership. `OD-02=OPEN`, `PWA-02=NOT_RUN`. | نقش/grant تغییر نمی‌کند؛ ماتریس و پذیرش کامل `BLOCKED/UNKNOWN` تا کارت/تصمیم مربوط. |

- **آزمون محدود مرتبط (همه synthetic):** از `mp-app/backend/` روی `HEAD=e0ae95f48bf8451bd59b972a92c55fed404e6a92`, Python `3.11.2`, pytest `9.2.0`: پنج فایل `test_phase8_privacy.py`, `test_m65_qr_security.py`, `test_qf10_period_report.py`, `test_phase5_admin_permissions.py`, `test_routes_effective_guards.py` ⇒ `34 passed, 1 warning`. raw اجرای بازتولیدشده: `../../evidence/2026-11-23/DOC-06/backend-privacy-qr-tests-rerun.txt`. این testها سطح‌های اشاره‌شده را پوشش می‌دهند؛ policy/owner/reviewer/device/live-bank پذیرش نمی‌شود؛ diff محصول backend خالی ماند.
- **Ruff شفافیت:** `ruff 0.17.6` روی ۹ فایل مرتبط: `ruff check` **failed** با ۹ finding (`TC001/TC002` import-type rules، `RUF059` متغیر استفاده‌نشده)؛ `ruff format --check` روی همان ۹ فایل **pass**. هیچ source/test تغییر نکرد و fix ناامن خارج از DOC-06 اجرا نشد؛ بنابراین lint را PASS گزارش نکن. raw: `../../evidence/2026-11-23/DOC-06/backend-ruff-check-final.txt`, `backend-ruff-format-check-final.txt`.
- **محل شواهد:** `../../evidence/2026-11-23/DOC-06/`؛ شامل test raw، source crosswalk، Ruff stdout/stderr/exit code و marker audit.
- **Revalidation چرخهٔ صفر (همه synthetic):** Python `3.11.2`, pytest `9.2.0`: ۵ integration file ⇒ `34 passed, 1 warning`؛ Ruff `0.17.6`: `check` همان ۹ فایل `exit=1` با ۹ finding موجود (`TC001/TC002`, `RUF059`)، `format --check` `exit=0` (۹ فایل). هیچ Ruff auto-fix یا source/test edit انجام نشد. Raw: `../../evidence/2026-11-23/DOC-06/current-cycle-backend-revalidation.txt`; Ruff failure مانع ادعای lint PASS است، نه مجوز تضعیف گیت.
- **نتیجهٔ پذیرش:** `PASS local — ثبت مرز و blockerها برای DOC-06`; تا push و remote witness `DONE` نیست. تمام approvalهای سیاستی/حساس `BLOCKED/UNKNOWN/OPEN` و release `NO-GO` باقی‌اند.

### INV-01 — snapshot غیرمخرب

- **Acceptance canonical:** branch/HEAD، وضعیت tracked و untracked، نسخهٔ ابزارها و CI ثبت شوند؛ secret/PII چاپ نشود؛ هیچ `pull/reset/clean` یا stage/delete روی untracked خصوصی انجام نشود.
- **وضعیت چرخهٔ صفر:** `PASS local — snapshot only; remote-DONE pending`. branch=`arena/5e0f64cf-mp` (base اعلام‌شده `35d4b35184b4148c658b415bd009fc076bf24e00`)، `HEAD=e0ae95f48bf8451bd59b972a92c55fed404e6a92`, `origin/main=352781043ad2ba202d8b3b459df1ce7e3d914ef7`؛ relation کامل در snapshot تازه ثبت شد.
- **Worktree زمان snapshot پیشین (تاریخی):** ۲۴ tracked path تغییرکرده، همه در README/docs؛ index خالی؛ ۲۹۳ untracked غیر از خود فایل snapshot. عددهای قدیمی ۱۵۷ artifact/۱۱۲ زیرپوشهٔ receipt به همان زمان محدودند؛ هیچ نامی در این دفتر نمی‌آید.
- **Snapshot تازهٔ چرخهٔ صفر:** ۲۴ tracked change همگی README/docs، index خالی؛ ۳۰۹ untracked پیش از افزودن `current-snapshot.txt` و ۳۱۰ دربرگیرندهٔ همان فایل؛ صفر tracked product diff. فهرست و محتوا باز/چاپ نشدند؛ شاهد sanitized در `../../evidence/2026-11-23/INV-01/current-snapshot.txt`. HEAD local در remote ref نیست؛ ancestry و tree-equality در همان transcript مستند شده‌اند.
- **Toolchain ثبت‌شده:** Git `2.39.5`, Node `v22.22.3`, npm `10.9.8`, Python `3.11.2`, pytest `9.2.0`, Ruff `0.17.6`, gh `2.23.0`.
- **CI query چرخهٔ صفر:** GitHub CLI `2.23.0` از `gh run list --commit` پشتیبانی نمی‌کند (exit=1)؛ fallback `gh run list --branch arena/5e0f64cf-mp --limit 100 ... --jq 'map(select(.headSha == e0ae95f…))'` موفق شد و `[]` داد. بنابراین در ۱۰۰ run اخیرِ شاخه، run منطبق با local HEAD دیده نشد؛ هیچ workflowای dispatch نشد. خام: `../../evidence/2026-11-23/INV-01/ci-current-sha-query.txt`. پس از push باید روی SHA ریموت، `gh pr checks` و `gh run list` دوباره اجرا شوند.
- **محل شاهد:** `../../evidence/2026-11-23/INV-01/snapshot.txt`؛ خروجی status به‌شکل aggregate امن و فهرست فقط tracked docs در آن ثبت است. هیچ pull/reset/clean/stage/commit/push/deploy در INV-01 انجام نشد.
- **نتیجهٔ پذیرش:** `PASS — non-destructive snapshot only`; inventory crosswalk، QA و release جدا هستند.

### INV-02 — crosswalk عضو (`PWA-01`)

- **Acceptance canonical:** تمام قابلیت‌های Flutter به رفتار، API، صفحه/route React موجود یا `GAP`، role/data-owner، test/evidence و یکی از `CURRENT/GAP/TARGET/BLOCKED` وصل شوند. canonical `PWA-01` هنوز `PROPOSED/NOT_RUN` است.
- **Crosswalk draft:** [`member-capability-crosswalk.md`](../../evidence/2026-11-23/INV-02/member-capability-crosswalk.md) همهٔ ۱۷ directory عضو را در ردیف‌های رفتاری map می‌کند، policy targetهای ADR-007 را از وضع فعلی جدا می‌سازد، و routeهای تأییدنشده را `TBD` می‌گذارد. نتیجه `PARTIAL / NOT_ACCEPTED`; tracker checkbox باز می‌ماند.
- **Source evidence:** v3 literal scan ۱۷ directory، ۳۱ فایل/۹٬۵۰۱ خط feature، ۱۴ GoRouter path، ۲۸ test file موجود و ۶۰ call-site را به method/path shape manifest تطبیق داد؛ `api/routes.json` دارای ۱۴۱ path/۱۶۳ operation است. v2 چهار `ref.watch(apiClientProvider)` را از دست می‌داد و به‌عنوان baseline coverage superseded است. raw: `../../evidence/2026-11-23/INV-02/member-static-inventory-v3.txt`; manifest/source/test hashes همان‌جا.
- **React و ownership boundary:** `/member` هنوز `MemberRoutePending` بدون member-data است؛ guard برنامه، member را از `/staff/*` رد می‌کند. Manifest roles/scopes با handler/service/model برای ownership cross-read شده، اما `owner_scope` اثبات runtime/negative authorization نیست. پنج/چند ردیف policy/safety حساس `BLOCKED` مانده‌اند؛ staff pages، diagrams و test-file presence معادل flow/member acceptance نیستند.
- **گیت‌های audit ایستای اولیه:** هنگام ساخت crosswalk، Flutter/React/backend tests/build، browser/device، error/persistence E2E و reviewer/product-owner sign-off اجرا نشدند؛ این گزاره به همان snapshot اولیه محدود است.
- **Revalidation چرخهٔ صفر:** scan v3 دوباره اجرا شد؛ نتیجه همچنان ۱۷ feature directory، ۳۱ فایل/۹٬۵۰۱ خط، ۱۴ route، ۲۸ test-file presence و ۶۰/۶۰ literal API shape-match (`member-static-inventory-v3-rerun.txt`). `npm ci`, `npm run lint`, `npm run build` و کل `npm test -- --reporter=dot` روی Studio با product-source diff صفر موفق شدند: ۵۲ test file PASS/۲ SKIP، ۳۶۲ test PASS/۱۰ SKIP؛ warnings JSDOM/React `act`/Recharts بدون layout باقی‌اند. raw شامل install audit (۴ advisory) و خروجی کامل در `studio-current-cycle-validation.txt` است؛ هیچ dependency/source/lockfile تغییر نکرد.
- **گیت‌های پذیرش باز:** Flutter/Dart و browser binary/Playwright موجود نیست؛ Flutter/browser/device، member route/ownership/error/persistence E2E و reviewer acceptance `NOT_RUN/BLOCKED`. `/member` هنوز placeholder؛ بنابراین `INV-02=PARTIAL/NOT_ACCEPTED`, checkbox باز و `PWA-01=PROPOSED/NOT_RUN` بدون تغییر. هیچ تغییر Flutter/native، role, DB, checkout یا biometric انجام نشد.

### INV-03 — crosswalk کارکنان

- **وضعیت:** `PARTIAL — static route/API/role/test inventory, NOT_ACCEPTED`; مسیر مستقل staff باقی می‌ماند و checkbox باز است. اسکریپت corrected `../../evidence/2026-11-23/INV-03/staff_crosswalk_audit.py` route keyها را با kind+name جدا می‌کند تا collision با Flutter surface هم‌نام رخ ندهد؛ raw `staff-crosswalk-static.txt` شامل ۱۲ Studio page، route، endpoint/manifest roles و test reference است.
- **گیت فعلی:** `interaction_map.py --check` PASS با ۳۱ surface/۱۶۳ contract/drift صفر. اعضا و role-restricted APIs در map دیده می‌شوند، اما map برای هر صفحه state/loading/empty/error/persistence و DB-owner ندارند. `members` و `analytics` test reference ندارند؛ سایر testها فقط در scan حاضر شمرده شدند، اجرا نشدند. ۶۹ operation manifest در هیچ interaction surface ثبت نشده‌اند؛ این absence dead-code proof نیست.
- **Revalidation چرخهٔ صفر:** `staff_crosswalk_audit.py` دوباره اجرا شد؛ ۱۲ Studio page، ۵۹ endpoint shape و manifest map ۳۱ surface/۱۶۳ operation، ۶۹ operation بدون surface (absence به‌تنهایی dead-code نیست)، `interaction_map_has_state_field=False` و دو صفحهٔ `members`/`analytics` بدون test reference. خروجی `../../evidence/2026-11-23/INV-03/staff-crosswalk-static-rerun.txt`; فقط static/source scan است.
- **باقی‌مانده:** behavior-level actor/role→route/API/permission→model/ownership→state/error→test-ID matrix، test negative/evidence و reviewer acceptance. PWA-01 canonical/status از این static inventory تغییر نمی‌کند؛ full `INV-04…INV-09` هنوز باز است.
- **بازتولید و بازبینی source در ادامهٔ جاری:** [`INV-02 raw + review`](../../evidence/2026-11-27/INV-02/review.md) و [`INV-03 raw + review`](../../evidence/2026-11-27/INV-03/review.md) از SHA جداشدهٔ `352781043ad2ba202d8b3b459df1ce7e3d914ef7` ثبت شدند. خروجی خام و hashها حفظ شده‌اند؛ بازبینی دستی false-negativeهای dynamic template را تشخیص داد، اما هیچ تست محصول یا مجوزی اجرا نشد. هردو کارت partial/non-accepted و checkbox باز؛ `PWA-01=PROPOSED/NOT_RUN`.

### INV-04 — برش ساختاری statusهای عضو (کل کارت باز)

- **Acceptance canonical:** برای هر capability یکی از `CURRENT/GAP/TARGET/BLOCKED` به‌همراه owner/scope، test موجود/لازم، فایل/line و منبع داده؛ صرف وجود صفحه/API کافی نیست.
- **برش انجام‌شده:** [`member-status-slice.txt`](../../evidence/2026-11-23/INV-04/member-status-slice.txt) روی crosswalk `INV-02` تأیید کرد ۲۱/۲۱ ردیف member یک status دارند و ستون‌های Flutter source/API/owner/React/test-reference خالی نیستند: `CURRENT=0`, `GAP=12`, `TARGET=4`, `BLOCKED=5`. این یک structural status slice است، نه full `INV-04`.
- **Blocker:** crosswalk فیلد row-specific «test لازم» ندارد، test-referenceها فقط presence هستند، صفحه‌های کادر در این slice پوشش داده نشده‌اند و ownership/runtime منفی/positives اجرا نشده؛ `INV-04` و checkbox باز می‌ماند.

### INV-05 — Dashboard KPI/fallback (برش مستقل؛ کل inventory باز)

- **Acceptance canonical:** hard-coded/mock data، silent fallback، controls بی‌اثر، local-only state و KPI بی‌منبع شناسایی شوند؛ fixture با دادهٔ واقعی اشتباه نشود.
- **برش بررسی‌شده:** `Dashboard.tsx` از `fetchKpis` و `fetchAttendance` استفاده می‌کند؛ KPI از `/admin/kpis`، حضور از `/admin/attendance`; `useApi` سه حالت loading/error/data و `needsSession` را جدا نگه می‌دارد. `null` برای ظرفیت «نامعلوم» است؛ پیام zero attendance فقط پس از پاسخ حاوی عدد صفر می‌آید؛ خطا به‌صورت متن خطا می‌ماند. fixtureهای تست صرفاً synthetic هستند و هیچ مقدارشان در evidence کپی نشده.
- **تست:** `npm test -- tests/dashboard.test.tsx --reporter=dot` روی `HEAD=e0ae95f48bf8451bd59b972a92c55fed404e6a92`: ۱ فایل/۳ تست PASS، یک سری React `act(...)` warnings؛ raw `../../evidence/2026-11-23/INV-05/dashboard-current-cycle-test.txt`.
- **Blocker/حد:** فقط Dashboard KPI/fallback/error بررسی شد؛ سایر ۱۲ Studio page، Flutter/member, backend data provenance و source-less KPIها هنوز inventory نشده‌اند. `INV-05`/checkbox باز می‌ماند.

### INV-06 — Dashboard actor/data/route slice (کل کارت باز)

- **Acceptance canonical:** actor، داده، scope/ownership، مجوز و مسیر direct API برای هر view/mutation/file/export/job/event map شود.
- **برش بررسی‌شده:** [`dashboard-actor-data-slice.txt`](../../evidence/2026-11-23/INV-06/dashboard-actor-data-slice.txt) سه GET dashboard/KPI/attendance/member-summary را با endpoint-specific guards/roles، router permission dependency، model/source و single-club scope کنار هم می‌گذارد. KPI از `Member/Membership/Payment/GymClass/ClassBooking` و حضور از `CheckIn` aggregate می‌شود؛ `members-summary` روی `Member/User/Membership` staff list است. هیچ row-owner claim برای club-wide staff endpoint ساخته نشد.
- **تست منفی/مثبت همان برش:** `dashboard-actor-data-tests.txt`, rerun در 2026-11-27 UTC؛ Python 3.11.2/pytest 9.2.0: ۳ فایل، ۳۴ passed/۲ warning (Starlette/httpx deprecation و InsecureKeyLengthWarning برای JWT تستی)؛ temp SQLite فقط. anonymous/member denial و چند positive staff read، KPI admin/null-capacity و empty attendance پوشش دارند؛ کل نقش‌ها×مسیرها آزموده نشده‌اند. فایل خام header تاریخ مرجع مسیر evidence را دارد، نه زمان اجرای آزمون.
- **Blocker/حد:** component `Dashboard.tsx` بدون role gate، `fetchKpis` را فراخوانی می‌کند؛ اگر برای coach/reception render شود، current `security/rbac.py` policy برای آنان KPI allow ندارد و `require_permission()` route/method enforcement را انجام می‌دهد؛ پاسخ باید fail-closed شود. page reachability و error UI از UI تا API به‌صورت E2E تأیید نشده؛ تغییر grant/policy انجام نشد. باقی Studio/Flutter/member, download/export/file/event/job و field-level ownership هنوز map/test نشده؛ `INV-06` و checkbox باز؛ next مستقل `INV-07` CI evidence per-job روی exact SHA.
- **Snapshot Git پالایش‌شده (2026-11-27 UTC):** [`local-state-sanitized.txt`](../../evidence/2026-11-23/INV-06/local-state-sanitized.txt): همان branch/HEAD، index خالی، ۲۴ tracked worktree changes، ۳۲۲ untracked path entry (۱۱۷ زیر `mp-app`؛ نام‌ها عمداً حذف و محتوا بررسی‌نشده)، tracked product-source diff صفر. untrackedها را نمی‌توان به candidate پاک یا source بی‌تغییر نسبت داد؛ stage/commit انجام نشد.

## قرارداد شواهد و checkpoint

- برای هر چرخه raw output پالایش‌شده در `evidence/2026-11-23/<ID>/` نگه‌داری شود؛ secret، PII، token، receipt، دادهٔ واقعی و فهرست مسیرهای خصوصی وارد سند یا evidence نشود.
- هر PASS باید command، نتیجهٔ دقیق، SHA و نسخهٔ ابزار را داشته باشد؛ skip/mock، preview، آزمون تاریخی یا CI روی SHA دیگر PASS نیست. برای worktree dirty، همان محدودیت و hash/fingerprint تغییرات ثبت شود.
- بعد از هر ۵ آیتم یا پیش از push، این دفتر، handoff و tracker با شواهد همان revision همگام شوند. هیچ CI، browser/device، reviewer، operator، staging، SMS/provider، bank reconciliation، backup/restore یا production evidence که اجرا نشده `UNKNOWN/NOT_RUN/BLOCKED` می‌شود.
- در هر مشکل واحد، پس از سه تلاش ناموفق پیاپی آن را `BLOCKED` و دلیل دقیق را ثبت کن و سراغ کار مستقل بعدی برو؛ گیت یا تست را تضعیف نکن.

## گیت‌های بیرونی باز

Browser/OS/device فیزیکی، screen reader، نسخه/مدل دقیق، reviewer مستقل حقوقی/پزشکی/مالی، SMS/provider واقعی، تطبیق بانکی، میزبان/staging، backup خارج‌میزبان و آزمون restore/RPO/RTO، secret/key عملیاتی، deploy/rollback و release همچنان `UNKNOWN/BLOCKED/NOT_RUN` تا ثبت شاهد مجاز همان موردند. این فایل مجوز دسترسی، ایجاد secret، استفاده از دادهٔ واقعی، deploy، release یا merge نیست.
