#!/usr/bin/env bash
# Manual rollback request. The previous image tag is supplied explicitly by the operator.
# Usage: bash rollback.sh <https-dokploy-webhook-url> <explicit-ghcr-backend-image>
set -euo pipefail

WEBHOOK="${1:?Dokploy HTTPS webhook URL is required}"
IMAGE="${2:?an explicit prior GHCR image tag is required}"

[[ "$WEBHOOK" == https://* ]] || {
  echo "Dokploy webhook must use HTTPS" >&2
  exit 1
}
[[ "$IMAGE" =~ ^ghcr\.io/[a-z0-9._-]+/mp-backend:([0-9a-f]{40}|v[0-9]+(\.[0-9]+){1,2}([-+][A-Za-z0-9.-]+)?)$ ]] || {
  echo "expected ghcr.io/<owner>/mp-backend:<40-char-sha-or-version-tag>" >&2
  exit 1
}

# IMAGE is restricted to an explicit SHA/version-shaped tag; GHCR immutability is a separate policy.
payload="{\"image\":\"$IMAGE\",\"action\":\"rollback\"}"
echo "[rollback] requesting the explicit prior image: $IMAGE"
curl -fsS --max-time 20 -X POST "$WEBHOOK" \
  -H "Content-Type: application/json" \
  -d "$payload"
echo "[rollback] request sent; verify readiness and schema compatibility"
