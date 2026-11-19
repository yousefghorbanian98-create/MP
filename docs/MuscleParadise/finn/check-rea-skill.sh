#!/usr/bin/env bash
# Compare an installed REA skill without mutating either tree. A single
# additional root LICENSE-REA is permitted only if it matches the package's
# license byte-for-byte. Never treat other local differences as equivalent.
set -euo pipefail

if [ "$#" -ne 3 ]; then
  printf 'Usage: %s SOURCE_SKILL INSTALLED_SKILL PACKAGE_LICENSE\n' "$0" >&2
  exit 2
fi
src=$1
dst=$2
license=$3
[ -d "$src" ] && [ -d "$dst" ] && [ -f "$license" ] || exit 1
[ ! -L "$src" ] && [ ! -L "$dst" ] || exit 1
# Symlinks within a pre-existing installation are not followed or accepted.
[ -z "$(find "$src" "$dst" -type l -print -quit)" ] || exit 1
if diff -qr -- "$src" "$dst" >/dev/null; then
  exit 0
fi
# Exclusion is safe only after proving there are no other same-named files
# hidden at any depth in either tree.
[ -z "$(find "$src" -name LICENSE-REA -print -quit)" ] || exit 1
[ -f "$dst/LICENSE-REA" ] && [ ! -L "$dst/LICENSE-REA" ] || exit 1
count=$(find "$dst" -name LICENSE-REA -print | wc -l)
[ "$count" -eq 1 ] || exit 1
cmp -s -- "$license" "$dst/LICENSE-REA" || exit 1
diff -qr --exclude=LICENSE-REA -- "$src" "$dst" >/dev/null
