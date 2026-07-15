const { param, body } = require('express-validator');

const idParamRule = [param('id').isUUID().withMessage('id must be a valid UUID')];

const createOrderRules = [
  body('items').isArray({ min: 1 }).withMessage('items must be a non-empty array'),
  body('items.*.productId').isUUID().withMessage('Each item needs a valid productId'),
  body('items.*.quantity')
    .isInt({ min: 1 })
    .withMessage('Each item quantity must be an integer of at least 1'),
];

const updateStatusRules = [
  ...idParamRule,
  body('status')
    .isIn(['pending', 'paid', 'shipped', 'cancelled'])
    .withMessage('status must be one of: pending, paid, shipped, cancelled'),
];

module.exports = { idParamRule, createOrderRules, updateStatusRules };
