"""
ORM models for the job data model (SDD Section 7.6 - Data Model).

Field-for-field match to the ER diagram in the SDD:

    JOB { job_id, idempotency_key, status, progress, input_payload, result,
          error_detail, retry_count, max_retries, created_at, updated_at,
          started_at, completed_at, client_id }
    RETRY_ATTEMPT { attempt_id, job_id FK, attempt_number, outcome,
                    error_message, attempted_at }
    JOB ||--o{ RETRY_ATTEMPT : has

`JobStatus` values match the state machine in SDD Section 9 exactly, so the
state diagram is the single source of truth for what a job's status can be.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.session import Base


class JobStatus(str, enum.Enum):
    """
    Extends the 7 states in the SDD Section 9 state diagram with CANCELLED,
    needed for FR9 (SDD Section 2) - job cancellation wasn't modeled in the
    original state diagram, and "cancelled" isn't equivalent to any existing
    state (it's not a failure, and it's distinct from never having run).
    """

    PENDING = "PENDING"
    QUEUED = "QUEUED"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILED_TRANSIENT = "FAILED_TRANSIENT"
    FAILED_PERMANENT = "FAILED_PERMANENT"
    DEAD_LETTER = "DEAD_LETTER"
    CANCELLED = "CANCELLED"


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        # Enforces idempotent submission at the database level (SDD Section 11)
        UniqueConstraint("client_id", "idempotency_key", name="uq_job_client_idempotency"),
        CheckConstraint("progress >= 0 AND progress <= 100", name="ck_job_progress_range"),
        Index("ix_jobs_status_created_at", "status", "created_at"),
    )

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    client_id: Mapped[str] = mapped_column(String(128), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)

    status: Mapped[JobStatus] = mapped_column(
        String(32), nullable=False, default=JobStatus.PENDING
    )
    progress: Mapped[int] = mapped_column(default=0)

    input_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_detail: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    retry_count: Mapped[int] = mapped_column(default=0)
    max_retries: Mapped[int] = mapped_column(default=5)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    retry_attempts: Mapped[list["RetryAttempt"]] = relationship(
        back_populates="job", cascade="all, delete-orphan", order_by="RetryAttempt.attempt_number"
    )

    def __repr__(self) -> str:
        return f"<Job {self.job_id} status={self.status}>"


class RetryAttempt(Base):
    """
    Audit trail of retry attempts for a job (SDD Section 10 - Retry Strategy,
    and Section 18 - Monitoring, which sources retry-rate metrics from this
    table).
    """

    __tablename__ = "retry_attempts"
    __table_args__ = (
        UniqueConstraint("job_id", "attempt_number", name="uq_retry_job_attempt_number"),
    )

    attempt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.job_id", ondelete="CASCADE"), nullable=False
    )
    attempt_number: Mapped[int] = mapped_column(nullable=False)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False)  # e.g. "failed", "succeeded"
    error_message: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    attempted_at: Mapped[datetime] = mapped_column(server_default=func.now())

    job: Mapped["Job"] = relationship(back_populates="retry_attempts")

    def __repr__(self) -> str:
        return f"<RetryAttempt job_id={self.job_id} attempt={self.attempt_number}>"
