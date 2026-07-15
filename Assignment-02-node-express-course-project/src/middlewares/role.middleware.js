/**
 * Role-based access-control middleware factory.
 * Usage: router.delete('/:id', authenticate, authorize('admin'), controller.remove)
 * Must run AFTER the `authenticate` middleware, since it relies on req.user.
 */
const ApiError = require('../utils/ApiError');

function authorize(...allowedRoles) {
  return (req, res, next) => {
    if (!req.user) {
      return next(ApiError.unauthorized('Authentication required'));
    }
    if (!allowedRoles.includes(req.user.role)) {
      return next(ApiError.forbidden('You do not have permission to perform this action'));
    }
    return next();
  };
}

module.exports = authorize;
