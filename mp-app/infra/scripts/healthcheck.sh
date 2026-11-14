#!/usr/bin/env bash
# health-check cron (M13) — اگر /health/ready ناسالم بود به ntfy اطلاع بده
# cron: */2 * * * * /opt/mp/scripts/healthcheck.sh
set -u
URL="${MP_HEALTH_URL:-http://localhost:8751/api/v1/health/ready}"
NTFY_TOPIC="${MP_NTFY_TOPIC:-muscleparadise-ops}"

RESP=$(curl -fsS --max-time 5 "$URL" || echo '{"ready": false}')
if ! echo "$RESP" | grep -q '"ready": true'; then
  curl -sS -H "Title: MP health-check FAILED" -d "$RESP" "https://ntfy.sh/$NTFY_TOPIC" >/dev/null 2>&1 || true
  exit 1
fi
exit 0
