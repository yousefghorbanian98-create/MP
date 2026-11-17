#!/usr/bin/env bash
# Host cron health check. Set MP_HEALTH_URL to the public HTTPS readiness URL
# for the Caddy stack; the default checks the loopback-only deploy Studio port.
# Optional notifications must point to a self-hosted endpoint (MP_NTFY_URL).
set -u
URL="${MP_HEALTH_URL:-http://127.0.0.1:${STUDIO_PORT:-8080}/api/v1/health/ready}"

RESP=$(curl -fsS --max-time 5 "$URL" || echo '{"ready": false}')
if ! echo "$RESP" | grep -q '"ready": true'; then
  echo "MP readiness check failed for configured endpoint" >&2
  if [ -n "${MP_NTFY_URL:-}" ] && [ -n "${MP_NTFY_TOPIC:-}" ]; then
    curl -fsS --max-time 5 -H "Title: MP readiness check failed" \
      -d 'Readiness probe failed; inspect the local runbook.' \
      "${MP_NTFY_URL%/}/${MP_NTFY_TOPIC}" >/dev/null 2>&1 || true
  fi
  exit 1
fi
exit 0
