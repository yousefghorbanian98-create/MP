# GitHub Codespaces — Flutter validation

This devcontainer uses the maintained MIT-licensed `mcr.microsoft.com/devcontainers/base:ubuntu24.04` image, then downloads the official Flutter Linux x64 stable archive pinned to Flutter 3.50.0 and its published SHA-256. It intentionally does **not** use Cirrus Labs Flutter images. The container verifies the framework version/revision after creation.

The image includes OpenJDK 17 and is intended for source validation: `flutter pub get`, `flutter analyze --no-fatal-infos`, and `flutter test`. It does **not** install the Android SDK, accept Android licenses, build/sign an APK, or use signing files. APK creation remains a separate, explicitly gated task.

## First run

1. Create a Codespace from the active branch `arena/4f336f66-mp` only after the reviewed package has been pushed. Creating a Codespace can incur GitHub billing; this repository setup does not create one.
2. In the Codespaces terminal:

   ```bash
   cd mp-app/client
   flutter pub get
   flutter analyze --no-fatal-infos
   flutter test
   ```

3. Save the exact Flutter/Dart versions and complete command results. Keep all loop statuses `UNKNOWN` until the corresponding runtime gate actually passes on this source.

If the image build, archive checksum, dependency resolution, analyzer, or tests fail, retain the failure output and do not treat the missing gate as a pass. See `finn/reports/codespaces-user-handoff.md` for the loop-specific commands and evidence handoff.

## Optional Android witness (M107)

`provision-android-sdk.sh` is an **opt-in** script for one purpose: making `flutter build apk --debug`
(and therefore the Kotlin/Gradle compile of `MainActivity.kt` / `OfflineFeedbackDatabase.kt`) possible inside a
Codespace. It is not part of the image build, because installing the SDK also means accepting the Android SDK
licenses — that must stay an explicit human action (`ACCEPT_ANDROID_LICENSES=1`). The script refuses to install
an unverified archive unless you pass `SDK_SHA256` or acknowledge `SDK_ALLOW_UNPINNED=1`; it records the hash it
observed so the pin can be made honestly later.

It has **not** been executed by the agent that wrote it (that sandbox has no access to `dl.google.com`), so the
first run is itself a gate: keep the log. Full ordered steps, expected outputs and what each witness unlocks:
[`docs/MuscleParadise/runbooks/codespaces-execution.md`](../docs/MuscleParadise/runbooks/codespaces-execution.md).
APK signing and release remain outside this container by design (SEC-01 is open).
