const PostgresRepository = require('./postgres.repository');

class CategoryRepository extends PostgresRepository {
  constructor() {
    super('categories');
  }
}

module.exports = new CategoryRepository();
