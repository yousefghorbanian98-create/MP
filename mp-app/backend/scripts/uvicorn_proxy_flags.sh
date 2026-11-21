#!/bin/sh
# WP 1.1 / F-01: اعتماد به هدرهای پروکسی فقط برای IPهای `MP_TRUSTED_PROXIES`.
# قبلاً `--forwarded-allow-ips='*'` هر peer را معتمد می‌کرد و `request.client`
# پیش از اپ از X-Forwarded-For جعلی پر می‌شد. خالی بودن فهرست = هیچ هدری پذیرفته
# نمی‌شود (`--no-proxy-headers`). خروجی برای `$(...)` در CMD داکر است.
trusted=$(printf '%s' "${MP_TRUSTED_PROXIES:-}" | tr -d ' ')
if [ -n "$trusted" ]; then
  printf '%s\n' "--proxy-headers --forwarded-allow-ips=$trusted"
else
  printf '%s\n' "--no-proxy-headers"
fi
