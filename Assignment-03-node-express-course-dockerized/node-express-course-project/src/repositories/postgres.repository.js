/**
 * PostgresRepository — drop-in replacement for BaseRepository.
 *
 * Exposes EXACTLY the same public methods as src/repositories/base.repository.js
 * (findAll, findById, findOne, create, update, remove), so every resource
 * repository can swap its parent class without services, controllers, or
 * routes ever knowing storage changed.
 *
 * Compatibility note: findAll(filterFn) and findOne(predicate) are called
 * throughout the app with plain JavaScript functions (e.g. product.service.js
 * builds a dynamic filter over categoryId/minPrice/maxPrice/search). Rather
 * than reimplementing that logic as dynamic SQL — which would require
 * touching services — this repository selects rows, converts them from
 * Postgres' snake_case columns to the app's camelCase shape, and applies the
 * existing JS predicate in memory. This keeps behavior byte-for-byte
 * compatible with the in-memory implementation.
 */
const pool = require('../database/db');
const { v4: uuid } = require('uuid');

// Whitelist of tables this repository is allowed to target. Table names
// can't be parameterized in SQL ($1 only works for values), so instead of
// string-concatenating arbitrary input we validate against this list.
const ALLOWED_TABLES = new Set(['users', 'categories', 'products', 'orders', 'reviews']);

// Columns whose Postgres NUMERIC type comes back as a string (to avoid
// floating-point precision loss) and needs to be coerced back to a JS number
// to match the shape the in-memory repository always returned.
const NUMERIC_COLUMNS = new Set(['price', 'totalAmount']);

function toSnakeCase(key) {
  return key.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`);
}

function toCamelCase(key) {
  return key.replace(/_([a-z0-9])/g, (_match, letter) => letter.toUpperCase());
}

// node-postgres does NOT automatically serialize JS arrays/objects for
// jsonb columns (e.g. orders.items) — it needs an actual JSON string.
// Everything else (strings, numbers, booleans, null, Date) is passed through
// untouched since `pg` already knows how to serialize those.
function serializeValue(value) {
  if (value !== null && typeof value === 'object' && !(value instanceof Date)) {
    return JSON.stringify(value);
  }
  return value;
}

function mapRowToCamelCase(row) {
  if (!row) return null;
  const mapped = {};
  for (const [key, value] of Object.entries(row)) {
    const camelKey = toCamelCase(key);
    if (value !== null && NUMERIC_COLUMNS.has(camelKey)) {
      mapped[camelKey] = parseFloat(value);
    } else if (value instanceof Date) {
      mapped[camelKey] = value.toISOString();
    } else {
      mapped[camelKey] = value;
    }
  }
  return mapped;
}

class PostgresRepository {
  /**
   * @param {string} table - must be one of ALLOWED_TABLES
   */
  constructor(table) {
    if (!ALLOWED_TABLES.has(table)) {
      throw new Error(`Unknown table: ${table}`);
    }
    this.table = table;
  }

  async findAll(filterFn) {
    const { rows } = await pool.query(`SELECT * FROM ${this.table}`);
    const mapped = rows.map(mapRowToCamelCase);
    return typeof filterFn === 'function' ? mapped.filter(filterFn) : mapped;
  }

  async findById(id) {
    const { rows } = await pool.query(`SELECT * FROM ${this.table} WHERE id = $1`, [id]);
    return mapRowToCamelCase(rows[0]) || null;
  }

  async findOne(predicate) {
    // No generic single-column shortcut exists here since `predicate` is an
    // arbitrary function (see compatibility note above), so this mirrors
    // findAll() and returns the first in-memory match.
    const all = await this.findAll();
    return all.find(predicate) || null;
  }

  async create(data) {
    const id = uuid();
    const payload = { id, ...data };

    const columns = Object.keys(payload);
    const values = Object.values(payload).map(serializeValue);
    const placeholders = columns.map((_, index) => `$${index + 1}`);
    const columnNames = columns.map(toSnakeCase);

    const { rows } = await pool.query(
      `INSERT INTO ${this.table} (${columnNames.join(', ')})
       VALUES (${placeholders.join(', ')})
       RETURNING *`,
      values
    );

    return mapRowToCamelCase(rows[0]);
  }

  async update(id, data) {
    const columns = Object.keys(data);
    if (columns.length === 0) {
      return this.findById(id);
    }

    const setClauses = columns.map((column, index) => `${toSnakeCase(column)} = $${index + 2}`);
    setClauses.push('updated_at = now()');
    const values = [id, ...columns.map((column) => serializeValue(data[column]))];

    const { rows } = await pool.query(
      `UPDATE ${this.table}
       SET ${setClauses.join(', ')}
       WHERE id = $1
       RETURNING *`,
      values
    );

    return mapRowToCamelCase(rows[0]) || null;
  }

  async remove(id) {
    const { rows } = await pool.query(`DELETE FROM ${this.table} WHERE id = $1 RETURNING *`, [id]);
    return mapRowToCamelCase(rows[0]) || null;
  }
}

module.exports = PostgresRepository;
