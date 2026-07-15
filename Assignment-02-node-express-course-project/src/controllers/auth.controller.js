/**
 * Auth controller — thin HTTP layer over auth.service.
 * Controllers only: parse the request, call a service, shape the response.
 * No business logic lives here.
 */
const asyncHandler = require('../utils/asyncHandler');
const ApiResponse = require('../utils/ApiResponse');
const authService = require('../services/auth.service');
const httpStatus = require('../constants/httpStatus');

const register = asyncHandler(async (req, res) => {
  const result = await authService.register(req.body);
  return new ApiResponse(httpStatus.CREATED, result, 'User registered successfully').send(res);
});

const login = asyncHandler(async (req, res) => {
  const result = await authService.login(req.body);
  return new ApiResponse(httpStatus.OK, result, 'Login successful').send(res);
});

const me = asyncHandler(async (req, res) => {
  const profile = await authService.getProfile(req.user.id);
  return new ApiResponse(httpStatus.OK, profile, 'Profile fetched successfully').send(res);
});

module.exports = { register, login, me };
