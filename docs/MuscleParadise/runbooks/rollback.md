# Runbook — Rollback

> Rollback is a manual, high-risk operation. Never roll back during peak traffic without an incident lead and verified backup.

## Trigger
- Readiness remains 503 or the backend is unavailable after deployment.
- 5xx rate or check-in latency breaches the configured alert for the incident window.
- A confirmed regression cannot be mitigated by disabling a feature flag.

## Before changing the image
1. Record the incident UTC time, environment, deployment SHA, and a request ID if available.
2. Confirm the last known-good backend SHA tag and matching Studio tag from protected release history; verify each image digest in GHCR before use. `latest` is not a rollback target.
3. Verify a recent backup exists outside the host and inspect the schema migration compatibility. Image rollback does **not** downgrade Alembic or restore the database.
4. If the previous schema is incompatible, stop: follow the database restore runbook with an approved maintenance window instead of blindly starting the old image.

## Image rollback
1. In GitHub Actions, run `mp-deploy` manually with `operation=rollback`, the protected `staging` or `production` environment, and a full `ghcr.io/<owner>/mp-backend:<40-char-sha-or-version-tag>` value.
2. The workflow validates HTTPS endpoints, calls Dokploy with the explicit backend image, and waits for `/api/v1/health/ready` to report `ready=true`.
3. If the deployment includes Studio, select/redeploy the matching Studio tag as well and verify the browser app; the webhook currently sends the backend image only.
4. Check `/api/v1/metrics`, application logs and the relevant alert state. Keep the failed image tag for investigation.

The rollback script refuses floating aliases such as `latest` and accepts only explicit SHA/version-shaped tags; this format check does not prove GHCR tag immutability. Verify the image digest and restrict package write access separately. It does not read or write a local `.last-good-image`; the previous image must be supplied explicitly. Direct `docker run` is not supported because it can omit the Compose volumes, Valkey network, secrets, and health checks.

## After rollback
- [ ] Backend readiness returns HTTP 200 and `ready=true`.
- [ ] Studio/API smoke test passes; no unexpected 5xx or SLO breach remains.
- [ ] Backup state and schema version are recorded; no migration was silently reversed.
- [ ] Incident timeline, exact image tags, actions, and follow-up are recorded.

## Drill
Monthly on staging only: deploy a SHA-tagged test image, record and verify its GHCR digest, exercise a known-safe failure, roll back to an explicit prior tag, verify backend and Studio, and record time-to-recovery. A SHA tag can still be overwritten unless registry permissions prevent it. No production rollout or restore drill has been executed from this workspace.
