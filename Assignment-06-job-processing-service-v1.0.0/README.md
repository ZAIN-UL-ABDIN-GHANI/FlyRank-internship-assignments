# job-processing-service

**Version 1.0.0**

Asynchronous background job processing system for long-running AI
operations. Built against `background-job-processing-system-design.md`
(SDD v1.0) - that document is the source of truth for anything not covered
below. See `docs/VERIFICATION_MATRIX.md` for a requirement-by-requirement
trace to this implementation, and `docs/KNOWN_LIMITATIONS.md` before
deploying.

## What's implemented

- Full job lifecycle: submit (`POST /v1/jobs`), status (`GET /v1/jobs/{id}`),
  cancel (`DELETE /v1/jobs/{id}`), list (`GET /v1/jobs`)
- Celery worker execution with retry/backoff, dead-lettering, and both
  client-side and worker-side idempotency
- PostgreSQL persistence + Redis status cache (fails open if Redis is down)
- Rate limiting, payload size limits, and an operation allow-list
- Structured JSON logging (API and worker)
- Prometheus metrics (API and worker) + example alert rules
- Unit tests (mocked I/O) and integration tests (real Postgres/Redis via
  testcontainers) - see `docs/KNOWN_LIMITATIONS.md` for what's verified
  versus written-but-unrun in this environment
- CI (GitHub Actions): lint, type check, unit tests, integration tests,
  Docker build

## Quickstart (local development)

```bash
cp .env.example .env          # then edit SECRET_KEY at minimum
cd deploy
docker compose up --build
```

Starts Postgres, Redis, the API (`localhost:8000`), and one worker replica.
Interactive API docs: `http://localhost:8000/docs`. Worker metrics:
`http://localhost:9100/metrics`. API metrics: `http://localhost:8000/metrics`.

Run database migrations:

```bash
pip install -r requirements-dev.txt
alembic upgrade head
```

## Running the tests

```bash
pip install -r requirements-dev.txt

pytest tests/unit                 # mocked I/O, no external services needed
pytest tests/integration          # needs Docker (testcontainers) - see note below
locust -f tests/load/locustfile.py --host http://localhost:8000  # needs a running service
```

**Integration and load tests were written but not executed in this
project's development environment** (no Docker daemon / no network access
to pull images or a running service to point Locust at). Run them for real
before relying on them - see `docs/KNOWN_LIMITATIONS.md`.

## API endpoints

| Method | Path | Auth | Rate limited |
|---|---|---|---|
| POST | `/v1/jobs` | Required | Yes |
| GET | `/v1/jobs/{job_id}` | Required | Yes |
| DELETE | `/v1/jobs/{job_id}` | Required | Yes |
| GET | `/v1/jobs` | Required | Yes |
| GET | `/v1/health` | None | No |
| GET | `/v1/health/ready` | None | No |
| GET | `/metrics` | None | No |

## Project layout

See SDD Section 14 for the original annotated tree; additions since:

- `app/core/rate_limit.py`, `app/core/metrics.py` - added during hardening
- `app/db/worker_session.py` - sync DB session for the Celery worker
  (kept separate from the API's async session - see its docstring)
- `app/cache/job_status_cache.py` - shared cache key/serialization used by
  both the API and worker
- `monitoring/prometheus/` - scrape config, alert rules, Alertmanager routing
- `.github/workflows/ci.yml` - CI pipeline
- `docs/` - verification matrix, known limitations, this release's changelog

## Local dev without Docker

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env  # point DATABASE_URL / REDIS_URL at local instances
alembic upgrade head
uvicorn app.main:app --reload
```
