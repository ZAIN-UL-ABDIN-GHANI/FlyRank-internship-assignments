const BaseRepository = require('./base.repository');

class ReviewRepository extends BaseRepository {
  constructor() {
    super('reviews');
  }

  async findByProduct(productId) {
    return this.findAll((review) => review.productId === productId);
  }
}

module.exports = new ReviewRepository();
