"""
Unit tests for app.core.rate_limit (SDD Section 16 - Security).
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.core.rate_limit import enforce_rate_limit


@pytest.fixture
def mock_redis():
    with patch("app.core.rate_limit.get_redis_client") as mock_get_redis:
        redis = AsyncMock()
        mock_get_redis.return_value = redis
        yield redis


async def test_requests_within_limit_are_allowed(mock_redis):
    mock_redis.incr.return_value = 1
    await enforce_rate_limit("client-1")  # should not raise
    mock_redis.expire.assert_called_once()


async def test_requests_over_limit_raise_429(mock_redis):
    from app.core.config import settings

    mock_redis.incr.return_value = settings.RATE_LIMIT_PER_MINUTE + 1

    with pytest.raises(HTTPException) as exc_info:
        await enforce_rate_limit("client-1")

    assert exc_info.value.status_code == 429


async def test_expire_only_set_on_first_request_in_window(mock_redis):
    mock_redis.incr.return_value = 2  # not the first request this window
    await enforce_rate_limit("client-1")
    mock_redis.expire.assert_not_called()


async def test_redis_unavailable_fails_open_rather_than_blocking(mock_redis):
    mock_redis.incr.side_effect = ConnectionError("redis down")
    await enforce_rate_limit("client-1")  # should not raise despite Redis being down
