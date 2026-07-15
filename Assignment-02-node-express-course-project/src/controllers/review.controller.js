const asyncHandler = require('../utils/asyncHandler');
const ApiResponse = require('../utils/ApiResponse');
const reviewService = require('../services/review.service');
const httpStatus = require('../constants/httpStatus');

const list = asyncHandler(async (req, res) => {
  const { productId } = req.query;
  const reviews = await reviewService.listReviews({ productId });
  return new ApiResponse(httpStatus.OK, reviews, 'Reviews fetched successfully').send(res);
});

const getById = asyncHandler(async (req, res) => {
  const review = await reviewService.getReview(req.params.id);
  return new ApiResponse(httpStatus.OK, review, 'Review fetched successfully').send(res);
});

const create = asyncHandler(async (req, res) => {
  const review = await reviewService.createReview(req.user.id, req.body);
  return new ApiResponse(httpStatus.CREATED, review, 'Review created successfully').send(res);
});

const update = asyncHandler(async (req, res) => {
  const review = await reviewService.updateReview(req.params.id, req.user.id, req.body);
  return new ApiResponse(httpStatus.OK, review, 'Review updated successfully').send(res);
});

const remove = asyncHandler(async (req, res) => {
  await reviewService.deleteReview(req.params.id, req.user);
  return new ApiResponse(httpStatus.OK, null, 'Review deleted successfully').send(res);
});

module.exports = { list, getById, create, update, remove };
