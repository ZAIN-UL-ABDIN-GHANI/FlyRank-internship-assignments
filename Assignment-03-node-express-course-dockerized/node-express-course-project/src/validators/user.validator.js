const { param, body } = require('express-validator');

const idParamRule = [param('id').isUUID().withMessage('id must be a valid UUID')];

const updateUserRules = [
  ...idParamRule,
  body('name').optional().trim().notEmpty().withMessage('Name cannot be empty'),
  body('email').optional().isEmail().withMessage('A valid email is required').normalizeEmail(),
];

module.exports = { idParamRule, updateUserRules };
