/**
 * Wraps an async Express route/controller so that any rejected promise
 * (or thrown error) is forwarded to next(), instead of requiring a
 * try/catch block in every single controller ("async error wrapper").
 *
 * Usage: router.get('/', asyncHandler(controller.list));
 */
const asyncHandler = (fn) => (req, res, next) => {
  Promise.resolve(fn(req, res, next)).catch(next);
};

module.exports = asyncHandler;
