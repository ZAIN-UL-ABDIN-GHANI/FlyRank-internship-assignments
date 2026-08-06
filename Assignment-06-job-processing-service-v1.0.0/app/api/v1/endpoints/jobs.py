"""
Job endpoints (SDD Section 15 - API Design).

All four routes are fully implemented, backed by app/services/job_service.py.
Auth (SDD Section 16) and rate limiting (app/core/rate_limit.py) are applied
uniformly via the rate_limited_client dependency.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import enforce_rate_limit
from app.core.security import ClientIdentity, get_current_client
from app.db.session import get_db
from app.models.job import JobStatus
from app.models.schemas import (
    JobCancelResponse,
    JobListResponse,
    JobStatusResponse,
    JobSubmitRequest,
    JobSubmitResponse,
)
from app.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["jobs"])


def get_job_service(db: AsyncSession = Depends(get_db)) -> JobService:
    return JobService(db)


async def rate_limited_client(
    client: ClientIdentity = Depends(get_current_client),
) -> ClientIdentity:
    """Auth first, then rate limit - a rejected token shouldn't consume rate-limit budget."""
    await enforce_rate_limit(client.client_id)
    return client


@router.post("", response_model=JobSubmitResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_job(
    request: JobSubmitRequest,
    response: Response,
    client: ClientIdentity = Depends(rate_limited_client),
    service: JobService = Depends(get_job_service),
) -> JobSubmitResponse:
    """
    FR1/FR2 (SDD Section 2): returns 202 + Job ID immediately for a new job;
    the AI operation runs asynchronously via the worker.

    Per SDD Section 8.1, an idempotent replay (existing idempotency_key)
    returns 200 with the existing job instead of creating a duplicate -
    handled by overriding the decorator's default 202 via `response`.
    """
    result, is_new = await service.create_job(client_id=client.client_id, request=request)
    response.status_code = status.HTTP_202_ACCEPTED if is_new else status.HTTP_200_OK
    return result


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job(
    job_id: UUID,
    client: ClientIdentity = Depends(rate_limited_client),
    service: JobService = Depends(get_job_service),
) -> JobStatusResponse:
    """FR4 (SDD Section 2): status, progress, result, or error for one job."""
    return await service.get_job_status(client_id=client.client_id, job_id=job_id)


@router.delete("/{job_id}", response_model=JobCancelResponse)
async def cancel_job(
    job_id: UUID,
    client: ClientIdentity = Depends(rate_limited_client),
    service: JobService = Depends(get_job_service),
) -> JobCancelResponse:
    """FR9 (SDD Section 2): best-effort cancellation of a not-yet-started job."""
    return await service.cancel_job(client_id=client.client_id, job_id=job_id)


@router.get("", response_model=JobListResponse)
async def list_jobs(
    job_status: JobStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    client: ClientIdentity = Depends(rate_limited_client),
    service: JobService = Depends(get_job_service),
) -> JobListResponse:
    """Paginated, filterable job listing scoped to the authenticated client."""
    return await service.list_jobs(
        client_id=client.client_id, status=job_status, limit=limit, offset=offset
    )
