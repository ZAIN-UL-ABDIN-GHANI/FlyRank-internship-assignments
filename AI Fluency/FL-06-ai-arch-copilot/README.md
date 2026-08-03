# AI Architecture & Code Review Copilot

A LangGraph agent that (1) forces requirements-gathering on a feature request, (2) produces a phased
implementation plan grounded in a FAISS-retrieved knowledge base, and (3) optionally reviews supplied
code/diffs against the same rules and best practices. Exposed via FastAPI.

## Architecture

```
retrieve_context -> gather_requirements --[incomplete]--> END (clarifying question)
                                        --[READY]--> generate_plan --[no code]--> END
                                                                    --[code given]--> review_code -> END
```

- **retrieve_context** - FAISS search over `kb/*.md` using the latest user message.
- **gather_requirements** - asks one clarifying question at a time until the request is fully specified.
- **generate_plan** - structured `ImplementationPlan` (tech stack + small sequential phases).
- **review_code** - structured `CodeReviewReport` (severity-ranked findings), only runs if `code` is supplied.

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
| `LOG_LEVEL` | `INFO` | stdlib logging level |

## API

**`GET /health`** - liveness check.

**`POST /kb/ingest`** - (re)build the FAISS index after editing `kb/`.
```bash
curl -X POST http://localhost:8000/kb/ingest
```

**`POST /agent/gather`** - run the workflow. `history` is the full conversation so far (client keeps state);
`code` is optional raw source/diff text.

Incomplete request (returns a clarifying question):
```bash
curl -X POST http://localhost:8000/agent/gather \
  -H "Content-Type: application/json" \
  -d '{"history": [{"role": "user", "content": "add caching"}]}'
```

Complete request with code attached (returns a plan and a review):
```bash
curl -X POST http://localhost:8000/agent/gather \
  -H "Content-Type: application/json" \
  -d '{
    "history": [{"role": "user", "content": "Cache GET /users in Redis for 5 minutes, keyed by query params."}],
    "code": "query = f\"SELECT * FROM users WHERE id={user_id}\""
  }'
```

## Testing

```bash
pytest tests/ -v
```

All 23 tests run offline (LLM and embedding calls are mocked/faked - no API key or network needed).

## Project Structure

```
app/            FastAPI app, LangGraph workflow, schemas, ingestion, retriever
kb/             Knowledge base markdown (dev rules, best practices) - source for FAISS index
data/           Generated FAISS index (gitignored)
tests/          Unit + integration tests, mirrors app/ structure
```

a
