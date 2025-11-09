/**
 * IndexedDB Manager Type Definitions
 */

/**
 * Storage estimate information
 */
export interface StorageEstimate {
  usage: number;
  quota: number;
  percentage: number;
}

/**
 * Batch operation result
 */
export interface BatchOperationResult {
  count: number;
  duration: number;
}

/**
 * Generic type for store data
 */
export type StoreData = Record<string, unknown>;

/**
 * Transaction mode types
 */
export type TransactionMode = 'readonly' | 'readwrite';
