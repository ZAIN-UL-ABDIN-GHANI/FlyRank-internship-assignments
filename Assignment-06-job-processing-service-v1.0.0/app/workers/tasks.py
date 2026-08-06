"""
Celery task: executes the AI operation for a job (SDD Section 8, 9, 10, 11).

The Celery-decorated function is a thin wrapper around
_process_ai_operation_impl, which takes a plain `task` object (anything
with a `.retry()` method) instead of relying on `self` directly. This means
tests can call _process_ai_operation_impl with a mock task and mock
DB/Redis, with no Celery broker, event loop, or eager-mode setup required.
"""

import asyncio
import random
from datetime import datetime, timezone
from uuid import UUID

from app.cache.job_status_cache import job_status_cache_key, serialize_for_cache
from app.cache.redis_client import get_redis_client_sync
from app.core.logging import get_logger
from app.core.metrics import JOB_PROCESSING_DURATION_SECONDS, JOB_RETRIES, JOBS_COMPLETED
from app.db.worker_session import get_worker_session
from app.models.job import Job, JobStatus, RetryAttempt
from app.services.ai_operation import AIOperationError, run_ai_operation
from app.workers import retry_policy
from app.workers.celery_app import celery_app

logger = get_logger(__name__)

# Generous relative to expected AI operation duration, but bounded so a
# crashed worker's lock doesn't block reprocessing forever (SDD Section 11).
_LOCK_TIMEOUT_SECONDS = 600

_TERMINAL_STATUSES = frozenset(
    {JobStatus.SUCCESS, JobStatus.FAILED_PERMANENT, JobStatus.DEAD_LETTER, JobStatus.CANCELLED}
)


def _classify_error(exc: Exception) -> tuple[str, str, bool]:
    """
    Maps an exception to (code, message, retryable). AIOperationError
    carries its own code; anything else is an unclassified failure, treated
    as retryable by default so a transient bug doesn't masquerade as
    permanent - if it truly persists, max_retries still bounds it and it
    lands in DEAD_LETTER rather than retrying forever (SDD Section 10, 12).

    retryable is derived from retry_policy.PERMANENT_ERROR_CODES - the
    single source of truth for classification - rather than trusted from
    the exception itself.
    """
    if isinstance(exc, AIOperationError):
        code, message = exc.code, exc.message
    else:
        code, message = "UNKNOWN_ERROR", str(exc)
    retryable = code not in retry_policy.PERMANENT_ERROR_CODES
    return code, message, retryable


def _apply_jitter(base_delay: int) -> float:
    jitter = base_delay * retry_policy.JITTER_FRACTION * random.uniform(-1, 1)
    return max(0.0, base_delay + jitter)


def _update_cache(redis_client, job: Job) -> None:
    try:
        redis_client.set(job_status_cache_key(job.job_id), serialize_for_cache(job))
    except Exception:
        logger.warning(
            "Cache write failed - continuing without caching this update",
            extra={"event": "cache.write_failed", "job_id": str(job.job_id)},
        )


def _process_ai_operation_impl(task, job_id: str) -> None:
    redis_client = get_redis_client_sync()

    with get_worker_session() as db:
        job = db.get(Job, UUID(job_id))
        if job is None:
            # Defensive only - would mean a task was enqueued for a job_id
            # that was never committed, which job_service.py's ordering
            # (commit before .delay()) should make impossible.
            logger.error("Job not found for task", extra={"event": "job.not_found", "job_id": job_id})
            return

        if job.status in _TERMINAL_STATUSES:
            # Worker-side idempotency guard (SDD Section 11) - handles the
            # at-least-once redelivery from task_acks_late (SDD Section 9).
            logger.info(
                "Job already in terminal state, skipping re-execution",
                extra={"event": "job.skipped_already_terminal", "job_id": job_id, "status": job.status},
            )
            return

        lock = redis_client.lock(f"job_lock:{job_id}", timeout=_LOCK_TIMEOUT_SECONDS)
        if not lock.acquire(blocking=False):
            # Another worker holds the lock - almost certainly a redelivery
            # of a task still being actively processed elsewhere. We
            # deliberately don't retry here: the other worker's own commits
            # are the source of truth, and this delivery's job is done.
            logger.info(
                "Lock held by another worker, backing off",
                extra={"event": "job.skipped_lock_contention", "job_id": job_id},
            )
            return

        try:
            job.status = JobStatus.IN_PROGRESS
            job.started_at = datetime.now(timezone.utc)
            db.commit()
            _update_cache(redis_client, job)
            logger.info("Job started", extra={"event": "job.started", "job_id": job_id})

            try:
                operation = job.input_payload["operation"]
                payload = job.input_payload["payload"]
                result = asyncio.run(run_ai_operation(operation, payload))

                job.status = JobStatus.SUCCESS
                job.progress = 100
                job.result = result
                job.completed_at = datetime.now(timezone.utc)
                db.commit()
                _update_cache(redis_client, job)
                JOBS_COMPLETED.labels(outcome="success").inc()
                JOB_PROCESSING_DURATION_SECONDS.observe(
                    (job.completed_at - job.created_at).total_seconds()
                )
                logger.info("Job succeeded", extra={"event": "job.succeeded", "job_id": job_id})

            except Exception as exc:  # noqa: BLE001 - intentionally broad, classified below
                code, message, retryable = _classify_error(exc)
                attempt_number = job.retry_count + 1

                db.add(
                    RetryAttempt(
                        job_id=job.job_id,
                        attempt_number=attempt_number,
                        outcome="retrying" if retryable else "failed_permanent",
                        error_message=message,
                    )
                )

                action = retry_policy.determine_next_action(
                    retry_count=job.retry_count, max_retries=job.max_retries, retryable=retryable
                )

                if action == "RETRY":
                    job.retry_count += 1
                    job.status = JobStatus.FAILED_TRANSIENT
                    job.error_detail = {"code": code, "message": message, "retryable": True}
                    db.commit()
                    _update_cache(redis_client, job)
                    JOB_RETRIES.labels(error_code=code).inc()
                    delay = _apply_jitter(retry_policy.compute_backoff_seconds(job.retry_count))
                    logger.warning(
                        "Transient error, scheduling retry",
                        extra={
                            "event": "job.retry_scheduled",
                            "job_id": job_id,
                            "attempt": job.retry_count,
                            "countdown_seconds": round(delay, 2),
                            "error_code": code,
                        },
                    )
                    # task.retry() raises celery.exceptions.Retry internally
                    # under a real bound task (throw=True is the default) -
                    # no explicit `raise` needed, and omitting it means a
                    # plain mock `task` in tests doesn't need to simulate
                    # raising anything to exercise this branch.
                    task.retry(exc=exc, countdown=delay)

                elif action == "DEAD_LETTER":
                    job.status = JobStatus.DEAD_LETTER
                    job.error_detail = {"code": code, "message": message, "retryable": True}
                    db.commit()
                    _update_cache(redis_client, job)
                    JOBS_COMPLETED.labels(outcome="dead_letter").inc()
                    logger.error(
                        "Max retries exceeded, moved to dead letter",
                        extra={"event": "job.dead_lettered", "job_id": job_id, "error_code": code},
                    )

                else:  # FAIL_PERMANENT
                    job.status = JobStatus.FAILED_PERMANENT
                    job.error_detail = {"code": code, "message": message, "retryable": False}
                    db.commit()
                    _update_cache(redis_client, job)
                    JOBS_COMPLETED.labels(outcome="failed_permanent").inc()
                    logger.error(
                        "Permanent error, not retrying",
                        extra={"event": "job.failed_permanent", "job_id": job_id, "error_code": code},
                    )
        finally:
            try:
                lock.release()
            except Exception:  # noqa: BLE001 - lock may already be expired; not fatal
                pass


@celery_app.task(name="jobs.process_ai_operation", bind=True)
def process_ai_operation(self, job_id: str) -> None:
    _process_ai_operation_impl(self, job_id)
