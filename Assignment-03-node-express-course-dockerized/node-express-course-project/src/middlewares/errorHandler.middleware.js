/**
 * Global error handler.
 * The last middleware in the stack (4 args = Express error middleware).
 * Normalizes ANY thrown/forwarded error (ApiError, express-validator error,
 * JSON parse error, or an unexpected bug) into the standard error envelope:
 *   { "success": false, "message": "...", "error": {} }
 */
const config = require('../config/env');
const logger = require('../utils/logger');
const ApiError = require('../utils/ApiError');

// eslint-disable-next-line no-unused-vars
function errorHandler(err, req, res, next) {
  let error = err;

  // Normalize non-ApiError errors (e.g. malformed JSON body, library errors)
  if (!(error instanceof ApiError)) {
    const statusCode = error.statusCode || 500;
    const message = error.message || 'Internal server error';
    error = new ApiError(statusCode, message, null, false);
  }

  if (!error.isOperational || error.statusCode >= 500) {
    logger.error(`${req.method} ${req.originalUrl} - ${error.message}`, {
      stack: config.isDevelopment ? err.stack : undefined,
    });
  }

  const body = {
    success: false,
    message: error.message,
    error: {
      statusCode: error.statusCode,
      ...(error.details ? { details: error.details } : {}),
      ...(config.isDevelopment ? { stack: err.stack } : {}),
    },
  };

  res.status(error.statusCode || 500).json(body);
}

module.exports = errorHandler;
