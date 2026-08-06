FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/
COPY kb/ kb/

ENV PYTHONUNBUFFERED=1
# FAISS index and session DB live here - mount a volume in production so they persist across restarts.
ENV FAISS_INDEX_DIR=/app/data/faiss_index
ENV SESSION_DB_PATH=/app/data/sessions.db

EXPOSE 8000

# Build the FAISS index at container start if it doesn't already exist (e.g. fresh volume), then serve.
CMD ["sh", "-c", "test -f $FAISS_INDEX_DIR/index.faiss || python -m app.ingest; uvicorn app.main:app --host 0.0.0.0 --port 8000"]
