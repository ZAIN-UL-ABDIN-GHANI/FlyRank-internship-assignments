# Node.js + Express Course API

A production-style REST API built with **Node.js**, **Express.js**, and plain **JavaScript** (CommonJS). It was built to demonstrate — end to end, in real working code — every core Node.js/Express backend concept: the event loop and async programming, routing, middleware, request/response handling, validation, JWT authentication, the repository pattern, centralized error handling, and Swagger API documentation.

It's structured the way a real internship/junior-engineer assessment repo should be: modular, layered, documented, and runnable in under a minute.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Architecture](#architecture)
- [Folder Structure](#folder-structure)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [How to Run](#how-to-run)
- [API Endpoints](#api-endpoints)
- [Example Requests & Responses](#example-requests--responses)
- [Routing](#routing)
- [Middleware](#middleware)
- [Request & Response Handling](#request--response-handling)
- [Validation](#validation)
- [Authentication](#authentication)
- [Error Handling](#error-handling)
- [Database Layer (Repository Pattern)](#database-layer-repository-pattern)
- [API Documentation (Swagger)](#api-documentation-swagger)
- [Persistence Verification](#persistence-verification)
- [Testing](#testing)
- [Developer Experience](#developer-experience)
- [Security](#security)
- [JavaScript on the Server](#javascript-on-the-server)
- [Future Improvements](#future-improvements)
- [License](#license)

---

## Project Overview

The API models a small e-commerce backend with five resources — **Users**, **Categories**, **Products**, **Orders**, and **Reviews** — plus a JWT-based **Auth** flow (register/login/profile) and a small **Demo** router that isolates individual `req`/`res` features for teaching purposes.

Every response, success or failure, follows one consistent JSON envelope so API consumers never have to guess the shape of a response.

**Storage backend:** the project now runs on **PostgreSQL 16** (via Docker Compose) instead of the original in-memory store. This was a deliberate architecture exercise: **only the repository layer was replaced. Services, controllers, and routes remained unchanged.** The original in-memory implementation (`src/database/inMemoryStore.js`, `src/repositories/base.repository.js`) is still in the codebase, untouched and simply no longer wired up — proof that the architecture supports swapping storage implementations without touching business logic.

## Architecture

```
Client
  │
  ▼
Express App (app.js)
  │  helmet, cors, rate limiter, compression, body/cookie parsers, morgan, request timer
  ▼
Routes  (src/routes/*)          — URL + HTTP verb + validation + auth wiring   [UNCHANGED]
  │
  ▼
Controllers (src/controllers/*) — parse request, call a service, shape response [UNCHANGED]
  │
  ▼
Services (src/services/*)       — business logic, orchestration, rules         [UNCHANGED]
  │
  ▼
Repositories (src/repositories/*) — the ONLY layer that touches storage
  │
  ▼
PostgreSQL 16 (Docker)  ◄── swapped in, replacing the in-memory Map store
```

**Why this matters (dependency inversion in practice):** services never import `pg` or the database directly — they only call repository methods (`findAll`, `findById`, `create`, `update`, `remove`) defined by an interface. Concretely, each resource repository (`src/repositories/user.repository.js`, `product.repository.js`, etc.) is a one-line change:

```diff
- const BaseRepository = require('./base.repository');       // in-memory Map
+ const PostgresRepository = require('./postgres.repository'); // real PostgreSQL

- class UserRepository extends BaseRepository {
+ class UserRepository extends PostgresRepository {
```

That's the entire "dependency injection" swap point in this project (there's no separate DI container — the `require()` graph *is* the composition root). Everything above the repository layer — services, controllers, routes, validators, middleware — is byte-for-byte identical to before the migration. This is the Dependency Inversion Principle: high-level modules (services) depend on an abstraction (the repository's method signatures), not on a concrete storage technology, so the concrete implementation can be swapped freely.

## Folder Structure

```
node-express-course-project/
├── src/
│   ├── config/           # env.js (dotenv config), swagger.js (OpenAPI spec)
│   ├── constants/        # httpStatus.js, roles.js
│   ├── controllers/      # thin HTTP layer per resource + demo.controller.js
│   ├── database/
│   │   ├── db.js             # pg Pool, built from DATABASE_URL
│   │   ├── init.sql          # schema (CREATE TABLE IF NOT EXISTS, FKs, indexes)
│   │   ├── seed.js           # idempotent demo admin/catalog seed
│   │   └── inMemoryStore.js  # ORIGINAL in-memory store — kept, no longer used
│   ├── middlewares/      # auth, role, validate, requestTimer, notFound, errorHandler
│   ├── models/           # schema documentation (JSDoc typedefs) + sanitizers
│   ├── repositories/
│   │   ├── postgres.repository.js  # active — PostgreSQL-backed repository interface
│   │   ├── base.repository.js      # ORIGINAL in-memory repository — kept, no longer used
│   │   └── {user,product,category,order,review}.repository.js  # extend PostgresRepository
│   ├── routes/           # one router file per resource, mounted in routes/index.js
│   ├── services/         # business logic per resource
│   ├── utils/            # ApiResponse, ApiError, asyncHandler, logger
│   ├── validators/       # express-validator rule sets per resource
│   ├── app.js            # Express app assembly (no .listen())
│   └── server.js         # entry point: connects to Postgres, seeds, starts the HTTP server
├── public/
│   └── sample.txt        # used by the res.download()/res.sendFile() demo routes
├── docker-compose.yml    # postgres-db + app services, named volume for persistence
├── Dockerfile            # Node LTS image for the app service
├── .env.example
├── .eslintrc.json
├── .prettierrc
├── package.json
├── postman_collection.json
├── thunder-collection_node-express-course-project.json
└── README.md
```

## Installation

```bash
npm install
cp .env.example .env
```

(Skip `npm install` entirely if you're only running via `docker compose up --build` — the Dockerfile installs dependencies inside the image.)

## Environment Variables

Defined in `.env.example` — copy it to `.env` and adjust as needed. Secrets are **never** hardcoded in source.

| Variable              | Description                                              | Default (dev)                                       |
|------------------------|-------------------------------------------------------------|--------------------------------------------------------|
| `PORT`                 | Port the server listens on                                   | `3000`                                                  |
| `NODE_ENV`             | `development` or `production`                                | `development`                                           |
| `POSTGRES_DB`          | Database name (used by both `docker-compose.yml` and the app) | `appdb`                                                 |
| `POSTGRES_USER`        | Database user                                                 | `postgres`                                              |
| `POSTGRES_PASSWORD`    | Database password                                             | `postgres`                                              |
| `DATABASE_URL`         | Full Postgres connection string the app connects with          | `postgres://postgres:postgres@localhost:5432/appdb`     |
| `JWT_SECRET`           | Secret used to sign JWTs                                       | *(set your own)*                                        |
| `JWT_EXPIRES_IN`       | Token lifetime                                                  | `1d`                                                     |
| `API_KEY`              | Placeholder for any external API key                            | *(set your own)*                                        |

`.env` is git-ignored; `.env.example` is committed with placeholder values.

> **Note on `DATABASE_URL` host:** when the app runs *inside* Docker Compose, the host must be the service name `postgres-db` (Compose gives each service DNS resolution on its internal network) — `docker-compose.yml` sets this automatically. If you run the Node app directly on your machine against just the `postgres-db` container, use `localhost` instead, as shown in `.env.example`.

## How to Run

### Option A — Docker Compose (recommended, runs the full stack)

```bash
cp .env.example .env      # adjust POSTGRES_PASSWORD / JWT_SECRET as you like
docker compose up --build
```

This starts both containers: `postgres-db` (Postgres 16, with `src/database/init.sql` executed automatically on first boot) and the `app` service (waits for Postgres to be healthy before starting, via `depends_on: condition: service_healthy`).

```bash
docker compose down          # stop the stack (keeps the volume/data)
docker compose logs -f app   # tail the app's logs
docker compose logs -f postgres-db
```

### Option B — Run the app locally against a Dockerized Postgres

```bash
cp .env.example .env
docker compose up postgres-db -d
npm install
npm run dev     # nodemon, auto-restarts on file changes
```

The server prints its URL and the Swagger docs URL on startup. By default:

- API root: `http://localhost:3000/`
- Health check: `http://localhost:3000/health`
- Swagger UI: `http://localhost:3000/docs`

On first boot (empty database), a seeded admin account and sample catalog are created automatically (see [Database Layer](#database-layer-repository-pattern)):

```
email:    admin@example.com
password: Admin123!
```

## API Endpoints

All endpoints below are prefixed with `/api`.

| Resource   | Method | Path                     | Auth        | Description                         |
|------------|--------|--------------------------|-------------|--------------------------------------|
| Auth       | POST   | `/auth/register`         | Public      | Register a new user                  |
| Auth       | POST   | `/auth/login`             | Public      | Log in, receive a JWT                 |
| Auth       | GET    | `/auth/me`                 | Bearer      | Get your own profile                  |
| Users      | GET    | `/users`                   | Admin       | List all users                        |
| Users      | GET    | `/users/:id`               | Bearer      | Get a user by id                      |
| Users      | PUT    | `/users/:id`               | Bearer      | Update your profile (name/email)      |
| Users      | DELETE | `/users/:id`               | Admin       | Delete a user                         |
| Categories | GET    | `/categories`               | Public      | List categories                       |
| Categories | GET    | `/categories/:id`           | Public      | Get a category                        |
| Categories | POST   | `/categories`               | Admin       | Create a category                     |
| Categories | PUT    | `/categories/:id`           | Admin       | Update a category                     |
| Categories | DELETE | `/categories/:id`           | Admin       | Delete a category                     |
| Products   | GET    | `/products`                 | Public      | List products (filter via query)      |
| Products   | GET    | `/products/:id`             | Public      | Get a product                         |
| Products   | POST   | `/products`                 | Admin       | Create a product                      |
| Products   | PUT    | `/products/:id`             | Admin       | Fully update a product                |
| Products   | PATCH  | `/products/:id`             | Admin       | Partially update a product            |
| Products   | DELETE | `/products/:id`             | Admin       | Delete a product                      |
| Orders     | GET    | `/orders`                    | Bearer      | List your orders (all, if admin)      |
| Orders     | GET    | `/orders/:id`                 | Bearer      | Get an order                          |
| Orders     | POST   | `/orders`                     | Bearer      | Place an order                        |
| Orders     | PATCH  | `/orders/:id/status`          | Bearer      | Update order status                   |
| Orders     | DELETE | `/orders/:id`                 | Bearer      | Delete/cancel an order                |
| Reviews    | GET    | `/reviews`                     | Public      | List reviews (filter by productId)    |
| Reviews    | GET    | `/reviews/:id`                 | Public      | Get a review                          |
| Reviews    | POST   | `/reviews`                     | Bearer      | Create a review                       |
| Reviews    | PUT    | `/reviews/:id`                 | Bearer      | Update your own review                |
| Reviews    | DELETE | `/reviews/:id`                 | Bearer      | Delete your own review (or any, admin)|
| Demo       | *      | `/demo/*`                       | mixed       | Isolated req/res feature showcase     |

Full details (request/response schemas) are in Swagger at `/docs`.

## Example Requests & Responses

### Register

```bash
curl -X POST http://localhost:3000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Jane Doe","email":"jane@example.com","password":"SecurePass1"}'
```

```json
{
  "success": true,
  "message": "User registered successfully",
  "data": {
    "user": { "id": "…", "name": "Jane Doe", "email": "jane@example.com", "role": "user" },
    "token": "eyJhbGciOi..."
  }
}
```

### Login

```bash
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"Admin123!"}'
```

### Create a product (admin)

```bash
curl -X POST http://localhost:3000/api/products \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Keyboard","price":89.99,"stock":20,"categoryId":"<CATEGORY_ID>"}'
```

### List products with filters

```bash
curl "http://localhost:3000/api/products?search=key&minPrice=10&maxPrice=200"
```

### Validation error shape (422)

```json
{
  "success": false,
  "message": "Validation failed",
  "error": {
    "statusCode": 422,
    "details": [
      { "field": "password", "message": "Password must be at least 8 characters long", "value": "123" }
    ]
  }
}
```

### Not found (404)

```json
{
  "success": false,
  "message": "Product not found",
  "error": { "statusCode": 404 }
}
```

## Routing

Every resource has its own router file under `src/routes/`, mounted in `src/routes/index.js` under `/api`:

```js
router.use('/auth', require('./auth.routes'));
router.use('/users', require('./user.routes'));
router.use('/categories', require('./category.routes'));
router.use('/products', require('./product.routes'));
router.use('/orders', require('./order.routes'));
router.use('/reviews', require('./review.routes'));
router.use('/demo', require('./demo.routes'));
```

Each router wires together validation middleware, auth/role middleware, and its controller for every HTTP verb it supports (GET, POST, PUT, PATCH, DELETE).

## Middleware

| Type                  | File                                          | Purpose                                                        |
|------------------------|------------------------------------------------|------------------------------------------------------------------|
| Application middleware | `app.js` (`helmet`, `cors`, `compression`, `express.json`) | Runs on every request                                    |
| Router middleware      | each `routes/*.js`                              | Per-route validation/auth chains                                 |
| Custom middleware      | `requestTimer.middleware.js`                    | Times and logs every request                                     |
| Authentication         | `auth.middleware.js`                            | Verifies the JWT, attaches `req.user`                             |
| Authorization (roles)  | `role.middleware.js`                            | Restricts routes to specific roles (e.g. admin)                   |
| Validation              | `validate.middleware.js`                        | Turns express-validator errors into a 422 `ApiError`               |
| Logging                 | `morgan` (in `app.js`) + custom `logger.js`     | HTTP access logs + application event logs                          |
| 404 handler              | `notFound.middleware.js`                       | Catches unmatched routes                                            |
| Global error handler     | `errorHandler.middleware.js`                   | Normalizes every error into the standard error envelope (must be last) |

## Request & Response Handling

The `src/controllers/demo.controller.js` + `src/routes/demo.routes.js` files exist specifically to demonstrate, in isolation:

- `req.params`, `req.query`, `req.body`, `req.headers`, `req.cookies`, `req.ip`, `req.method`, `req.originalUrl`
- `res.json()`, `res.status()`, `res.send()`, `res.redirect()`, `res.download()`, `res.sendFile()`, custom response headers via `res.setHeader()`, and `res.cookie()`

Try them at `/api/demo/*` (see the Postman/Thunder collections or Swagger UI).

## Validation

Built with **express-validator**. Rule sets live in `src/validators/*` and are composed into route chains, then enforced by `validate.middleware.js`. Covers required fields, email format, password strength, numeric ranges (price, stock, rating), and UUID format for ids/foreign keys.

## Authentication

Simple JWT auth (`jsonwebtoken` + `bcryptjs`):

- `POST /api/auth/register` — hashes the password, creates a `user`-role account, returns a token
- `POST /api/auth/login` — verifies credentials, returns a token
- `GET /api/auth/me` — protected route, requires `Authorization: Bearer <token>`
- **Role middleware** (`authorize('admin')`) protects admin-only routes like creating/deleting products and categories

## Error Handling

- Every async controller is wrapped in `asyncHandler` (the "async error wrapper"), so a rejected promise is automatically forwarded to `next()` — no repeated try/catch blocks.
- All expected errors are thrown as `ApiError` (400/401/403/404/409/422) from services or middleware.
- The **global error handler** (`errorHandler.middleware.js`) is the single place that turns any error — operational or an unexpected bug — into the standard error envelope, and logs 5xx-level errors.
- The **404 middleware** runs after all routes and converts unmatched routes into a proper `ApiError`.

## Database Layer (Repository Pattern)

The project now runs on **PostgreSQL 16** in Docker. The repository pattern is what made that swap possible without touching anything above it:

```
Controller → Service → Repository Interface → PostgresRepository → PostgreSQL
                                             ↳ (BaseRepository / in-memory Map — kept in the repo, unused)
```

**What actually changed, file by file:**

| File                                         | Status                                                              |
|------------------------------------------------|------------------------------------------------------------------------|
| `src/database/db.js`                            | **New.** Exports a shared `pg` connection `Pool`, built from `DATABASE_URL`. |
| `src/database/init.sql`                         | **New.** `CREATE TABLE IF NOT EXISTS` for all 5 tables, FKs, indexes. Auto-run by the official `postgres:16` image on first container boot. |
| `src/database/seed.js`                          | **New.** Idempotent: checks `SELECT COUNT(*) FROM users` and only inserts the demo admin + sample catalog if the database is empty. Needed because a bcrypt password hash can't be generated in plain SQL. |
| `src/repositories/postgres.repository.js`       | **New.** `PostgresRepository` — implements the exact same public methods as `BaseRepository` (`findAll`, `findById`, `findOne`, `create`, `update`, `remove`), backed by parameterized SQL instead of a `Map`. |
| `src/repositories/{user,product,category,order,review}.repository.js` | **Modified — one line each.** `extends BaseRepository` → `extends PostgresRepository`. Nothing else in these files changed. |
| `src/server.js`                                 | **Modified.** Verifies the DB connection and runs the seed step before calling `app.listen()`; closes the pool on shutdown. |
| `src/database/inMemoryStore.js`, `src/repositories/base.repository.js` | **Unchanged, kept in the project on purpose** — the original in-memory implementation, no longer referenced by anything, left in place as proof the architecture supports swapping storage without deleting the old implementation. |
| `src/controllers/*`, `src/services/*`, `src/routes/*`, `src/middlewares/*`, `src/validators/*` | **Untouched.** Zero changes. |

**A compatibility note worth calling out:** several services pass plain JavaScript predicate functions into `findAll`/`findOne` (e.g. `product.service.js` builds a dynamic filter combining `categoryId`/`minPrice`/`maxPrice`/`search`). Rewriting that as dynamic SQL would have meant touching the service layer, which was off-limits. Instead, `PostgresRepository.findAll(filterFn)` runs `SELECT * FROM <table>`, maps each row from Postgres' snake_case columns to the app's camelCase shape, and applies the existing JS predicate in memory — identical behavior to the old in-memory repository, with zero service-layer changes. This is a deliberate, documented tradeoff (fine at this project's scale; a larger system would push filtering into SQL and accept touching the service signatures).

## API Documentation (Swagger)

Full interactive API docs, generated from JSDoc `@openapi` comments in every route file, are served at:

```
GET /docs
```

## Persistence Verification

Persistence was verified against a live PostgreSQL 16 instance (schema created via `init.sql`, exactly as `docker-compose.yml`'s `postgres-db` service would run it) with the following steps:

1. **Created records** through the running API: registered users, created categories/products via the admin token, placed an order (exercising the `orders.items` JSONB column), and posted a review.
2. **Restarted the application process** (`kill` + relaunch `node src/server.js`) — on reconnect, the server logged `Database already contains data — skipping seed.` (the idempotency check in `seed.js` working correctly) and every previously-created record was still retrievable through the API (e.g. `GET /api/auth/me`, `GET /api/orders/:id`).
3. **Restarted the PostgreSQL server itself** (`service postgresql restart`, the equivalent of `docker compose restart postgres-db`) — row counts for `users` and `orders` were identical before and after (verified directly with `psql`), confirming the data directory was never wiped.
4. **Re-queried after both restarts** — `SELECT` on `users` returned all 3 accounts created during the test (the seeded admin + 2 registered users), and the `orders` row still contained its full JSONB `items` array and correct `total_amount`.

Data survives because PostgreSQL writes to `/var/lib/postgresql/data`, which `docker-compose.yml` mounts as the named volume `postgres_data`. As long as that volume isn't explicitly removed (`docker compose down -v` or `docker volume rm`), the data outlives container restarts, `docker compose down` / `docker compose up` cycles, and application restarts.

> Note: this sandbox environment doesn't have a Docker daemon available, so the verification above ran against a real, locally-installed PostgreSQL 16 (same version, same `init.sql`, same connection code) rather than through `docker compose up` itself. The `docker-compose.yml` and `Dockerfile` follow standard, well-established patterns for this exact setup — please run `docker compose up --build` on your machine to confirm the containerized flow end-to-end.

## Testing

Three ways to exercise the API:

1. **Postman** — import [`postman_collection.json`](./postman_collection.json). Run "Login (Admin)" / "Login (User)" first; tokens auto-populate as collection variables.
2. **Thunder Client** (VS Code) — import [`thunder-collection_node-express-course-project.json`](./thunder-collection_node-express-course-project.json).
3. **curl** — see the [Example Requests](#example-requests--responses) above, and `/docs` for every endpoint's schema.

## Developer Experience

```bash
npm run dev        # nodemon — auto-restart on save
npm run lint        # ESLint
npm run lint:fix     # ESLint --fix
npm run format        # Prettier --write
```

## Security

- **helmet** — sensible security headers
- **cors** — cross-origin requests
- **express-rate-limit** — 300 requests / 15 min per IP on `/api`
- **compression** — gzip response bodies
- Input validation & sanitization via **express-validator** (`.trim()`, `.normalizeEmail()`, type/format checks) on every mutating endpoint
- Passwords hashed with **bcryptjs**, never returned in any response (`toSafeUser` strips them)

## JavaScript on the Server

Node.js runs JavaScript outside the browser on Google's V8 engine, using an event-driven, non-blocking I/O model — a single thread handles many concurrent connections by delegating I/O (file, network, DB) to the event loop instead of blocking on it. This project embraces that model throughout:

- **async/await** everywhere (services, repositories, controllers) — no callback hell
- **Promises** under the hood of every repository/service method
- **CommonJS modules** (`require`/`module.exports`) per the `"type"` omitted in `package.json`
- **npm ecosystem** — the whole dependency tree (Express, JWT, bcrypt, Swagger, etc.) comes from npm, declared in `package.json`

## Future Improvements

- Push dynamic filtering (product search/price range) into SQL `WHERE` clauses instead of in-memory filtering, once/if the service layer's filter contract is revisited
- Add automated tests (Jest + Supertest) for every route
- Add refresh tokens and token revocation
- Add pagination and sorting to list endpoints
- Add file upload support (e.g. product images) with multer
- Add a migration tool (e.g. `node-pg-migrate`) instead of a single `init.sql` as the schema grows

## Screenshots

_Add screenshots of Swagger UI (`/docs`) and sample Postman runs here._

## License

MIT
