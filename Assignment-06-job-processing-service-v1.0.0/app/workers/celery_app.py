"""
Celery application instance and configuration (SDD Section 7.2, Section 9).

Configuration only - no task bodies live here (see tasks.py). Two settings
are load-bearing for the reliability guarantees in the SDD and must not be
changed casually:

  task_acks_late=True + worker_prefetch_multiplier=1
      A task is only ack'd (removed from the queue) after it finishes, not
      when it's received. A worker crash mid-task causes redelivery instead
      of silent job loss (SDD Section 9, Section 20 - Risks). This is *why*
      the worker-side idempotency guard in Section 11 is mandatory.
"""

from celery import Celery
from celery.signals import setup_logging as celery_setup_logging_signal
from celery.signals import worker_init, worker_process_shutdown

from app.core.config import settings
from app.core.logging import configure_logging, get_logger

logger = get_logger(__name__)

# Celery's prefork pool forks multiple child processes, each with its own
# memory space - a Counter incremented in one child is invisible to the
# others. A naive start_http_server() per child would also mean every
# child trying to bind the same port, crashing all but the first.
# prometheus_client's documented fix is multiprocess mode: each process
# writes to per-PID files under PROMETHEUS_MULTIPROC_DIR, and one
# aggregating collector (started once, here, before fork) merges them.
_WORKER_METRICS_PORT = 9100

celery_app = Celery(
    "job_processing_service",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_queue="default",
    task_track_started=True,
    result_expires=settings.JOB_RETENTION_DAYS * 24 * 60 * 60,
    broker_connection_retry_on_startup=True,
    timezone="UTC",
    enable_utc=True,
)


@celery_setup_logging_signal.connect
def _configure_worker_logging(**_kwargs) -> None:
    """
    Takes over Celery's own logging setup entirely (that's what connecting
    to this specific signal does) so the worker process emits the same
    structured JSON as the API (SDD Section 17), rather than Celery's
    default unstructured format. Without this, the worker - where most
    lifecycle events actually happen - would silently not be structured.
    """
    configure_logging()


@worker_init.connect
def _start_worker_metrics_server(**_kwargs) -> None:
    """
    Fires once in the parent process, before the prefork pool forks any
    children - avoids the port-conflict bug described above. Requires
    PROMETHEUS_MULTIPROC_DIR to be set to a writable, empty directory
    (see .env.example); without it, this logs a warning and metrics are
    unavailable for this worker rather than crashing startup.
    """
    import os

    if "PROMETHEUS_MULTIPROC_DIR" not in os.environ:
        logger.warning(
            "PROMETHEUS_MULTIPROC_DIR not set - worker metrics disabled",
            extra={"event": "metrics.multiproc_dir_missing"},
        )
        return

    from prometheus_client import CollectorRegistry, multiprocess
    from prometheus_client.exposition import make_wsgi_app
    from wsgiref.simple_server import make_server
    import threading

    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    server = make_server("0.0.0.0", _WORKER_METRICS_PORT, make_wsgi_app(registry))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    logger.info(
        "Worker metrics server started",
        extra={"event": "metrics.server_started", "port": _WORKER_METRICS_PORT},
    )


@worker_process_shutdown.connect
def _cleanup_worker_metrics(pid, **_kwargs) -> None:
    """Prevents stale per-PID metric files from accumulating as child processes recycle."""
    import os

    if "PROMETHEUS_MULTIPROC_DIR" in os.environ:
        from prometheus_client import multiprocess

        multiprocess.mark_process_dead(pid)
