#!/usr/bin/env bash
# M28 — ساخت APK اندروید (اجرا در CI با Flutter نصب‌شده)
set -euo pipefail

cd "$(dirname "$0")"
LOG="${BUILD_LOG:-/tmp/apk-build.log}"
exec > >(tee "$LOG") 2>&1

BUILD_NUMBER="${BUILD_NUMBER:-1}"
echo "==> version: $(grep '^version:' pubspec.yaml) build=$BUILD_NUMBER"

flutter --version
flutter pub get
flutter analyze --no-fatal-infos
flutter test
flutter build apk --release --split-per-abi --build-number="$BUILD_NUMBER"

APK="build/app/outputs/flutter-apk/app-arm64-v8a-release.apk"
if [ -f "$APK" ]; then
  sha256sum "$APK" | tee "$APK.sha256"
  echo "OK: $APK"
else
  echo "ERROR: APK not found" >&2
  exit 1
fi
