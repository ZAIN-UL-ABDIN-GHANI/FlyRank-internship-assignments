/**
 * 404 middleware.
 * Placed after every route in app.js — if a request reaches this point,
 * no route matched, so we turn it into a standard ApiError.
 */
const ApiError = require('../utils/ApiError');

function notFound(req, res, next) {
  next(ApiError.notFound(`Route not found: ${req.method} ${req.originalUrl}`));
}

module.exports = notFound;
