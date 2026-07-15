const PostgresRepository = require('./postgres.repository');

class OrderRepository extends PostgresRepository {
  constructor() {
    super('orders');
  }

  async findByUser(userId) {
    return this.findAll((order) => order.userId === userId);
  }
}

module.exports = new OrderRepository();
