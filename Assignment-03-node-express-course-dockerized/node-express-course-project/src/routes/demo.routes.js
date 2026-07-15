const router = require('express').Router();
const controller = require('../controllers/demo.controller');

/**
 * @openapi
 * tags:
 *   name: Demo
 *   description: >
 *     Teaching-only endpoints that isolate specific req/res features
 *     called out in the course learning objectives (params, query, headers,
 *     cookies, redirect, download, sendFile, plain send).
 */

/**
 * @openapi
 * /api/demo/request-info/{id}:
 *   get:
 *     tags: [Demo]
 *     summary: Echoes req.params, req.query, req.headers, req.cookies, req.ip, req.method, req.originalUrl
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema: { type: string }
 *       - in: query
 *         name: anything
 *         schema: { type: string }
 *     responses:
 *       200: { description: Request info captured }
 */
router.get('/request-info/:id', controller.requestInfo);

/**
 * @openapi
 * /api/demo/echo-body:
 *   post:
 *     tags: [Demo]
 *     summary: Echoes req.body back to the caller
 *     responses:
 *       200: { description: Body echoed }
 */
router.post('/echo-body', controller.echoBody);

/**
 * @openapi
 * /api/demo/set-cookie:
 *   get:
 *     tags: [Demo]
 *     summary: Demonstrates res.cookie() and a custom response header
 *     responses:
 *       200: { description: Cookie and header set }
 */
router.get('/set-cookie', controller.setCookie);

/**
 * @openapi
 * /api/demo/redirect:
 *   get:
 *     tags: [Demo]
 *     summary: Demonstrates res.redirect()
 *     responses:
 *       302: { description: Redirects to /api/demo/request-info/redirected }
 */
router.get('/redirect', controller.redirectDemo);

/**
 * @openapi
 * /api/demo/download:
 *   get:
 *     tags: [Demo]
 *     summary: Demonstrates res.download()
 *     responses:
 *       200: { description: File downloaded }
 */
router.get('/download', controller.downloadDemo);

/**
 * @openapi
 * /api/demo/send-file:
 *   get:
 *     tags: [Demo]
 *     summary: Demonstrates res.sendFile()
 *     responses:
 *       200: { description: File streamed inline }
 */
router.get('/send-file', controller.sendFileDemo);

/**
 * @openapi
 * /api/demo/raw-send:
 *   get:
 *     tags: [Demo]
 *     summary: Demonstrates res.send() with a plain text body
 *     responses:
 *       200: { description: Plain text response }
 */
router.get('/raw-send', controller.rawSend);

module.exports = router;
