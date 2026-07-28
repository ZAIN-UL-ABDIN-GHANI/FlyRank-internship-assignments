"""FastAPI application entry point."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    """Application factory: wires config, logging, routers, and error handling."""
    configure_logging()
    settings = get_settings()

    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
    )
    application.include_router(api_router)

    @application.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=500, content={"detail": str(exc)})

    return application


app = create_app()
