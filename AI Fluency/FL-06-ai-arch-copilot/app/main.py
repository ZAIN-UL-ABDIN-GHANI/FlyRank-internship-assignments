import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.config import settings
from app.graph import build_graph
from app.ingest import build_index
from app.logging_config import configure_logging
from app.schemas import AgentRequest, AgentResponse

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not settings.google_api_key:
        logger.warning("GOOGLE_API_KEY is not set - /agent/gather will fail until it is configured.")
    yield


app = FastAPI(title="AI Architecture Copilot", lifespan=lifespan)
_graph = build_graph()


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": "internal server error"})


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/kb/ingest")
def ingest_kb():
    try:
        count = build_index()
    except ValueError as e:
        raise HTTPException(400, str(e))
    logger.info("kb/ingest: indexed %d chunks", count)
    return {"chunks_indexed": count}


@app.post("/agent/gather", response_model=AgentResponse)
def gather(req: AgentRequest):
    if not req.history:
        raise HTTPException(400, "history must not be empty")

    logger.info("agent/gather: %d history messages, code_provided=%s", len(req.history), bool(req.code))

    state = {
        "history": [m.model_dump() for m in req.history],
        "retrieved_context": [],
        "clarifying_question": None,
        "requirements_complete": False,
        "plan": None,
        "code_context": req.code,
        "review": None,
    }
    try:
        result = _graph.invoke(state)
    except Exception as e:
        logger.exception("agent/gather: workflow failed")
        raise HTTPException(502, f"agent workflow failed: {e}")

    return AgentResponse(
        requirements_complete=result["requirements_complete"],
        clarifying_question=result["clarifying_question"],
        retrieved_context=result["retrieved_context"],
        plan=result.get("plan"),
        review=result.get("review"),
    )
