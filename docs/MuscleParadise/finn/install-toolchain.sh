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
REA_VERSION="${REA_VERSION:-6.9.0}"
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
  local v major minor patch
  command -v node >/dev/null 2>&1 || return 1
  v="$(node -p 'process.versions.node')"
  IFS=. read -r major minor patch <<< "$v"
  patch="${patch%%-*}"
  case "$major" in
    22) (( minor > 23 || (minor == 23 && patch >= 4) )) ;;
    24) (( minor > 22 || (minor == 22 && patch >= 1) )) ;;
    26) (( minor > 12 || (minor == 12 && patch >= 1) )) ;;
    *)  (( major > 26 )) ;;
  esac
}

ensure_node() {
  if node_ok; then
    log "Node موجود کافی است: $(node -v)"
    NODE_BIN="$(command -v node)"
    return
  fi
  log "Node سیستم برای REA کافی نیست → نصب portable node $NODE_PKG_VERSION در $TOOLCHAIN_DIR"
  local arch dir stage
  arch="$(uname -m)"
  case "$arch" in
    x86_64|amd64) dir="node-linux-x64" ;;
    aarch64|arm64) dir="node-linux-arm64" ;;
    *) die "معماری پشتیبانی‌نشده برای node portable: $arch" ;;
  esac
  if [ ! -x "$TOOLCHAIN_DIR/$dir/bin/node" ]; then
    [ ! -e "$TOOLCHAIN_DIR/$dir" ] || die "مسیر موجود و ناقص است؛ برای حفظ داده‌ها دست‌نخورده ماند: $TOOLCHAIN_DIR/$dir"
    stage="$(mktemp -d "$TOOLCHAIN_DIR/.node-install.XXXXXX")"
    if ! ( cd "$stage" \
      && npm pack --silent "${dir}@${NODE_PKG_VERSION}" \
      && tar xzf "${dir}-${NODE_PKG_VERSION}.tgz" ); then
      rm -rf -- "$stage"
      die "دریافت یا استخراج portable Node ناموفق بود"
    fi
    [ -x "$stage/package/bin/node" ] || { rm -rf -- "$stage"; die "بستهٔ Node معتبر نیست"; }
    mv "$stage/package" "$TOOLCHAIN_DIR/$dir"
    rm -rf -- "$stage"
  fi
  NODE_BIN="$TOOLCHAIN_DIR/$dir/bin/node"
  [ -x "$NODE_BIN" ] || die "نصب node portable ناموفق بود"
  log "Node portable: $("$NODE_BIN" -v) → $NODE_BIN"
}

# ------------------------------------------------------------
# 1) ECC — checkout دقیقِ کامیت پین‌شده؛ .claude موجود هرگز حذف/بازنویسی نمی‌شود
# ------------------------------------------------------------
install_ecc() {
  log "== ECC =="
  [ ! -L "$FINN_DIR" ] || die "مسیر FINN نباید symlink باشد: $FINN_DIR"
  [ ! -L "$ECC_DIR" ] || die "مسیر ECC نباید symlink باشد: $ECC_DIR"
  [ ! -L "$CLAUDE_DIR" ] || die "مسیر .claude نباید symlink باشد: $CLAUDE_DIR"
  [ -s "$FINN_DIR/ecc-commit.txt" ] || die "پین ECC موجود نیست: $FINN_DIR/ecc-commit.txt"
  local commit actual part src_file rel dst_file added conflicts
  commit="$(tr -d '[:space:]' < "$FINN_DIR/ecc-commit.txt")"
  [[ "$commit" =~ ^[0-9a-f]{40}$ ]] || die "پین ECC باید یک SHA کامل ۴۰ رقمی باشد"

  if [ -e "$ECC_DIR" ]; then
    [ -d "$ECC_DIR/.git" ] || die "مسیر ECC موجود اما مخزن git نیست؛ برای حفظ داده‌ها دست‌نخورده ماند: $ECC_DIR"
    [ -z "$(git -C "$ECC_DIR" status --porcelain --untracked-files=all)" ] || die "کلون ECC تغییرات محلی دارد؛ برای حفظ آن متوقف شدم"
    if git -C "$ECC_DIR" remote get-url origin >/dev/null 2>&1; then
      git -C "$ECC_DIR" remote set-url origin "$ECC_REPO"
    else
      git -C "$ECC_DIR" remote add origin "$ECC_REPO"
    fi
  else
    mkdir -p "$ECC_DIR"
    git -C "$ECC_DIR" init -q
    git -C "$ECC_DIR" remote add origin "$ECC_REPO"
  fi
  git -C "$ECC_DIR" fetch --depth 1 origin "$commit"
  git -C "$ECC_DIR" checkout -q --detach FETCH_HEAD
  actual="$(git -C "$ECC_DIR" rev-parse HEAD)"
  [ "$actual" = "$commit" ] || die "کامیت دریافتی ECC با پین برابر نیست"
  log "کامیت ECC تأیید شد: $actual"

  # همگام‌سازی افزایشی: فایل‌های حاضر حفظ می‌شوند؛ فقط فایل غایب کپی می‌شود.
  # اختلاف نسخه با prompt محلی گزارش می‌شود، نه اینکه بی‌اجازه overwrite شود.
  mkdir -p "$CLAUDE_DIR"
  for part in agents commands skills rules hooks; do
    [ -d "$ECC_DIR/$part" ] || continue
    [ ! -L "$CLAUDE_DIR/$part" ] || die "مسیر مؤلفه symlink است و دست‌نخورده ماند: $CLAUDE_DIR/$part"
    if [ -d "$CLAUDE_DIR/$part" ] && [ -n "$(find "$CLAUDE_DIR/$part" -type l -print -quit)" ]; then
      die "داخل مؤلفهٔ محلی symlink وجود دارد؛ برای حفظ داده‌ها متوقف شدم: $CLAUDE_DIR/$part"
    fi
    added=0
    conflicts=0
    while IFS= read -r -d '' src_file; do
      rel="${src_file#"$ECC_DIR/$part/"}"
      dst_file="$CLAUDE_DIR/$part/$rel"
      if [ -e "$dst_file" ] || [ -L "$dst_file" ]; then
        if ! cmp -s -- "$src_file" "$dst_file" 2>/dev/null; then
          conflicts=$((conflicts + 1))
        fi
      else
        mkdir -p "$(dirname "$dst_file")"
        cp -p -- "$src_file" "$dst_file"
        added=$((added + 1))
      fi
    done < <(find "$ECC_DIR/$part" -type f -print0)
    log "$part: $added فایل افزوده شد؛ $conflicts فایلِ محلی متفاوت حفظ شد"
  done

  # تأیید ۹ ایجنت قرارداد FINN
  local a missing=0
  for a in planner architect tdd-guide code-reviewer security-reviewer \
           build-error-resolver e2e-runner refactor-cleaner doc-updater; do
    if [ -f "$CLAUDE_DIR/agents/$a.md" ]; then printf '   ✓ %s\n' "$a"; else printf '   ✗ MISSING %s\n' "$a"; missing=1; fi
  done
  [ "$missing" -eq 0 ] || die "همهٔ ۹ ایجنت FINN نصب نشدند"
}

# ------------------------------------------------------------
# 2) REA — نصب rea-agents + نصب skill در .claude/skills + ثبت MCP پروژه‌ای
# ------------------------------------------------------------
install_rea() {
  log "== REA =="
  ensure_node
  local rea_home="$TOOLCHAIN_DIR/rea"
  local rea_bin="$rea_home/node_modules/.bin/rea"
  local package_json="$rea_home/node_modules/${REA_PKG}/package.json"
  local installed_ver=""
  if [ -f "$package_json" ]; then
    installed_ver="$("$NODE_BIN" -e 'process.stdout.write(require(process.argv[1]).version)' "$package_json" 2>/dev/null || true)"
  fi
  if [ ! -x "$rea_bin" ] || [ "$installed_ver" != "$REA_VERSION" ]; then
    # npm سیستم فقط بسته را دریافت می‌کند؛ اجرای REA همیشه با Node سازگارِ بالا انجام می‌شود.
    local npm_bin; npm_bin="$(command -v npm || true)"
    [ -n "$npm_bin" ] || die "npm لازم است (برای نصب rea-agents)"
    ( cd "$TOOLCHAIN_DIR" && "$npm_bin" install --no-audit --no-fund \
        --prefix "$rea_home" "${REA_PKG}@${REA_VERSION}" >/dev/null )
  fi
  [ -x "$rea_bin" ] || die "نصب REA ناموفق بود"

  local ver; ver="$("$NODE_BIN" "$rea_bin" --version 2>/dev/null || echo unknown)"
  [ "$ver" = "$REA_VERSION" ] || die "نسخهٔ REA با نسخهٔ پین‌شده برابر نیست: $ver"
  log "REA نسخهٔ پین‌شده: $ver"

  # skill: محلی و افزایشی؛ محتوای موجود هرگز بی‌اجازه حذف یا overwrite نمی‌شود.
  local skill_src="$rea_home/node_modules/${REA_PKG}/.cursor-plugin/skills/reverse-engineer-anything"
  local skill_dst="$CLAUDE_DIR/skills/reverse-engineer-anything"
  [ ! -L "$CLAUDE_DIR/skills" ] || die "مسیر .claude/skills symlink است و دست‌نخورده ماند"
  mkdir -p "$CLAUDE_DIR/skills"
  if [ -d "$skill_src" ]; then
    [ ! -L "$skill_dst" ] || die "مسیر REA skill symlink است و دست‌نخورده ماند: $skill_dst"
    if [ -e "$skill_dst" ]; then
      [ -d "$skill_dst" ] || die "مسیر skill موجود اما پوشه نیست؛ دست‌نخورده ماند: $skill_dst"
      bash "$ROOT/docs/MuscleParadise/finn/check-rea-skill.sh" \
        "$skill_src" "$skill_dst" "$rea_home/node_modules/${REA_PKG}/LICENSE" \
        || die "skill محلی با نسخهٔ پین‌شده فرق دارد؛ برای حفظ محتوا overwrite نشد: $skill_dst"
      log "skill از قبل نصب و با نسخهٔ پین‌شده سازگار است (مجوز محلی معتبر حفظ می‌شود؛ $(find "$skill_dst" -type f | wc -l) فایل)"
    else
      cp -R "$skill_src" "$skill_dst"
      log "skill نصب شد: .claude/skills/reverse-engineer-anything ($(find "$skill_dst" -type f | wc -l) فایل)"
    fi
  else
    log "هشدار: skill مبدأ پیدا نشد ($skill_src) — ادامه بدون skill"
  fi

  # ثبت MCP پروژه‌ای با حفظ سرورهای دیگر در فایل موجود.
  "$NODE_BIN" - "$MCP_FILE" "$NODE_BIN" "$rea_bin" <<'NODE'
const fs = require("node:fs");
const [file, nodeBin, reaBin] = process.argv.slice(2);
let config = {};
if (fs.existsSync(file)) {
  config = JSON.parse(fs.readFileSync(file, "utf8"));
  if (!config || typeof config !== "object" || Array.isArray(config)) {
    throw new Error("MCP config root must be a JSON object");
  }
}
const servers = config.mcpServers ?? {};
if (!servers || typeof servers !== "object" || Array.isArray(servers)) {
  throw new Error("mcpServers must be a JSON object");
}
servers.rea = { command: nodeBin, args: [reaBin, "mcp"] };
config.mcpServers = servers;
const temp = `${file}.tmp-${process.pid}`;
fs.writeFileSync(temp, `${JSON.stringify(config, null, 2)}\n`, { mode: 0o600 });
fs.renameSync(temp, file);
NODE
  log "MCP ثبت شد: $MCP_FILE (سایر پیکربندی‌ها حفظ شدند)"

  # بررسی سلامت؛ موتورهای native اختیاری‌اند و خودکار نصب نمی‌شوند.
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
