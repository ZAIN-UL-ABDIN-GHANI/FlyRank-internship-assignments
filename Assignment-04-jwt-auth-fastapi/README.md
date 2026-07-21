# JWT Auth API (FastAPI)

A minimal, production-style JWT authentication backend: register, login,
and a JWT-protected route. Built with FastAPI, SQLAlchemy (SQLite), bcrypt,
and PyJWT.

## Authentication Overview

- **Registration** (`POST /register`) creates a user. Passwords are hashed
  with **bcrypt** before being stored — the plain password is never persisted
  or logged, and hashes are never returned in API responses.
- **Login** (`POST /login`) verifies the password with `bcrypt.checkpw()`
  and, on success, issues a signed **JWT access token** (HS256).
- **Protected routes** (e.g. `GET /me`) require an `Authorization: Bearer <token>`
  header. A single reusable dependency, `get_current_user` (in
  `app/middleware/auth.py`), validates the header, verifies the token's
  signature and expiration, loads the user, and attaches it to the request.
  No route re-implements any part of this logic.
- All expected errors (validation, duplicate user, bad credentials,
  missing/invalid/expired token) are converted by a **centralized exception
  handler** into a consistent JSON shape:
  ```json
  { "success": false, "message": "Invalid email or password" }
  ```
  Unexpected errors are logged server-side and returned as a generic
  `500` — stack traces are never sent to the client.

## Project Structure

```
app/
├── main.py                 # App factory, router registration, exception handlers
├── core/
│   ├── config.py           # Settings loaded from environment variables
│   └── exceptions.py       # Custom exception classes (ValidationError, etc.)
├── database.py              # SQLAlchemy engine, session, Base, init_db()
├── models/
│   └── user.py              # User table definition
├── schemas/
│   ├── user.py               # UserCreate / UserResponse (Pydantic)
│   └── auth.py               # LoginRequest / TokenResponse (Pydantic)
├── utils/
│   └── security.py           # bcrypt hashing + JWT encode/decode (no business logic)
├── services/
│   └── auth_service.py       # register_user / authenticate_user (business logic)
├── middleware/
│   └── auth.py                # get_current_user — the reusable auth dependency
└── routes/
    ├── auth.py                 # POST /register, POST /login
    └── users.py                 # GET /me (protected)
tests/
└── test_auth.py                # Automated pytest suite (17 tests)
```

Business logic lives in `services/`, not in routes. Routes are thin —
they validate input via Pydantic, call a service, and return the result.

## Setup Instructions

```bash
# 1. Clone / enter the project
cd jwt-auth-fastapi

# 2. Create a virtual environment
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# then edit .env and set a real JWT_SECRET_KEY, e.g.:
python -c "import secrets; print(secrets.token_hex(32))"

# 5. Run the server
uvicorn app.main:app --reload
```

The API is now available at `http://127.0.0.1:8000`.
Interactive docs (Swagger UI): `http://127.0.0.1:8000/docs`.

## Environment Variables

| Variable            | Description                                   | Default                    |
|---------------------|------------------------------------------------|-----------------------------|
| `JWT_SECRET_KEY`    | Secret used to sign/verify JWTs                | `CHANGE_ME_IN_PRODUCTION`  |
| `JWT_ALGORITHM`      | JWT signing algorithm                          | `HS256`                     |
| `JWT_EXPIRE_MINUTES` | Access token lifetime, in minutes              | `60`                        |
| `DATABASE_URL`       | SQLAlchemy connection string                   | `sqlite:///./app.db`        |
| `BCRYPT_ROUNDS`      | bcrypt cost factor (salt rounds)               | `12`                         |

**Important:** always set a strong, random `JWT_SECRET_KEY` in production —
never use the default.

## API Endpoints

| Method | Path        | Auth required | Description                     |
|--------|-------------|:---:|----------------------------------|
| POST   | `/register` | No  | Create a new user account        |
| POST   | `/login`    | No  | Authenticate and receive a JWT   |
| GET    | `/me`       | Yes | Get the authenticated user's profile |
| GET    | `/health`   | No  | Health check                     |

---

### `POST /register`

Creates a new user. The password is validated for strength (min 8 chars,
at least one uppercase letter, one lowercase letter, one digit) and hashed
with bcrypt before storage.

**Request**
```json
{
  "full_name": "Ada Lovelace",
  "email": "ada@example.com",
  "password": "Sup3rSecret"
}
```

**Success — `201 Created`**
```json
{
  "id": "01e1ca7d-2407-4f65-8bd1-b05eb3fd719a",
  "full_name": "Ada Lovelace",
  "email": "ada@example.com",
  "created_at": "2026-07-15T12:48:56.500222"
}
```
Note: the response never includes the password or its hash.

**Duplicate email — `409 Conflict`**
```json
{ "success": false, "message": "A user with email 'ada@example.com' already exists" }
```

**Validation error — `400 Bad Request`**
```json
{ "success": false, "message": "password: Value error, password must contain at least one uppercase letter" }
```

---

### `POST /login`

**Request**
```json
{
  "email": "ada@example.com",
  "password": "Sup3rSecret"
}
```

**Success — `200 OK`**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in_minutes": 60
}
```

**Invalid credentials — `401 Unauthorized`**
```json
{ "success": false, "message": "Invalid email or password" }
```
(The same message is used whether the email doesn't exist or the password
is wrong, so the API never reveals which emails are registered.)

---

### `GET /me` (protected)

**Request**
```
GET /me
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Success — `200 OK`**
```json
{
  "id": "01e1ca7d-2407-4f65-8bd1-b05eb3fd719a",
  "full_name": "Ada Lovelace",
  "email": "ada@example.com",
  "created_at": "2026-07-15T12:48:56.500222"
}
```

**Missing token — `401 Unauthorized`**
```json
{ "success": false, "message": "Missing Authorization header" }
```

**Invalid token — `401 Unauthorized`**
```json
{ "success": false, "message": "Invalid token" }
```

**Expired token — `401 Unauthorized`**
```json
{ "success": false, "message": "Token has expired" }
```

## JWT Usage

1. Call `POST /login` to receive `access_token`.
2. Send it on every subsequent request to a protected route as:
   `Authorization: Bearer <access_token>`
3. Tokens expire after `JWT_EXPIRE_MINUTES` (default 60). After expiry,
   log in again to get a new token. (Refresh tokens are intentionally
   out of scope for this implementation.)

The token payload contains only `sub` (user id), `iat` (issued-at), and
`exp` (expiration) — no sensitive data is embedded in the JWT itself.

## Sample `curl` Requests

```bash
# Register
curl -X POST http://127.0.0.1:8000/register \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Ada Lovelace","email":"ada@example.com","password":"Sup3rSecret"}'

# Login
curl -X POST http://127.0.0.1:8000/login \
  -H "Content-Type: application/json" \
  -d '{"email":"ada@example.com","password":"Sup3rSecret"}'

# Access protected route
curl http://127.0.0.1:8000/me \
  -H "Authorization: Bearer <access_token>"

# Missing token
curl http://127.0.0.1:8000/me

# Invalid token
curl http://127.0.0.1:8000/me -H "Authorization: Bearer not.a.valid.jwt"
```

## Testing

An automated pytest suite covers every requirement (17 tests): successful
and failing registration/login, missing/invalid/expired/tampered tokens,
and the protected route.

```bash
pip install -r requirements-dev.txt
pytest -v
```

Tests run against an isolated in-memory SQLite database (via a FastAPI
dependency override), so they never touch your real `app.db`.

## Design Notes / Constraints Followed

- No OAuth, refresh tokens, email verification, social login, or RBAC —
  intentionally out of scope per the assignment.
- Only the libraries needed were added: `fastapi`, `uvicorn`, `sqlalchemy`,
  `bcrypt`, `PyJWT`, `pydantic-settings`, `email-validator` (+ `pytest`/`httpx`
  for testing only).
- Passwords are never logged, compared as plain strings, or returned in
  any response.
