const asyncHandler = require('../utils/asyncHandler');
const ApiResponse = require('../utils/ApiResponse');
const categoryService = require('../services/category.service');
const httpStatus = require('../constants/httpStatus');

const list = asyncHandler(async (req, res) => {
  const categories = await categoryService.listCategories();
  return new ApiResponse(httpStatus.OK, categories, 'Categories fetched successfully').send(res);
});

const getById = asyncHandler(async (req, res) => {
  const category = await categoryService.getCategory(req.params.id);
  return new ApiResponse(httpStatus.OK, category, 'Category fetched successfully').send(res);
});

const create = asyncHandler(async (req, res) => {
  const category = await categoryService.createCategory(req.body);
  return new ApiResponse(httpStatus.CREATED, category, 'Category created successfully').send(res);
});

const update = asyncHandler(async (req, res) => {
  const category = await categoryService.updateCategory(req.params.id, req.body);
  return new ApiResponse(httpStatus.OK, category, 'Category updated successfully').send(res);
});

const remove = asyncHandler(async (req, res) => {
  await categoryService.deleteCategory(req.params.id);
  return new ApiResponse(httpStatus.OK, null, 'Category deleted successfully').send(res);
});

module.exports = { list, getById, create, update, remove };
