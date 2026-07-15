/**
 * Base repository — the "Repository Interface" every concrete repository
 * implements. It encapsulates ALL access to a single in-memory collection
 * (a Map) so services never touch storage directly.
 *
 * Swapping storage engines later (e.g. Postgres) means writing a new class
 * with these exact same method signatures — nothing above this layer changes.
 */
const { collections, uuid } = require('../database/inMemoryStore');

class BaseRepository {
  /**
   * @param {keyof typeof collections} collectionName
   */
  constructor(collectionName) {
    if (!collections[collectionName]) {
      throw new Error(`Unknown collection: ${collectionName}`);
    }
    this.collection = collections[collectionName];
  }

  async findAll(filterFn) {
    const all = Array.from(this.collection.values());
    return typeof filterFn === 'function' ? all.filter(filterFn) : all;
  }

  async findById(id) {
    return this.collection.get(id) || null;
  }

  async findOne(predicate) {
    return Array.from(this.collection.values()).find(predicate) || null;
  }

  async create(data) {
    const id = uuid();
    const record = { id, ...data, createdAt: new Date().toISOString() };
    this.collection.set(id, record);
    return record;
  }

  async update(id, data) {
    const existing = this.collection.get(id);
    if (!existing) return null;
    const updated = { ...existing, ...data, id, updatedAt: new Date().toISOString() };
    this.collection.set(id, updated);
    return updated;
  }

  async remove(id) {
    const existing = this.collection.get(id);
    if (!existing) return null;
    this.collection.delete(id);
    return existing;
  }
}

module.exports = BaseRepository;
