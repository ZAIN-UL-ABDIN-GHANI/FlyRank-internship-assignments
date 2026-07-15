const asyncHandler = require('../utils/asyncHandler');
const ApiResponse = require('../utils/ApiResponse');
const productService = require('../services/product.service');
const httpStatus = require('../constants/httpStatus');

const list = asyncHandler(async (req, res) => {
  // Demonstrates req.query for filtering/searching
  const { categoryId, minPrice, maxPrice, search } = req.query;
  const products = await productService.listProducts({
    categoryId,
    minPrice: minPrice !== undefined ? Number(minPrice) : undefined,
    maxPrice: maxPrice !== undefined ? Number(maxPrice) : undefined,
    search,
  });
  return new ApiResponse(httpStatus.OK, products, 'Products fetched successfully').send(res);
});

const getById = asyncHandler(async (req, res) => {
  const product = await productService.getProduct(req.params.id);
  return new ApiResponse(httpStatus.OK, product, 'Product fetched successfully').send(res);
});

const create = asyncHandler(async (req, res) => {
  const product = await productService.createProduct(req.body);
  return new ApiResponse(httpStatus.CREATED, product, 'Product created successfully').send(res);
});

const update = asyncHandler(async (req, res) => {
  const product = await productService.updateProduct(req.params.id, req.body);
  return new ApiResponse(httpStatus.OK, product, 'Product updated successfully').send(res);
});

const patch = asyncHandler(async (req, res) => {
  // PATCH: partial update, same underlying service as PUT since the
  // in-memory repository already merges partial data.
  const product = await productService.updateProduct(req.params.id, req.body);
  return new ApiResponse(httpStatus.OK, product, 'Product patched successfully').send(res);
});

const remove = asyncHandler(async (req, res) => {
  await productService.deleteProduct(req.params.id);
  return new ApiResponse(httpStatus.OK, null, 'Product deleted successfully').send(res);
});

module.exports = { list, getById, create, update, patch, remove };
