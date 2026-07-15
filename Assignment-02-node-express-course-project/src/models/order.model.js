/**
 * @typedef {Object} OrderItem
 * @property {string} productId
 * @property {number} quantity
 * @property {number} unitPrice
 *
 * @typedef {Object} Order
 * @property {string} id
 * @property {string} userId
 * @property {OrderItem[]} items
 * @property {number} totalAmount
 * @property {'pending'|'paid'|'shipped'|'cancelled'} status
 * @property {string} createdAt
 */
module.exports = {};
