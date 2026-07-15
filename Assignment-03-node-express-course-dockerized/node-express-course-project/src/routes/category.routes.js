const router = require('express').Router();
const controller = require('../controllers/category.controller');
const validate = require('../middlewares/validate.middleware');
const authenticate = require('../middlewares/auth.middleware');
const authorize = require('../middlewares/role.middleware');
const roles = require('../constants/roles');
const {
  idParamRule,
  createCategoryRules,
  updateCategoryRules,
} = require('../validators/category.validator');

/**
 * @openapi
 * tags:
 *   name: Categories
 *   description: Product categories
 */

/**
 * @openapi
 * /api/categories:
 *   get:
 *     tags: [Categories]
 *     summary: List all categories
 *     responses:
 *       200: { description: Categories fetched successfully }
 */
router.get('/', controller.list);

/**
 * @openapi
 * /api/categories/{id}:
 *   get:
 *     tags: [Categories]
 *     summary: Get a category by id
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema: { type: string, format: uuid }
 *     responses:
 *       200: { description: Category fetched successfully }
 *       404: { description: Category not found }
 */
router.get('/:id', idParamRule, validate, controller.getById);

/**
 * @openapi
 * /api/categories:
 *   post:
 *     tags: [Categories]
 *     summary: Create a category (admin only)
 *     security: [{ bearerAuth: [] }]
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required: [name]
 *             properties:
 *               name: { type: string, example: Electronics }
 *               description: { type: string, example: Gadgets and devices }
 *     responses:
 *       201: { description: Category created successfully }
 *       409: { description: Category name already exists }
 */
router.post(
  '/',
  authenticate,
  authorize(roles.ADMIN),
  createCategoryRules,
  validate,
  controller.create
);

/**
 * @openapi
 * /api/categories/{id}:
 *   put:
 *     tags: [Categories]
 *     summary: Update a category (admin only)
 *     security: [{ bearerAuth: [] }]
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema: { type: string, format: uuid }
 *     responses:
 *       200: { description: Category updated successfully }
 *       404: { description: Category not found }
 */
router.put(
  '/:id',
  authenticate,
  authorize(roles.ADMIN),
  updateCategoryRules,
  validate,
  controller.update
);

/**
 * @openapi
 * /api/categories/{id}:
 *   delete:
 *     tags: [Categories]
 *     summary: Delete a category (admin only)
 *     security: [{ bearerAuth: [] }]
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema: { type: string, format: uuid }
 *     responses:
 *       200: { description: Category deleted successfully }
 *       409: { description: Category still has products }
 *       404: { description: Category not found }
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
