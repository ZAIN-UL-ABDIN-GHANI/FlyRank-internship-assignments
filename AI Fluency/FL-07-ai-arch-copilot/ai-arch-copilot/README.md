# AI Architecture & Code Review Copilot

A LangGraph agent that (1) forces requirements-gathering on a feature request, (2) produces a phased
implementation plan grounded in a FAISS-retrieved knowledge base, and (3) optionally reviews supplied
code/diffs against the same rules and best practices. Exposed via FastAPI.

Full spec, sprint-by-sprint build log, and decisions: [`docs/FL-07.md`](docs/FL-07.md).

## Architecture

```
retrieve_context -> gather_requirements --[incomplete]--> END (clarifying question)
                                        --[READY]--> generate_plan --[no code]--> END
                                                                    --[code given]--> review_code -> END

/agent/review (standalone) -> review_code -> END   # skips retrieve_context/gather/plan entirely
```

- **retrieve_context** - FAISS search over `kb/*.md` using the latest user message.
- **gather_requirements** - asks one clarifying question at a time until the request is fully specified.
- **generate_plan** - structured `ImplementationPlan` (tech stack + small sequential phases).
- **review_code** - structured `CodeReviewReport` (severity-ranked findings); runs if `code` or `files` is
  supplied. Git unified diffs and multi-file input are parsed/formatted into per-file sections
  (`app/diff_parser.py`) before review so findings can reference the right file. Called either from the
  main graph (after a plan) or directly by `/agent/review` for a standalone review with no session/plan.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in GOOGLE_API_KEY
python -m app.ingest    # builds the FAISS index from kb/
uvicorn app.main:app --reload
```

## Configuration (`.env`)

| Variable | Default | Purpose |
|---|---|---|
| `GOOGLE_API_KEY` | - | required for all LLM calls (Google AI Studio) |
| `GOOGLE_MODEL` | `gemini-2.5-flash` | Gemini chat model used by all three agents |
| `KB_DIR` | `kb` | knowledge base source folder |
| `FAISS_INDEX_DIR` | `data/faiss_index` | generated index location (gitignored) |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | sentence-transformers model |
| `SESSION_DB_PATH` | `data/sessions.db` | SQLite file storing per-session conversation history |
| `LOG_LEVEL` | `INFO` | stdlib logging level |

## API

**`GET /health`** - liveness check.

**`POST /kb/ingest`** - (re)build the FAISS index after editing `kb/`.
```bash
curl -X POST http://localhost:8000/kb/ingest
```

**`POST /agent/gather`** - run the workflow. `session_id` identifies the conversation (history is held
server-side in SQLite); `message` is the new user message for this turn. `code` (raw text or a unified
Git diff) or `files` (list of `{filename, content}`) are optional - `files` takes priority if both given.

Incomplete request (returns a clarifying question):
```bash
curl -X POST http://localhost:8000/agent/gather \
  -H "Content-Type: application/json" \
  -d '{"session_id": "demo", "message": "add caching"}'
```

Follow-up turn, same session, now with a Git diff attached (returns a plan and a review):
```bash
curl -X POST http://localhost:8000/agent/gather \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo",
    "message": "Cache GET /users in Redis for 5 minutes, keyed by query params.",
    "code": "diff --git a/db.py b/db.py\n--- a/db.py\n+++ b/db.py\n@@ -1,3 +1,3 @@\n def get_user(user_id):\n-    query = \"SELECT * FROM users WHERE id=\" + user_id\n+    query = f\"SELECT * FROM users WHERE id={user_id}\"\n     return db.execute(query)\n"
  }'
```

Multi-file review (no diff needed):
```bash
curl -X POST http://localhost:8000/agent/gather \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo2",
    "message": "Review these files for issues.",
    "files": [
      {"filename": "db.py", "content": "query = f\"SELECT * FROM users WHERE id={user_id}\""},
      {"filename": "utils.py", "content": "def helper():\n    pass"}
    ]
  }'
```

**`POST /session/{session_id}/reset`** - clear a session's stored history.
```bash
curl -X POST http://localhost:8000/session/demo/reset
```

**`POST /agent/review`** - standalone code review, no session/requirements-gathering/planning involved.
Same `code`/`files` input as above (`files` takes priority if both given); requires at least one.

```bash
curl -X POST http://localhost:8000/agent/review \
  -H "Content-Type: application/json" \
  -d '{"code": "query = f\"SELECT * FROM users WHERE id={user_id}\""}'
```

```bash
curl -X POST http://localhost:8000/agent/review \
  -H "Content-Type: application/json" \
  -d '{
    "files": [
      {"filename": "db.py", "content": "query = f\"SELECT * FROM users WHERE id={user_id}\""},
      {"filename": "utils.py", "content": "def helper():\n    pass"}
    ]
  }'
```

## Testing

```bash
pytest tests/ -v
```

All 48 tests run offline (LLM and embedding calls are mocked/faked - no API key or network needed).

## Deployment

```bash
docker build -t ai-arch-copilot .
docker run -p 8000:8000 --env-file .env -v $(pwd)/data:/app/data ai-arch-copilot
```

The container builds the FAISS index on first start if `/app/data/faiss_index` is empty (mount a volume, as
above, so it - and the session database - persist across restarts). `.github/workflows/ci.yml` runs the
test suite and validates the Docker build on every push/PR to `main`.

## Project Structure

```
app/                     FastAPI app, LangGraph workflow, schemas, ingestion, retriever, session store, diff parser
kb/                      Knowledge base markdown (dev rules, best practices) - source for FAISS index
data/                    Generated FAISS index + session SQLite db (gitignored)
tests/                   Unit + integration tests, mirrors app/ structure
Dockerfile, .dockerignore   Container image definition
.github/workflows/ci.yml   Test suite + Docker build on push/PR
```

