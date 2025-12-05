/**
 * Connection Log Storage
 * IndexedDB storage for connection activity logs with rotation
 * @updated 2025-11-21T12:22:00Z - Fixed getUnsentLogs to use cursor iteration
 *
 * @features
 * - Store network and server connection logs
 * - Automatic rotation (max 1000 entries OR 7 days)
 * - Track upload status (sent/unsent)
 * - Fast queries with indexes (using cursor to avoid boolean index issues)
 */

import { SharedLogger } from '@shared/logger';

export interface ConnectionLogEntry {
  id: string;                    // UUID
  timestamp: number;             // Unix timestamp (ms)
  eventType: 'network' | 'server' | 'speed_test' | 'playback';
  status: 'online' | 'offline' | 'connected' | 'disconnected' | 'tested' | 'stall' | 'buffer' | 'quality_switch' | 'load_fail' | 'play' | 'pause' | 'error' | 'started' | 'completed';

  // Optional fields
  latencyMs?: number;            // Ping latency
  errorMessage?: string;         // Error details if failed

  // Speed test data
  downloadSpeedMbps?: number;    // Download speed in Mbps
  uploadSpeedMbps?: number;      // Upload speed in Mbps

  // Metadata
  metadata?: Record<string, any>; // Additional context

  // Upload tracking
  isSent: boolean;               // Has been uploaded to server?
}

class ConnectionLogStorageClass {
  private readonly DB_NAME = 'player-connection-logs';
  private readonly STORE_NAME = 'logs';
  private readonly DB_VERSION = 1;

  private readonly MAX_ENTRIES = 1000;  // Keep last 1000 logs
  private readonly MAX_AGE_MS = 7 * 24 * 60 * 60 * 1000; // 7 days

  private db: IDBDatabase | null = null;

  /**
   * Initialize IndexedDB
   */
  async init(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.DB_NAME, this.DB_VERSION);

      request.onerror = () => {
        SharedLogger.error('[ConnectionLogStorage] Failed to open DB:', request.error);
        reject(request.error);
      };

      request.onsuccess = () => {
        this.db = request.result;
        SharedLogger.log('[ConnectionLogStorage] ✅ Initialized');
        resolve();
      };

      request.onupgradeneeded = (event: IDBVersionChangeEvent) => {
        const db = (event.target as IDBOpenDBRequest).result;

        // Create object store if doesn't exist
        if (!db.objectStoreNames.contains(this.STORE_NAME)) {
          const store = db.createObjectStore(this.STORE_NAME, { keyPath: 'id' });

          // Create indexes for fast queries
          store.createIndex('timestamp', 'timestamp', { unique: false });
          store.createIndex('eventType', 'eventType', { unique: false });
          store.createIndex('isSent', 'isSent', { unique: false });
          store.createIndex('timestamp_eventType', ['timestamp', 'eventType'], { unique: false });

          SharedLogger.log('[ConnectionLogStorage] Created object store with indexes');
        }
      };
    });
  }

  /**
   * Add a log entry
   */
  async addLog(log: ConnectionLogEntry): Promise<void> {
    if (!this.db) {
      await this.init();
    }

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(this.STORE_NAME, 'readwrite');
      const store = transaction.objectStore(this.STORE_NAME);

      const request = store.add(log);

      request.onsuccess = async () => {
        SharedLogger.log(`[ConnectionLogStorage] Added log: ${log.eventType} - ${log.status}`);

        // Rotate old logs after adding new one
        await this.rotateOldLogs();
        resolve();
      };

      request.onerror = () => {
        SharedLogger.error('[ConnectionLogStorage] Failed to add log:', request.error);
        reject(request.error);
      };
    });
  }

  /**
   * Get recent logs (sorted by timestamp DESC)
   */
  async getLogs(limit = 100, eventTypeFilter?: 'network' | 'server' | 'speed_test' | 'playback'): Promise<ConnectionLogEntry[]> {
    if (!this.db) {
      await this.init();
    }

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(this.STORE_NAME, 'readonly');
      const store = transaction.objectStore(this.STORE_NAME);

      const logs: ConnectionLogEntry[] = [];
      let request: IDBRequest;

      if (eventTypeFilter) {
        // Use index if filtering by eventType
        const index = store.index('eventType');
        request = index.openCursor(IDBKeyRange.only(eventTypeFilter), 'prev');
      } else {
        // Get all logs, sorted by timestamp DESC
        const index = store.index('timestamp');
        request = index.openCursor(null, 'prev');
      }

      request.onsuccess = (event) => {
        const cursor = (event.target as IDBRequest<IDBCursorWithValue>).result;

        if (cursor && logs.length < limit) {
          logs.push(cursor.value);
          cursor.continue();
        } else {
          resolve(logs);
        }
      };

      request.onerror = () => {
        SharedLogger.error('[ConnectionLogStorage] Failed to get logs:', request.error);
        reject(request.error);
      };
    });
  }

  /**
   * Get unsent logs (for batch upload)
   * Uses cursor iteration to avoid browser-specific IDBKeyRange issues with boolean values
   */
  async getUnsentLogs(): Promise<ConnectionLogEntry[]> {
    if (!this.db) {
      await this.init();
    }

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(this.STORE_NAME, 'readonly');
      const store = transaction.objectStore(this.STORE_NAME);

      // Use cursor iteration instead of index query to avoid DataError in some browsers
      const logs: ConnectionLogEntry[] = [];
      const request = store.openCursor();

      request.onsuccess = (event) => {
        const cursor = (event.target as IDBRequest<IDBCursorWithValue>).result;

        if (cursor) {
          const log = cursor.value as ConnectionLogEntry;
          // Manually filter for unsent logs (isSent === false or undefined)
          if (log.isSent === false || log.isSent === undefined) {
            logs.push(log);
          }
          cursor.continue();
        } else {
          // All records processed
          SharedLogger.log(`[ConnectionLogStorage] Found ${logs.length} unsent logs`);
          resolve(logs);
        }
      };

      request.onerror = () => {
        SharedLogger.error('[ConnectionLogStorage] Failed to get unsent logs:', request.error);
        reject(request.error);
      };
    });
  }

  /**
   * Mark logs as sent to server
   */
  async markAsSent(ids: string[]): Promise<void> {
    if (!this.db) {
      await this.init();
    }

    return new Promise((resolve) => {
      const transaction = this.db!.transaction(this.STORE_NAME, 'readwrite');
      const store = transaction.objectStore(this.STORE_NAME);

      let completed = 0;
      let errors = 0;

      ids.forEach(id => {
        const getRequest = store.get(id);

        getRequest.onsuccess = () => {
          const log = getRequest.result as ConnectionLogEntry;
          if (log) {
            log.isSent = true;
            const putRequest = store.put(log);

            putRequest.onsuccess = () => {
              completed++;
              if (completed + errors === ids.length) {
                SharedLogger.log(`[ConnectionLogStorage] Marked ${completed} logs as sent`);
                resolve();
              }
            };

            putRequest.onerror = () => {
              errors++;
              if (completed + errors === ids.length) {
                resolve();
              }
            };
          } else {
            errors++;
            if (completed + errors === ids.length) {
              resolve();
            }
          }
        };
      });

      if (ids.length === 0) {
        resolve();
      }
    });
  }

  /**
   * Rotate old logs (delete if > MAX_ENTRIES or > MAX_AGE_MS)
   */
  async rotateOldLogs(): Promise<void> {
    if (!this.db) {
      return;
    }

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(this.STORE_NAME, 'readwrite');
      const store = transaction.objectStore(this.STORE_NAME);
      const index = store.index('timestamp');

      // Get all logs sorted by timestamp ASC (oldest first)
      const request = index.openCursor(null, 'next');

      const logs: { id: string; timestamp: number }[] = [];

      request.onsuccess = (event) => {
        const cursor = (event.target as IDBRequest<IDBCursorWithValue>).result;

        if (cursor) {
          logs.push({
            id: cursor.value.id,
            timestamp: cursor.value.timestamp
          });
          cursor.continue();
        } else {
          // All logs collected, now rotate
          const now = Date.now();
          const cutoffTime = now - this.MAX_AGE_MS;
          let deleteCount = 0;

          // Delete logs older than MAX_AGE_MS
          logs.forEach(log => {
            if (log.timestamp < cutoffTime) {
              store.delete(log.id);
              deleteCount++;
            }
          });

          // If still > MAX_ENTRIES, delete oldest
          const remainingCount = logs.length - deleteCount;
          if (remainingCount > this.MAX_ENTRIES) {
            const toDelete = remainingCount - this.MAX_ENTRIES;
            logs.slice(deleteCount, deleteCount + toDelete).forEach(log => {
              store.delete(log.id);
              deleteCount++;
            });
          }

          if (deleteCount > 0) {
            SharedLogger.log(`[ConnectionLogStorage] Rotated ${deleteCount} old logs`);
          }

          resolve();
        }
      };

      request.onerror = () => {
        SharedLogger.error('[ConnectionLogStorage] Failed to rotate logs:', request.error);
        reject(request.error);
      };
    });
  }

  /**
   * Get total log count
   */
  async getCount(): Promise<number> {
    if (!this.db) {
      await this.init();
    }

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(this.STORE_NAME, 'readonly');
      const store = transaction.objectStore(this.STORE_NAME);

      const request = store.count();

      request.onsuccess = () => {
        resolve(request.result);
      };

      request.onerror = () => {
        SharedLogger.error('[ConnectionLogStorage] Failed to get count:', request.error);
        reject(request.error);
      };
    });
  }

  /**
   * Clear all logs (for testing/debugging)
   */
  async clearAll(): Promise<void> {
    if (!this.db) {
      await this.init();
    }

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(this.STORE_NAME, 'readwrite');
      const store = transaction.objectStore(this.STORE_NAME);

      const request = store.clear();

      request.onsuccess = () => {
        SharedLogger.log('[ConnectionLogStorage] ✅ All logs cleared');
        resolve();
      };

      request.onerror = () => {
        SharedLogger.error('[ConnectionLogStorage] Failed to clear logs:', request.error);
        reject(request.error);
      };
    });
  }
}

// Export singleton instance
export const ConnectionLogStorage = new ConnectionLogStorageClass();

// Make available globally for debugging
if (typeof window !== 'undefined') {
  (window as any).ConnectionLogStorage = ConnectionLogStorage;
}
