"""WP 0.2 scratch runner: the kit's 163x7 matrix with principal re-login when a token is revoked.

Reuses probe_contract's ROUTES/body_for/fill_path/classify unchanged. The only difference from
run_matrix is: after each operation, a cheap liveness call is made per principal; any principal
whose token was revoked by an earlier cell (logout / logout-all / phone-change / role change)
is re-logged-in. Writes /tmp/wp02/matrix-cells.json.
"""
import json, sys, time
from pathlib import Path
import httpx
import probe_contract as pc
from harness_common import Principals, BASE, EVIDENCE, ROLES

ids = json.loads((EVIDENCE / "contract-rbac-findings.json").read_text(encoding="utf-8"))["ids"]
assert ids, "ids must be captured first"
pr = Principals()
principals = [None, *ROLES]
cells, relogins = [], 0

# WP 0.2: the kit probe's generated bodies fail validation for every role on these five
# service-level super_admin-only operations (ensure_owner runs after validation), so the
# matrix could not decide them. Valid bodies make the 403-vs-accept verdict observable.
_SUF = str(int(time.time()))
OVERRIDE = {
    ("POST", "/api/v1/shop/products"): lambda: {"title": "WP02 probe " + _SUF, "sku": "WP02-" + _SUF, "price_rial": 1000},
    ("PATCH", "/api/v1/shop/products/{product_id}"): lambda: {"title": "WP02 probe"},
    ("POST", "/api/v1/shop/gateways"): lambda: {"kind": "cash", "title": "WP02 probe " + _SUF},
    ("PUT", "/api/v1/shop/gateways/{gateway_id}"): lambda: {"kind": "cash", "title": "WP02 probe"},
    ("POST", "/api/v1/shop/prices"): lambda: {"category": "membership", "code": "wp02-" + _SUF, "title": "WP02 probe", "price_rial": 1000},
    ("POST", "/api/v1/shop/change-requests/{request_id}/review"): lambda: {"approve": False, "note": "wp02"},
}

def alive(c, role):
    r = c.get(BASE + "/api/v1/members/me", headers=pr.headers(role))
    return r.status_code == 200

with httpx.Client(base_url=BASE, timeout=60.0) as c:
    for rt in pc.ROUTES:
        method, path = rt["method"], rt["path"]
        guards = rt.get("guards") or []
        allowed = set(rt.get("roles") or [])
        url = pc.fill_path(path, ids)
        body = pc.body_for(method, path, ids)
        if (method, path) in OVERRIDE:
            body = OVERRIDE[(method, path)]()
        for role in principals:
            t0 = time.perf_counter()
            try:
                resp = c.request(method, url, json=body, headers=pr.headers(role))
                status, text = resp.status_code, resp.text
            except Exception as exc:
                status, text = None, f"{type(exc).__name__}: {exc}"
            cls = pc.classify(status)
            obs = cls in ("allowed_2xx", "reached_4xx")
            exp = (role is None and not guards) or (role in allowed) or (role is not None and not guards)
            cells.append(dict(method=method, path=path, role=role or "anon", guards=guards,
                              contract_roles=sorted(allowed), status=status, classification=cls,
                              observed_pass=obs, expected_pass=exp, mismatch=obs != exp,
                              ms=round((time.perf_counter() - t0) * 1000, 1),
                              body_head=text[:160] if isinstance(text, str) else None))
        # liveness check: revoked principals are re-logged-in before the next operation
        for role in ROLES:
            if not alive(c, role):
                relogins += 1
                print(f"relogin after {method} {path}: {role}", flush=True)
                pr = Principals()
                break

out = Path("/tmp/wp02/matrix-cells.json")
out.write_text(json.dumps({"cells": cells, "relogins": relogins}, ensure_ascii=False), encoding="utf-8")
mm = sum(c["mismatch"] for c in cells)
print("cells", len(cells), "mismatch", mm, "relogins", relogins, flush=True)
