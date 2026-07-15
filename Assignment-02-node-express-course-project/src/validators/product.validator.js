const { param, body } = require('express-validator');

const idParamRule = [param('id').isUUID().withMessage('id must be a valid UUID')];

const createProductRules = [
  body('name').trim().notEmpty().withMessage('Product name is required'),
  body('description').optional().trim().isString(),
  body('price').isFloat({ gt: 0 }).withMessage('Price must be a number greater than 0'),
  body('stock').isInt({ min: 0 }).withMessage('Stock must be a non-negative integer'),
  body('categoryId').isUUID().withMessage('categoryId must be a valid UUID'),
];

const updateProductRules = [
  ...idParamRule,
  body('name').optional().trim().notEmpty().withMessage('Product name cannot be empty'),
  body('description').optional().trim().isString(),
  body('price').optional().isFloat({ gt: 0 }).withMessage('Price must be a number greater than 0'),
  body('stock').optional().isInt({ min: 0 }).withMessage('Stock must be a non-negative integer'),
  body('categoryId').optional().isUUID().withMessage('categoryId must be a valid UUID'),
];

module.exports = { idParamRule, createProductRules, updateProductRules };
