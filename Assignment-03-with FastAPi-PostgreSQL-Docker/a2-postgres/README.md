# Assignment 3 — FastAPI + PostgreSQL + Docker

## Project Overview

A task management REST API built with FastAPI, backed by PostgreSQL for persistent storage, and fully containerized with Docker Compose. The application implements a clean layered architecture where the storage engine can be swapped via a single environment variable without changing any business logic or route handlers.

## Architecture

```
Client -> Router -> Service Layer -> Repository Interface -> [Memory | Postgres] Repository
```

| Layer | Responsibility |
|---|---|
| Router (`app/routers/`) | HTTP handling, status codes, request/response models |
| Service (`app/services/`) | Business logic, delegates to repository |
| Repository (`app/repositories/`) | Data access, implements abstract interface |
| Interface (`app/repositories/interface.py`) | ABC contract all repositories must satisfy |

Which repository backs the app is decided in exactly one place — `app/dependencies.py` — controlled by the `REPOSITORY_TYPE` env var (`memory` or `postgres`).

## Installation

### Prerequisites

- Docker and Docker Compose
- Git

### Clone

```bash
git clone <repository-url>
cd Assignment-03-with\ FastAPi-PostgreSQL-Docker/a2-postgres
```

### Setup Environment

```bash
cp .env.example .env
```

Edit `.env` with your desired values (defaults work out of the box for local development).

## Docker

The project uses two containers orchestrated with Docker Compose:

| Container | Image | Purpose |
|---|---|---|
| `app` | Built from `./Dockerfile` | FastAPI application on port 8000 |
| `db` | `postgres:16` | PostgreSQL database on port 5432 |

**Dockerfile** uses `python:3.11-slim`, installs dependencies from `requirements.txt`, and runs the app with Uvicorn.

**docker-compose.yml** wires both services together:
- App waits for DB to be healthy before starting (`depends_on` with healthcheck)
- DB schema and seed data are auto-applied on first boot via `/docker-entrypoint-initdb.d/`
- A named volume (`db_data`) ensures data persists across container restarts

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `POSTGRES_USER` | PostgreSQL username | `postgres` |
| `POSTGRES_PASSWORD` | PostgreSQL password | `postgres` |
| `POSTGRES_DB` | Database name | `tasks_db` |
| `REPOSITORY_TYPE` | Storage backend (`postgres` or `memory`) | `postgres` |
| `DATABASE_URL` | Connection string (auto-constructed in docker-compose) | — |

## API Endpoints

Base URL: `http://localhost:8000`

| Method | Endpoint | Request Body | Success | Error |
|---|---|---|---|---|
| `POST` | `/tasks` | `{"title": "string"}` | `201` + Task | `400` if title missing/empty |
| `GET` | `/tasks` | — | `200` + Task[] | — |
| `GET` | `/tasks/{id}` | — | `200` + Task | `404` if not found |
| `PUT` | `/tasks/{id}` | `{"title": "string", "done": bool}` | `200` + Task | `404` / `400` |
| `DELETE` | `/tasks/{id}` | — | `204` No Content | `404` if not found |

### Response Shape

```json
{
  "id": 1,
  "title": "Learn FastAPI",
  "done": false,
  "created_at": "2026-01-01T00:00:00+00:00"
}
```

Interactive docs: `http://localhost:8000/docs`

## Database

**Engine:** PostgreSQL 16

**Table:** `tasks`

| Column | Type | Constraints |
|---|---|---|
| `id` | `SERIAL` | `PRIMARY KEY` |
| `title` | `TEXT` | `NOT NULL` |
| `done` | `BOOLEAN` | `NOT NULL DEFAULT FALSE` |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()` |

**Initialization:** Schema is created automatically on first container boot (`sql/schema.sql`). Three seed tasks are inserted when the table is empty (both via `sql/seed.sql` and app-level code in `db.py`).

**Persistence:** Data survives `docker compose down` because it lives in the named volume `db_data`. Use `docker compose down -v` to delete the volume and reset.

## Run Commands

```bash
# Start the full stack (build + run)
docker compose up --build

# Start in detached mode
docker compose up --build -d

# Stop containers (data persists)
docker compose down

# Stop and delete all data
docker compose down -v

# View logs
docker compose logs -f app

# Access the database shell
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB
```

### Verify it works

```bash
# Create a task
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "My first task"}'

# List all tasks
curl http://localhost:8000/tasks

# Get a single task
curl http://localhost:8000/tasks/1

# Update a task
curl -X PUT http://localhost:8000/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"title": "Updated task", "done": true}'

# Delete a task
curl -X DELETE http://localhost:8000/tasks/1
```

## File Map

| File | Purpose |
|---|---|
| `app/main.py` | FastAPI app setup, lifespan, exception handler |
| `app/models.py` | Pydantic request/response schemas |
| `app/dependencies.py` | DI wiring — switches repository based on env var |
| `app/routers/items.py` | Route handlers for `/tasks` |
| `app/services/item_service.py` | Business logic layer |
| `app/repositories/interface.py` | Abstract base class for repositories |
| `app/repositories/postgres_repository.py` | PostgreSQL implementation |
| `app/repositories/memory_repository.py` | In-memory implementation (for comparison) |
| `app/db.py` | Connection pool management, schema + seed on startup |
| `sql/schema.sql` | Table definition (run by Postgres on first boot) |
| `sql/seed.sql` | Seed data (run by Postgres on first boot) |
| `sql/index_demo.sql` | Index performance demo queries |
| `Dockerfile` | App container image |
| `docker-compose.yml` | Multi-container orchestration |
| `.env.example` | Template for required environment variables |
