#!/usr/bin/env bash
# measure-baseline.sh — اندازه‌گیری‌های خط پایه (WP 0.1) روی یک درخت کاری.
#
# کاربرد:  measure-baseline.sh <مسیر-ریشهٔ-مخزن> <برچسب> <مسیر-خروجی>
#   مثال:  measure-baseline.sh /path/base-662ff88 before docs/MuscleParadise/audit/evidence/before
#          measure-baseline.sh /home/user/MP        after  docs/MuscleParadise/audit/evidence/after
#
# پیش‌نیاز: ابزارها در مسیرهای زیر (ENV قابل بازنویسی):
#   RUFF (0.17.6)، RADON، LIZARD، VULTURE، BANDIT، PIPAUDIT، DETECT_SECRETS، SEMGREP
#   RECOMMENDED_TOML = ruff-recommended.toml (همین پوشه)
# هر اندازه‌گیری خروجی خام دارد؛ خلاصهٔ عددی در summary.json است.
set -u
ROOT="$(cd "$1" && pwd)"; LABEL="$2"; mkdir -p "$3"; OUT="$(cd "$3" && pwd)"
HERE="$(cd "$(dirname "$0")" && pwd)"
RUFF="${RUFF:-ruff}"; RADON="${RADON:-radon}"; LIZARD="${LIZARD:-lizard}"
VULTURE="${VULTURE:-vulture}"; BANDIT="${BANDIT:-bandit}"; PIPAUDIT="${PIPAUDIT:-pip-audit}"
DETECT="${DETECT_SECRETS:-detect-secrets}"; SEMGREP="${SEMGREP:-semgrep}"
RECOMMENDED_TOML="${RECOMMENDED_TOML:-$HERE/ruff-recommended.toml}"
mkdir -p "$OUT"
BE="$ROOT/mp-app/backend"

# ── ruff: پیکربندی توصیه‌شده (مقایسهٔ منصفانه با base) و پیکربندی همان درخت ──
( cd "$BE" && "$RUFF" check --no-cache --config "$RECOMMENDED_TOML" --output-format concise . > "$OUT/ruff-recommended.txt" 2>&1; echo $? > "$OUT/ruff-recommended.rc" )
( cd "$BE" && "$RUFF" check --no-cache --config "$RECOMMENDED_TOML" --statistics . > "$OUT/ruff-recommended-stats.txt" 2>/dev/null )
( cd "$BE" && "$RUFF" format --no-cache --check . > "$OUT/ruff-format.txt" 2>&1; echo $? > "$OUT/ruff-format.rc" )
( cd "$BE" && "$RUFF" check --no-cache --output-format concise . > "$OUT/ruff-tree-config.txt" 2>&1; echo $? > "$OUT/ruff-tree-config.rc" )
( cd "$BE" && "$RUFF" check --no-cache --select E,F,W,I,N,UP,B,SIM --ignore E501 . > "$OUT/ruff-blocking.txt" 2>&1; echo $? > "$OUT/ruff-blocking.rc" )

# ── تحلیل پیچیدگی و نگه‌داشتنی ──
( cd "$BE" && "$RADON" cc app modules db engine security jobs cache api scripts -s -n C --total-average > "$OUT/radon-cc.txt" 2>&1 )
( cd "$BE" && "$RADON" mi app modules db engine security jobs cache api scripts > "$OUT/radon-mi.txt" 2>&1 )
( cd "$BE" && "$LIZARD" app modules db engine security jobs cache api --CCN 10 --length 60 -w > "$OUT/lizard-warnings.txt" 2>&1 )
( cd "$BE" && "$VULTURE" app modules db engine security jobs cache api scripts devtools --min-confidence 80 > "$OUT/vulture.txt" 2>&1 )
( cd "$BE" && "$BANDIT" -r app modules db engine security jobs cache api scripts -f json -q -o "$OUT/bandit.json" >/dev/null 2>&1 )
( cd "$ROOT" && "$DETECT" scan --all-files --exclude-files 'node_modules|^\.git/|var/|docs/MuscleParadise/audit/evidence' > "$OUT/detect-secrets.json" 2>"$OUT/detect-secrets.err" )

# ── semgrep: قاعدهٔ پروژه و قاعدهٔ ممیزی (کیت) روی backend + studio ──
( cd "$ROOT" && "$SEMGREP" --config .semgrep/project-rules.yml --metrics=off --json -o "$OUT/semgrep-project.json" mp-app/backend >/dev/null 2>&1 )

# ── خلاصهٔ عددی ──
ROOT="$ROOT" OUT="$OUT" LABEL="$LABEL" python3 - <<'PY'
import json, os, re, pathlib
out = pathlib.Path(os.environ["OUT"])
def rc(name):
    p = out / f"{name}.rc"
    return int(p.read_text().strip()) if p.exists() else None
def count_ruff(name):
    t = (out / f"{name}.txt").read_text(encoding="utf-8", errors="replace")
    m = re.search(r"Found (\d+) error", t)
    return int(m.group(1)) if m else (0 if "All checks passed" in t else None)
def count_radon_cc(name):
    lines = (out / name).read_text(encoding="utf-8", errors="replace").splitlines()
    return sum(1 for l in lines if re.search(r" [CDEF] \(", l))
def bandit():
    d = json.loads((out / "bandit.json").read_text())["metrics"]["_totals"]
    return {k.split(".")[1].lower(): d[k] for k in d if k.startswith("SEVERITY.")}
def secrets():
    d = json.loads((out / "detect-secrets.json").read_text())["results"]
    return sum(len(v) for v in d.values())
def semgrep():
    d = json.loads((out / "semgrep-project.json").read_text())
    return {"findings": len(d["results"]), "errors": len(d["errors"])}
s = {
    "label": os.environ["LABEL"],
    "ruff_recommended_findings": count_ruff("ruff-recommended"),
    "ruff_recommended_rc": rc("ruff-recommended"),
    "ruff_format_rc": rc("ruff-format"),
    "ruff_tree_config_findings": count_ruff("ruff-tree-config"),
    "ruff_blocking_rc": rc("ruff-blocking"),
    "radon_cc_C_or_worse": count_radon_cc("radon-cc.txt"),
    "lizard_ccn_over_10": sum(1 for l in (out/"lizard-warnings.txt").read_text(errors="replace").splitlines() if "warning:" in l),
    "vulture_80": sum(1 for l in (out/"vulture.txt").read_text(errors="replace").splitlines() if l.strip()),
    "bandit": bandit(),
    "detect_secrets": secrets(),
    "semgrep_project": semgrep(),
}
(out / "summary.json").write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(s, ensure_ascii=False, indent=2))
PY
