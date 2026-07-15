const reviewRepository = require('../repositories/review.repository');
const productRepository = require('../repositories/product.repository');
const ApiError = require('../utils/ApiError');

async function listReviews({ productId } = {}) {
  if (productId) {
    return reviewRepository.findByProduct(productId);
  }
  return reviewRepository.findAll();
}

async function getReview(id) {
  const review = await reviewRepository.findById(id);
  if (!review) throw ApiError.notFound('Review not found');
  return review;
}

async function createReview(userId, data) {
  const product = await productRepository.findById(data.productId);
  if (!product) throw ApiError.badRequest('productId does not reference an existing product');

  return reviewRepository.create({ ...data, userId });
}

async function updateReview(id, userId, data) {
  const review = await reviewRepository.findById(id);
  if (!review) throw ApiError.notFound('Review not found');
  if (review.userId !== userId) throw ApiError.forbidden('You can only edit your own review');
  return reviewRepository.update(id, data);
}

async function deleteReview(id, user) {
  const review = await reviewRepository.findById(id);
  if (!review) throw ApiError.notFound('Review not found');
  if (review.userId !== user.id && user.role !== 'admin') {
    throw ApiError.forbidden('You can only delete your own review');
  }
  await reviewRepository.remove(id);
}

module.exports = { listReviews, getReview, createReview, updateReview, deleteReview };
