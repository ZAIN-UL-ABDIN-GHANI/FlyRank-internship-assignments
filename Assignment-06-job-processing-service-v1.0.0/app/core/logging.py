"""
Structured JSON logging (SDD Section 17).

Every log line is emitted as a single-line JSON object so it can be shipped
to a log aggregator (Loki/ELK) and correlated by `job_id` across the API and
every worker that touches a given job. Fields beyond the standard ones are
attached via the stdlib `extra={...}` kwarg, e.g.:

    logger.info(
        "Transient error from AI provider, scheduling retry",
        extra={"job_id": job_id, "event": "job.retry_scheduled", "attempt": 2},
    )

which produces exactly the shape documented in the SDD:

    {"timestamp": "...", "level": "INFO", "job_id": "...",
     "event": "job.retry_scheduled", "attempt": 2, "message": "..."}

Raw input/output payloads must never be passed via `extra` - only IDs,
enums, counts, and short status strings. See SDD Section 17 on PII handling.
"""

import logging
import sys
from datetime import datetime, timezone
from json import dumps
from typing import Any

from app.core.config import settings

# Attributes already present on every stdlib LogRecord - anything else
# attached via extra={} is treated as a structured field to surface.
_STANDARD_RECORD_ATTRS = set(logging.LogRecord("", 0, "", 0, "", None, None).__dict__) | {
    "message",
    "asctime",
}


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(
                timespec="milliseconds"
            ),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Merge any extra={...} fields (job_id, event, attempt, worker_id, ...)
        for key, value in record.__dict__.items():
            if key not in _STANDARD_RECORD_ATTRS:
                payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return dumps(payload, default=str)


def configure_logging() -> None:
    """Call once at process startup (API and worker entrypoints both call this)."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(settings.LOG_LEVEL)

    # Quiet noisy third-party loggers down to the configured level without
    # letting them fall back to unstructured default formatting.
    for noisy_logger in ("uvicorn", "uvicorn.access", "celery", "sqlalchemy.engine"):
        logging.getLogger(noisy_logger).handlers = [handler]
        logging.getLogger(noisy_logger).propagate = False


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
