const { param, body } = require('express-validator');

const idParamRule = [param('id').isUUID().withMessage('id must be a valid UUID')];

const createCategoryRules = [
  body('name').trim().notEmpty().withMessage('Category name is required'),
  body('description').optional().trim().isString(),
];

const updateCategoryRules = [
  ...idParamRule,
  body('name').optional().trim().notEmpty().withMessage('Category name cannot be empty'),
  body('description').optional().trim().isString(),
];

module.exports = { idParamRule, createCategoryRules, updateCategoryRules };
