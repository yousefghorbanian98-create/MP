#!/usr/bin/env bash
# Muscle Paradise — فشرده‌سازی فایل‌های استاتیک (ویدیوهای حرکات) با ffmpeg (لایهٔ ۱۱/۱۲)
# استفاده: bash compress-media.sh <input-dir> <output-dir>
set -euo pipefail

IN_DIR="${1:?ورودی لازم است}"
OUT_DIR="${2:?خروجی لازم است}"
mkdir -p "$OUT_DIR"

for f in "$IN_DIR"/*.mp4 "$IN_DIR"/*.mov "$IN_DIR"/*.mkv; do
  [ -e "$f" ] || continue
  name="$(basename "$f")"
  out="$OUT_DIR/${name%.*}.mp4"
  echo "[compress] $name → $out"
  ffmpeg -y -i "$f" \
    -vcodec libx264 -crf 26 -preset medium \
    -acodec aac -b:a 128k \
    -movflags +faststart \
    "$out" </dev/null >/dev/null 2>&1
done
echo "[compress] انجام شد → $OUT_DIR"
