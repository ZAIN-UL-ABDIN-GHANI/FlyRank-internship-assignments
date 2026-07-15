# Assignment 2 — PostgreSQL Edition

FastAPI app from Assignment 2, now backed by PostgreSQL in Docker instead
of an in-memory list. **Only the repository layer changed** —
`app/services/item_service.py` and `app/routers/items.py` are byte-for-byte
the same shape as the in-memory version.

## Architecture

```
Client -> Routes -> Service Layer -> Repository Interface -> [Memory | Postgres] Repository
```

Which repository backs the app is decided in exactly one place —
`app/dependencies.py` — controlled by the `REPOSITORY_TYPE` env var
(`memory` or `postgres`). Nothing else in the app knows or cares.

## Run it

```bash
cp .env.example .env      # then edit real values in .env
docker compose up --build
```

This starts three containers:
- `app` — FastAPI
- `db` — Postgres 16, data stored in the named volume `db_data`, schema
  auto-applied from `sql/schema.sql` on first boot
- `redis` — stretch goal

API: `http://localhost:8000` · Docs: `http://localhost:8000/docs`

## Proving persistence

```bash
# 1. Create a row
curl -X POST http://localhost:8000/items \
  -H "Content-Type: application/json" \
  -d '{"name": "keyboard", "description": "mechanical", "price": 89.99}'

# 2. Confirm it's there
curl http://localhost:8000/items

# 3. Restart the whole stack (containers, not just the app process)
docker compose down
docker compose up

# 4. Query again — the row is still there
curl http://localhost:8000/items
```

`docker compose down` removes the containers but **not** the named
volume `db_data`, which is why the data survives. (`docker compose down -v`
would delete the volume too — avoid that if you want to keep data.)

## Stretch: Redis

```bash
curl http://localhost:8000/health/redis
```

## Stretch: indexes + EXPLAIN ANALYZE

```bash
# seed 100k rows
docker compose exec -T db psql -U $POSTGRES_USER -d $POSTGRES_DB < sql/seed.sql

# open a psql shell and paste sql/index_demo.sql statement by statement
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB
```

Compare the `Seq Scan` (before the index) to the `Index Scan` (after)
and the drop in execution time in the `EXPLAIN ANALYZE` output.

## File map

| File | Purpose |
|---|---|
| `app/repositories/interface.py` | Abstraction the Service Layer depends on |
| `app/repositories/memory_repository.py` | Original A2 storage, kept for comparison |
| `app/repositories/postgres_repository.py` | New storage, same interface, uses `psycopg` |
| `app/dependencies.py` | The one switch point deciding which repository is wired in |
| `sql/schema.sql` | Table definition, auto-run by Postgres on first container start |
| `docker-compose.yml` | app + db + redis, one command to start all three |
| `.env.example` | Documents required env vars without leaking real credentials |
