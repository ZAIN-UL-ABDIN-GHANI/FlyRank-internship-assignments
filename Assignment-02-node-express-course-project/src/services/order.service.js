const orderRepository = require('../repositories/order.repository');
const productRepository = require('../repositories/product.repository');
const ApiError = require('../utils/ApiError');

async function buildOrder(userId, items) {
  let totalAmount = 0;
  const resolvedItems = [];

  for (const item of items) {
    const product = await productRepository.findById(item.productId);
    if (!product) {
      throw ApiError.badRequest(`Product ${item.productId} does not exist`);
    }
    if (product.stock < item.quantity) {
      throw ApiError.badRequest(`Insufficient stock for product "${product.name}"`);
    }
    totalAmount += product.price * item.quantity;
    resolvedItems.push({
      productId: product.id,
      quantity: item.quantity,
      unitPrice: product.price,
    });
  }

  return {
    userId,
    items: resolvedItems,
    totalAmount: Math.round(totalAmount * 100) / 100,
    status: 'pending',
  };
}

async function listOrders(user) {
  if (user.role === 'admin') {
    return orderRepository.findAll();
  }
  return orderRepository.findByUser(user.id);
}

async function getOrder(id, user) {
  const order = await orderRepository.findById(id);
  if (!order) throw ApiError.notFound('Order not found');
  if (user.role !== 'admin' && order.userId !== user.id) {
    throw ApiError.forbidden('You do not have access to this order');
  }
  return order;
}

async function createOrder(userId, items) {
  const orderData = await buildOrder(userId, items);
  return orderRepository.create(orderData);
}

async function updateOrderStatus(id, status, user) {
  const order = await getOrder(id, user);
  return orderRepository.update(order.id, { status });
}

async function deleteOrder(id, user) {
  const order = await getOrder(id, user);
  await orderRepository.remove(order.id);
}

module.exports = { listOrders, getOrder, createOrder, updateOrderStatus, deleteOrder };
