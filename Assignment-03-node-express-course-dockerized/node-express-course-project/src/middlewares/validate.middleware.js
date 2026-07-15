/**
 * Validation middleware.
 * Runs after an express-validator chain (defined in src/validators/*) and,
 * if any rule failed, short-circuits the request with a 422 and a clear,
 * field-by-field error payload instead of letting bad data reach the controller.
 */
const { validationResult } = require('express-validator');
const ApiError = require('../utils/ApiError');

function validate(req, res, next) {
  const errors = validationResult(req);

  if (errors.isEmpty()) {
    return next();
  }

  const formatted = errors.array().map((err) => ({
    field: err.path,
    message: err.msg,
    value: err.value,
  }));

  return next(new ApiError(422, 'Validation failed', formatted));
}

module.exports = validate;
