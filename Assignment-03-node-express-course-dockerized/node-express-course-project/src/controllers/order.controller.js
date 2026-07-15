const asyncHandler = require('../utils/asyncHandler');
const ApiResponse = require('../utils/ApiResponse');
const orderService = require('../services/order.service');
const httpStatus = require('../constants/httpStatus');

const list = asyncHandler(async (req, res) => {
  const orders = await orderService.listOrders(req.user);
  return new ApiResponse(httpStatus.OK, orders, 'Orders fetched successfully').send(res);
});

const getById = asyncHandler(async (req, res) => {
  const order = await orderService.getOrder(req.params.id, req.user);
  return new ApiResponse(httpStatus.OK, order, 'Order fetched successfully').send(res);
});

const create = asyncHandler(async (req, res) => {
  const order = await orderService.createOrder(req.user.id, req.body.items);
  return new ApiResponse(httpStatus.CREATED, order, 'Order created successfully').send(res);
});

const updateStatus = asyncHandler(async (req, res) => {
  const order = await orderService.updateOrderStatus(req.params.id, req.body.status, req.user);
  return new ApiResponse(httpStatus.OK, order, 'Order status updated successfully').send(res);
});

const remove = asyncHandler(async (req, res) => {
  await orderService.deleteOrder(req.params.id, req.user);
  return new ApiResponse(httpStatus.OK, null, 'Order deleted successfully').send(res);
});

module.exports = { list, getById, create, updateStatus, remove };
