"""
Unit tests for request schema validation (SDD Section 16 - Security).

Covers the payload-size cap and operation allow-list added during the
Phase 3 hardening pass - both were previously unenforced gaps.
"""

import pytest
from pydantic import ValidationError

from app.models.schemas import JobSubmitRequest


def test_allowed_operation_is_accepted():
    request = JobSubmitRequest(
        operation="rag_query", payload={"query": "test"}, idempotency_key="k1"
    )
    assert request.operation == "rag_query"


def test_disallowed_operation_is_rejected():
    with pytest.raises(ValidationError, match="not in the allowed set"):
        JobSubmitRequest(
            operation="delete_production_database",
            payload={"query": "test"},
            idempotency_key="k1",
        )


def test_payload_within_size_limit_is_accepted():
    request = JobSubmitRequest(
        operation="rag_query", payload={"query": "x" * 100}, idempotency_key="k1"
    )
    assert len(request.payload["query"]) == 100


def test_oversized_payload_is_rejected():
    from app.core.config import settings

    oversized = {"query": "x" * (settings.MAX_PAYLOAD_SIZE_BYTES + 1)}
    with pytest.raises(ValidationError, match="exceeding"):
        JobSubmitRequest(operation="rag_query", payload=oversized, idempotency_key="k1")
