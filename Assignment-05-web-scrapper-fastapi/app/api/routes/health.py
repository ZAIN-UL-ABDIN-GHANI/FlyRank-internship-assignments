"""Health check endpoint."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.api.deps import SettingsDep

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    app: str
    environment: str


@router.get("/health", response_model=HealthResponse, tags=["health"])
def health_check(settings: SettingsDep) -> HealthResponse:
    return HealthResponse(status="ok", app=settings.app_name, environment=settings.app_env)
