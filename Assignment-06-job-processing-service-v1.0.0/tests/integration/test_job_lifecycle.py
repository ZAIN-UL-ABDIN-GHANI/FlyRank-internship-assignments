"""
Integration tests: real Postgres + Redis via testcontainers, real Alembic
migration, real JobService and task logic (only run_ai_operation is mocked,
since its real implementation is out of scope per SDD Section 4).

*** WRITTEN BUT NOT EXECUTED ***
This sandbox has no Docker daemon and no network access to pull container
images, so these tests could not actually be run or debugged here - only
reasoned through carefully and statically checked. Run them for real
(`pytest tests/integration`) before trusting this file. If anything here
doesn't pass first try, that is expected for code that has never executed -
treat this as a strong first draft, not a verified suite.

These specifically test what unit tests (mocked DB) cannot: that the real
`uq_job_client_idempotency` constraint from the Alembic migration actually
enforces idempotency at the database level, and that the cache/DB round
trip works against a real Redis instance.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from app.models.job import Job, JobStatus
from app.models.schemas import JobSubmitRequest
from app.services.ai_operation import AIOperationError
from app.services.job_service import JobService


@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg


@pytest.fixture(scope="session")
def redis_container():
    with RedisContainer("redis:7-alpine") as rc:
        yield rc


@pytest.fixture(scope="session")
def postgres_url(postgres_container) -> str:
    # testcontainers gives a psycopg2-style URL; swap the driver for asyncpg,
    # matching how the app itself expects DATABASE_URL to be shaped.
    raw = postgres_container.get_connection_url()
    return raw.replace("postgresql+psycopg2", "postgresql+asyncpg")


@pytest.fixture(scope="session", autouse=True)
def run_migrations(postgres_url):
    """Runs the real Alembic migration (0001_initial_schema) against the container."""
    config = Config("alembic.ini")
    sync_url = postgres_url.replace("+asyncpg", "+psycopg")
    config.set_main_option("sqlalchemy.url", sync_url)
    command.upgrade(config, "head")


@pytest.fixture
async def db_session(postgres_url):
    engine = create_async_engine(postgres_url)
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        # Integration tests share one container across the session (scope
        # above) - clean up so tests don't see each other's rows.
        await session.rollback()
    async with engine.begin() as conn:
        await conn.execute(__import__("sqlalchemy").text("TRUNCATE jobs, retry_attempts CASCADE"))
        await conn.commit()
    await engine.dispose()


@pytest.fixture
def redis_url(redis_container) -> str:
    host = redis_container.get_container_host_ip()
    port = redis_container.get_exposed_port(6379)
    return f"redis://{host}:{port}/0"


@pytest.fixture
def job_service_with_real_redis(db_session, redis_url):
    """
    JobService constructed against the real testcontainer Redis instead of
    the module-level client from app.cache.redis_client (which points at
    whatever REDIS_URL was set at import time, not the container's dynamic
    port).
    """
    from redis.asyncio import Redis

    service = JobService(db_session)
    service._redis = Redis.from_url(redis_url, decode_responses=True)
    return service


class TestIdempotencyAgainstRealConstraint:
    async def test_duplicate_idempotency_key_returns_same_job(self, job_service_with_real_redis):
        request = JobSubmitRequest(
            operation="rag_query", payload={"query": "test"}, idempotency_key="integration-key-1"
        )
        with patch("app.services.job_service.process_ai_operation") as mock_task:
            response_1, is_new_1 = await job_service_with_real_redis.create_job("client-a", request)
            response_2, is_new_2 = await job_service_with_real_redis.create_job("client-a", request)

        assert is_new_1 is True
        assert is_new_2 is False
        assert response_1.job_id == response_2.job_id
        mock_task.delay.assert_called_once()  # only enqueued once, not twice

    async def test_same_idempotency_key_different_clients_creates_two_jobs(
        self, job_service_with_real_redis
    ):
        request = JobSubmitRequest(
            operation="rag_query", payload={"query": "test"}, idempotency_key="shared-key"
        )
        with patch("app.services.job_service.process_ai_operation"):
            response_a, is_new_a = await job_service_with_real_redis.create_job("client-a", request)
            response_b, is_new_b = await job_service_with_real_redis.create_job("client-b", request)

        assert is_new_a is True
        assert is_new_b is True  # unique constraint is (client_id, idempotency_key), not idempotency_key alone
        assert response_a.job_id != response_b.job_id


class TestStatusCacheRoundTrip:
    async def test_status_is_readable_after_cache_populated(self, job_service_with_real_redis, db_session):
        request = JobSubmitRequest(
            operation="rag_query", payload={"query": "test"}, idempotency_key="cache-test-key"
        )
        with patch("app.services.job_service.process_ai_operation"):
            submit_response, _ = await job_service_with_real_redis.create_job("client-a", request)

        # First read: cache miss (create_job doesn't populate the status-read
        # cache key, only the submit path's own cache write) - reads through
        # to the real Postgres row and repopulates the real Redis cache.
        status_1 = await job_service_with_real_redis.get_job_status("client-a", submit_response.job_id)
        # Second read: should now be a real cache hit.
        status_2 = await job_service_with_real_redis.get_job_status("client-a", submit_response.job_id)

        assert status_1.status == status_2.status == JobStatus.QUEUED


@pytest.fixture
def sync_db_session(postgres_url):
    """
    _process_ai_operation_impl uses a sync Session by design (see
    app/db/worker_session.py's docstring on why workers stay synchronous).
    This mirrors that against the same container, rather than reusing the
    async db_session fixture and testing something subtly different from
    what actually runs in production.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    sync_url = postgres_url.replace("+asyncpg", "+psycopg")
    engine = create_engine(sync_url)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    with session_factory() as session:
        yield session
    engine.dispose()


class TestFullLifecycleAgainstRealDatabase:
    async def test_successful_job_reaches_success_state(
        self, job_service_with_real_redis, sync_db_session, redis_url
    ):
        from contextlib import contextmanager

        from app.workers.tasks import _process_ai_operation_impl

        request = JobSubmitRequest(
            operation="rag_query", payload={"query": "test"}, idempotency_key="lifecycle-key-1"
        )
        with patch("app.services.job_service.process_ai_operation"):
            submit_response, _ = await job_service_with_real_redis.create_job("client-a", request)

        @contextmanager
        def _real_session():
            yield sync_db_session

        with (
            patch("app.workers.tasks.get_worker_session", side_effect=_real_session),
            patch("app.workers.tasks.get_redis_client_sync") as mock_get_redis_sync,
            patch(
                "app.workers.tasks.run_ai_operation",
                new=AsyncMock(return_value={"summary": "integration test result"}),
            ),
        ):
            from redis import Redis as SyncRedis

            mock_get_redis_sync.return_value = SyncRedis.from_url(redis_url, decode_responses=True)
            task = MagicMock()
            _process_ai_operation_impl(task, str(submit_response.job_id))
            sync_db_session.commit()

        final_status = await job_service_with_real_redis.get_job_status(
            "client-a", submit_response.job_id
        )
        assert final_status.status == JobStatus.SUCCESS
        assert final_status.result == {"summary": "integration test result"}

    async def test_job_exhausting_retries_reaches_dead_letter(
        self, job_service_with_real_redis, sync_db_session, redis_url
    ):
        from contextlib import contextmanager

        from app.workers.tasks import _process_ai_operation_impl

        request = JobSubmitRequest(
            operation="rag_query", payload={"query": "test"}, idempotency_key="lifecycle-key-2"
        )
        with patch("app.services.job_service.process_ai_operation"):
            submit_response, _ = await job_service_with_real_redis.create_job("client-a", request)

        @contextmanager
        def _real_session():
            yield sync_db_session

        job = sync_db_session.get(Job, submit_response.job_id)
        job.retry_count = job.max_retries  # simulate having already exhausted retries
        sync_db_session.commit()

        with (
            patch("app.workers.tasks.get_worker_session", side_effect=_real_session),
            patch("app.workers.tasks.get_redis_client_sync") as mock_get_redis_sync,
            patch(
                "app.workers.tasks.run_ai_operation",
                new=AsyncMock(side_effect=AIOperationError("AI_PROVIDER_TIMEOUT", "timed out")),
            ),
        ):
            from redis import Redis as SyncRedis

            mock_get_redis_sync.return_value = SyncRedis.from_url(redis_url, decode_responses=True)
            task = MagicMock()
            _process_ai_operation_impl(task, str(submit_response.job_id))
            sync_db_session.commit()

        final_status = await job_service_with_real_redis.get_job_status(
            "client-a", submit_response.job_id
        )
        assert final_status.status == JobStatus.DEAD_LETTER
