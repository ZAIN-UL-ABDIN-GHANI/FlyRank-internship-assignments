const router = require('express').Router();
const controller = require('../controllers/product.controller');
const validate = require('../middlewares/validate.middleware');
const authenticate = require('../middlewares/auth.middleware');
const authorize = require('../middlewares/role.middleware');
const roles = require('../constants/roles');
const {
  idParamRule,
  createProductRules,
  updateProductRules,
} = require('../validators/product.validator');

/**
 * @openapi
 * tags:
 *   name: Products
 *   description: Product catalog CRUD
 */

/**
 * @openapi
 * /api/products:
 *   get:
 *     tags: [Products]
 *     summary: List products (supports filtering via query params)
 *     parameters:
 *       - in: query
 *         name: categoryId
 *         schema: { type: string, format: uuid }
 *       - in: query
 *         name: minPrice
 *         schema: { type: number }
 *       - in: query
 *         name: maxPrice
 *         schema: { type: number }
 *       - in: query
 *         name: search
 *         schema: { type: string }
 *     responses:
 *       200: { description: Products fetched successfully }
 */
router.get('/', controller.list);

/**
 * @openapi
 * /api/products/{id}:
 *   get:
 *     tags: [Products]
 *     summary: Get a product by id
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema: { type: string, format: uuid }
 *     responses:
 *       200: { description: Product fetched successfully }
 *       404: { description: Product not found }
 */
router.get('/:id', idParamRule, validate, controller.getById);

/**
 * @openapi
 * /api/products:
 *   post:
 *     tags: [Products]
 *     summary: Create a product (admin only)
 *     security: [{ bearerAuth: [] }]
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required: [name, price, stock, categoryId]
 *             properties:
 *               name: { type: string }
 *               description: { type: string }
 *               price: { type: number, example: 49.99 }
 *               stock: { type: integer, example: 10 }
 *               categoryId: { type: string, format: uuid }
 *     responses:
 *       201: { description: Product created successfully }
 *       422: { description: Validation failed }
 */
router.post(
  '/',
  authenticate,
  authorize(roles.ADMIN),
  createProductRules,
  validate,
  controller.create
);

/**
 * @openapi
 * /api/products/{id}:
 *   put:
 *     tags: [Products]
 *     summary: Fully update a product (admin only)
 *     security: [{ bearerAuth: [] }]
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema: { type: string, format: uuid }
 *     responses:
 *       200: { description: Product updated successfully }
 *       404: { description: Product not found }
 */
router.put(
  '/:id',
  authenticate,
  authorize(roles.ADMIN),
  updateProductRules,
  validate,
  controller.update
);

/**
 * @openapi
 * /api/products/{id}:
 *   patch:
 *     tags: [Products]
 *     summary: Partially update a product (admin only), e.g. just stock or price
 *     security: [{ bearerAuth: [] }]
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema: { type: string, format: uuid }
 *     responses:
 *       200: { description: Product patched successfully }
 *       404: { description: Product not found }
 */
router.patch(
  '/:id',
  authenticate,
  authorize(roles.ADMIN),
  updateProductRules,
  validate,
  controller.patch
);

/**
 * @openapi
 * /api/products/{id}:
 *   delete:
 *     tags: [Products]
 *     summary: Delete a product (admin only)
 *     security: [{ bearerAuth: [] }]
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema: { type: string, format: uuid }
 *     responses:
 *       200: { description: Product deleted successfully }
 *       404: { description: Product not found }
 */
router.delete(
  '/:id',
  authenticate,
  authorize(roles.ADMIN),
  idParamRule,
  validate,
  controller.remove
);

module.exports = router;
