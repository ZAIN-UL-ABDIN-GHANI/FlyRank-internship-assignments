import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import close_pool, init_pool
from app.routers import items


@asynccontextmanager
async def lifespan(app: FastAPI):
    repo_type = os.environ.get("REPOSITORY_TYPE", "postgres").lower()
    if repo_type != "memory":
        await init_pool()
    yield
    if repo_type != "memory":
        await close_pool()


app = FastAPI(title="Assignment 2 — Postgres Edition", lifespan=lifespan)
app.include_router(items.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/health/redis")
async def health_redis():
    """Stretch goal: ping Redis to prove the compose stack wired it up."""
    import redis.asyncio as redis

    url = os.environ.get("REDIS_URL", "redis://redis:6379/0")
    client = redis.from_url(url)
    try:
        pong = await client.ping()
    finally:
        await client.aclose()
    return {"redis": "reachable" if pong else "unreachable"}
