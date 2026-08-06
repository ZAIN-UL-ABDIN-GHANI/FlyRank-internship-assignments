"""
Unit tests for app.workers.tasks (SDD Section 9 - Lifecycle, Section 10 -
Retry, Section 11 - Idempotency).

_process_ai_operation_impl takes a plain `task` object and acquires its own
session/redis via get_worker_session()/get_redis_client_sync() - both
patched here. No real Celery, DB, or Redis is involved; run_ai_operation is
always mocked, since it currently just raises NotImplementedError and its
real implementation is explicitly out of scope (SDD Section 4).
"""

from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock

from app.models.job import JobStatus
from app.services.ai_operation import AIOperationError
from app.workers.tasks import _apply_jitter, _classify_error, _process_ai_operation_impl


class TestClassifyError:
    def test_permanent_error_code_is_not_retryable(self):
        code, message, retryable = _classify_error(AIOperationError("INVALID_INPUT", "bad payload"))
        assert code == "INVALID_INPUT"
        assert retryable is False

    def test_transient_error_code_is_retryable(self):
        code, message, retryable = _classify_error(
            AIOperationError("AI_PROVIDER_TIMEOUT", "upstream timed out")
        )
        assert retryable is True

    def test_unclassified_exception_defaults_to_unknown_and_retryable(self):
        code, message, retryable = _classify_error(RuntimeError("unexpected bug"))
        assert code == "UNKNOWN_ERROR"
        assert retryable is True


class TestApplyJitter:
    def test_jitter_stays_within_20_percent_and_never_negative(self):
        for _ in range(100):
            delay = _apply_jitter(10)
            assert 8.0 <= delay <= 12.0


@contextmanager
def _session_returning(db_mock):
    yield db_mock


class TestProcessAiOperationImpl:
    def _patch_worker_deps(self, mocker, job, lock_acquired=True):
        db = MagicMock()
        db.get.return_value = job
        mocker.patch("app.workers.tasks.get_worker_session", return_value=_session_returning(db))

        redis_client = MagicMock()
        lock = MagicMock()
        lock.acquire.return_value = lock_acquired
        redis_client.lock.return_value = lock
        mocker.patch("app.workers.tasks.get_redis_client_sync", return_value=redis_client)

        return db, redis_client, lock

    def test_already_terminal_job_is_skipped_without_touching_lock(self, mocker, make_job):
        job = make_job(status=JobStatus.SUCCESS)
        db, redis_client, lock = self._patch_worker_deps(mocker, job)
        task = MagicMock()

        _process_ai_operation_impl(task, str(job.job_id))

        redis_client.lock.assert_not_called()
        task.retry.assert_not_called()

    def test_lock_contention_backs_off_without_processing(self, mocker, make_job):
        job = make_job(status=JobStatus.QUEUED)
        db, redis_client, lock = self._patch_worker_deps(mocker, job, lock_acquired=False)
        task = MagicMock()

        _process_ai_operation_impl(task, str(job.job_id))

        assert job.status == JobStatus.QUEUED  # untouched - never entered processing
        task.retry.assert_not_called()
        lock.release.assert_not_called()

    def test_successful_execution_marks_job_success(self, mocker, make_job):
        job = make_job(status=JobStatus.QUEUED)
        db, redis_client, lock = self._patch_worker_deps(mocker, job)
        mocker.patch(
            "app.workers.tasks.run_ai_operation",
            new=AsyncMock(return_value={"summary": "generated result"}),
        )
        task = MagicMock()

        _process_ai_operation_impl(task, str(job.job_id))

        assert job.status == JobStatus.SUCCESS
        assert job.progress == 100
        assert job.result == {"summary": "generated result"}
        lock.release.assert_called_once()
        task.retry.assert_not_called()

    def test_transient_failure_within_retry_budget_schedules_retry(self, mocker, make_job):
        job = make_job(status=JobStatus.QUEUED, retry_count=0, max_retries=5)
        db, redis_client, lock = self._patch_worker_deps(mocker, job)
        mocker.patch(
            "app.workers.tasks.run_ai_operation",
            new=AsyncMock(side_effect=AIOperationError("AI_PROVIDER_TIMEOUT", "timed out")),
        )
        task = MagicMock()

        _process_ai_operation_impl(task, str(job.job_id))

        assert job.status == JobStatus.FAILED_TRANSIENT
        assert job.retry_count == 1
        task.retry.assert_called_once()
        _, kwargs = task.retry.call_args
        assert 1.6 <= kwargs["countdown"] <= 2.4  # attempt 1 -> 2s +/- 20% jitter
        lock.release.assert_called_once()

    def test_transient_failure_beyond_retry_budget_is_dead_lettered(self, mocker, make_job):
        job = make_job(status=JobStatus.QUEUED, retry_count=5, max_retries=5)
        db, redis_client, lock = self._patch_worker_deps(mocker, job)
        mocker.patch(
            "app.workers.tasks.run_ai_operation",
            new=AsyncMock(side_effect=AIOperationError("AI_PROVIDER_TIMEOUT", "timed out")),
        )
        task = MagicMock()

        _process_ai_operation_impl(task, str(job.job_id))

        assert job.status == JobStatus.DEAD_LETTER
        assert job.retry_count == 5  # exhausted, not incremented further
        task.retry.assert_not_called()

    def test_permanent_failure_fails_immediately_without_retry(self, mocker, make_job):
        job = make_job(status=JobStatus.QUEUED, retry_count=0, max_retries=5)
        db, redis_client, lock = self._patch_worker_deps(mocker, job)
        mocker.patch(
            "app.workers.tasks.run_ai_operation",
            new=AsyncMock(side_effect=AIOperationError("INVALID_INPUT", "bad payload")),
        )
        task = MagicMock()

        _process_ai_operation_impl(task, str(job.job_id))

        assert job.status == JobStatus.FAILED_PERMANENT
        assert job.retry_count == 0
        task.retry.assert_not_called()
        lock.release.assert_called_once()

    def test_unknown_exception_is_treated_as_retryable_not_permanent(self, mocker, make_job):
        job = make_job(status=JobStatus.QUEUED, retry_count=0, max_retries=5)
        db, redis_client, lock = self._patch_worker_deps(mocker, job)
        mocker.patch(
            "app.workers.tasks.run_ai_operation",
            new=AsyncMock(side_effect=RuntimeError("unexpected")),
        )
        task = MagicMock()

        _process_ai_operation_impl(task, str(job.job_id))

        assert job.status == JobStatus.FAILED_TRANSIENT
        task.retry.assert_called_once()
