/**
 * PostgreSQL connection pool.
 *
 * This is the ONLY place in the app that talks to `pg` directly. Everything
 * else (PostgresRepository, seed.js) imports this shared `Pool` instance
 * instead of opening its own connections, which is what makes connection
 * pooling actually work.
 */
const { Pool } = require('pg');
const config = require('../config/env');
const logger = require('../utils/logger');

const pool = new Pool({
  connectionString: config.databaseUrl,
});

// Pooled, idle clients can still throw (e.g. the network connection to
// Postgres drops). Without this handler an unhandled 'error' event on the
// pool would crash the whole process.
pool.on('error', (err) => {
  logger.error('Unexpected error on idle PostgreSQL client', err);
});

module.exports = pool;
