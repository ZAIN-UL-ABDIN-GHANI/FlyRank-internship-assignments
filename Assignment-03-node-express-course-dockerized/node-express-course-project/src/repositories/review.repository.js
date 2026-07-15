const PostgresRepository = require('./postgres.repository');

class ReviewRepository extends PostgresRepository {
  constructor() {
    super('reviews');
  }

  async findByProduct(productId) {
    return this.findAll((review) => review.productId === productId);
  }
}

module.exports = new ReviewRepository();
