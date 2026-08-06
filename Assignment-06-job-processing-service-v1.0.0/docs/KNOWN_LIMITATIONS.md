# Known Limitations

Consolidated from notes made throughout development. Read this before
deploying — nothing here is hidden or minimized, but scattered across many
file comments it's easy to miss one.

## Not verified by execution (sandbox constraint, not a code quality gap)

This entire project was built in an environment with no network access and
no Docker daemon. No dependency was ever `pip install`-ed; no test ever
ran. What *was* done in place of execution: full syntax compilation of
every file, and AST-based static cross-checking of every mock patch target,
every ORM/schema field the code touches, and every dict literal that gets
reconstructed into a Pydantic model elsewhere. That catches a real class of
bugs (and did, several times during this build — see `docs/VERIFICATION_MATRIX.md`
history) but is not a substitute for actually running `pytest`, `docker
compose up`, and the CI pipeline for real before trusting this in
production.

## Gaps found but not fixed (out of scope, not overlooked)

- **No PostgreSQL retention/purge job.** `JOB_RETENTION_DAYS` only
  configures Celery's *result backend* expiry (Redis). Nothing purges or
  archives old rows from the `jobs`/`retry_attempts` tables themselves —
  NFR8 is only half-implemented. A scheduled Celery beat task or a cron'd
  `DELETE ... WHERE created_at < now() - interval` would close this.
- **Queue depth is not instrumented anywhere** (metrics, HPA, or alerting).
  Every place that would need it (`hpa.yaml`, `alert_rules.yml`) says so
  explicitly and explains what a real fix looks like (a Redis/Celery
  exporter). This was a deliberate, repeated scope decision, not three
  separate oversights.
- **`WorkerPoolDown` and `JobSLABreach` alerts are placeholders.** They
  reference metrics that don't exist yet. Left in (rather than deleted) to
  match the SDD's alert table, with the gap documented in the file itself.
- **No circuit breaker for broker/DB outages** (SDD Section 12 mentions
  this). Retries handle task-level failures; a sustained infra outage
  currently just means every task's retries fail individually rather than
  the worker recognizing the outage and backing off as a whole.
- **No distributed tracing.** Structured logs correlate by `job_id`, but
  there's no OpenTelemetry span linking an API request to the worker task
  it enqueued.
- **No Grafana dashboards, contract tests (schemathesis), or chaos tests.**
  Explained in `monitoring/grafana/README.md` and the verification matrix.

## Deliberate simplifications (with reasoning, not defects)

- **State machine has 8 states, not the SDD's original 7.** `CANCELLED`
  was added for FR9; the original Section 9 diagram didn't model
  cancellation. Documented in `app/models/job.py`.
- **`FAILED_TRANSIENT` doesn't pass through a literal `QUEUED` write**
  before the next attempt, unlike the arrow in Section 9's diagram. Same
  client-visible information, one fewer DB write. Documented in `tasks.py`.
- **Auth doesn't validate token issuer/audience.** SDD Section 5 assumes
  the *existing* platform auth is reused, and this app has no way to know
  the real platform's claims schema. The mechanism (signature + expiry
  verification) is real; the specific claims checked may need adjusting to
  match whatever actually issues these tokens.
- **`ALLOWED_OPERATIONS` defaults to a single placeholder value**
  (`rag_query`). This app has no way to know the real supported operation
  set (SDD Section 4 keeps that out of scope by design) — must be updated
  in production config.
- **Rate limiting fails open on Redis outage**, by design — a cache/broker
  blip shouldn't compound into blocking all API traffic. This means the
  rate limit is *not* enforced during a Redis outage, which is the correct
  trade-off given the alternative (failing closed) would take down the
  whole API over a non-critical-path dependency.

## Infrastructure this code assumes but doesn't provide

TLS termination, secrets management (Vault/K8s Secrets — this app reads
plain env vars), Postgres/Redis high availability (Sentinel/Cluster/managed
services), and network segmentation are all deployment-time concerns
referenced throughout the SDD and the k8s manifests, not something
application code can provide on its own.
