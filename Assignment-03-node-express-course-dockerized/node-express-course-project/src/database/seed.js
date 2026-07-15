/**
 * Idempotent database seed.
 *
 * init.sql intentionally contains ONLY schema (no data), because SQL alone
 * can't reproduce the bcrypt password hash the app needs for the demo admin
 * account. This script runs once at server startup, checks whether data
 * already exists, and only inserts the demo admin/catalog rows if the
 * tables are empty — safe to run on every boot, including container
 * restarts against a volume that already has data.
 */
const bcrypt = require('bcryptjs');
const { v4: uuid } = require('uuid');
const pool = require('./db');
const logger = require('../utils/logger');

async function seedDatabase() {
  const { rows: userRows } = await pool.query('SELECT COUNT(*)::int AS count FROM users');
  if (userRows[0].count > 0) {
    logger.info('Database already contains data — skipping seed.');
    return;
  }

  logger.info('Seeding database with demo admin account and sample catalog...');

  const adminId = uuid();
  const hashedPassword = await bcrypt.hash('Admin123!', 10);
  await pool.query(
    `INSERT INTO users (id, name, email, password, role)
     VALUES ($1, $2, $3, $4, $5)`,
    [adminId, 'Admin User', 'admin@example.com', hashedPassword, 'admin']
  );

  const categoryElectronicsId = uuid();
  const categoryBooksId = uuid();
  await pool.query(
    `INSERT INTO categories (id, name, description) VALUES
       ($1, $2, $3),
       ($4, $5, $6)`,
    [
      categoryElectronicsId,
      'Electronics',
      'Gadgets, devices, and accessories',
      categoryBooksId,
      'Books',
      'Fiction and non-fiction books',
    ]
  );

  await pool.query(
    `INSERT INTO products (id, name, description, price, stock, category_id) VALUES
       ($1, $2, $3, $4, $5, $6),
       ($7, $8, $9, $10, $11, $12)`,
    [
      uuid(),
      'Wireless Headphones',
      'Noise-cancelling over-ear wireless headphones',
      129.99,
      42,
      categoryElectronicsId,
      uuid(),
      'The Pragmatic Programmer',
      'A classic book on software craftsmanship',
      34.5,
      15,
      categoryBooksId,
    ]
  );

  logger.info('Database seeded successfully.');
}

module.exports = seedDatabase;
