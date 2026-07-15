/**
 * User "model" — documents the shape of a User record.
 * Since this project uses an in-memory store instead of an ORM, this file
 * exists to describe the schema and provide a sanitizer that strips secrets
 * (like the password hash) before a user object is ever sent in a response.
 *
 * @typedef {Object} User
 * @property {string} id
 * @property {string} name
 * @property {string} email
 * @property {string} password - bcrypt hash, never returned to clients
 * @property {'user'|'admin'} role
 * @property {string} createdAt
 */

function toSafeUser(user) {
  if (!user) return null;
  const { password: _password, ...safe } = user;
  return safe;
}

module.exports = { toSafeUser };
