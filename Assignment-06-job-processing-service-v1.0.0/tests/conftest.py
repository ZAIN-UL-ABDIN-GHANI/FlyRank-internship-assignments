"""Shared fixtures for the test suite."""

import uuid
from datetime import datetime, timezone

import pytest

from app.models.job import Job, JobStatus


@pytest.fixture
def make_job():
    """
    Factory fixture for an in-memory Job ORM instance - no database
    involved. SQLAlchemy models are plain Python objects until a session
    actually flushes them, so this is safe to use across all unit tests.
    """

    def _make_job(**overrides):
        defaults = dict(
            job_id=uuid.uuid4(),
            client_id="test-client",
            idempotency_key="test-idempotency-key",
            status=JobStatus.PENDING,
            progress=0,
            input_payload={"operation": "rag_query", "payload": {"query": "test query"}},
            result=None,
            error_detail=None,
            retry_count=0,
            max_retries=5,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            started_at=None,
            completed_at=None,
        )
        defaults.update(overrides)
        return Job(**defaults)

    return _make_job
