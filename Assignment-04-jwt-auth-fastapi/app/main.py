"""
Application entry point.

Wires together routers and centralized exception handling.
Run with:  uvicorn app.main:app --reload
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    AppError,
    DuplicateUserError,
    InvalidCredentialsError,
    UnauthorizedError,
    ValidationError,
)
from app.database import init_db
from app.routes import auth as auth_routes
from app.routes import users as user_routes

logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # create tables on startup
    yield


app = FastAPI(
    title="JWT Auth API",
    description="Minimal, production-style JWT authentication for FastAPI.",
    version="1.0.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Centralized error handling
#
# Every error response has the same shape:
#   {"success": false, "message": "<human readable message>"}
# Stack traces are never sent to the client; unexpected errors are logged
# server-side and returned as a generic 500.
# ---------------------------------------------------------------------------

_STATUS_MAP = {
    ValidationError: status.HTTP_400_BAD_REQUEST,
    DuplicateUserError: status.HTTP_409_CONFLICT,
    InvalidCredentialsError: status.HTTP_401_UNAUTHORIZED,
    UnauthorizedError: status.HTTP_401_UNAUTHORIZED,
}


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    status_code = _STATUS_MAP.get(type(exc), status.HTTP_400_BAD_REQUEST)
    return JSONResponse(
        status_code=status_code,
        content={"success": False, "message": exc.message},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Turns Pydantic's default 422 payload into our consistent error shape (400)."""
    first_error = exc.errors()[0]
    field = ".".join(str(loc) for loc in first_error["loc"] if loc != "body")
    message = f"{field}: {first_error['msg']}" if field else first_error["msg"]
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"success": False, "message": message},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Catch-all safety net: never leak stack traces to the client."""
    logger.exception("Unhandled exception while processing %s %s", request.method, request.url)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"success": False, "message": "Internal server error"},
    )


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(auth_routes.router)
app.include_router(user_routes.router)


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}
