# FasalRakshak backend image (Phase 1).
# Python 3.13-slim: stable wheel availability for FastAPI/SQLAlchemy/asyncpg.
# asyncpg is a self-contained driver — no libpq needed at runtime.

FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Migrations run on start so the schema matches the deployed code (docs/15 §3),
# then the API serves. Compose may override `command`.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]