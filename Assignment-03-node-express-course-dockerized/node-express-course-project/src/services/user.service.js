const userRepository = require('../repositories/user.repository');
const ApiError = require('../utils/ApiError');
const { toSafeUser } = require('../models/user.model');

async function listUsers() {
  const users = await userRepository.findAll();
  return users.map(toSafeUser);
}

async function getUser(id) {
  const user = await userRepository.findById(id);
  if (!user) throw ApiError.notFound('User not found');
  return toSafeUser(user);
}

async function updateUser(id, data) {
  const user = await userRepository.findById(id);
  if (!user) throw ApiError.notFound('User not found');

  // Never allow role or password to be changed through this generic endpoint
  const { role: _role, password: _password, ...safeData } = data;
  const updated = await userRepository.update(id, safeData);
  return toSafeUser(updated);
}

async function deleteUser(id) {
  const user = await userRepository.findById(id);
  if (!user) throw ApiError.notFound('User not found');
  await userRepository.remove(id);
}

module.exports = { listUsers, getUser, updateUser, deleteUser };
