#!/usr/bin/env bash
set -euo pipefail
here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
check="$here/check-rea-skill.sh"
fixture=$(mktemp -d "${TMPDIR:-/tmp}/mp-rea-skill-test.XXXXXX")
trap 'rm -rf -- "$fixture"' EXIT
mkdir -p "$fixture/src/sub" "$fixture/dst/sub"
printf 'original\n' > "$fixture/src/sub/skill.txt"
cp "$fixture/src/sub/skill.txt" "$fixture/dst/sub/skill.txt"
printf 'license\n' > "$fixture/LICENSE"
pass() { bash "$check" "$fixture/src" "$fixture/dst" "$fixture/LICENSE" || { echo "FAIL: $1" >&2; exit 1; }; echo "PASS: $1"; }
reject() { if bash "$check" "$fixture/src" "$fixture/dst" "$fixture/LICENSE"; then echo "FAIL: accepted $1" >&2; exit 1; fi; echo "PASS: rejects $1"; }
pass 'identical trees'
cp "$fixture/LICENSE" "$fixture/dst/LICENSE-REA"
pass 'matching package license'
printf 'wrong\n' > "$fixture/dst/LICENSE-REA"
reject 'wrong license'
cp "$fixture/LICENSE" "$fixture/dst/LICENSE-REA"
printf 'changed\n' > "$fixture/dst/sub/skill.txt"
reject 'changed skill'
cp "$fixture/src/sub/skill.txt" "$fixture/dst/sub/skill.txt"
printf 'extra\n' > "$fixture/dst/sub/LICENSE-REA"
reject 'nested license'
rm -- "$fixture/dst/sub/LICENSE-REA"
ln -s "$fixture/src/sub/skill.txt" "$fixture/dst/symlink"
reject 'symlink'
