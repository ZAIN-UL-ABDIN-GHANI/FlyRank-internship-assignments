# W5 – Phase 1: Planning & System Design
*Responsible Web Scraping System for RAG Data Ingestion*

## 1. Project Overview
A modular system that fetches data from a practice website, extracts and cleans it, and stores structured records for future RAG ingestion. Built to the same production standard as the rest of the stack: clean architecture, env-based config, Dockerized, ready for CI/CD.

## 2. Goal
Produce clean, deduplicated, schema-validated records ready for future chunking/embedding — while treating responsible crawling (robots.txt, rate limits, retries) as a core requirement, not an afterthought.

## 3. Functional Requirements
- Fetch pages from the target site, honoring robots.txt.
- Parse HTML and locate relevant content blocks.
- Extract defined fields per record type (title, description, category, price/attributes, source URL, timestamp).
- Clean/normalize text (whitespace, encoding, casing, units/dates/currency).
- Validate extracted data against a strict schema before persistence.
- Persist records with duplicate prevention (URL + content hash).
- Trigger/monitor scrape runs and check system health via API.
- Log every stage and failure with enough context to debug without re-crawling.

## 4. Non-Functional Requirements
- **Reliability** — one bad page never stops a run.
- **Compliance** — robots.txt and crawl-delay always respected.
- **Observability** — structured logs, health endpoint, per-run correlation ID.
- **Maintainability** — fetch/parse/extract/clean/store fully decoupled and independently replaceable.
- **Security** — all config via environment variables; no hardcoded secrets/URLs.
- **Scalability** — serving/storage side scales horizontally for many future RAG consumers; crawl side scales by adding sources/workers, never by exceeding politeness limits on one target.
- **Portability** — fully Dockerized, environment-based configuration.

## 5. Assumptions & Constraints
- Target: a public scraping-practice site (e.g., books.toscrape.com) — static/server-rendered HTML, no JS rendering needed.
- Single site in scope this phase; design is source-agnostic for future additions.
- No authentication/login wall on the target site.
- Data volume is practice-scale; design favors correctness over raw throughput.
- Embedding/vector indexing (FAISS) is out of scope — this system only prepares data for it.
- Only pages permitted by robots.txt are crawled; no bypassing of access controls.

## 6. High-Level Architecture
Layered pipeline, strict separation of concerns:
- **API/Control layer** (FastAPI) — trigger runs, expose health/status.
- **Orchestration layer** — sequences pipeline stages, manages concurrency/rate limits per run.
- **Scraping pipeline** — Fetcher → Parser → Extractor → Cleaner → Structurer, each single-responsibility and swappable.
- **Storage layer** — repository pattern; isolates persistence from business logic.
- **Cross-cutting layer** — config, structured logging, error handling; used by all layers, owned by none.
- Inter-layer data is always typed/validated (Pydantic) — no implicit dict-passing.

## 7. Data Flow
**Fetch → Parse → Extract → Clean → Structure → Store**
- **Fetch** — raw HTML, respecting robots.txt + rate limits.
- **Parse** — raw HTML → navigable DOM.
- **Extract** — DOM → raw (untyped) field dict.
- **Clean** — normalize text/formats, strip artifacts.
- **Structure** — validate/coerce into the final schema.
- **Store** — persist via repository, deduplicating against existing records.

## 8. Main Components and Responsibilities
- **Config Manager** — loads/validates env-based settings.
- **Fetcher** — HTTP client: retries, rate limiting, User-Agent, robots.txt checks.
- **Parser** — HTML → DOM navigation.
- **Extractor** — DOM → raw fields, per record type.
- **Cleaner/Normalizer** — text/format normalization.
- **Structurer/Validator** — raw dict → validated record.
- **Repository** — all DB I/O, dedupe, transactions.
- **Job Orchestrator** — sequences a full run, manages concurrency, emits run status.
- **Logger** — structured, correlated logging.
- **API Layer** — thin FastAPI routers for trigger/status/health.

## 9. Recommended Folder Structure
```
scraper-service/
├── app/
│   ├── main.py
│   ├── core/          # config, logging, exceptions
│   ├── api/            # thin routers: health, scrape, status
│   ├── services/        # orchestration logic
│   ├── scraping/        # fetcher, parser, extractor, cleaner
│   ├── schemas/         # Pydantic models
│   ├── storage/         # repository, ORM models, migrations
│   └── jobs/            # background task definitions
├── docker/
├── .env.example
└── requirements.txt
```

## 10. Technology Choices
- **httpx (async)** — non-blocking fetches, matches FastAPI's async model.
- **BeautifulSoup + lxml** — fast, forgiving parsing for a well-formed target site.
- **FastAPI** — thin control-plane API; async-ready.
- **Pydantic** — enforces the structuring/validation boundary.
- **PostgreSQL** — production store; JSONB for flexible fields, strong indexing/transactions.
- **SQLite** — local/dev-only mirror of the same schema.
- **Redis** — rate-limit counters, dedupe cache, background job broker.
- **RQ/Celery (Redis-backed)** — background execution, keeps API responsive.
- **Docker** — consistent runtime across environments.

## 11. Database/Data Storage Strategy
- Primary table: normalized records — id, source_url (unique), extracted fields, content_hash, scraped_at, updated_at, status.
- Optional raw-capture store: original HTML/text keyed by source_url, for reprocessing without re-fetching.
- Dedupe via unique constraint on source_url + content_hash (detects unchanged vs. changed re-crawls).
- Indexes: source_url, content_hash, category/type, scraped_at.
- JSONB column for attributes that don't fit the fixed schema, to avoid frequent migrations.
- Schema designed for clean future chunking/embedding (stable IDs, clean text fields).

## 12. Error Handling Strategy
- **Transient** (timeouts, 5xx, connection errors) — bounded retry, exponential backoff + jitter.
- **Permanent** (4xx, robots.txt disallow) — logged and skipped, never retried.
- **Parsing/extraction failures** — isolated per record, captured to a failed-items log; run continues.
- **Validation failures** — record rejected before storage, reason logged.
- **Source-level protection** — circuit-breaker style pause if a source's error rate spikes.

## 13. Logging Strategy
- Structured JSON logs; one correlation/run ID per crawl execution.
- Levels: DEBUG (raw payloads, dev-only), INFO (milestones/counts), WARNING (retries/skips), ERROR (failures needing attention).
- No full response bodies logged above DEBUG.
- Output to stdout — container-friendly, ready for log aggregation later without code changes.

## 14. Responsible Crawling Strategy
- **robots.txt** — fetched/parsed once per domain per run; disallowed paths never fetched; crawl-delay honored.
- **User-Agent** — descriptive, identifiable, env-configurable; never a spoofed browser UA.
- **Rate Limiting** — minimum delay between requests to the same domain (env-configurable), domain-level concurrency cap, token-bucket limiter backed by Redis so limits hold across workers.
- **Retry Policy** — bounded retries, exponential backoff + jitter, transient errors only; `Retry-After` honored; 4xx never retried (429 backs off longer).

## 15. Scalability Considerations
- Stateless workers — all state in DB/Redis, any worker can pick up any job.
- Horizontal scaling via additional workers on a shared Redis-backed queue.
- Work partitioned by source/category to avoid duplicate crawling.
- Idempotent writes (URL + content-hash dedupe) make re-runs/overlapping workers safe.
- Scale target: the serving side (API/DB/cache, for many RAG consumers) and breadth (more sources/workers) — never crawl rate against one target, which stays capped regardless of available capacity.

## 16. Implementation Roadmap
1. Fetcher + Parser proof of concept (no persistence).
2. Extractor + Cleaner + Pydantic schema; full in-memory pipeline.
3. Storage layer: schema, repository, dedupe logic.
4. Responsible crawling controls: robots.txt, rate limiting, retries, structured logging.
5. FastAPI control layer (trigger/status/health) + background job execution.
6. Hardening: multi-worker support, Dockerization, monitoring hooks — handoff point for RAG ingestion next.
