const categoryRepository = require('../repositories/category.repository');
const productRepository = require('../repositories/product.repository');
const ApiError = require('../utils/ApiError');

async function listCategories() {
  return categoryRepository.findAll();
}

async function getCategory(id) {
  const category = await categoryRepository.findById(id);
  if (!category) throw ApiError.notFound('Category not found');
  return category;
}

async function createCategory(data) {
  const existing = await categoryRepository.findOne(
    (c) => c.name.toLowerCase() === data.name.toLowerCase()
  );
  if (existing) throw ApiError.conflict('A category with this name already exists');
  return categoryRepository.create(data);
}

async function updateCategory(id, data) {
  const category = await categoryRepository.findById(id);
  if (!category) throw ApiError.notFound('Category not found');
  return categoryRepository.update(id, data);
}

async function deleteCategory(id) {
  const category = await categoryRepository.findById(id);
  if (!category) throw ApiError.notFound('Category not found');

  const productsInCategory = await productRepository.findByCategory(id);
  if (productsInCategory.length > 0) {
    throw ApiError.conflict('Cannot delete a category that still has products');
  }

  await categoryRepository.remove(id);
}

module.exports = { listCategories, getCategory, createCategory, updateCategory, deleteCategory };
