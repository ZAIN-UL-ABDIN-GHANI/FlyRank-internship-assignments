const BaseRepository = require('./base.repository');

class CategoryRepository extends BaseRepository {
  constructor() {
    super('categories');
  }
}

module.exports = new CategoryRepository();
