/**
 * In-memory "database".
 *
 * This module simulates a database using plain JS Maps, keyed by id.
 * It exists purely so the rest of the app (controllers, services) never
 * has to know or care what storage engine is behind the repositories.
 *
 * --- Swapping this for PostgreSQL later ---
 * Because every repository implements the same interface
 * (findAll, findById, create, update, remove) against this store, moving to
 * Postgres later only means writing a new repository per resource (e.g.
 * PostgresUserRepository using `pg` or an ORM like Prisma/Sequelize) that
 * implements the exact same methods. Nothing in services/controllers changes:
 *
 *   Controller -> Service -> Repository Interface -> [Memory | Postgres] Repository
 */
const { v4: uuid } = require('uuid');

const collections = {
  users: new Map(),
  products: new Map(),
  categories: new Map(),
  orders: new Map(),
  reviews: new Map(),
};

function seed() {
  const bcrypt = require('bcryptjs');

  const adminId = uuid();
  collections.users.set(adminId, {
    id: adminId,
    name: 'Admin User',
    email: 'admin@example.com',
    password: bcrypt.hashSync('Admin123!', 10),
    role: 'admin',
    createdAt: new Date().toISOString(),
  });

  const categoryElectronics = uuid();
  const categoryBooks = uuid();
  collections.categories.set(categoryElectronics, {
    id: categoryElectronics,
    name: 'Electronics',
    description: 'Gadgets, devices, and accessories',
    createdAt: new Date().toISOString(),
  });
  collections.categories.set(categoryBooks, {
    id: categoryBooks,
    name: 'Books',
    description: 'Fiction and non-fiction books',
    createdAt: new Date().toISOString(),
  });

  const productHeadphones = uuid();
  collections.products.set(productHeadphones, {
    id: productHeadphones,
    name: 'Wireless Headphones',
    description: 'Noise-cancelling over-ear wireless headphones',
    price: 129.99,
    stock: 42,
    categoryId: categoryElectronics,
    createdAt: new Date().toISOString(),
  });

  const productNovel = uuid();
  collections.products.set(productNovel, {
    id: productNovel,
    name: 'The Pragmatic Programmer',
    description: 'A classic book on software craftsmanship',
    price: 34.5,
    stock: 15,
    categoryId: categoryBooks,
    createdAt: new Date().toISOString(),
  });

  return { adminId, categoryElectronics, categoryBooks, productHeadphones, productNovel };
}

const seedIds = seed();

module.exports = { collections, uuid, seedIds };
