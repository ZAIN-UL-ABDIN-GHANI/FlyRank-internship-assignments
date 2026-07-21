import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.db import close_pool, init_pool, initialize_database
from app.routers import items


@asynccontextmanager
async def lifespan(app: FastAPI):
    repo_type = os.environ.get("REPOSITORY_TYPE", "postgres").lower()
    if repo_type != "memory":
        await init_pool()
        await initialize_database()
    yield
    if repo_type != "memory":
        await close_pool()


app = FastAPI(title="Assignment 2 — Postgres Edition", lifespan=lifespan)
app.include_router(items.router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    if request.method == "POST" and request.url.path == "/tasks":
        for error in exc.errors():
            if error.get("loc") == ("body", "title") and error.get("type") == "missing":
                return JSONResponse(status_code=400, content={"error": "Title is required"})
    return JSONResponse(status_code=400, content={"error": "Invalid request body"})


@app.get("/health")
async def health():
    return {"status": "ok"}
