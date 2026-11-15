#!/usr/bin/env bash
# ============================================================
# FINN Loop — Phase 0 کامل: نصب ECC (هارنس ایجنت) + REA (بازبینی رقبا/باگ‌یابی)
#
# منابع رسمی (فقط این‌ها):
#   ECC : https://github.com/affaan-m/ECC            (MIT)
#   REA : https://github.com/morluto/rea             (MIT) — package: rea-agents
#
# این اسکریپت idempotent است: هر بار اجرا شود همان نتیجه را می‌سازد.
# مکان نصب ابزار: TOOLCHAIN_DIR (پیش‌فرض: بیرون از مخزن، ~/toolchain)
#   دلیل بیرون بودن: node_modules هرگز نباید وارد گیت شود و در snapshot ها
#   ضبط نمی‌شود؛ پس نصب باید با اسکریپت بازتولید شود، نه با commit.
#
# استفاده:
#   bash docs/MuscleParadise/finn/install-toolchain.sh            # هر دو
#   bash docs/MuscleParadise/finn/install-toolchain.sh ecc        # فقط ECC
#   bash docs/MuscleParadise/finn/install-toolchain.sh rea        # فقط REA
# ============================================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
TOOLCHAIN_DIR="${TOOLCHAIN_DIR:-$HOME/toolchain}"
FINN_DIR="$ROOT/.finn"
ECC_DIR="$FINN_DIR/ecc"
CLAUDE_DIR="$ROOT/.claude"
MCP_FILE="$ROOT/.mcp.json"

ECC_REPO="${ECC_REPO:-https://github.com/affaan-m/ECC.git}"
REA_PKG="${REA_PKG:-rea-agents}"
# Node حداقلی که REA الزام می‌کند (engines: ^22.23.4 || ^24.22.1 || >=26.12.1)
NODE_PKG_VERSION="${NODE_PKG_VERSION:-24.22.3}"

WHAT="${1:-all}"

log() { printf '[FINN/toolchain] %s\n' "$*"; }
die() { printf '[FINN/toolchain] خطا: %s\n' "$*" >&2; exit 1; }

mkdir -p "$TOOLCHAIN_DIR"

# ------------------------------------------------------------
# 0) Node سازگار با REA — اگر Node موجود کافی نبود، نسخهٔ portable از npm
# ------------------------------------------------------------
node_ok() {
  local v major minor
  command -v node >/dev/null 2>&1 || return 1
  v="$(node -p 'process.versions.node')"
  major="${v%%.*}"
  minor="$(echo "$v" | cut -d. -f2)"
  case "$major" in
    22) [ "$minor" -ge 23 ] ;;
    24) [ "$minor" -ge 22 ] ;;
    26) [ "$minor" -ge 12 ] ;;
    *)  [ "$major" -gt 26 ] ;;
  esac
}

ensure_node() {
  if node_ok; then
    log "Node موجود کافی است: $(node -v)"
    NODE_BIN="$(command -v node)"
    return
  fi
  log "Node سیستم برای REA کافی نیست → نصب portable node $NODE_PKG_VERSION در $TOOLCHAIN_DIR"
  local arch tarball dir
  arch="$(uname -m)"
  case "$arch" in
    x86_64|amd64) dir="node-linux-x64" ;;
    aarch64|arm64) dir="node-linux-arm64" ;;
    *) die "معماری پشتیبانی‌نشده برای node portable: $arch" ;;
  esac
  if [ ! -x "$TOOLCHAIN_DIR/$dir/bin/node" ]; then
    # بستهٔ node-linux-* داخلش پوشهٔ `package/` دارد → بعد از استخراج تغییر نام می‌دهیم
    ( cd "$TOOLCHAIN_DIR" \
      && npm pack "${dir}@${NODE_PKG_VERSION}" >/dev/null \
      && rm -rf "$dir" package \
      && tar xzf "${dir}-${NODE_PKG_VERSION}.tgz" \
      && mv package "$dir" )
  fi
  NODE_BIN="$TOOLCHAIN_DIR/$dir/bin/node"
  [ -x "$NODE_BIN" ] || die "نصب node portable ناموفق بود"
  log "Node portable: $("$NODE_BIN" -v) → $NODE_BIN"
}

# ------------------------------------------------------------
# 1) ECC — کلون رسمی + پین کامیت + نصب در .claude/
# ------------------------------------------------------------
install_ecc() {
  log "== ECC =="
  if [ -d "$ECC_DIR/.git" ]; then
    git -C "$ECC_DIR" fetch --depth 1 origin main
    git -C "$ECC_DIR" checkout -q FETCH_HEAD
  else
    rm -rf "$ECC_DIR"
    git clone --depth 1 --branch main "$ECC_REPO" "$ECC_DIR"
  fi
  local commit; commit="$(git -C "$ECC_DIR" rev-parse HEAD)"
  mkdir -p "$FINN_DIR"
  printf '%s\n' "$commit" > "$FINN_DIR/ecc-commit.txt"
  log "کامیت ECC: $commit"

  # نصب مؤلفه‌ها روی .claude/ (Phase-0 protocol)
  mkdir -p "$CLAUDE_DIR"
  local part
  for part in agents commands skills rules hooks; do
    [ -d "$ECC_DIR/$part" ] || continue
    rm -rf "${CLAUDE_DIR:?}/$part"
    cp -R "$ECC_DIR/$part" "$CLAUDE_DIR/$part"
    printf '   نصب شد: %-9s %s فایل\n' "$part" "$(find "$CLAUDE_DIR/$part" -type f | wc -l)"
  done

  # تأیید ۹ ایجنت قرارداد FINN
  local a missing=0
  for a in planner architect tdd-guide code-reviewer security-reviewer \
           build-error-resolver e2e-runner refactor-cleaner doc-updater; do
    if [ -f "$CLAUDE_DIR/agents/$a.md" ]; then printf '   ✓ %s\n' "$a"; else printf '   ✗ MISSING %s\n' "$a"; missing=1; fi
  done
  [ "$missing" -eq 0 ] || die "همهٔ ۹ ایجنت FINN نصب نشدند"

  # از بین بردن حجم غیرلازم (تصاویر/docs چندزبانه) — نصب‌مایهٔ لازم دست‌نخورده
  local prunable="assets docs docker ecc2 pi tests examples integrations scaffolds legacy-command-shims schemas config .adal .agents .claude-plugin .codebuddy .codex .codex-plugin .cursor .gemini .hermes .kimi .kiro .openclaw .opencode .pi .qwen .trae .github"
  ( cd "$ECC_DIR" && rm -rf $prunable )
  log "صرفه‌جویی فضا: $(du -sh "$ECC_DIR" | cut -f1) باقی ماند"
}

# ------------------------------------------------------------
# 2) REA — نصب rea-agents + نصب skill در .claude/skills + ثبت MCP پروژه‌ای
# ------------------------------------------------------------
install_rea() {
  log "== REA =="
  ensure_node
  local rea_home="$TOOLCHAIN_DIR/rea"
  if [ ! -x "$rea_home/node_modules/.bin/rea" ]; then
    # بستهٔ node-linux-* فقط باینری node دارد، npm ندارد → npm سیستم را کوپل می‌کنیم
    local npm_bin; npm_bin="$(command -v npm || true)"
    [ -n "$npm_bin" ] || die "npm لازم است (برای نصب rea-agents)"
    ( cd "$TOOLCHAIN_DIR" && "$npm_bin" install --no-audit --no-fund \
        --prefix "$rea_home" "${REA_PKG}@latest" >/dev/null )
  fi
  [ -x "$rea_home/node_modules/.bin/rea" ] || die "نصب REA ناموفق بود"

  local rea_bin="$rea_home/node_modules/.bin/rea"
  local ver; ver="$("$NODE_BIN" "$rea_bin" --version 2>/dev/null || echo unknown)"
  log "REA نسخه: $ver"

  # skill: عمداً only-local (بدون نوشتن در ~/.claude تا خودِ مخزن مرجع باشد)
  local skill_src="$rea_home/node_modules/${REA_PKG}/.cursor-plugin/skills/reverse-engineer-anything"
  mkdir -p "$CLAUDE_DIR/skills"
  if [ -d "$skill_src" ]; then
    rm -rf "$CLAUDE_DIR/skills/reverse-engineer-anything"
    cp -R "$skill_src" "$CLAUDE_DIR/skills/"
    log "skill نصب شد: .claude/skills/reverse-engineer-anything ($(find "$CLAUDE_DIR/skills/reverse-engineer-anything" -type f | wc -l) فایل)"
  else
    log "هشدار: skill مبدأ پیدا نشد ($skill_src) — ادامه بدون skill"
  fi

  # ثبت MCP برای این مخزن (مسیرها مطلق و محیط‌محلی‌اند → .mcp.json در گیت نیست)
  cat > "$MCP_FILE" <<EOF
{
  "mcpServers": {
    "rea": {
      "command": "$NODE_BIN",
      "args": ["$rea_bin", "mcp"]
    }
  }
}
EOF
  log "MCP ثبت شد: $MCP_FILE"

  # بررسی سلامت (بدون نصب هیچ موتور native)
  "$NODE_BIN" "$rea_bin" doctor 2>&1 | head -20 || true
}

case "$WHAT" in
  ecc) install_ecc ;;
  rea) install_rea ;;
  all) install_ecc; install_rea ;;
  *) die "استفاده: $0 [all|ecc|rea]" ;;
esac

log "✓ تمام شد. یادآوری: ECC در .finn/ecc (gitignored، کامیت پین‌شده) و REA در $TOOLCHAIN_DIR/rea"
log "  REA برای تحلیل native به Hopper/Ghidra/IDA نیاز دارد (اختیاری)؛ تحلیل JavaScript/APK/SQLite بدون آن کار می‌کند."
