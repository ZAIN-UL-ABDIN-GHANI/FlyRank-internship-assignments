/**
 * Custom "request timer" middleware.
 * Demonstrates application-level middleware: it runs on every request,
 * records how long the request took, and logs it once the response finishes.
 */
const logger = require('../utils/logger');

function requestTimer(req, res, next) {
  const start = process.hrtime.bigint();

  res.on('finish', () => {
    const end = process.hrtime.bigint();
    const durationMs = Number(end - start) / 1_000_000;
    logger.info(
      `${req.method} ${req.originalUrl} -> ${res.statusCode} (${durationMs.toFixed(2)}ms)`
    );
  });

  next();
}

module.exports = requestTimer;
