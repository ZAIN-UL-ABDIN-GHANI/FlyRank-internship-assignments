const asyncHandler = require('../utils/asyncHandler');
const ApiResponse = require('../utils/ApiResponse');
const userService = require('../services/user.service');
const httpStatus = require('../constants/httpStatus');

const list = asyncHandler(async (req, res) => {
  const users = await userService.listUsers();
  return new ApiResponse(httpStatus.OK, users, 'Users fetched successfully').send(res);
});

const getById = asyncHandler(async (req, res) => {
  const user = await userService.getUser(req.params.id);
  return new ApiResponse(httpStatus.OK, user, 'User fetched successfully').send(res);
});

const update = asyncHandler(async (req, res) => {
  const user = await userService.updateUser(req.params.id, req.body);
  return new ApiResponse(httpStatus.OK, user, 'User updated successfully').send(res);
});

const remove = asyncHandler(async (req, res) => {
  await userService.deleteUser(req.params.id);
  return new ApiResponse(httpStatus.OK, null, 'User deleted successfully').send(res);
});

module.exports = { list, getById, update, remove };
