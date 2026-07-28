# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app

FROM base AS builder
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM base AS runtime
RUN addgroup --system app \
    && adduser --system --ingroup app --home /home/app app
ENV HOME=/home/app \
    PATH=/home/app/.local/bin:$PATH
COPY --from=builder --chown=app:app /root/.local /home/app/.local
COPY --chown=app:app app ./app
USER app

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
