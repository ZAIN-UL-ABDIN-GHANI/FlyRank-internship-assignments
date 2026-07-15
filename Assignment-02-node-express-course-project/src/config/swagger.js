/**
 * Swagger / OpenAPI configuration
 */

const swaggerJsdoc = require('swagger-jsdoc');
const config = require('./env');

const options = {
  definition: {
    openapi: '3.0.0',
    info: {
      title: 'Node.js + Express Course API',
      version: '1.0.0',
      description:
        'A production-style REST API built to demonstrate Node.js and Express fundamentals including routing, middleware, validation, JWT authentication, the repository pattern, and centralized error handling.',
    },

    servers: [
      {
        url: `http://localhost:${config.port}`,
        description: 'Local Development Server',
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

    security: [
      {
        bearerAuth: [],
      },
    ],
  },

  // IMPORTANT:
  // Use a glob path instead of path.join() for cross-platform compatibility.
  apis: ['./src/routes/*.js'],
};

const swaggerSpec = swaggerJsdoc(options);

module.exports = swaggerSpec;