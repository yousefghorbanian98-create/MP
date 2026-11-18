#!/usr/bin/env bash
# M107 — نصب اختیاری Android SDK در GitHub Codespaces (برای «شاهد کامپایل» M87)
#
# چرا فایل جدا و نه بخشی از build تصویر:
#   ۱) تصویر devcontainer عمداً سبک و فقط «اعتبارسنجی منبع» است (Flutter پین‌شده + OpenJDK 17).
#      نصب خودکار SDK + پذیرفتن license اندروید در build، یعنی پذیرفتن یک توافق حقوقی از طرف
#      هر کسی که container را می‌سازد — این انتخاب باید صریح و انسان‌محور بماند.
#   ۲) APK build/signing هرگز جزو handoff این مخزن نبوده (SEC-01 باز است)؛ این اسکریپت فقط
#      کامپایل (Kotlin/Gradle) را ممکن می‌کند، نه انتشار.
#
# این اسکریپت در agent sandbox **اجرا نشده** (dl.google.com از آن محیط مسدود بود)؛ اولین اجرا
# خودش یک گیت است. اگر چیزی رد شد، لاگ را نگه دار و حدس نزن.
#
# استفاده:
#   SDK_SHA256=<sha256> ACCEPT_ANDROID_LICENSES=1 bash .devcontainer/provision-android-sdk.sh
#   SDK_PACKAGES="platform-tools platforms;android-36 build-tools;36.0.0" bash …
set -euo pipefail

: "${ANDROID_SDK_ROOT:=$HOME/android-sdk}"
: "${CMDLINE_TOOLS_VERSION:=13114700}"      # شمارهٔ بیلِ «command line tools only» از صفحهٔ رسمی Android Studio
: "${SDK_URL:=https://dl.google.com/android/repository/commandlinetools-linux-${CMDLINE_TOOLS_VERSION}_latest.zip}"
: "${SDK_SHA256:=}"                        # خالی = بررسی نمی‌شود؛ صریح باید تأیید شود (پایین را بخوان)
: "${SDK_PACKAGES:=platform-tools platforms;android-36 build-tools;36.0.0}"

step() { printf '\n==> %s\n' "$*"; }

if [ ! -d "$ANDROID_SDK_ROOT/cmdline-tools/latest/bin" ]; then
  step "downloading command-line tools → $ANDROID_SDK_ROOT"
  tmp="$(mktemp -d)"
  curl --fail --location --retry 3 --retry-all-errors "$SDK_URL" --output "$tmp/cmdline.zip"

  if [ -n "$SDK_SHA256" ]; then
    printf '%s  %s\n' "$SDK_SHA256" "$tmp/cmdline.zip" | sha256sum --check -
    step "checksum verified"
  else
    # عمداً «ادامه با هشدار» نه «سکوت»: مخزن هیچ hash ساختگی در خود ندارد، و
    # ساختن یک مقدار بدون منبع، از نبودِ pin بدتر است. اگر می‌خواهی پین شود:
    #   sha256sum cmdline.zip → همان را در SDK_SHA256 بگذار و در RUNBOOK ثبت کن.
    echo "WARNING: SDK_SHA256 unset — archive is NOT verified. Downloaded SHA-256:" >&2
    sha256sum "$tmp/cmdline.zip" >&2
    if [ "${SDK_ALLOW_UNPINNED:=0}" != "1" ]; then
      echo "Refusing to install an unverified SDK. Re-run with SDK_ALLOW_UNPINNED=1 (after checking the hash" >&2
      echo "against the official page) or with SDK_SHA256=<that hash> to pin it." >&2
      rm -rf "$tmp"
      exit 2
    fi
  fi

  mkdir -p "$ANDROID_SDK_ROOT/cmdline-tools"
  unzip -q "$tmp/cmdline.zip" -d "$tmp/unz"
  # آرشیو یک پوشهٔ `cmdline-tools/` می‌دهد که sdkmanager در ساختار `latest/` لازم دارد
  rm -rf "$ANDROID_SDK_ROOT/cmdline-tools/latest"
  mv "$tmp/unz/cmdline-tools" "$ANDROID_SDK_ROOT/cmdline-tools/latest"
  rm -rf "$tmp"
else
  step "command-line tools already present — skipping download"
fi

export ANDROID_SDK_ROOT ANDROID_HOME="$ANDROID_SDK_ROOT"
export PATH="$ANDROID_SDK_ROOT/cmdline-tools/latest/bin:$ANDROID_SDK_ROOT/platform-tools:$PATH"

SDKMGR="$ANDROID_SDK_ROOT/cmdline-tools/latest/bin/sdkmanager"
test -x "$SDKMGR" || { echo "sdkmanager missing at $SDKMGR" >&2; exit 3; }

step "sdkmanager --version"
"$SDKMGR" --version

if [ "${ACCEPT_ANDROID_LICENSES:=0}" = "1" ]; then
  step "accepting Android SDK licenses (explicit opt-in: ACCEPT_ANDROID_LICENSES=1)"
  yes | "$SDKMGR" --licenses >/dev/null
else
  step "licenses NOT accepted (set ACCEPT_ANDROID_LICENSES=1 to accept)"
  echo "sdkmanager will fail on the next step unless the licenses are already accepted." >&2
  exit 4
fi

step "installing: $SDK_PACKAGES"
# shellcheck disable=SC2086  # منظور: باز شدن فهرست پکیج‌ها از متغیر
"$SDKMGR" --install $SDK_PACKAGES

step "java in this container"
java -version 2>&1 | head -2

if command -v flutter >/dev/null 2>&1; then
  step "pointing Flutter at the SDK"
  flutter config --android-sdk "$ANDROID_SDK_ROOT" >/dev/null
  flutter doctor -v 2>&1 | sed -n '1,40p'
fi

step "done"
cat <<EOF
Now run (from mp-app/client):
  flutter build apk --debug 2>&1 | tail -20
Expected witness: Kotlin/Gradle compile of MainActivity.kt and OfflineFeedbackDatabase.kt
with NO keystore involvement. If Flutter asks for a different platform/build-tools pair,
re-run with:  SDK_PACKAGES="platform-tools platforms;android-XX build-tools;XX.0.0" bash $0
EOF
