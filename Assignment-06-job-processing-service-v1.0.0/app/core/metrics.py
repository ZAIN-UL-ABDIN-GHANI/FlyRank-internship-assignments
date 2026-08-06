"""
Prometheus metrics (SDD Section 18 - Monitoring).

Job-lifecycle and API-request metrics are instrumented directly at their
source (job_service.py, tasks.py, and an ASGI middleware in main.py).

Queue depth is deliberately NOT instrumented here. It would just mean
polling the same Redis list length a dedicated Celery/Redis exporter reads
more directly and efficiently - the same reasoning already applied to the
HPA gap in deploy/k8s/hpa.yaml (SDD NFR2). Run a redis_exporter or
celery-exporter sidecar for that metric rather than duplicating it in the
application.
"""

from prometheus_client import Counter, Histogram

JOBS_SUBMITTED = Counter(
    "jobs_submitted_total", "Total jobs submitted", ["operation"]
)

JOBS_COMPLETED = Counter(
    "jobs_completed_total",
    "Total jobs reaching a terminal state",
    ["outcome"],  # success | dead_letter | failed_permanent | cancelled
)

JOB_RETRIES = Counter(
    "job_retries_total", "Total retry attempts scheduled", ["error_code"]
)

JOB_PROCESSING_DURATION_SECONDS = Histogram(
    "job_processing_duration_seconds",
    "Wall-clock time from job creation to reaching a terminal state",
    buckets=(1, 5, 15, 30, 60, 120, 300, 600, 1800, 3600),
)

API_REQUESTS_TOTAL = Counter(
    "api_requests_total", "Total API requests", ["method", "path", "status_code"]
)

API_REQUEST_DURATION_SECONDS = Histogram(
    "api_request_duration_seconds", "API request duration", ["method", "path"]
)
