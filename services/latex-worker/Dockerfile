FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN useradd --create-home --uid 10001 appuser

COPY packages/tailored_kit /app/packages/tailored_kit
COPY services/latex-worker/requirements.txt /app/requirements.txt

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -e /app/packages/tailored_kit \
    && pip install -r /app/requirements.txt

COPY services/latex-worker/app /app/app

RUN chown -R appuser:appuser /app
USER appuser

CMD ["python", "-m", "app.worker"]
