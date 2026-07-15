/**
 * Router aggregator.
 * Every resource lives in its own router file; this module just mounts
 * them all under a single /api namespace, keeping app.js clean.
 */
const router = require('express').Router();

router.use('/auth', require('./auth.routes'));
router.use('/users', require('./user.routes'));
router.use('/categories', require('./category.routes'));
router.use('/products', require('./product.routes'));
router.use('/orders', require('./order.routes'));
router.use('/reviews', require('./review.routes'));
router.use('/demo', require('./demo.routes'));

module.exports = router;
