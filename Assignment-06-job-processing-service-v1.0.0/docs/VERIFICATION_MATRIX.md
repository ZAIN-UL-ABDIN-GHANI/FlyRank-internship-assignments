# Verification Matrix — SDD Requirement → Implementation

Status legend:
- **Verified** — statically checked in this environment (compiles, AST
  cross-checked against every consuming schema/model) AND covered by unit
  tests that would run in a real environment. This project's sandbox has
  no network access, so no dependency could actually be `pip install`-ed
  and no test was actually executed — "Verified" here means the strongest
  confidence achievable without running code, not a green CI run.
- **Written, unverified** — implemented and statically reviewed, but needs
  real infrastructure (Docker, a running service, CI) that this
  environment doesn't have, to actually execute.
- **Partial** — implemented with a specific, named gap.
- **Not implemented** — with the reason.

## Functional Requirements (SDD Section 2)

| ID | Requirement | Implementation | Status |
|---|---|---|---|
| FR1 | 202 + Job ID on submit | `job_service.create_job`, `jobs.py::submit_job` | Verified |
| FR2 | Enqueue for async processing | `process_ai_operation.delay()` in `create_job` | Verified |
| FR3 | Worker executes the operation | `tasks.py::_process_ai_operation_impl` | Verified |
| FR4 | Status endpoint (status/progress/result/error) | `job_service.get_job_status`, `jobs.py::get_job` | Verified |
| FR5 | Idempotent submission | Client-side check + DB unique constraint fallback | Verified (unit) + Written, unverified (integration test covers the real constraint) |
| FR6 | Automatic retry with backoff | `retry_policy.py` + `tasks.py` RETRY branch | Verified |
| FR7 | DLQ + alert past max retries | Status transition to `DEAD_LETTER`: Verified. Alert *routing*: written (`alertmanager.yml`). Alert *rule* for this specific condition: Verified (`DeadLetterQueueGrowth`, backed by a real metric) | Verified |
| FR8 | Persist job metadata/results | `Job`/`RetryAttempt` models + migration `0001` | Verified |
| FR9 | Best-effort cancellation | `job_service.cancel_job` | Verified |
| FR10 | Webhook callbacks (stretch) | — | Not implemented — explicitly marked optional/stretch in the SDD; never in scope for any phase |

## Non-Functional Requirements

| ID | Requirement | Implementation | Status |
|---|---|---|---|
| NFR1 | <200ms p95 ack latency | API does one DB write + one enqueue call, no AI-call blocking | Written, unverified — needs `tests/load/locustfile.py` run against a live instance |
| NFR2 | Worker autoscaling on queue depth | `deploy/k8s/hpa.yaml` | Partial — scales on CPU, not queue depth; true queue-depth scaling needs a KEDA/Redis exporter not deployed here (documented in the file itself) |
| NFR3 | At-least-once, no job loss | `task_acks_late` + worker-side idempotency lock + terminal-status skip | Verified |
| NFR4 | No single point of failure | `deploy/k8s/*.yaml` runs 2+ replicas of API/worker | Partial — Redis/Postgres themselves are single instances in `docker-compose.yml` (fine for dev); HA (Sentinel/Cluster, managed Postgres) is a deployment-time infra choice, not application code |
| NFR5 | End-to-end correlation via job_id | Every log line includes `job_id` via `extra={}` | Verified |
| NFR6 | AuthN/AuthZ, encryption in transit/at rest | JWT auth: Verified. TLS, disk encryption: deployment/infra concerns, not app code | Partial (see note) |
| NFR7 | Maintainability, layer separation | API/service/worker/db/cache folders, no cross-layer imports | Verified |
| NFR8 | 30-day retention | `JOB_RETENTION_DAYS` sets Celery *result backend* expiry only | **Partial — see Known Limitations.** No job actually purges/archives old rows from the `jobs` table itself |

## Architecture & Design (Sections 6–12)

| Section | Coverage | Status |
|---|---|---|
| 6 — High-Level Architecture | All components in the diagram exist and are wired as shown | Verified |
| 7 — System Design | All 5 layers implemented; data model matches the ER diagram field-for-field | Verified |
| 8 — Request Flow | Both sequence diagrams match the actual code path | Verified |
| 9 — Queue/Worker Lifecycle | All 8 states reachable (7 from the SDD + `CANCELLED`, added for FR9 - see `app/models/job.py` docstring) | Verified, with one documented, deliberate extension |
| 10 — Retry Strategy | Backoff table match confirmed by `test_retry_policy.py` (this is the regression test for the off-by-one bug found and fixed during Phase 1 validation) | Verified |
| 11 — Idempotency | Both client-side and worker-side mechanisms implemented and unit-tested | Verified |
| 12 — Failure Handling | Error triage (infra/task/crash) implemented; circuit breaker for broker/DB outages specifically NOT implemented | Partial |

## Section 13 — Alerting

| Rule | Backed by a real metric? |
|---|---|
| APIErrorRateHigh | Yes |
| DeadLetterQueueGrowth | Yes |
| WorkerPoolDown | Proxy only (Prometheus scrape health, not true Celery heartbeat — see `alert_rules.yml` header) |
| QueueBacklogAge | No — needs a queue-depth exporter, not built |
| JobSLABreach | No — needs a periodic in-flight-duration check, not built |

## Section 18 — Monitoring

| Item | Status |
|---|---|
| API metrics + `/metrics` endpoint | Verified |
| Worker metrics + `/metrics` (multiprocess-aware) | Verified — see `celery_app.py` for why naive `start_http_server()` per forked child would have crashed; fixed before shipping |
| Grafana dashboards | Not implemented — `monitoring/grafana/README.md` explains why and lists starting panels |
| Distributed tracing (OpenTelemetry) | Not implemented — never in scope for any phase of this build |

## Section 21 — Testing Strategy

| Test type | Status |
|---|---|
| Unit | Verified (statically) — `tests/unit/`, 6 files, covers retry policy, job service, tasks, schemas, rate limiting |
| Integration | Written, unverified — `tests/integration/test_job_lifecycle.py`, needs Docker |
| Load | Written, unverified — `tests/load/locustfile.py`, needs a running service |
| Contract (schemathesis) | Not implemented |
| Chaos | Not implemented |
| CI | Written, unverified — `.github/workflows/ci.yml`, needs a real GitHub Actions run to confirm it passes |
