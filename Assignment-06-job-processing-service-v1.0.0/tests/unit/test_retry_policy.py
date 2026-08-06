"""
Unit tests for app.workers.retry_policy (SDD Section 10).

test_compute_backoff_seconds_matches_sdd_table exists specifically because
of the off-by-one bug found and fixed during Phase 1 validation - this is
the regression test for that fix.
"""

import pytest

from app.workers.retry_policy import (
    PERMANENT_ERROR_CODES,
    TRANSIENT_ERROR_CODES,
    compute_backoff_seconds,
    determine_next_action,
)


@pytest.mark.parametrize(
    "attempt,expected_delay_seconds",
    [(1, 2), (2, 4), (3, 8), (4, 16), (5, 32)],
)
def test_compute_backoff_seconds_matches_sdd_table(attempt, expected_delay_seconds):
    assert compute_backoff_seconds(attempt) == expected_delay_seconds


def test_compute_backoff_seconds_caps_beyond_the_table():
    # Uncapped, attempt=6 would be 64s - must hold at the 32s ceiling.
    assert compute_backoff_seconds(6) == 32


def test_cumulative_wait_across_all_five_attempts_matches_sdd_table():
    total = sum(compute_backoff_seconds(attempt) for attempt in range(1, 6))
    assert total == 62


@pytest.mark.parametrize(
    "retry_count,max_retries,retryable,expected_action",
    [
        (0, 5, False, "FAIL_PERMANENT"),
        (3, 5, False, "FAIL_PERMANENT"),  # permanent overrides retry_count entirely
        (0, 5, True, "RETRY"),
        (4, 5, True, "RETRY"),
        (5, 5, True, "DEAD_LETTER"),  # exactly exhausted
        (7, 5, True, "DEAD_LETTER"),  # defensively past max
    ],
)
def test_determine_next_action(retry_count, max_retries, retryable, expected_action):
    assert determine_next_action(retry_count, max_retries, retryable) == expected_action


def test_transient_and_permanent_error_codes_are_disjoint():
    """A code classified as both would make retryability depend on set iteration order."""
    assert TRANSIENT_ERROR_CODES.isdisjoint(PERMANENT_ERROR_CODES)
