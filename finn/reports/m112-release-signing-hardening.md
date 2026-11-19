# M112 — release signing and publication hardening

## Evidence and scope

On `a0ec758`, CI run `44385060074` completed with backend, Studio, live-contract,
Flutter, pinned Flutter/Android debug compile, docs and e2e-api successful. The
secret scan failed on two historical Android signing-password findings. The
historical keystore and its passwords must be treated as compromised; Git removal
alone would not revoke copies. Existing releases signed by it cannot safely be
claimed to have an uncompromised signer. This work does not rewrite history,
remove other branches or tags, or claim that the historical key has been revoked.

The current GitHub integration returned HTTP 403 when listing Actions secrets, so
it cannot currently provision or inspect repository-level signing secrets. No
secret was generated or transmitted in chat. A durable, separately backed-up
release key must be generated and provisioned through an appropriately authorized
secure channel. Installation over older builds signed with a different key will
fail; a clean install can remove locally stored app data. Plan migration before
replacing installed apps.

## Changes

- Android Gradle release signing is explicitly PKCS#12 and takes its path,
  alias and passwords from the build environment. It cannot fall back to the
  standard debug signing configuration; debug builds remain independent.
- APK workflow requires four distinct repository secrets and a pinned public
  certificate SHA-256 repository variable. It decodes the keystore in the runner
  temporary directory with restrictive permissions, checks every APK with
  `apksigner` against the expected signer, and removes the temporary keystore
  even on failure.
- Each ABI APK is passed explicitly to the deep audit, and each gets a checksum.
  Previously the audit defaulted to the unrelated `client/release` directory,
  not the directory just built by CI.
- Dispatch no longer commits binaries and a tag no longer automatically uploads
  them to a GitHub Release. An artifact is not a release: publication remains
  conditional on all required gates and product requirements being satisfied.

Provision the following via repository Actions secrets: `MP_ANDROID_KEYSTORE_BASE64`
(single-line base64 of the PKCS#12 file), `MP_ANDROID_STORE_PASSWORD`,
`MP_ANDROID_KEY_ALIAS`, and `MP_ANDROID_KEY_PASSWORD`. Set Actions variable
`MP_ANDROID_CERT_SHA256` to the SHA-256 fingerprint of the **new** release
certificate, from an independent trusted source. Do not put keys or passwords in
Git, logs, issues or chat. Store a recoverable offline backup independently of CI.
Verify that the new certificate differs from the exposed certificate; our code
cannot establish this without evidence from the signing-key provisioning step.

## Verification limits

`test_release_signing_policy.py` checks configuration invariants and output
paths, not cryptographic correctness of a built APK. A signed release build,
independent signer verification, per-ABI deep audit and full CI on the new
commit remain required. Photo privacy feature L4 is not implemented. Neither the
red secret gate nor these missing checks is a PASS.
