/**
 * Centralized environment configuration.
 * Loads variables from .env (via dotenv) and exposes them as a single
 * typed object so the rest of the app never touches `process.env` directly.
 */
require('dotenv').config();

const config = {
  env: process.env.NODE_ENV || 'development',
  port: parseInt(process.env.PORT, 10) || 3000,
  databaseUrl: process.env.DATABASE_URL || 'postgres://postgres:postgres@localhost:5432/appdb',
  jwt: {
    secret: process.env.JWT_SECRET || 'dev-secret-change-me',
    expiresIn: process.env.JWT_EXPIRES_IN || '1d',
  },
  apiKey: process.env.API_KEY || '',
};

config.isProduction = config.env === 'production';
config.isDevelopment = config.env === 'development';

module.exports = config;
