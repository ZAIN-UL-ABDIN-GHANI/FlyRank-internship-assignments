const { param, body } = require('express-validator');

const idParamRule = [param('id').isUUID().withMessage('id must be a valid UUID')];

const createReviewRules = [
  body('productId').isUUID().withMessage('productId must be a valid UUID'),
  body('rating').isInt({ min: 1, max: 5 }).withMessage('rating must be an integer from 1 to 5'),
  body('comment').optional().trim().isLength({ max: 1000 }).withMessage('comment is too long'),
];

const updateReviewRules = [
  ...idParamRule,
  body('rating')
    .optional()
    .isInt({ min: 1, max: 5 })
    .withMessage('rating must be an integer from 1 to 5'),
  body('comment').optional().trim().isLength({ max: 1000 }).withMessage('comment is too long'),
];

module.exports = { idParamRule, createReviewRules, updateReviewRules };
