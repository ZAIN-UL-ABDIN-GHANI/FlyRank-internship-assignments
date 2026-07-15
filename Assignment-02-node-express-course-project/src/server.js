/**
 * Server entry point.
 * Responsible only for starting the HTTP server and handling process-level
 * concerns (startup logging, graceful shutdown, unhandled errors).
 */
const app = require('./app');
const config = require('./config/env');
const logger = require('./utils/logger');

const server = app.listen(config.port, () => {
  logger.info(`Server running in ${config.env} mode on http://localhost:${config.port}`);
  logger.info(`Swagger docs available at http://localhost:${config.port}/docs`);
});

function shutdown(signal) {
  logger.warn(`${signal} received. Shutting down gracefully...`);
  server.close(() => {
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
