const router = require('express').Router();
const controller = require('../controllers/auth.controller');
const validate = require('../middlewares/validate.middleware');
const authenticate = require('../middlewares/auth.middleware');
const { registerRules, loginRules } = require('../validators/auth.validator');

/**
 * @openapi
 * tags:
 *   name: Auth
 *   description: Registration, login, and the current user's profile
 */

/**
 * @openapi
 * /api/auth/register:
 *   post:
 *     tags: [Auth]
 *     summary: Register a new user
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required: [name, email, password]
 *             properties:
 *               name: { type: string, example: Jane Doe }
 *               email: { type: string, example: jane@example.com }
 *               password: { type: string, example: SecurePass1 }
 *     responses:
 *       201: { description: User registered successfully }
 *       409: { description: Email already registered }
 *       422: { description: Validation failed }
 */
router.post('/register', registerRules, validate, controller.register);

/**
 * @openapi
 * /api/auth/login:
 *   post:
 *     tags: [Auth]
 *     summary: Log in and receive a JWT
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required: [email, password]
 *             properties:
 *               email: { type: string, example: admin@example.com }
 *               password: { type: string, example: Admin123! }
 *     responses:
 *       200: { description: Login successful, returns a JWT }
 *       401: { description: Invalid credentials }
 */
router.post('/login', loginRules, validate, controller.login);

/**
 * @openapi
 * /api/auth/me:
 *   get:
 *     tags: [Auth]
 *     summary: Get the currently authenticated user's profile
 *     security: [{ bearerAuth: [] }]
 *     responses:
 *       200: { description: Profile fetched successfully }
 *       401: { description: Missing or invalid token }
 */
router.get('/me', authenticate, controller.me);

module.exports = router;
