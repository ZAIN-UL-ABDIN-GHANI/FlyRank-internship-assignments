"""
Retry policy configuration (SDD Section 10 - Retry Strategy).

These are the numbers behind the backoff table in the SDD:

    Attempt  Backoff Delay  Cumulative Wait
    1        2s             2s
    2        4s             6s
    3        8s             14s
    4        16s            30s
    5(final) 32s            62s

This module only holds the *policy* (numbers + the classification of which
errors are retryable) - the code that actually applies it during task
execution (scheduling retries, dead-lettering) belongs in tasks.py and has
not been implemented yet.
"""

from app.core.config import settings

MAX_RETRIES: int = settings.JOB_DEFAULT_MAX_RETRIES
BASE_DELAY_SECONDS: int = settings.JOB_RETRY_BASE_DELAY_SECONDS
MAX_DELAY_SECONDS: int = settings.JOB_RETRY_MAX_DELAY_SECONDS

# Jitter fraction applied on top of the exponential delay to avoid
# synchronized retry storms (SDD Section 10).
JITTER_FRACTION: float = 0.2


def compute_backoff_seconds(attempt: int) -> int:
    """
    Exponential backoff with a hard cap: delay = base * 2^(attempt - 1),
    capped at MAX_DELAY_SECONDS.

    `attempt` is 1-indexed and must match the "Attempt" column of the SDD
    Section 10 table exactly: attempt=1 -> 2s, attempt=2 -> 4s, attempt=3 ->
    8s, attempt=4 -> 16s, attempt=5 -> 32s. Callers scheduling the Nth retry
    should pass N, not N-1 or the count of retries already made.

    Jitter is applied by the caller at schedule time (kept separate here so
    this function stays deterministic and testable).
    """
    return min(BASE_DELAY_SECONDS * (2 ** (attempt - 1)), MAX_DELAY_SECONDS)


# Error classification (SDD Section 10 / Section 12): only transient errors
# are retried; permanent errors go straight to FAILED_PERMANENT.
TRANSIENT_ERROR_CODES: frozenset[str] = frozenset(
    {
        "AI_PROVIDER_TIMEOUT",
        "AI_PROVIDER_RATE_LIMITED",
        "AI_PROVIDER_UNAVAILABLE",
        "NETWORK_ERROR",
        "DATABASE_UNAVAILABLE",
    }
)
PERMANENT_ERROR_CODES: frozenset[str] = frozenset(
    {
        "INVALID_INPUT",
        "UNSUPPORTED_OPERATION",
        "AUTH_FAILURE",
        "CONTENT_POLICY_VIOLATION",
    }
)


def determine_next_action(retry_count: int, max_retries: int, retryable: bool) -> str:
    """
    The decision diamond from the SDD Section 10 flowchart, as a pure
    function: given the retry count *before* this failure and whether the
    error is retryable, what happens next?

    Returns one of "RETRY", "DEAD_LETTER", "FAIL_PERMANENT". Performs no
    I/O and mutates nothing - app/workers/tasks.py is responsible for
    acting on the result (incrementing retry_count, scheduling the actual
    Celery retry, persisting status).

    `retry_count` must be the count *before* incrementing for this failure,
    since this function itself doesn't increment it - the caller does, and
    only after deciding "RETRY" is the right action.
    """
    if not retryable:
        return "FAIL_PERMANENT"
    if retry_count < max_retries:
        return "RETRY"
    return "DEAD_LETTER"
