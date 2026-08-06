"""
Job service - the layer between API routes and (DB + broker).

Implements create_job, get_job_status (SDD Section 8.1/8.2/11), and now
cancel_job and list_jobs (SDD FR9, Section 15).

Refactored from the previous version: cache reads/writes are best-effort
(a Redis outage degrades to DB-only rather than failing the request - the
cache is an optimization, not the source of truth), and status-response
construction is deduplicated into _to_status_response so get_job_status
and list_jobs don't each reimplement the same field mapping.
"""

import json
from uuid import UUID

from fastapi import HTTPException, status as http_status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.job_status_cache import (
    job_status_cache_key,
    job_to_cache_dict,
    serialize_for_cache,
)
from app.cache.redis_client import get_redis_client
from app.core.config import settings
from app.core.logging import get_logger
from app.core.metrics import JOBS_COMPLETED, JOBS_SUBMITTED
from app.models.job import Job, JobStatus
from app.models.schemas import (
    JobCancelResponse,
    JobErrorDetail,
    JobListResponse,
    JobStatusResponse,
    JobSubmitRequest,
    JobSubmitResponse,
)
from app.workers.tasks import process_ai_operation

logger = get_logger(__name__)

# Only jobs that haven't started executing can be cancelled (FR9) - once a
# worker has picked it up, cancellation would race the in-flight AI call
# with no clean way to abort it, so it's out of scope by design, not
# an oversight.
_CANCELLABLE_STATUSES = frozenset({JobStatus.PENDING, JobStatus.QUEUED})


class JobService:
    def __init__(self, db: AsyncSession):
        self._db = db
        self._redis = get_redis_client()

    async def create_job(
        self, client_id: str, request: JobSubmitRequest
    ) -> tuple[JobSubmitResponse, bool]:
        """Returns (response, is_new). is_new is False for an idempotent replay."""
        existing = await self._find_existing(client_id, request.idempotency_key)
        if existing is not None:
            logger.info(
                "Idempotent replay - returning existing job",
                extra={"event": "job.idempotent_replay", "job_id": str(existing.job_id)},
            )
            return self._to_submit_response(existing), False

        job = Job(
            client_id=client_id,
            idempotency_key=request.idempotency_key,
            status=JobStatus.PENDING,
            input_payload={"operation": request.operation, "payload": request.payload},
        )
        self._db.add(job)
        try:
            await self._db.commit()
        except IntegrityError:
            await self._db.rollback()
            existing = await self._find_existing(client_id, request.idempotency_key)
            if existing is not None:
                logger.info(
                    "Idempotency race resolved via unique constraint",
                    extra={"event": "job.idempotent_replay", "job_id": str(existing.job_id)},
                )
                return self._to_submit_response(existing), False
            raise

        await self._db.refresh(job)

        # Persist QUEUED *before* enqueueing, so the worker can never race
        # ahead of this write and have its own IN_PROGRESS update clobbered
        # by this one landing late. updated_at is set in Python rather than
        # via a second refresh() round-trip - the only reason to refresh
        # again would be to read this same value back.
        job.status = JobStatus.QUEUED
        job.updated_at = job.created_at
        await self._db.commit()
        await self._cache_set(job)

        process_ai_operation.delay(str(job.job_id))
        JOBS_SUBMITTED.labels(operation=request.operation).inc()

        logger.info(
            "Job created and enqueued",
            extra={
                "event": "job.created",
                "job_id": str(job.job_id),
                "operation": request.operation,
            },
        )
        return self._to_submit_response(job), True

    async def get_job_status(self, client_id: str, job_id: UUID) -> JobStatusResponse:
        cache_key = job_status_cache_key(job_id)
        cached_raw = await self._cache_get(cache_key)

        if cached_raw is not None:
            data = json.loads(cached_raw)
            logger.info(
                "Job status served from cache",
                extra={"event": "job.status_cache_hit", "job_id": str(job_id)},
            )
        else:
            job = await self._db.get(Job, job_id)
            if job is None:
                raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Job not found")
            data = job_to_cache_dict(job)
            await self._cache_set_raw(cache_key, json.dumps(data))
            logger.info(
                "Job status served from database, cache repopulated",
                extra={"event": "job.status_cache_miss", "job_id": str(job_id)},
            )

        # Ownership check runs regardless of cache hit/miss (SDD Section 16) -
        # see app/cache/job_status_cache.py docstring for why client_id is
        # carried in the cached payload.
        if data["client_id"] != client_id:
            raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Job not found")

        return self._response_from_dict(data)

    async def cancel_job(self, client_id: str, job_id: UUID) -> JobCancelResponse:
        job = await self._db.get(Job, job_id)
        if job is None or job.client_id != client_id:
            raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Job not found")

        if job.status not in _CANCELLABLE_STATUSES:
            raise HTTPException(
                status_code=http_status.HTTP_409_CONFLICT,
                detail=(
                    f"Cannot cancel a job in status {job.status} - only jobs that "
                    "haven't started processing can be cancelled"
                ),
            )

        job.status = JobStatus.CANCELLED
        await self._db.commit()
        await self._cache_set(job)
        JOBS_COMPLETED.labels(outcome="cancelled").inc()

        logger.info(
            "Job cancelled", extra={"event": "job.cancelled", "job_id": str(job_id)}
        )
        return JobCancelResponse(
            job_id=job.job_id, status=job.status, message="Job cancelled successfully"
        )

    async def list_jobs(
        self, client_id: str, status: JobStatus | None, limit: int, offset: int
    ) -> JobListResponse:
        base_filter = Job.client_id == client_id
        if status is not None:
            base_filter = base_filter & (Job.status == status)

        count_result = await self._db.execute(
            select(func.count()).select_from(Job).where(base_filter)
        )
        total = count_result.scalar_one()

        rows_result = await self._db.execute(
            select(Job).where(base_filter).order_by(Job.created_at.desc()).limit(limit).offset(offset)
        )
        jobs = rows_result.scalars().all()

        return JobListResponse(
            items=[self._response_from_dict(job_to_cache_dict(job)) for job in jobs],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def _find_existing(self, client_id: str, idempotency_key: str) -> Job | None:
        result = await self._db.execute(
            select(Job).where(Job.client_id == client_id, Job.idempotency_key == idempotency_key)
        )
        return result.scalar_one_or_none()

    async def _cache_get(self, key: str) -> str | None:
        try:
            return await self._redis.get(key)
        except Exception:
            logger.warning(
                "Cache read failed, falling back to database",
                extra={"event": "cache.read_failed", "key": key},
            )
            return None

    async def _cache_set_raw(self, key: str, value: str) -> None:
        try:
            await self._redis.set(key, value, ex=settings.STATUS_CACHE_TTL_SECONDS)
        except Exception:
            logger.warning(
                "Cache write failed - continuing without caching this update",
                extra={"event": "cache.write_failed", "key": key},
            )

    async def _cache_set(self, job: Job) -> None:
        await self._cache_set_raw(job_status_cache_key(job.job_id), serialize_for_cache(job))

    @staticmethod
    def _response_from_dict(data: dict) -> JobStatusResponse:
        error = JobErrorDetail(**data["error"]) if data.get("error") else None
        return JobStatusResponse(
            job_id=data["job_id"],
            status=data["status"],
            progress=data["progress"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            result=data.get("result"),
            error=error,
        )

    @staticmethod
    def _to_submit_response(job: Job) -> JobSubmitResponse:
        return JobSubmitResponse(
            job_id=job.job_id,
            status=job.status,
            status_url=f"{settings.API_V1_PREFIX}/jobs/{job.job_id}",
            created_at=job.created_at,
        )
