/**
 * Demo/playground controller.
 * Not part of the "real" API — exists purely to explicitly showcase every
 * req.* and res.* method/property called out in the learning objectives,
 * in one obvious place, for teaching purposes.
 */
const path = require('path');
const asyncHandler = require('../utils/asyncHandler');
const ApiResponse = require('../utils/ApiResponse');
const httpStatus = require('../constants/httpStatus');

// GET /api/demo/request-info/:id  -> shows req.params, req.query, req.headers,
// req.cookies, req.ip, req.method, req.originalUrl
const requestInfo = asyncHandler(async (req, res) => {
  const info = {
    method: req.method,
    originalUrl: req.originalUrl,
    params: req.params,
    query: req.query,
    headers: {
      'user-agent': req.headers['user-agent'],
      'content-type': req.headers['content-type'],
    },
    cookies: req.cookies,
    ip: req.ip,
  };
  return new ApiResponse(httpStatus.OK, info, 'Request info captured').send(res);
});

// POST /api/demo/echo-body -> shows req.body
const echoBody = asyncHandler(async (req, res) => {
  return new ApiResponse(httpStatus.OK, { received: req.body }, 'Body echoed').send(res);
});

// GET /api/demo/set-cookie -> shows res.cookie + custom header + res.status
const setCookie = asyncHandler(async (req, res) => {
  res.cookie('demo_session', 'sample-session-value', { httpOnly: true, maxAge: 60_000 });
  res.setHeader('X-Demo-Header', 'node-express-course-project');
  return new ApiResponse(httpStatus.OK, null, 'Cookie and custom header set').send(res);
});

// GET /api/demo/redirect -> shows res.redirect
const redirectDemo = asyncHandler(async (req, res) => {
  res.redirect(302, '/api/demo/request-info/redirected');
});

// GET /api/demo/download -> shows res.download
const downloadDemo = asyncHandler(async (req, res) => {
  const filePath = path.join(__dirname, '../../public/sample.txt');
  res.download(filePath, 'sample-download.txt');
});

// GET /api/demo/send-file -> shows res.sendFile
const sendFileDemo = asyncHandler(async (req, res) => {
  const filePath = path.join(__dirname, '../../public/sample.txt');
  res.sendFile(filePath);
});

// GET /api/demo/raw-send -> shows res.send (plain text, not the JSON envelope)
const rawSend = asyncHandler(async (req, res) => {
  res.status(httpStatus.OK).send('Plain text response via res.send()');
});

module.exports = {
  requestInfo,
  echoBody,
  setCookie,
  redirectDemo,
  downloadDemo,
  sendFileDemo,
  rawSend,
};
