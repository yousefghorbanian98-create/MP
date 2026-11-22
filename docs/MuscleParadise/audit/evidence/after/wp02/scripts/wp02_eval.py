"""WP 0.2 evaluator: observed matrix cells vs declared effective access (api/routes.json).

Rule (3-valued, per cell):
  observed_pass = status in 2xx or 4xx (guard passed; FastAPI runs guards before body validation).
  role r in always_roles       -> must observed_pass
  role r not in roles          -> must NOT observed_pass
  otherwise (conditional)      -> either outcome accepted; reason recorded from scopes/guards
  anonymous: 'always' -> pass, 'never' -> deny, 'may' -> either
Also reports the kit's binary rule (role in roles <=> observed_pass) for transparency.
"""
import json, collections, sys
CELLS = json.load(open(sys.argv[1]))["cells"]
ROUTES = {(o["method"], o["path"]): o for o in json.load(open(sys.argv[2]))["operations"]}
out = {"cells": len(CELLS), "exact": 0, "conditional": collections.Counter(), "mismatch": [], "server_errors": 0, "binary_kit_mismatch": 0}
for c in CELLS:
    op = ROUTES[(c["method"], c["path"])]
    cls = c["classification"]
    if cls in ("server_error_5xx", "transport_error", "other_500") or (c["status"] or 0) >= 500:
        out["server_errors"] += 1
    obs = c["observed_pass"]
    r = c["role"]
    if r == "anon":
        decl = op["anonymous"]
        ok = (decl == "always" and obs) or (decl == "never" and not obs) or decl == "may"
        kind = "exact" if decl in ("always", "never") else f"conditional:anonymous={decl}"
        binary = (not op["guards"]) == obs
    else:
        if r in op["always_roles"]:
            ok, kind = obs, "exact"
        elif r not in op["roles"]:
            ok, kind = (not obs), "exact"
        else:
            ok = True
            kind = "conditional:" + ",".join(op["scopes"]) if op["scopes"] else "conditional:grant" if any(g.startswith("grant:") for g in op["guards"]) else "conditional:unknown"
        binary = (r in op["roles"]) == obs
    if not binary:
        out["binary_kit_mismatch"] += 1
    if ok:
        if kind == "exact":
            out["exact"] += 1
        else:
            out["conditional"][kind] += 1
    else:
        out["mismatch"].append({"method": c["method"], "path": c["path"], "role": r, "status": c["status"], "declared_roles": op["roles"], "always": op["always_roles"], "anonymous": op["anonymous"]})
out["conditional"] = dict(out["conditional"])
out["conditional_total"] = sum(out["conditional"].values())
out["mismatch_total"] = len(out["mismatch"])
print(json.dumps({k: v for k, v in out.items() if k != "mismatch"}, ensure_ascii=False, indent=1))
print("mismatch_total", out["mismatch_total"])
for m in out["mismatch"][:40]:
    print(m)
json.dump(out, open(sys.argv[3], "w"), ensure_ascii=False, indent=1)
