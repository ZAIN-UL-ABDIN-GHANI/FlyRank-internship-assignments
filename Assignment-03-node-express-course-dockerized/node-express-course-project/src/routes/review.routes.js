const router = require('express').Router();
const controller = require('../controllers/review.controller');
const validate = require('../middlewares/validate.middleware');
const authenticate = require('../middlewares/auth.middleware');
const {
  idParamRule,
  createReviewRules,
  updateReviewRules,
} = require('../validators/review.validator');

/**
 * @openapi
 * tags:
 *   name: Reviews
 *   description: Product reviews
 */

/**
 * @openapi
 * /api/reviews:
 *   get:
 *     tags: [Reviews]
 *     summary: List reviews (optionally filter by productId)
 *     parameters:
 *       - in: query
 *         name: productId
 *         schema: { type: string, format: uuid }
 *     responses:
 *       200: { description: Reviews fetched successfully }
 */
router.get('/', controller.list);

/**
 * @openapi
 * /api/reviews/{id}:
 *   get:
 *     tags: [Reviews]
 *     summary: Get a review by id
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema: { type: string, format: uuid }
 *     responses:
 *       200: { description: Review fetched successfully }
 *       404: { description: Review not found }
 */
router.get('/:id', idParamRule, validate, controller.getById);

/**
 * @openapi
 * /api/reviews:
 *   post:
 *     tags: [Reviews]
 *     summary: Create a review for a product
 *     security: [{ bearerAuth: [] }]
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required: [productId, rating]
 *             properties:
 *               productId: { type: string, format: uuid }
 *               rating: { type: integer, example: 5 }
 *               comment: { type: string, example: Great product! }
 *     responses:
 *       201: { description: Review created successfully }
 */
router.post('/', authenticate, createReviewRules, validate, controller.create);

/**
 * @openapi
 * /api/reviews/{id}:
 *   put:
 *     tags: [Reviews]
 *     summary: Update your own review
 *     security: [{ bearerAuth: [] }]
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema: { type: string, format: uuid }
 *     responses:
 *       200: { description: Review updated successfully }
 *       403: { description: Not your review }
 */
router.put('/:id', authenticate, updateReviewRules, validate, controller.update);

/**
 * @openapi
 * /api/reviews/{id}:
 *   delete:
 *     tags: [Reviews]
 *     summary: Delete your own review (or any review, if admin)
 *     security: [{ bearerAuth: [] }]
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema: { type: string, format: uuid }
 *     responses:
 *       200: { description: Review deleted successfully }
 */
router.delete('/:id', authenticate, idParamRule, validate, controller.remove);

module.exports = router;
