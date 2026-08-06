"""
Job status cache format (SDD Section 7.5, Section 8.2).

Both the API (async, via app/services/job_service.py) and the worker (sync,
via app/workers/tasks.py) write to this same cache, so the key format and
serialization live in one place rather than being reimplemented twice and
risking drift. The functions here are pure (no I/O) - each caller does its
own get/set with its own (async or sync) Redis client.

`client_id` is included in the cached payload deliberately: without it, a
cache *hit* would skip the ownership check that the DB-query path performs
(SDD Section 16 - clients may only access their own jobs), since Redis has
no concept of who's asking. Including it means the same check runs whether
the data came from cache or from Postgres.
"""

import json
from typing import Any
from uuid import UUID

from app.models.job import Job


def job_status_cache_key(job_id: UUID | str) -> str:
    return f"job_status:{job_id}"


def job_to_cache_dict(job: Job) -> dict[str, Any]:
    """
    Shape matches JobStatusResponse (SDD Section 15) plus `client_id`, which
    callers must check before returning data to a client and must strip (or
    simply not pass through) before constructing the response model itself.
    """
    return {
        "job_id": str(job.job_id),
        "client_id": job.client_id,
        "status": job.status,
        "progress": job.progress,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "result": job.result,
        "error": job.error_detail,
    }


def serialize_for_cache(job: Job) -> str:
    return json.dumps(job_to_cache_dict(job))


def deserialize_from_cache(raw: str) -> dict[str, Any]:
    return json.loads(raw)
