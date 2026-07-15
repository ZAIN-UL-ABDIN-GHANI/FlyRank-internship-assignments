/**
 * Swagger/OpenAPI configuration.
 * Generates the OpenAPI spec from JSDoc comments found in the route files
 * and exposes it through swagger-ui-express at GET /docs.
 */
const swaggerJsdoc = require('swagger-jsdoc');
const path = require('path');
const config = require('./env');

const options = {
  definition: {
    openapi: '3.0.0',
    info: {
      title: 'Node.js + Express Course API',
      version: '1.0.0',
      description:
        'A production-style REST API built to demonstrate Node.js and Express fundamentals: ' +
        'routing, middleware, validation, JWT authentication, the repository pattern, and ' +
        'centralized error handling.',
    },
    servers: [
      {
        url: `http://localhost:${config.port}`,
        description: 'Local development server',
      },
    ],
    components: {
      securitySchemes: {
        bearerAuth: {
          type: 'http',
          scheme: 'bearer',
          bearerFormat: 'JWT',
        },
      },
    },
  },
  apis: [path.join(__dirname, '../routes/*.js')],
};

module.exports = swaggerJsdoc(options);
