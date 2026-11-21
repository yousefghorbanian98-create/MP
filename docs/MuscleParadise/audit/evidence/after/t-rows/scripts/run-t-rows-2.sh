#!/bin/bash
export AUDIT_EVIDENCE=/home/user/MP/docs/MuscleParadise/audit/evidence/after
export MP_SECRET_KEY=audit-harness-only-secret-0123456789abcdef
export MP_ENVIRONMENT=development
cd /tmp/run/audit
PY=/tmp/run/venv/bin/python
step(){ name=$1; shift; echo "=== $name START $(date +%T)"; "$@" > "$AUDIT_EVIDENCE/t-rows/$name.log" 2>&1; rc=$?; echo "=== $name RC=$rc $(date +%T)"; }
step contract_seed $PY probe_contract.py seed
step contract_matrix $PY probe_contract.py matrix
step contract_invalid $PY probe_contract.py invalid
step invalid_authed $PY probe_invalid_authed.py
step otp_limits_all $PY probe_otp_limits.py all
step otp_bruteforce $PY probe_otp_limits.py bruteforce
step live_security $PY probe_live_security.py
echo ALL_STEPS_DONE
