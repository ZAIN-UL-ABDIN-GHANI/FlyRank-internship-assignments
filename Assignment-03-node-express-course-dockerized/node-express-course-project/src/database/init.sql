-- =============================================================================
-- Database schema for the Node.js + Express Course API.
--
-- This file is mounted into the official postgres:16 image's
-- /docker-entrypoint-initdb.d/ directory, which runs it automatically the
-- FIRST time the container starts with an empty data volume. It is safe to
-- re-run manually thanks to IF NOT EXISTS everywhere.
--
-- Column names are snake_case (Postgres convention); the application's
-- PostgresRepository layer converts to/from the camelCase shape the rest of
-- the app already expects (e.g. category_id <-> categoryId), so nothing
-- above the repository layer needs to know about this naming difference.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- users
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id            UUID PRIMARY KEY,
    name          TEXT NOT NULL,
    email         TEXT NOT NULL,
    password      TEXT NOT NULL,
    role          TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ
);

CREATE UNIQUE INDEX IF NOT EXISTS users_email_unique_idx ON users (LOWER(email));

-- ---------------------------------------------------------------------------
-- categories
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS categories (
    id            UUID PRIMARY KEY,
    name          TEXT NOT NULL,
    description   TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ
);

CREATE UNIQUE INDEX IF NOT EXISTS categories_name_unique_idx ON categories (LOWER(name));

-- ---------------------------------------------------------------------------
-- products
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS products (
    id            UUID PRIMARY KEY,
    name          TEXT NOT NULL,
    description   TEXT,
    price         NUMERIC(10, 2) NOT NULL CHECK (price > 0),
    stock         INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    category_id   UUID NOT NULL REFERENCES categories (id),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS products_category_id_idx ON products (category_id);
CREATE INDEX IF NOT EXISTS products_name_idx ON products (LOWER(name));

-- ---------------------------------------------------------------------------
-- orders
-- items is stored as JSONB: [{ productId, quantity, unitPrice }, ...]
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS orders (
    id            UUID PRIMARY KEY,
    user_id       UUID NOT NULL REFERENCES users (id),
    items         JSONB NOT NULL,
    total_amount  NUMERIC(10, 2) NOT NULL CHECK (total_amount >= 0),
    status        TEXT NOT NULL DEFAULT 'pending'
                  CHECK (status IN ('pending', 'paid', 'shipped', 'cancelled')),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS orders_user_id_idx ON orders (user_id);

-- ---------------------------------------------------------------------------
-- reviews
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reviews (
    id            UUID PRIMARY KEY,
    product_id    UUID NOT NULL REFERENCES products (id),
    user_id       UUID NOT NULL REFERENCES users (id),
    rating        INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment       TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS reviews_product_id_idx ON reviews (product_id);
CREATE INDEX IF NOT EXISTS reviews_user_id_idx ON reviews (user_id);
