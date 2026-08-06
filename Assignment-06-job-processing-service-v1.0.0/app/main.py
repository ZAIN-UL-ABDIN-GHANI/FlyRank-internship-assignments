"""
FastAPI application entrypoint.

Deliberately thin: configuration, logging, CORS, metrics, error handling,
and router wiring only. No business logic lives here (SDD Section 7.1 -
API Layer: "contains no AI logic and performs no blocking I/O beyond a
single DB write and a single enqueue call").
"""

import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.core.metrics import API_REQUEST_DURATION_SECONDS, API_REQUESTS_TOTAL
from app.db.session import engine

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Application starting", extra={"event": "app.startup", "env": settings.ENVIRONMENT})
    yield
    logger.info("Application shutting down", extra={"event": "app.shutdown"})
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """API request metrics (SDD Section 18) - path is the route template,
    not the raw URL, so /v1/jobs/{job_id} doesn't create a metrics series
    per distinct job ID."""
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start

    route = request.scope.get("route")
    path = route.path if route is not None else request.url.path

    API_REQUESTS_TOTAL.labels(
        method=request.method, path=path, status_code=response.status_code
    ).inc()
    API_REQUEST_DURATION_SECONDS.labels(method=request.method, path=path).observe(duration)
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catches anything that escapes route handlers so a bug returns a clean
    500 with a logged, correlatable event instead of an unstructured
    traceback leaking implementation details to the client.
    """
    logger.error(
        "Unhandled exception",
        extra={"event": "app.unhandled_exception", "path": request.url.path},
        exc_info=True,
    )
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(api_router, prefix=settings.API_V1_PREFIX)
# Deliberately unauthenticated and outside the /v1 prefix - Prometheus
# scrapers don't send app-level bearer tokens, and /metrics is
# conventionally at the root regardless of API versioning.
app.mount("/metrics", make_asgi_app())
