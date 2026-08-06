"""
Rate limiting (SDD Section 16 - Security).

RATE_LIMIT_PER_MINUTE was defined in app/core/config.py since Phase 1 but
never enforced anywhere - this closes that gap. Redis-backed fixed-window
counter, scoped per client_id (post-auth) rather than per-IP, so it works
correctly across multiple API replicas (SDD Section 6: API1..APIN) - an
in-memory counter would be per-process and trivially bypassed by hitting a
different replica.
"""

import time

from fastapi import HTTPException, status

from app.cache.redis_client import get_redis_client
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


async def enforce_rate_limit(client_id: str) -> None:
    redis = get_redis_client()
    window = int(time.time() // 60)  # current 60-second window
    key = f"rate_limit:{client_id}:{window}"

    try:
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, 60)
    except Exception:
        # Redis unavailable: fail open rather than let a cache outage take
        # down all API traffic. The cache is an optimization/safety layer,
        # not the source of truth (SDD Section 7.4 - Postgres is), so a
        # Redis blip shouldn't compound into a full outage.
        logger.warning(
            "Rate limiter could not reach Redis - failing open",
            extra={"event": "rate_limit.redis_unavailable", "client_id": client_id},
        )
        return

    if count > settings.RATE_LIMIT_PER_MINUTE:
        logger.warning(
            "Rate limit exceeded",
            extra={"event": "rate_limit.exceeded", "client_id": client_id, "count": count},
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded - try again shortly",
        )
