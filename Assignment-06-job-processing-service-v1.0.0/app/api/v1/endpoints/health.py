"""
Health endpoints (SDD Section 15 - API Design, Section 18 - Monitoring).

Two endpoints, reconciling a minor naming difference between two SDD
sections: Section 15's API table lists a single `GET /v1/health`; Section 18
separately calls for liveness *and* readiness checks "for orchestrator-
driven restarts". Both are implemented here rather than picking one:

    GET /v1/health        - liveness: process is up, no dependency checks.
                             Matches Section 15 exactly.
    GET /v1/health/ready   - readiness: verifies DB and Redis are reachable.
                             Matches Section 18's intent. Use this one for a
                             Kubernetes readinessProbe; use /v1/health for
                             livenessProbe.

No authentication (SDD Section 15: Auth = None for this endpoint) - it must
be reachable by the orchestrator without a token.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.redis_client import check_redis_connection
from app.db.session import get_db
from app.models.schemas import HealthResponse, ReadinessResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def liveness() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/health/ready", response_model=ReadinessResponse)
async def readiness(db: AsyncSession = Depends(get_db)) -> ReadinessResponse:
    db_ok = True
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    redis_ok = await check_redis_connection()

    return ReadinessResponse(
        status="ok" if (db_ok and redis_ok) else "degraded",
        database="ok" if db_ok else "unreachable",
        redis="ok" if redis_ok else "unreachable",
    )
