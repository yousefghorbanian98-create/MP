#!/usr/bin/env bash
# Muscle Paradise — اسکریپت rollback (M10)
# استفاده: bash rollback.sh <dokploy-webhook-url> [image-tag]
# منطق: بازگشت به ایمیج قبلی (last-known-good) ثبت‌شده در فایل state
set -euo pipefail

WEBHOOK="${1:?webhook لازم است}"
STATE_FILE="$(dirname "$0")/.last-good-image"

if [ -n "${2:-}" ]; then
  IMAGE="$2"
elif [ -f "$STATE_FILE" ]; then
  IMAGE="$(cat "$STATE_FILE")"
else
  echo "هیچ ایمیج last-known-good ثبت نشده و image-tag داده نشده است" >&2
  exit 1
fi

echo "[rollback] بازگشت به ایمیج: $IMAGE"
curl -fsS -X POST "$WEBHOOK" \
  -H "Content-Type: application/json" \
  -d "{\"image\":\"$IMAGE\",\"action\":\"rollback\"}"
echo "[rollback] درخواست rollback ارسال شد"
