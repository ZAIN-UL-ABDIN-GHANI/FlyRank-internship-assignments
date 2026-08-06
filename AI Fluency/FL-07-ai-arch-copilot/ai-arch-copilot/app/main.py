import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.config import settings
from app.graph import build_graph, review_code
from app.ingest import build_index
from app.logging_config import configure_logging
from app.schemas import AgentRequest, AgentResponse, ReviewRequest, ReviewResponse
from app.session_store import append, get_history, reset

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
    if not req.message.strip():
        raise HTTPException(400, "message must not be empty")

    prior_history = get_history(req.session_id)
    append(req.session_id, "user", req.message)
    history = prior_history + [{"role": "user", "content": req.message}]

    logger.info(
        "agent/gather: session=%s, %d history messages, code_provided=%s, files_provided=%s",
        req.session_id,
        len(history),
        bool(req.code),
        len(req.files) if req.files else 0,
    )

    state = {
        "history": history,
        "retrieved_context": [],
        "clarifying_question": None,
        "requirements_complete": False,
        "plan": None,
        "code_context": req.code,
        "code_files": [f.model_dump() for f in req.files] if req.files else None,
        "review": None,
    }
    try:
        result = _graph.invoke(state)
    except Exception as e:
        logger.exception("agent/gather: workflow failed")
        raise HTTPException(502, f"agent workflow failed: {e}")

    if result["clarifying_question"]:
        assistant_reply = result["clarifying_question"]
    else:
        assistant_reply = "Requirements complete. Plan generated."
        if result.get("review"):
            assistant_reply += " Code review generated."
    append(req.session_id, "assistant", assistant_reply)

    return AgentResponse(
        requirements_complete=result["requirements_complete"],
        clarifying_question=result["clarifying_question"],
        retrieved_context=result["retrieved_context"],
        plan=result.get("plan"),
        review=result.get("review"),
    )


@app.post("/session/{session_id}/reset")
def reset_session(session_id: str):
    reset(session_id)
    logger.info("session/reset: session=%s", session_id)
    return {"session_id": session_id, "reset": True}


@app.post("/agent/review", response_model=ReviewResponse)
def review(req: ReviewRequest):
    if not req.code and not req.files:
        raise HTTPException(400, "either code or files must be provided")

    logger.info(
        "agent/review: code_provided=%s, files_provided=%d",
        bool(req.code),
        len(req.files) if req.files else 0,
    )

    state = {
        "history": [],
        "retrieved_context": [],
        "clarifying_question": None,
        "requirements_complete": True,
        "plan": None,
        "code_context": req.code,
        "code_files": [f.model_dump() for f in req.files] if req.files else None,
        "review": None,
    }
    try:
        result = review_code(state)
    except Exception as e:
        logger.exception("agent/review: review failed")
        raise HTTPException(502, f"code review failed: {e}")

    return ReviewResponse(review=result["review"])
