const PostgresRepository = require('./postgres.repository');

class UserRepository extends PostgresRepository {
  constructor() {
    super('users');
  }

  async findByEmail(email) {
    return this.findOne((user) => user.email.toLowerCase() === email.toLowerCase());
  }
}

module.exports = new UserRepository();
