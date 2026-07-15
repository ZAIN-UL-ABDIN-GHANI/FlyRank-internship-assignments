const router = require('express').Router();
const controller = require('../controllers/order.controller');
const validate = require('../middlewares/validate.middleware');
const authenticate = require('../middlewares/auth.middleware');
const {
  idParamRule,
  createOrderRules,
  updateStatusRules,
} = require('../validators/order.validator');

/**
 * @openapi
 * tags:
 *   name: Orders
 *   description: Orders placed by authenticated users
 */

/**
 * @openapi
 * /api/orders:
 *   get:
 *     tags: [Orders]
 *     summary: List orders (own orders for users, all orders for admins)
 *     security: [{ bearerAuth: [] }]
 *     responses:
 *       200: { description: Orders fetched successfully }
 */
router.get('/', authenticate, controller.list);

/**
 * @openapi
 * /api/orders/{id}:
 *   get:
 *     tags: [Orders]
 *     summary: Get a single order by id
 *     security: [{ bearerAuth: [] }]
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema: { type: string, format: uuid }
 *     responses:
 *       200: { description: Order fetched successfully }
 *       403: { description: Not your order }
 *       404: { description: Order not found }
 */
router.get('/:id', authenticate, idParamRule, validate, controller.getById);

/**
 * @openapi
 * /api/orders:
 *   post:
 *     tags: [Orders]
 *     summary: Place a new order
 *     security: [{ bearerAuth: [] }]
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required: [items]
 *             properties:
 *               items:
 *                 type: array
 *                 items:
 *                   type: object
 *                   properties:
 *                     productId: { type: string, format: uuid }
 *                     quantity: { type: integer, example: 2 }
 *     responses:
 *       201: { description: Order created successfully }
 *       400: { description: Invalid product or insufficient stock }
 */
router.post('/', authenticate, createOrderRules, validate, controller.create);

/**
 * @openapi
 * /api/orders/{id}/status:
 *   patch:
 *     tags: [Orders]
 *     summary: Update an order's status
 *     security: [{ bearerAuth: [] }]
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema: { type: string, format: uuid }
 *     responses:
 *       200: { description: Order status updated successfully }
 */
router.patch('/:id/status', authenticate, updateStatusRules, validate, controller.updateStatus);

/**
 * @openapi
 * /api/orders/{id}:
 *   delete:
 *     tags: [Orders]
 *     summary: Cancel/delete an order
 *     security: [{ bearerAuth: [] }]
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema: { type: string, format: uuid }
 *     responses:
 *       200: { description: Order deleted successfully }
 */
router.delete('/:id', authenticate, idParamRule, validate, controller.remove);

module.exports = router;
