const router = require('express').Router();
const controller = require('../controllers/user.controller');
const validate = require('../middlewares/validate.middleware');
const authenticate = require('../middlewares/auth.middleware');
const authorize = require('../middlewares/role.middleware');
const roles = require('../constants/roles');
const { idParamRule, updateUserRules } = require('../validators/user.validator');

/**
 * @openapi
 * tags:
 *   name: Users
 *   description: User management (admin-only listing/removal)
 */

/**
 * @openapi
 * /api/users:
 *   get:
 *     tags: [Users]
 *     summary: List all users (admin only)
 *     security: [{ bearerAuth: [] }]
 *     responses:
 *       200: { description: Users fetched successfully }
 *       403: { description: Admin role required }
 */
router.get('/', authenticate, authorize(roles.ADMIN), controller.list);

/**
 * @openapi
 * /api/users/{id}:
 *   get:
 *     tags: [Users]
 *     summary: Get a single user by id
 *     security: [{ bearerAuth: [] }]
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema: { type: string, format: uuid }
 *     responses:
 *       200: { description: User fetched successfully }
 *       404: { description: User not found }
 */
router.get('/:id', authenticate, idParamRule, validate, controller.getById);

/**
 * @openapi
 * /api/users/{id}:
 *   put:
 *     tags: [Users]
 *     summary: Update a user's own profile fields (name/email)
 *     security: [{ bearerAuth: [] }]
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema: { type: string, format: uuid }
 *     responses:
 *       200: { description: User updated successfully }
 *       404: { description: User not found }
 */
router.put('/:id', authenticate, updateUserRules, validate, controller.update);

/**
 * @openapi
 * /api/users/{id}:
 *   delete:
 *     tags: [Users]
 *     summary: Delete a user (admin only)
 *     security: [{ bearerAuth: [] }]
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema: { type: string, format: uuid }
 *     responses:
 *       200: { description: User deleted successfully }
 *       403: { description: Admin role required }
 *       404: { description: User not found }
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
