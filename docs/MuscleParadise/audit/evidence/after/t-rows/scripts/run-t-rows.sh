#!/bin/bash
# Runs the non-server and API-server probes for T-rows; each step logs its exit code.
export AUDIT_EVIDENCE=/home/user/MP/docs/MuscleParadise/audit/evidence/after/t-rows
export MP_SECRET_KEY=audit-harness-only-secret-0123456789abcdef
export MP_ENVIRONMENT=development
mkdir -p "$AUDIT_EVIDENCE"
cd /tmp/run/audit
PY=/tmp/run/venv/bin/python
step(){ name=$1; shift; echo "=== $name START $(date +%T)"; "$@" > "$AUDIT_EVIDENCE/$name.log" 2>&1; rc=$?; echo "=== $name RC=$rc $(date +%T)"; }
step scan_ui_wiring $PY scan_ui_wiring.py
step repro_rbac $PY repro_rbac_systemerror.py
step bench_logging $PY bench_logging.py
step contract_seed $PY probe_contract.py seed
step contract_matrix $PY probe_contract.py matrix
step contract_invalid $PY probe_contract.py invalid
step invalid_authed $PY probe_invalid_authed.py
step live_security $PY probe_live_security.py
step otp_limits_all $PY probe_otp_limits.py all
step otp_bruteforce $PY probe_otp_limits.py bruteforce
echo ALL_STEPS_DONE
