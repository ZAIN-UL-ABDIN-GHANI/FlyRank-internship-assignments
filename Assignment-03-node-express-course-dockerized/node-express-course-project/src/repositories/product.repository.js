const PostgresRepository = require('./postgres.repository');

class ProductRepository extends PostgresRepository {
  constructor() {
    super('products');
  }

  async findByCategory(categoryId) {
    return this.findAll((product) => product.categoryId === categoryId);
  }
}

module.exports = new ProductRepository();
