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

## Architecture

```
Client
  │
  ▼
Express App (app.js)
  │  helmet, cors, rate limiter, compression, body/cookie parsers, morgan, request timer
  ▼
Routes  (src/routes/*)          — URL + HTTP verb + validation + auth wiring
  │
  ▼
Controllers (src/controllers/*) — parse request, call a service, shape the response
  │
  ▼
Services (src/services/*)       — business logic, orchestration, rules
  │
  ▼
Repositories (src/repositories/*) — the ONLY layer that touches storage
  │
  ▼
In-Memory Store (src/database/inMemoryStore.js)
```

**Why this matters:** the service layer never imports the database directly — it only calls repository methods (`findAll`, `findById`, `create`, `update`, `remove`). That means swapping the in-memory store for PostgreSQL later is just a new repository implementation with the same method names; controllers and services don't change at all.

```js
// e.g. tomorrow's postgres.product.repository.js just needs to expose the same interface:
class PostgresProductRepository {
  async findAll(filter) { /* SELECT ... */ }
  async findById(id)   { /* SELECT ... WHERE id = $1 */ }
  async create(data)   { /* INSERT ... RETURNING * */ }
  async update(id, data) { /* UPDATE ... RETURNING * */ }
  async remove(id)      { /* DELETE ... */ }
}
```

## Folder Structure

```
node-express-course-project/
├── src/
│   ├── config/           # env.js (dotenv config), swagger.js (OpenAPI spec)
│   ├── constants/        # httpStatus.js, roles.js
│   ├── controllers/      # thin HTTP layer per resource + demo.controller.js
│   ├── database/         # in-memory "database" (Maps) + seed data
│   ├── middlewares/      # auth, role, validate, requestTimer, notFound, errorHandler
│   ├── models/           # schema documentation (JSDoc typedefs) + sanitizers
│   ├── repositories/     # base.repository.js + one repository per resource
│   ├── routes/           # one router file per resource, mounted in routes/index.js
│   ├── services/         # business logic per resource
│   ├── utils/            # ApiResponse, ApiError, asyncHandler, logger
│   ├── validators/       # express-validator rule sets per resource
│   ├── app.js            # Express app assembly (no .listen())
│   └── server.js         # entry point: starts the HTTP server
├── public/
│   └── sample.txt        # used by the res.download()/res.sendFile() demo routes
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

## Environment Variables

Defined in `.env.example` — copy it to `.env` and adjust as needed. Secrets are **never** hardcoded in source.

| Variable          | Description                                   | Default (dev)                |
|-------------------|------------------------------------------------|-------------------------------|
| `PORT`            | Port the server listens on                     | `3000`                        |
| `NODE_ENV`        | `development` or `production`                  | `development`                 |
| `DATABASE_URL`    | Placeholder for a future real DB connection    | `in-memory`                   |
| `JWT_SECRET`      | Secret used to sign JWTs                        | *(set your own)*              |
| `JWT_EXPIRES_IN`  | Token lifetime                                  | `1d`                           |
| `API_KEY`         | Placeholder for any external API key            | *(set your own)*              |

## How to Run

```bash
npm run dev     # nodemon, auto-restarts on file changes
npm start        # plain node, for production
```

The server prints its URL and the Swagger docs URL on startup. By default:

- API root: `http://localhost:3000/`
- Health check: `http://localhost:3000/health`
- Swagger UI: `http://localhost:3000/docs`

A seeded admin account is created automatically on boot:

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

This project intentionally starts with an **in-memory repository** (`src/database/inMemoryStore.js` + `src/repositories/*`) instead of a real database, so the course project runs with zero setup.

```
Controller → Service → Repository Interface → Memory Repository
```

To swap in **PostgreSQL** later:

1. Add `pg` (or an ORM like Prisma/Sequelize) and a real connection in `src/config/`.
2. Write a new repository class per resource (e.g. `postgres.product.repository.js`) implementing the same methods as `base.repository.js`: `findAll`, `findById`, `findOne`, `create`, `update`, `remove`.
3. Swap the `require(...)` in each service to point at the new repository.

Nothing in `controllers/` or `services/` needs to change — that's the whole point of the pattern.

## API Documentation (Swagger)

Full interactive API docs, generated from JSDoc `@openapi` comments in every route file, are served at:

```
GET /docs
```

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

- Swap the in-memory repositories for a real PostgreSQL (or MongoDB) implementation
- Add automated tests (Jest + Supertest) for every route
- Add refresh tokens and token revocation
- Add pagination and sorting to list endpoints
- Add file upload support (e.g. product images) with multer
- Containerize with Docker + docker-compose (API + Postgres)


