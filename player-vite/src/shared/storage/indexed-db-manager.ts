/**
 * IndexedDB Manager
 * Wrapper for IndexedDB operations with schema support
 */

import { SharedLogger } from '../logger';
import { DB_NAME, DB_VERSION, SCHEMA } from './storage-schema';
import type { StorageEstimate, StoreData } from './indexed-db.types';

class IndexedDBManager {
  private db: IDBDatabase | null = null;

  /**
   * Open database connection
   */
  async open(): Promise<IDBDatabase> {
    if (this.db) return this.db;

    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onerror = () => reject(new Error(request.error?.message || 'Failed to open IndexedDB'));

      request.onsuccess = () => {
        this.db = request.result;
        SharedLogger.log('IndexedDB opened successfully');
        resolve(this.db);
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;
        SharedLogger.log('Upgrading IndexedDB schema...');
        this.createStores(db);
      };
    });
  }

  /**
   * Create object stores based on schema
   */
  private createStores(db: IDBDatabase): void {
    Object.entries(SCHEMA).forEach(([storeName, config]) => {
      // Skip if store already exists
      if (db.objectStoreNames.contains(storeName)) {
        SharedLogger.log(`Store ${storeName} already exists`);
        return;
      }

      // Create object store
      const store = db.createObjectStore(storeName, {
        keyPath: config.keyPath,
        autoIncrement: config.autoIncrement || false,
      });

      // Create indexes
      if (config.indexes) {
        config.indexes.forEach((index) => {
          store.createIndex(index.name, index.keyPath, {
            unique: index.unique || false,
          });
          SharedLogger.log(`Created index ${index.name} on ${storeName}`);
        });
      }

      SharedLogger.log(`Created store: ${storeName}`);
    });
  }

  /**
   * Get data from store by key
   */
  async get<T = StoreData>(storeName: string, key: IDBValidKey): Promise<T | undefined> {
    const db = await this.open();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(storeName, 'readonly');
      const store = tx.objectStore(storeName);
      const request = store.get(key);

      request.onsuccess = () => resolve(request.result as T | undefined);
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Get all data from store
   */
  async getAll<T = StoreData>(storeName: string): Promise<T[]> {
    const db = await this.open();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(storeName, 'readonly');
      const store = tx.objectStore(storeName);
      const request = store.getAll();

      request.onsuccess = () => resolve(request.result as T[]);
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Put data to store (insert or update)
   */
  async put<T = StoreData>(storeName: string, data: T): Promise<IDBValidKey> {
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
   */
  async add<T = StoreData>(storeName: string, data: T): Promise<IDBValidKey> {
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
   */
  async delete(storeName: string, key: IDBValidKey): Promise<void> {
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
   */
  async clear(storeName: string): Promise<void> {
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
   */
  async getByIndex<T = StoreData>(
    storeName: string,
    indexName: string,
    value: IDBValidKey
  ): Promise<T | undefined> {
    const db = await this.open();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(storeName, 'readonly');
      const store = tx.objectStore(storeName);
      const index = store.index(indexName);
      const request = index.get(value);

      request.onsuccess = () => resolve(request.result as T | undefined);
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Query all by index
   */
  async getAllByIndex<T = StoreData>(
    storeName: string,
    indexName: string,
    value?: IDBValidKey
  ): Promise<T[]> {
    const db = await this.open();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(storeName, 'readonly');
      const store = tx.objectStore(storeName);
      const index = store.index(indexName);
      const request = value !== undefined ? index.getAll(value) : index.getAll();

      request.onsuccess = () => resolve(request.result as T[]);
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Count records in store
   */
  async count(storeName: string): Promise<number> {
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
   * Batch put operation (optimized for bulk inserts)
   */
  async putBatch<T = StoreData>(storeName: string, dataArray: T[]): Promise<number> {
    if (!Array.isArray(dataArray) || dataArray.length === 0) {
      return 0;
    }

    const db = await this.open();
    const startTime = performance.now();

    return new Promise((resolve, reject) => {
      const tx = db.transaction(storeName, 'readwrite');
      const store = tx.objectStore(storeName);
      let insertCount = 0;

      // Queue all puts in single transaction
      dataArray.forEach((data) => {
        const request = store.put(data);
        request.onsuccess = () => insertCount++;
      });

      // Transaction completion
      tx.oncomplete = () => {
        const duration = Math.round(performance.now() - startTime);
        SharedLogger.log(`[IndexedDB] Batch put ${insertCount} records to ${storeName} (${duration}ms)`);
        resolve(insertCount);
      };

      tx.onerror = () => {
        SharedLogger.error('[IndexedDB] Batch put failed:', tx.error);
        reject(tx.error);
      };
    });
  }

  /**
   * Batch delete operation (optimized for bulk deletes)
   */
  async deleteBatch(storeName: string, keysArray: IDBValidKey[]): Promise<number> {
    if (!Array.isArray(keysArray) || keysArray.length === 0) {
      return 0;
    }

    const db = await this.open();
    const startTime = performance.now();

    return new Promise((resolve, reject) => {
      const tx = db.transaction(storeName, 'readwrite');
      const store = tx.objectStore(storeName);
      let deleteCount = 0;

      // Queue all deletes in single transaction
      keysArray.forEach((key) => {
        const request = store.delete(key);
        request.onsuccess = () => deleteCount++;
      });

      // Transaction completion
      tx.oncomplete = () => {
        const duration = Math.round(performance.now() - startTime);
        SharedLogger.log(
          `[IndexedDB] Batch delete ${deleteCount} records from ${storeName} (${duration}ms)`
        );
        resolve(deleteCount);
      };

      tx.onerror = () => {
        SharedLogger.error('[IndexedDB] Batch delete failed:', tx.error);
        reject(tx.error);
      };
    });
  }

  /**
   * Get database size estimate
   */
  async getStorageEstimate(): Promise<StorageEstimate> {
    if ('storage' in navigator && 'estimate' in navigator.storage) {
      const estimate = await navigator.storage.estimate();
      return {
        usage: estimate.usage || 0,
        quota: estimate.quota || 0,
        percentage: estimate.quota ? Math.round(((estimate.usage || 0) / estimate.quota) * 100) : 0,
      };
    }

    // Fallback for browsers without storage API
    return { usage: 0, quota: 0, percentage: 0 };
  }

  /**
   * Close database connection
   */
  close(): void {
    if (this.db) {
      this.db.close();
      this.db = null;
      SharedLogger.log('IndexedDB closed');
    }
  }

  /**
   * Delete entire database
   */
  async deleteDatabase(): Promise<void> {
    this.close();
    return new Promise((resolve, reject) => {
      const request = indexedDB.deleteDatabase(DB_NAME);
      request.onsuccess = () => {
        SharedLogger.log('Database deleted');
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
