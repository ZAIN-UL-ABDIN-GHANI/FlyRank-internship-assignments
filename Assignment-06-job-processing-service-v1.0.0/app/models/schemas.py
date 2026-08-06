"""
Request/response schemas (SDD Section 15 - API Design).

Each schema below corresponds directly to one of the JSON examples in the
SDD. Keeping them 1:1 means the API Design section of the SDD IS the
contract test - any drift between this file and that section is a bug.
"""

from datetime import datetime
from json import dumps
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.core.config import settings
from app.models.job import JobStatus

# --- POST /v1/jobs ---------------------------------------------------------


class JobSubmitRequest(BaseModel):
    operation: str = Field(..., examples=["rag_query"])
    payload: dict[str, Any] = Field(
        ..., examples=[{"query": "Summarize the attached report", "document_id": "doc_8891"}]
    )
    idempotency_key: str = Field(..., min_length=1, max_length=255)

    @field_validator("operation")
    @classmethod
    def _operation_must_be_allowed(cls, value: str) -> str:
        allowed = {op.strip() for op in settings.ALLOWED_OPERATIONS.split(",") if op.strip()}
        if value not in allowed:
            raise ValueError(f"operation '{value}' is not in the allowed set: {sorted(allowed)}")
        return value

    @field_validator("payload")
    @classmethod
    def _payload_must_fit_size_limit(cls, value: dict[str, Any]) -> dict[str, Any]:
        size = len(dumps(value).encode("utf-8"))
        if size > settings.MAX_PAYLOAD_SIZE_BYTES:
            raise ValueError(
                f"payload is {size} bytes, exceeding the {settings.MAX_PAYLOAD_SIZE_BYTES}-byte limit"
            )
        return value


class JobSubmitResponse(BaseModel):
    job_id: UUID
    status: JobStatus
    status_url: str
    created_at: datetime


# --- GET /v1/jobs/{job_id} --------------------------------------------------


class JobErrorDetail(BaseModel):
    code: str
    message: str
    retryable: bool


class JobStatusResponse(BaseModel):
    job_id: UUID
    status: JobStatus
    progress: int = Field(ge=0, le=100)
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: dict[str, Any] | None = None
    error: JobErrorDetail | None = None


# --- GET /v1/jobs (list, paginated) ----------------------------------------


class JobListResponse(BaseModel):
    items: list[JobStatusResponse]
    total: int
    limit: int
    offset: int


# --- DELETE /v1/jobs/{job_id} ----------------------------------------------


class JobCancelResponse(BaseModel):
    job_id: UUID
    status: JobStatus
    message: str


# --- Shared error envelope (matches Section 15's HTTP status code table) ---


class ErrorResponse(BaseModel):
    detail: str


# --- GET /v1/health, /v1/health/ready ---------------------------------------


class HealthResponse(BaseModel):
    status: Literal["ok"]


class ReadinessResponse(BaseModel):
    status: Literal["ok", "degraded"]
    database: Literal["ok", "unreachable"]
    redis: Literal["ok", "unreachable"]
