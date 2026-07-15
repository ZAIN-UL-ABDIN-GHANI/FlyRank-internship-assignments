const productRepository = require('../repositories/product.repository');
const categoryRepository = require('../repositories/category.repository');
const ApiError = require('../utils/ApiError');

async function listProducts({ categoryId, minPrice, maxPrice, search } = {}) {
  return productRepository.findAll((product) => {
    if (categoryId && product.categoryId !== categoryId) return false;
    if (minPrice !== undefined && product.price < minPrice) return false;
    if (maxPrice !== undefined && product.price > maxPrice) return false;
    if (search && !product.name.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });
}

async function getProduct(id) {
  const product = await productRepository.findById(id);
  if (!product) throw ApiError.notFound('Product not found');
  return product;
}

async function createProduct(data) {
  const category = await categoryRepository.findById(data.categoryId);
  if (!category) throw ApiError.badRequest('categoryId does not reference an existing category');
  return productRepository.create(data);
}

async function updateProduct(id, data) {
  const product = await productRepository.findById(id);
  if (!product) throw ApiError.notFound('Product not found');

  if (data.categoryId) {
    const category = await categoryRepository.findById(data.categoryId);
    if (!category) throw ApiError.badRequest('categoryId does not reference an existing category');
  }

  return productRepository.update(id, data);
}

async function deleteProduct(id) {
  const product = await productRepository.findById(id);
  if (!product) throw ApiError.notFound('Product not found');
  await productRepository.remove(id);
}

module.exports = { listProducts, getProduct, createProduct, updateProduct, deleteProduct };
