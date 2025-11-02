/**
 * IndexedDB Manager
 * Wrapper for IndexedDB operations with schema support
 */

import { DB_NAME, DB_VERSION, SCHEMA } from './schema.js';

class IndexedDBManager {
  constructor() {
    this.db = null;
  }

  /**
   * Open database connection
   * @returns {Promise<IDBDatabase>}
   */
  async open() {
    if (this.db) return this.db;

    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onerror = () => reject(new Error(request.error));
      
      request.onsuccess = () => {
        this.db = request.result;
        console.log('IndexedDB opened successfully');
        resolve(this.db);
      };

      request.onupgradeneeded = (event) => {
        const db = event.target.result;
        console.log('Upgrading IndexedDB schema...');
        this.createStores(db);
      };
    });
  }

  /**
   * Create object stores based on schema
   * @param {IDBDatabase} db
   */
  createStores(db) {
    Object.entries(SCHEMA).forEach(([storeName, config]) => {
      // Skip if store already exists
      if (db.objectStoreNames.contains(storeName)) {
        console.log(`Store ${storeName} already exists`);
        return;
      }

      // Create object store
      const store = db.createObjectStore(storeName, {
        keyPath: config.keyPath,
        autoIncrement: config.autoIncrement || false,
      });

      // Create indexes
      if (config.indexes) {
        config.indexes.forEach(index => {
          store.createIndex(index.name, index.keyPath, {
            unique: index.unique || false,
          });
          console.log(`Created index ${index.name} on ${storeName}`);
        });
      }

      console.log(`Created store: ${storeName}`);
    });
  }

  /**
   * Get data from store by key
   * @param {string} storeName
   * @param {*} key
   * @returns {Promise<any>}
   */
  async get(storeName, key) {
    const db = await this.open();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(storeName, 'readonly');
      const store = tx.objectStore(storeName);
      const request = store.get(key);

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Get all data from store
   * @param {string} storeName
   * @returns {Promise<Array>}
   */
  async getAll(storeName) {
    const db = await this.open();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(storeName, 'readonly');
      const store = tx.objectStore(storeName);
      const request = store.getAll();

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Put data to store (insert or update)
   * @param {string} storeName
   * @param {*} data
   * @returns {Promise<any>} Key of inserted/updated record
   */
  async put(storeName, data) {
    const db = await this.open();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(storeName, 'readwrite');
      const store = tx.objectStore(storeName);
      const request = store.put(data);

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Add data to store (insert only, fails if exists)
   * @param {string} storeName
   * @param {*} data
   * @returns {Promise<any>}
   */
  async add(storeName, data) {
    const db = await this.open();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(storeName, 'readwrite');
      const store = tx.objectStore(storeName);
      const request = store.add(data);

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Delete data from store
   * @param {string} storeName
   * @param {*} key
   * @returns {Promise<void>}
   */
  async delete(storeName, key) {
    const db = await this.open();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(storeName, 'readwrite');
      const store = tx.objectStore(storeName);
      const request = store.delete(key);

      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Clear all data from store
   * @param {string} storeName
   * @returns {Promise<void>}
   */
  async clear(storeName) {
    const db = await this.open();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(storeName, 'readwrite');
      const store = tx.objectStore(storeName);
      const request = store.clear();

      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Query by index
   * @param {string} storeName
   * @param {string} indexName
   * @param {*} value
   * @returns {Promise<any>}
   */
  async getByIndex(storeName, indexName, value) {
    const db = await this.open();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(storeName, 'readonly');
      const store = tx.objectStore(storeName);
      const index = store.index(indexName);
      const request = index.get(value);

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Query all by index
   * @param {string} storeName
   * @param {string} indexName
   * @param {*} value
   * @returns {Promise<Array>}
   */
  async getAllByIndex(storeName, indexName, value) {
    const db = await this.open();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(storeName, 'readonly');
      const store = tx.objectStore(storeName);
      const index = store.index(indexName);
      const request = index.getAll(value);

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Count records in store
   * @param {string} storeName
   * @returns {Promise<number>}
   */
  async count(storeName) {
    const db = await this.open();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(storeName, 'readonly');
      const store = tx.objectStore(storeName);
      const request = store.count();

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Close database connection
   */
  close() {
    if (this.db) {
      this.db.close();
      this.db = null;
      console.log('IndexedDB closed');
    }
  }

  /**
   * Delete entire database
   * @returns {Promise<void>}
   */
  async deleteDatabase() {
    this.close();
    return new Promise((resolve, reject) => {
      const request = indexedDB.deleteDatabase(DB_NAME);
      request.onsuccess = () => {
        console.log('Database deleted');
        resolve();
      };
      request.onerror = () => reject(request.error);
    });
  }
}

// Export singleton instance
export const dbManager = new IndexedDBManager();

// Export class for testing
export { IndexedDBManager };

