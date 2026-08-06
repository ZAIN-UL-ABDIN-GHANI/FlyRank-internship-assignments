"""
Redis client for the cache layer (SDD Section 7.5).

This is the ephemeral, TTL-based status cache that sits in front of
PostgreSQL for high-frequency job status polling (SDD Section 8.2 - Status
Polling Flow). It is a distinct logical role from the Celery broker
connection, even though both point at the same Redis instance by default
in local development (see .env.example: REDIS_URL vs CELERY_BROKER_URL).
"""

from redis import ConnectionPool as SyncConnectionPool
from redis import Redis as SyncRedis
from redis.asyncio import ConnectionPool, Redis

from app.core.config import settings

_pool = ConnectionPool.from_url(settings.REDIS_URL, decode_responses=True)
_sync_pool = SyncConnectionPool.from_url(settings.REDIS_URL, decode_responses=True)


def get_redis_client() -> Redis:
    """Async Redis client backed by the shared connection pool (API use)."""
    return Redis(connection_pool=_pool)


def get_redis_client_sync() -> SyncRedis:
    """
    Sync Redis client for Celery worker use (see app/db/worker_session.py for
    why workers stay synchronous throughout rather than asyncio.run() per
    task). Also the client used for the distributed processing lock in SDD
    Section 11 (redis-py's .lock() needs a sync or async client matching the
    caller's own context - the worker's context is sync).
    """
    return SyncRedis(connection_pool=_sync_pool)


async def check_redis_connection() -> bool:
    """Used by the readiness probe (SDD Section 18)."""
    try:
        client = get_redis_client()
        return await client.ping()
    except Exception:
        return False
