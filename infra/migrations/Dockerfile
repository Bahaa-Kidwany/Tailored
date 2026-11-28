FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /workspace

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install "alembic>=1.13.0" "sqlalchemy>=2.0.30" "psycopg[binary]>=3.2.0"

COPY infra/migrations /workspace/infra/migrations

ENTRYPOINT ["python", "infra/migrations/run_migrations.py"]
