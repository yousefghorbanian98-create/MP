# Muscle Paradise — ایمیج بک‌اند (M32/استقرار)
# ساخت از ریشهٔ مخزن: docker build -f mp-app/backend/Dockerfile -t mp-backend .
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

WORKDIR /srv/mp
COPY mp-app/backend/ ./backend/
WORKDIR /srv/mp/backend

RUN pip install --no-cache-dir .

# داده/بکاپ روی ولوم (docker-compose) — داده هرگز داخل ایمیج نیست
ENV MP_DATABASE_URL=sqlite:////data/mp.db
VOLUME ["/data", "/backups"]

EXPOSE 8000
# مهاجرت ← سرویس؛ سلامت‌سنجی داخلی /health
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
