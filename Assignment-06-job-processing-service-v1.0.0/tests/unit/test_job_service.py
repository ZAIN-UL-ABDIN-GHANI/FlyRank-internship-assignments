"""
Unit tests for JobService (SDD Section 8.1 - Job Submission, Section 8.2 -
Status Polling, Section 11 - Idempotency).

DB and Redis are mocked throughout via AsyncMock - these tests verify
orchestration (which branch runs, what gets persisted/enqueued/cached),
not real database or cache behavior. asyncio_mode = "auto" (pyproject.toml)
means async test functions need no explicit marker.
"""

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.cache.job_status_cache import job_to_cache_dict
from app.models.job import JobStatus
from app.models.schemas import JobSubmitRequest
from app.services.job_service import JobService


def _execute_result(scalar_value):
    """Matches the shape of db.execute(select(...)).scalar_one_or_none()."""
    result = MagicMock()
    result.scalar_one_or_none.return_value = scalar_value
    return result


@pytest.fixture
def submit_request():
    return JobSubmitRequest(
        operation="rag_query",
        payload={"query": "Summarize this report"},
        idempotency_key="idem-key-1",
    )


@pytest.fixture
def mock_db():
    db = AsyncMock()

    async def _refresh(job):
        # A mocked refresh() wouldn't otherwise populate server_default
        # columns the way a real PostgreSQL round-trip would.
        now = datetime.now(timezone.utc)
        job.created_at = job.created_at or now
        job.updated_at = now

    db.refresh.side_effect = _refresh
    return db


@pytest.fixture(autouse=True)
def mock_redis():
    with patch("app.services.job_service.get_redis_client") as mock_get_redis:
        redis = AsyncMock()
        redis.get.return_value = None
        mock_get_redis.return_value = redis
        yield redis


@pytest.fixture(autouse=True)
def mock_task():
    with patch("app.services.job_service.process_ai_operation") as mock_task:
        yield mock_task


class TestCreateJob:
    async def test_new_job_is_created_queued_and_enqueued(self, mock_db, submit_request, mock_task):
        mock_db.execute.return_value = _execute_result(None)  # no existing job

        service = JobService(mock_db)
        response, is_new = await service.create_job(client_id="client-1", request=submit_request)

        assert is_new is True
        assert response.status == JobStatus.QUEUED
        mock_task.delay.assert_called_once_with(str(response.job_id))
        mock_db.add.assert_called_once()
        assert mock_db.commit.call_count == 2  # PENDING insert, then QUEUED transition

    async def test_idempotent_replay_returns_existing_job_without_enqueueing(
        self, mock_db, submit_request, make_job, mock_task
    ):
        existing = make_job(status=JobStatus.SUCCESS)
        mock_db.execute.return_value = _execute_result(existing)

        service = JobService(mock_db)
        response, is_new = await service.create_job(client_id="client-1", request=submit_request)

        assert is_new is False
        assert response.job_id == existing.job_id
        mock_task.delay.assert_not_called()
        mock_db.add.assert_not_called()

    async def test_concurrent_submission_race_falls_back_to_existing_job(
        self, mock_db, submit_request, make_job, mock_task
    ):
        existing = make_job(status=JobStatus.PENDING)
        # 1st check: nothing found -> proceeds to insert. Insert's commit
        # raises (another request won the DB-level unique-constraint race,
        # SDD Section 7.6/11). 2nd check: finds what the other request created.
        mock_db.execute.side_effect = [_execute_result(None), _execute_result(existing)]
        mock_db.commit.side_effect = IntegrityError("INSERT", {}, Exception("duplicate key"))

        service = JobService(mock_db)
        response, is_new = await service.create_job(client_id="client-1", request=submit_request)

        assert is_new is False
        assert response.job_id == existing.job_id
        mock_db.rollback.assert_called_once()
        mock_task.delay.assert_not_called()


class TestGetJobStatus:
    async def test_cache_hit_skips_database_entirely(self, mock_db, mock_redis, make_job):
        job = make_job(status=JobStatus.IN_PROGRESS, progress=40)
        mock_redis.get.return_value = json.dumps(job_to_cache_dict(job))

        service = JobService(mock_db)
        response = await service.get_job_status(client_id=job.client_id, job_id=job.job_id)

        assert response.status == JobStatus.IN_PROGRESS
        assert response.progress == 40
        mock_db.get.assert_not_called()

    async def test_cache_miss_queries_database_and_repopulates_cache(
        self, mock_db, mock_redis, make_job
    ):
        job = make_job(status=JobStatus.SUCCESS, progress=100, result={"summary": "done"})
        mock_redis.get.return_value = None
        mock_db.get.return_value = job

        service = JobService(mock_db)
        response = await service.get_job_status(client_id=job.client_id, job_id=job.job_id)

        assert response.status == JobStatus.SUCCESS
        assert response.result == {"summary": "done"}
        mock_redis.set.assert_called_once()

    async def test_job_owned_by_different_client_returns_404_on_db_path(
        self, mock_db, mock_redis, make_job
    ):
        job = make_job(status=JobStatus.SUCCESS, client_id="someone-elses-client")
        mock_redis.get.return_value = None
        mock_db.get.return_value = job

        service = JobService(mock_db)
        with pytest.raises(HTTPException) as exc_info:
            await service.get_job_status(client_id="client-1", job_id=job.job_id)

        assert exc_info.value.status_code == 404

    async def test_job_owned_by_different_client_returns_404_on_cache_path(
        self, mock_db, mock_redis, make_job
    ):
        """
        The security-relevant case: ownership must be checked even when the
        data comes from cache, not just on the DB-query path (SDD Section 16).
        """
        job = make_job(status=JobStatus.SUCCESS, client_id="someone-elses-client")
        mock_redis.get.return_value = json.dumps(job_to_cache_dict(job))

        service = JobService(mock_db)
        with pytest.raises(HTTPException) as exc_info:
            await service.get_job_status(client_id="client-1", job_id=job.job_id)

        assert exc_info.value.status_code == 404
        mock_db.get.assert_not_called()  # confirms this was rejected from the cached data, not a DB fallback

    async def test_missing_job_returns_404(self, mock_db, mock_redis):
        mock_redis.get.return_value = None
        mock_db.get.return_value = None

        service = JobService(mock_db)
        with pytest.raises(HTTPException) as exc_info:
            await service.get_job_status(client_id="client-1", job_id="00000000-0000-0000-0000-000000000000")

        assert exc_info.value.status_code == 404


class TestCancelJob:
    async def test_cancelling_a_queued_job_succeeds(self, mock_db, mock_redis, make_job):
        job = make_job(status=JobStatus.QUEUED)
        mock_db.get.return_value = job

        service = JobService(mock_db)
        response = await service.cancel_job(client_id=job.client_id, job_id=job.job_id)

        assert response.status == JobStatus.CANCELLED
        assert job.status == JobStatus.CANCELLED
        mock_db.commit.assert_called_once()

    async def test_cancelling_an_in_progress_job_returns_409(self, mock_db, mock_redis, make_job):
        job = make_job(status=JobStatus.IN_PROGRESS)
        mock_db.get.return_value = job

        service = JobService(mock_db)
        with pytest.raises(HTTPException) as exc_info:
            await service.cancel_job(client_id=job.client_id, job_id=job.job_id)

        assert exc_info.value.status_code == 409
        assert job.status == JobStatus.IN_PROGRESS  # untouched

    async def test_cancelling_a_completed_job_returns_409(self, mock_db, mock_redis, make_job):
        job = make_job(status=JobStatus.SUCCESS)
        mock_db.get.return_value = job

        service = JobService(mock_db)
        with pytest.raises(HTTPException) as exc_info:
            await service.cancel_job(client_id=job.client_id, job_id=job.job_id)

        assert exc_info.value.status_code == 409

    async def test_cancelling_another_clients_job_returns_404_not_409(self, mock_db, mock_redis, make_job):
        """404, not 409 - shouldn't confirm the job exists to a client who doesn't own it."""
        job = make_job(status=JobStatus.QUEUED, client_id="someone-elses-client")
        mock_db.get.return_value = job

        service = JobService(mock_db)
        with pytest.raises(HTTPException) as exc_info:
            await service.cancel_job(client_id="client-1", job_id=job.job_id)

        assert exc_info.value.status_code == 404


class TestListJobs:
    async def test_returns_items_and_total_scoped_to_client(self, mock_db, mock_redis, make_job):
        jobs = [make_job(status=JobStatus.SUCCESS), make_job(status=JobStatus.IN_PROGRESS)]

        count_result = MagicMock()
        count_result.scalar_one.return_value = 2
        rows_result = MagicMock()
        rows_result.scalars.return_value.all.return_value = jobs
        mock_db.execute.side_effect = [count_result, rows_result]

        service = JobService(mock_db)
        response = await service.list_jobs(client_id="client-1", status=None, limit=20, offset=0)

        assert response.total == 2
        assert len(response.items) == 2
        assert response.limit == 20
        assert response.offset == 0

    async def test_empty_result_when_client_has_no_jobs(self, mock_db, mock_redis):
        count_result = MagicMock()
        count_result.scalar_one.return_value = 0
        rows_result = MagicMock()
        rows_result.scalars.return_value.all.return_value = []
        mock_db.execute.side_effect = [count_result, rows_result]

        service = JobService(mock_db)
        response = await service.list_jobs(client_id="client-1", status=None, limit=20, offset=0)

        assert response.total == 0
        assert response.items == []
