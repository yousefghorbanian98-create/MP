# Muscle Paradise — ایمیج بک‌اند (M32/استقرار)
# ساخت از ریشهٔ مخزن: docker build -f mp-app/backend/Dockerfile -t mp-backend .
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 TZ=Asia/Tehran

WORKDIR /srv/mp
COPY mp-app/backend/ ./backend/
COPY mp-app/shared/design-tokens.json /srv/mp/shared/design-tokens.json
WORKDIR /srv/mp/backend

RUN pip install --no-cache-dir .

# داده/بکاپ روی ولوم (docker-compose) — داده هرگز داخل ایمیج نیست
ENV MP_DATABASE_URL=sqlite:////data/mp.db
VOLUME ["/data", "/backups"]

EXPOSE 8000
# مهاجرت ← سرویس؛ سلامت‌سنجی داخلی /health
# M48-c2 — worker count matters here, it is not a tuning detail.
# Measured in the sandbox with 300 concurrent users, identical code:
#   1 worker  → 373 ms p50, QueuePool timeout 500s, 199 req/s
#   4 workers →   9 ms p50, zero errors,           304 req/s
# The app is sync-only, so one process cannot use more than one core and the
# other cores idle while requests queue on the pool. WEB_CONCURRENCY lets the
# platform size this to the real CPU count; 4 is the measured floor.
CMD ["sh", "-c", "if [ -n \"${PROMETHEUS_MULTIPROC_DIR:-}\" ]; then mkdir -p \"$PROMETHEUS_MULTIPROC_DIR\" && rm -f \"$PROMETHEUS_MULTIPROC_DIR\"/*; fi && alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${WEB_CONCURRENCY:-4} $(sh scripts/uvicorn_proxy_flags.sh)"]
