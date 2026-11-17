#!/usr/bin/env bash
# Backward-compatible entry point. Use the pinned, non-destructive installer.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
exec bash "$ROOT/docs/MuscleParadise/finn/install-toolchain.sh" ecc
