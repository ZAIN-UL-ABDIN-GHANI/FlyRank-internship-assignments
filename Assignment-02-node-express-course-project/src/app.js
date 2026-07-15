/**
 * Express application setup.
 * This file wires together every piece of application-level middleware and
 * mounts the API routes. It exports the configured `app` but does NOT call
 * .listen() — that happens in server.js, keeping "app definition" separate
 * from "server startup" (useful for testing the app without opening a port).
 */
const express = require('express');
const helmet = require('helmet');
const cors = require('cors');
const compression = require('compression');
const cookieParser = require('cookie-parser');
const morgan = require('morgan');
const rateLimit = require('express-rate-limit');
const swaggerUi = require('swagger-ui-express');

const config = require('./config/env');
const swaggerSpec = require('./config/swagger');
const routes = require('./routes');
const requestTimer = require('./middlewares/requestTimer.middleware');
const notFound = require('./middlewares/notFound.middleware');
const errorHandler = require('./middlewares/errorHandler.middleware');
const ApiResponse = require('./utils/ApiResponse');
const httpStatus = require('./constants/httpStatus');

const app = express();

// ---- Security middleware ----
app.use(helmet());
app.use(cors());

// ---- Rate limiting (applies to the whole API) ----
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 300, // limit each IP to 300 requests per window
  standardHeaders: true,
  legacyHeaders: false,
  message: { success: false, message: 'Too many requests, please try again later.', error: {} },
});
app.use('/api', limiter);

// ---- Performance ----
app.use(compression());

// ---- Body/cookie parsing ----
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(cookieParser());

// ---- Logging ----
// Morgan handles HTTP access logs; requestTimer adds our own custom timing log.
app.use(morgan(config.isDevelopment ? 'dev' : 'combined'));
app.use(requestTimer);

// ---- API docs ----
app.use('/docs', swaggerUi.serve, swaggerUi.setup(swaggerSpec));

// ---- Health check ----
app.get('/health', (req, res) => {
  new ApiResponse(httpStatus.OK, { uptime: process.uptime() }, 'Service is healthy').send(res);
});

// ---- API routes ----
app.use('/api', routes);

// ---- Root ----
app.get('/', (req, res) => {
  new ApiResponse(
    httpStatus.OK,
    { docs: '/docs', health: '/health', api: '/api' },
    'Node.js + Express Course API'
  ).send(res);
});

// ---- 404 + centralized error handling (must be last) ----
app.use(notFound);
app.use(errorHandler);

module.exports = app;
