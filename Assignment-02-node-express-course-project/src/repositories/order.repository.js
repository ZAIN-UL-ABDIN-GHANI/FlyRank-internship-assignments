const BaseRepository = require('./base.repository');

class OrderRepository extends BaseRepository {
  constructor() {
    super('orders');
  }

  async findByUser(userId) {
    return this.findAll((order) => order.userId === userId);
  }
}

module.exports = new OrderRepository();
