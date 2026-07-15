const BaseRepository = require('./base.repository');

class UserRepository extends BaseRepository {
  constructor() {
    super('users');
  }

  async findByEmail(email) {
    return this.findOne((user) => user.email.toLowerCase() === email.toLowerCase());
  }
}

module.exports = new UserRepository();
