"""Aggregates all v1 endpoint routers (SDD Section 15)."""

from fastapi import APIRouter

from app.api.v1.endpoints import health, jobs

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(jobs.router)
