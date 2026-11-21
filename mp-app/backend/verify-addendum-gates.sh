#!/usr/bin/env bash
# verify-addendum-gates.sh — گیت‌های عددی الحاقیهٔ A1.3 (اجرای بی‌ناظر)
#
# کاربرد:    RUFF=/path/to/ruff ./verify-addendum-gates.sh [before|after-era|after-wp26|after-wp36|after-wp45]
# محل اجرا:  mp-app/backend
# نیازمندی:  ruff 0.17.x (با نسخهٔ دیگر اعداد فرق می‌کنند)
# خروجی:     جدول + «PASS» یا «ACTION» و exit code (0 = همهٔ گیت‌های مطلق منطبق)
#
# مبنای اعداد مطلق (430/52/419/51/39/6/3) commit 662ff88 است. روی شاخهٔ جاری (HEAD)
# کدِ WP 1.x اضافه شده و عددهای مطلق جابه‌جا می‌شوند؛ آن‌جا فقط گیت‌های «صفر» و
# «نگه‌داشتنیِ ۲۰ noqa» معتبرند و گیت‌های مطلق BLOCKED-NUMERIC گزارش می‌شوند.
# CFG را خالی بگذار اگر پیکربندی در pyproject.toml نصب است؛ وگرنه CFG=/path/to/ruff.toml.
set -u

STAGE="${1:-before}"
RUFF="${RUFF:-ruff}"
CFG="${CFG:-}"

case "$STAGE" in
  before|after-era|after-wp26|after-wp36|after-wp45) ;;
  *) echo "FATAL: stage نامعتبر: $STAGE"; exit 2 ;;
esac
command -v "$RUFF" >/dev/null 2>&1 || { echo "FATAL: ruff پیدا نشد ⇒ RUFF=/path/to/ruff"; exit 2; }

CARG=()
[ -n "$CFG" ] && CARG=(--config "$CFG")
OUT="$(mktemp)"; STAT="$(mktemp)"
trap 'rm -f "$OUT" "$STAT"' EXIT
"$RUFF" check --no-cache "${CARG[@]}" --output-format concise . >"$OUT" 2>&1
"$RUFF" check --no-cache "${CARG[@]}" --statistics . >"$STAT" 2>/dev/null
FMT="$("$RUFF" format --no-cache "${CARG[@]}" --check . 2>&1 | tail -1)"

RV="$("$RUFF" --version | awk '{print $2}')"
HEADSHA="$(git rev-parse --short HEAD 2>/dev/null || echo n/a)"

total_err() { grep -oE 'Found [0-9]+ error' "$OUT" | grep -oE '[0-9]+' | head -1; }
rule_count() { awk -v c="$1" '$2==c{print $1; f=1} END{if(!f) print 0}' "$STAT" | head -1; }
distinct_rules() { grep -cE '^[[:space:]]*[0-9]+[[:space:]]+[A-Z]+[0-9]+' "$STAT"; }

fail=0
row() { # <نام> <موردانتظار> <واقعی> <gate|info>
  local n="$1" e="$2" a="$3" lvl="${4:-gate}" v="INFO"
  if [ "$lvl" = gate ]; then
    if [ "$e" = "$a" ]; then v="MATCH"; else v="BLOCKED-NUMERIC"; fail=$((fail+1)); fi
  fi
  printf '| %-38s | %10s | %10s | %s |\n' "$n" "$e" "$a" "$v"
}

echo "== stage=$STAGE  head=$HEADSHA  ruff=$RV  cfg=${CFG:-<pyproject.toml>}"
echo "| گیت | موردانتظار | واقعی | نتیجه |"
echo "|---|---|---|---|"

case "$RV" in 0.17.*) RVOK=0.17.x ;; *) RVOK=other ;; esac
row "ruff نسخه (0.17.x)" "0.17.x" "$RVOK" gate

ERR="$(total_err)"; ERR="${ERR:-0}"
DIST="$(distinct_rules)"
case "$STAGE" in
  before)    row "کل یافته" 430 "$ERR" gate; row "قواعدِ متمایز" 52 "$DIST" gate ;;
  after-era) row "کل یافته" 419 "$ERR" gate; row "قواعدِ متمایز" 51 "$DIST" gate ;;
  *)         row "کل یافته (ثبتی)" "-" "$ERR" info; row "قواعدِ متمایز (ثبتی)" "-" "$DIST" info ;;
esac

case "$STAGE" in before|after-era|after-wp26|after-wp36) EXP_S608=4 ;; *) EXP_S608=0 ;; esac
case "$STAGE" in before|after-era) EXP_RUF=39 ;; after-wp26|after-wp36) EXP_RUF=4 ;; *) EXP_RUF=0 ;; esac
case "$STAGE" in after-wp26|after-wp36|after-wp45) EXP_TRY=0 ;; *) EXP_TRY=6 ;; esac
case "$STAGE" in after-wp36|after-wp45) EXP_DTZ=0 ;; *) EXP_DTZ=3 ;; esac
row "RUF100 (noqa بلااثر)" "$EXP_RUF" "$(rule_count RUF100)" gate
row "TRY400" "$EXP_TRY" "$(rule_count TRY400)" gate
row "DTZ011" "$EXP_DTZ" "$(rule_count DTZ011)" gate
row "C901 (پیچیدگی؛ F‑15 نه گیت این WP)" "-" "$(rule_count C901)" info
NEED="$(echo "$FMT" | grep -oE '^[0-9]+ files? would be reformatted' | grep -oE '^[0-9]+' || true)"
row "format: فایل‌های نیازمند قالب‌بندی" "0" "${NEED:-0}" gate

# ۲۰ noqa ممنوع‌الحذف (§۱‑الف) — هر کدام باید هنوز noqa داشته باشد
KEEP20="api/v1/monitoring.py:24 api/v1/monitoring.py:40 api/v1/monitoring.py:65
cache/store.py:65 cache/store.py:74 cache/store.py:83 cache/store.py:92 cache/store.py:103
modules/ai/router.py:28 modules/auth/router.py:56 modules/face_id/deep.py:74
modules/outbox/service.py:115 scripts/dast.py:81 scripts/dast.py:98 scripts/dast.py:115
scripts/dast.py:176 scripts/dast.py:187 scripts/deploy_gate.py:174
tests/integration/test_phase8_reports.py:79 tests/integration/test_qf10_period_report.py:73"
# شمارهٔ خط‌ها مبنای 662ff88 است؛ روی HEAD کدِ بالاتر جابه‌جا شده. پس شمارش به‌ازای فایل:
# هر فایل باید دست‌کم به‌تعداد ارجاع‌هایش noqa داشته باشد (حذف واقعی را می‌گیرد، جابه‌جایی را نه).
LIST="$(echo "$KEEP20" | tr ' ' '\n' | grep .)"
k=0
for f in $(echo "$LIST" | cut -d: -f1 | sort -u); do
  need=$(echo "$LIST" | grep -c "^$f:")
  have=$(grep -c '# noqa' "$f" 2>/dev/null || true)
  if [ "${have:-0}" -ge "$need" ]; then k=$((k+need)); fi
done
row "۲۰ noqa ممنوع‌الحذف" "20" "$k" gate

# چهار noqa: S608 روی خطوط F‑22 (§۳‑۲) — تا پیش از WP 4.5 باید بمانند
S608_N="$(grep -c '# noqa: S608' db/migrations/versions/c3f01ab129e2_*.py 2>/dev/null | head -1)"
row "noqa: S608 در c3f01ab129e2" "$EXP_S608" "${S608_N:-0}" gate

if [ "$STAGE" = after-wp36 ] || [ "$STAGE" = after-wp45 ]; then
  DT="$(grep -rn 'date\.today()' modules app engine jobs 2>/dev/null | wc -l | tr -d ' ')"
  row "date.today() در ۴ دایرکتوری" "0" "$DT" gate
  TZN="$(grep -rl 'TZ=' ../infra 2>/dev/null | wc -l | tr -d ' ')"
  row "ENV TZ در infra (لایهٔ دوم)" "-" "$TZN" info
fi

echo "== گیت‌های نامنطبق: $fail"
if [ "$fail" -eq 0 ]; then
  echo "PASS"
  exit 0
else
  echo "ACTION (§۳‑۱): همین WP را متوقف کن · بلوکِ §۳‑۵ را در EXECUTION-LOG.md بنویس · پیکربندی را دستکاری نکن · به WP مستقلِ بعدی برو."
  exit 1
fi
