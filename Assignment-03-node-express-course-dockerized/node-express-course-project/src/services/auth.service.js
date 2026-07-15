/**
 * Auth service — business logic for registration, login, and token issuing.
 * Controllers never talk to the repository directly; they go through here.
 */
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const userRepository = require('../repositories/user.repository');
const ApiError = require('../utils/ApiError');
const config = require('../config/env');
const { toSafeUser } = require('../models/user.model');
const roles = require('../constants/roles');

function signToken(user) {
  return jwt.sign({ id: user.id, email: user.email, role: user.role }, config.jwt.secret, {
    expiresIn: config.jwt.expiresIn,
  });
}

async function register({ name, email, password }) {
  const existing = await userRepository.findByEmail(email);
  if (existing) {
    throw ApiError.conflict('An account with this email already exists');
  }

  const hashed = await bcrypt.hash(password, 10);
  const user = await userRepository.create({
    name,
    email,
    password: hashed,
    role: roles.USER,
  });

  const token = signToken(user);
  return { user: toSafeUser(user), token };
}

async function login({ email, password }) {
  const user = await userRepository.findByEmail(email);
  if (!user) {
    throw ApiError.unauthorized('Invalid email or password');
  }

  const matches = await bcrypt.compare(password, user.password);
  if (!matches) {
    throw ApiError.unauthorized('Invalid email or password');
  }

  const token = signToken(user);
  return { user: toSafeUser(user), token };
}

async function getProfile(userId) {
  const user = await userRepository.findById(userId);
  if (!user) {
    throw ApiError.notFound('User not found');
  }
  return toSafeUser(user);
}

module.exports = { register, login, getProfile };
