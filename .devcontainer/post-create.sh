#!/usr/bin/env bash
set -euo pipefail

flutter --version --machine | python3 -c '
import json
import os
import sys

actual = json.load(sys.stdin)
expected = {
    "frameworkVersion": os.environ["FLUTTER_EXPECTED_VERSION"],
    "frameworkRevision": os.environ["FLUTTER_EXPECTED_REVISION"],
}
for field, value in expected.items():
    if actual.get(field) != value:
        raise SystemExit(f"Pinned Flutter mismatch for {field}: expected {value}, got {actual.get(field)}")
print(f"Verified Flutter {expected['frameworkVersion']} ({expected['frameworkRevision']}).")
'

printf '%s\n' '--- Dart ---'
dart --version
printf '%s\n' '--- Java ---'
java -version 2>&1
printf '%s\n' '--- Next step ---'
printf '%s\n' 'Run flutter pub get, flutter analyze, and flutter test from mp-app/client.'
printf '%s\n' 'Android SDK is not installed in this image; APK builds need a separate reviewed SDK setup.'
