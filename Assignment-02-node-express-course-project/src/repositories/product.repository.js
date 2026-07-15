const BaseRepository = require('./base.repository');

class ProductRepository extends BaseRepository {
  constructor() {
    super('products');
  }

  async findByCategory(categoryId) {
    return this.findAll((product) => product.categoryId === categoryId);
  }
}

module.exports = new ProductRepository();
