/**
 * Minimal, dependency-free custom logger.
 * Morgan handles HTTP access logs; this handles application-level events
 * (startup, shutdown, errors) with consistent, timestamped formatting.
 */
const levels = {
  info: '\x1b[36mINFO\x1b[0m',
  warn: '\x1b[33mWARN\x1b[0m',
  error: '\x1b[31mERROR\x1b[0m',
};

function log(level, message, meta) {
  const timestamp = new Date().toISOString();
  const line = `[${timestamp}] [${levels[level] || level}] ${message}`;
  if (meta) {
    // eslint-disable-next-line no-console
    console.log(line, meta);
  } else {
    // eslint-disable-next-line no-console
    console.log(line);
  }
}

module.exports = {
  info: (message, meta) => log('info', message, meta),
  warn: (message, meta) => log('warn', message, meta),
  error: (message, meta) => log('error', message, meta),
};
