# Changelog

## 1.0.0 — Initial release

Full implementation of the async job processing system described in
`background-job-processing-system-design.md` (SDD v1.0): a slow AI
operation migrated from synchronous execution to a queue-based
architecture returning `202 Accepted` + a Job ID immediately, processed by
an independently-scalable Celery worker pool, with a status endpoint for
progress and results.

See `docs/VERIFICATION_MATRIX.md` for the full requirement-by-requirement
trace and `docs/KNOWN_LIMITATIONS.md` for what to check before deploying.

### Added

**Core lifecycle**
- `POST /v1/jobs`, `GET /v1/jobs/{id}`, `DELETE /v1/jobs/{id}`, `GET /v1/jobs`
- Celery task execution with worker-side idempotency (distributed lock +
  terminal-state guard) and client-side idempotency (unique constraint +
  application-level check with a race-condition fallback)
- Exponential backoff retry with jitter, dead-lettering past max retries
- PostgreSQL persistence (`Job`, `RetryAttempt`) with an Alembic migration
- Redis status cache, fronting Postgres for high-frequency polling

**Reliability & security**
- Rate limiting (Redis-backed, fails open on cache outage)
- Payload size cap and operation allow-list
- Cache reads/writes are best-effort throughout — a Redis outage degrades
  to DB-only rather than failing requests
- JWT bearer auth, scoped per-client access control (enforced on both the
  cache-hit and DB-miss paths — see Fixed, below)
- Global unhandled-exception handler returning consistent error responses

**Observability**
- Structured JSON logging (API and worker), correlated by `job_id`
- Prometheus metrics: job lifecycle counters, processing-duration
  histogram, retry counter, API request counters/histogram
- Alert rules and Alertmanager routing config (PagerDuty/Slack/Email)

**Infrastructure**
- Separate Docker images for API and worker, `docker-compose.yml` for
  local dev, Kubernetes manifests (Deployments, Service, HPA)
- GitHub Actions CI: lint, type check, unit tests, integration tests,
  Docker build verification

**Testing**
- 6 unit test files covering retry policy, job service, task logic,
  schema validation, and rate limiting
- Integration tests against real Postgres/Redis (testcontainers)
- Locust load test scenario

### Fixed during development

- **Off-by-one in the retry backoff formula** (`base * 2^attempt` instead
  of `base * 2^(attempt-1)`), found by re-checking the code against the
  SDD's own table before building on top of it. Root cause, impact, and
  fix are detailed in conversation history; regression-tested in
  `test_retry_policy.py`.
- **Status cache bypassed the per-client ownership check on a cache hit**
  (only the DB-query path re-checked `client_id`). Fixed by including
  `client_id` in the cached payload and checking it uniformly regardless
  of data source.
- **Worker metrics would have crashed on startup** with more than one
  concurrent worker process — a naive `start_http_server()` per forked
  child all try to bind the same port. Replaced with
  `prometheus_client`'s documented multiprocess pattern.
- Two smaller bugs caught during self-review before ever being shown:
  an unnecessary DB round-trip via an inline `__import__` hack, and
  `completed_at` being copied from `started_at` instead of the actual
  completion time.
- A circular dependency (`rate_limited_client` depending on itself)
  introduced by an overly broad `sed` replacement, caught immediately by
  reviewing the diff rather than assuming the command did what was intended.

### Known limitations

See `docs/KNOWN_LIMITATIONS.md` in full. Headline items: no PostgreSQL
retention/purge job (NFR8 only half-implemented), queue depth isn't
instrumented anywhere (affects HPA scaling accuracy and two alert rules),
and integration/load tests were written but never executed against real
infrastructure in this development environment.
