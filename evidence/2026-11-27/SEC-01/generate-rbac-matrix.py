#!/usr/bin/env python3
"""Emit the SEC-01 static route-operation × role decisions from security.rbac."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "mp-app/backend"
ROUTES = BACKEND / "api/routes.json"
RBAC = BACKEND / "security/rbac.py"
ROLES = ["member", "coach", "reception", "manager", "admin", "super_admin"]

sys.path.insert(0, str(BACKEND))
from security.rbac import enforce  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).with_name("rbac-matrix.txt"),
    )
    args = parser.parse_args()

    data = json.loads(ROUTES.read_text(encoding="utf-8"))
    operations = data["operations"]
    manifest_roles = {role for op in operations for role in op.get("roles", [])}
    if manifest_roles != set(ROLES):
        raise SystemExit(f"route role set changed: {sorted(manifest_roles)}")

    target_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()
    counts: Counter[tuple[str, str]] = Counter()
    rows: list[tuple[str, str, str, str]] = []
    for operation in operations:
        method = operation["method"].upper()
        path = operation["path"]
        for role in ROLES:
            decision = "ALLOW" if enforce(role, path, method) else "DENY"
            counts[(role, decision)] += 1
            rows.append((method, path, role, decision))

    expected = len(operations) * len(ROLES)
    if len(rows) != expected:
        raise SystemExit(f"row count mismatch: expected={expected}, actual={len(rows)}")

    out = args.out if args.out.is_absolute() else ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "SEC-01 — routes.json × all six application roles — static RBAC decision matrix",
        f"tested_sha={target_sha}",
        f"generated_utc_date={datetime.now(timezone.utc).date().isoformat()}",
        f"route_manifest=mp-app/backend/api/routes.json sha256={sha256(ROUTES)}",
        f"rbac_source=mp-app/backend/security/rbac.py sha256={sha256(RBAC)}",
        "decision_function=security.rbac.enforce(role, path, method)",
        f"operations={len(operations)} unique_paths={len({op['path'] for op in operations})} roles={len(ROLES)} rows={len(rows)}",
        "role_order=" + ",".join(ROLES),
        "path_templates=used verbatim from routes.json (curly-brace parameter names retained)",
        "scope=policy-engine decision only; routes.json role annotations, route guards/grants, anonymous access, ownership/ABAC, handler/service behavior, and HTTP responses are not evaluated here.",
        "",
        "| method | path | role | decision |",
        "|---|---|---|---|",
    ]
    lines.extend(f"| {method} | {path} | {role} | {decision} |" for method, path, role, decision in rows)
    lines += ["", "## Counts by role", "", "| role | ALLOW | DENY | total |", "|---|---:|---:|---:|"]
    for role in ROLES:
        allow = counts[(role, "ALLOW")]
        deny = counts[(role, "DENY")]
        lines.append(f"| {role} | {allow} | {deny} | {allow + deny} |")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"out={out}")
    print(f"tested_sha={target_sha} operations={len(operations)} paths={len({op['path'] for op in operations})} rows={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
