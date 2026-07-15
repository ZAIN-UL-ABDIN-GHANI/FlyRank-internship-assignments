/**
 * Authentication middleware.
 * Verifies the "Authorization: Bearer <token>" header, decodes the JWT,
 * and attaches the resulting payload to req.user for downstream handlers.
 */
const jwt = require('jsonwebtoken');
const config = require('../config/env');
const ApiError = require('../utils/ApiError');
const asyncHandler = require('../utils/asyncHandler');

const authenticate = asyncHandler(async (req, res, next) => {
  const header = req.headers.authorization;

  if (!header || !header.startsWith('Bearer ')) {
    throw ApiError.unauthorized('Missing or malformed Authorization header');
  }

  const token = header.split(' ')[1];

  try {
    const payload = jwt.verify(token, config.jwt.secret);
    req.user = payload; // { id, email, role }
    next();
  } catch (err) {
    throw ApiError.unauthorized('Invalid or expired token');
  }
});

module.exports = authenticate;
