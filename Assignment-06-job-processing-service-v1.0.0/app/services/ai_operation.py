"""
AI operation wrapper - the boundary around the slow operation being migrated.

INTENTIONALLY NOT IMPLEMENTED YET, and by design stays a thin wrapper even
once implemented: SDD Section 4 (Scope) explicitly excludes "the internal
logic of the AI operation itself (prompt engineering, model selection, RAG
retrieval tuning)" from this design. This function is the seam where an
existing AI/RAG pipeline gets plugged in - everything on the other side of
it (queueing, retries, status tracking) should not need to know what
happens inside.

`operation` corresponds to the `operation` field in JobSubmitRequest
(SDD Section 15, e.g. "rag_query"); dispatch-by-operation-type logic, if
needed, belongs here.
"""

from typing import Any


class AIOperationError(Exception):
    """
    The error contract between the AI operation and the retry/dead-letter
    logic in app/workers/tasks.py. `code` should be one of the values in
    app.workers.retry_policy.TRANSIENT_ERROR_CODES / PERMANENT_ERROR_CODES
    - that module (not this exception) is the single source of truth for
    what's retryable, so this class deliberately does not carry its own
    `retryable` flag.

    A future implementation of run_ai_operation() should raise this (rather
    than a bare Exception) for any error it can classify, e.g.:

        raise AIOperationError("AI_PROVIDER_TIMEOUT", "Upstream model timed out")
    """

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


async def run_ai_operation(operation: str, payload: dict[str, Any]) -> dict[str, Any]:
    """
    Will invoke the underlying AI/RAG pipeline for the given operation type
    and return a JSON-serializable result matching the `result` field of
    JobStatusResponse (SDD Section 15).

    Progress reporting: once implemented, this should accept a progress
    callback so app/workers/tasks.py can update Job.progress incrementally
    (SDD Section 8.2), rather than jumping from 0 to 100.
    """
    raise NotImplementedError(
        f"AI operation '{operation}' not implemented - out of scope for this "
        "design per SDD Section 4 (Scope); wire in the existing pipeline here."
    )
