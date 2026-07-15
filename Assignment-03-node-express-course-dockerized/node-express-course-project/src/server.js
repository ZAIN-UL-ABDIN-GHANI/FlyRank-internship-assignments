/**
 * Server entry point.
 * Responsible only for starting the HTTP server and handling process-level
 * concerns (startup logging, graceful shutdown, unhandled errors).
 */
const app = require('./app');
const config = require('./config/env');
const logger = require('./utils/logger');
const pool = require('./database/db');
const seedDatabase = require('./database/seed');

let server;

async function start() {
  try {
    // Fail fast with a clear log line if Postgres isn't reachable yet,
    // instead of letting the first API request surface a confusing error.
    await pool.query('SELECT 1');
    logger.info('Connected to PostgreSQL.');

    await seedDatabase();

    server = app.listen(config.port, () => {
      logger.info(`Server running in ${config.env} mode on http://localhost:${config.port}`);
      logger.info(`Swagger docs available at http://localhost:${config.port}/docs`);
    });
  } catch (err) {
    logger.error('Failed to start server', err);
    process.exit(1);
  }
}

start();

function shutdown(signal) {
  logger.warn(`${signal} received. Shutting down gracefully...`);
  if (!server) {
    process.exit(0);
    return;
  }
  server.close(async () => {
    await pool.end();
    logger.info('Server closed. Process exiting.');
    process.exit(0);
  });
}

process.on('SIGTERM', () => shutdown('SIGTERM'));
process.on('SIGINT', () => shutdown('SIGINT'));

process.on('unhandledRejection', (reason) => {
  logger.error('Unhandled promise rejection', reason);
  throw reason;
});

process.on('uncaughtException', (err) => {
  logger.error('Uncaught exception', err);
  process.exit(1);
});
