# Test Report

**No test in this report was actually executed.** This development
environment has no network access to install dependencies (FastAPI,
SQLAlchemy, Celery, pytest, etc. are all absent) and no Docker daemon for
testcontainers. Every number below is a count of tests *written*, verified
only via Python's own `ast`/`py_compile` (real syntax parsing, not a
simulation) plus manual cross-referencing of mock targets and schema
fields against the actual implementation. Run `pytest` for real before
treating any of this as a pass/fail result.

## Unit tests — 38 test cases across 5 files

| File | Tests | Covers |
|---|---|---|
| `test_job_service.py` | 14 | `create_job` (new/replay/race), `get_job_status` (cache hit/miss/ownership), `cancel_job` (success/conflict/ownership), `list_jobs` |
| `test_tasks.py` | 11 | Error classification, jitter bounds, and all branches of the task's state machine (terminal-skip, lock-contention, success, retry, dead-letter, permanent-fail, unknown-exception) |
| `test_retry_policy.py` | 5 | Backoff formula against the SDD table (the regression test for the off-by-one bug), the cap, cumulative wait, `determine_next_action`'s full decision table, error-code set disjointness |
| `test_schemas.py` | 4 | Operation allow-list, payload size limit |
| `test_rate_limit.py` | 4 | Under/over limit, first-request-sets-expiry, fail-open on Redis error |

**Static verification performed on all of the above:**
- Every file compiles (`py_compile`) - confirmed, see tool output above
- Every `mocker.patch(...)`/`patch(...)` target cross-checked via AST
  against the actual module's imports/definitions - confirmed for all
  files, zero invalid targets found
- Every `Job`/`RetryAttempt` field the code accesses, and every dict
  literal reconstructed into a Pydantic schema, cross-checked against the
  real model/schema definitions - confirmed matching throughout

## Integration tests — 5 test cases, 1 file

`test_job_lifecycle.py`, against real Postgres + Redis via testcontainers
and the real Alembic migration:

- Duplicate idempotency key returns the same job (tests the real DB
  constraint, not a mock)
- Same idempotency key across two different clients creates two jobs
  (confirms the constraint is scoped to `(client_id, idempotency_key)`)
- Status cache miss-then-hit round trip against real Redis
- Full lifecycle: submit → task execution → `SUCCESS`, against the real DB
- Retry exhaustion → `DEAD_LETTER`, against the real DB

**Not executed** - written and reasoned through carefully, including one
self-caught defect (a missing `MagicMock` import) fixed before delivery,
but never actually run.

## Load tests — written, not executed

`tests/load/locustfile.py` - submission-weighted traffic pattern (3:1:1
submit:poll:list), needs a running instance to point at.

## Not present

Contract tests (schemathesis) and chaos tests, both named in SDD Section
21, were not written in any phase of this build.

## What "passing" would actually confirm

Even a fully green run of everything above would still leave the items in
`docs/KNOWN_LIMITATIONS.md` unaddressed (retention/purge job, queue-depth
metrics, circuit breakers, tracing) - those are scope gaps, not things the
existing tests would catch either way.
