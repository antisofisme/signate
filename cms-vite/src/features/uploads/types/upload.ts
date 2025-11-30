/**
 * Upload Queue Types
 *
 * Defines types for the upload queue manager feature.
 */

/**
 * Status of an upload item
 */
export type UploadStatus =
  | 'pending'      // Waiting in queue
  | 'uploading'    // Currently uploading
  | 'completed'    // Successfully uploaded
  | 'failed'       // Upload failed
  | 'cancelled';   // User cancelled

/**
 * Content type for uploaded file
 */
export type UploadContentType = 'image' | 'video' | 'audio';

/**
 * Single upload item in the queue
 */
export interface UploadItem {
  /** Unique identifier (UUID) */
  id: string;

  /** File object (NOT persisted to localStorage) */
  file?: File;

  /** Original filename */
  fileName: string;

  /** File size in bytes */
  fileSize: number;

  /** Content type */
  fileType: UploadContentType;

  /** MIME type */
  mimeType: string;

  // Upload settings
  /** Display duration in seconds */
  duration: number;

  /** Whether content is active on upload */
  isActive: boolean;

  // Progress tracking
  /** Current status */
  status: UploadStatus;

  /** Upload progress (0-100) */
  progress: number;

  /** Bytes uploaded so far */
  uploadedBytes: number;

  // Timestamps
  /** When item was added to queue */
  createdAt: number;

  /** When upload started */
  startedAt?: number;

  /** When upload completed */
  completedAt?: number;

  // Error handling
  /** Error message if failed */
  error?: string;

  /** Number of retry attempts */
  retryCount: number;

  // Result after success
  /** Content ID from backend */
  contentId?: number;

  // Cancellation (NOT persisted)
  /** AbortController for cancellation */
  abortController?: AbortController;
}

/**
 * Queue settings
 */
export interface QueueSettings {
  /** Maximum concurrent uploads (default: 1) */
  maxConcurrent: number;

  /** Maximum retry attempts (default: 3) */
  maxRetries: number;

  /** Auto-clear completed items (default: true) */
  autoClearCompleted: boolean;

  /** Delay before clearing completed items in ms (default: 30000) */
  clearCompletedDelay: number;
}

/**
 * Queue summary statistics
 */
export interface QueueSummary {
  /** Total items in queue */
  total: number;

  /** Items waiting */
  pending: number;

  /** Items currently uploading */
  uploading: number;

  /** Items completed successfully */
  completed: number;

  /** Items that failed */
  failed: number;

  /** Items cancelled by user */
  cancelled: number;

  /** Overall progress (0-100) */
  overallProgress: number;

  /** Total bytes to upload */
  totalBytes: number;

  /** Bytes uploaded so far */
  uploadedBytes: number;
}

/**
 * Upload queue state
 */
export interface UploadQueueState {
  /** List of upload items */
  items: UploadItem[];

  /** Queue settings */
  settings: QueueSettings;

  /** Whether panel is minimized */
  isMinimized: boolean;

  /** Whether queue is currently processing */
  isProcessing: boolean;
}

/**
 * Options for adding files to queue
 */
export interface AddToQueueOptions {
  /** Display duration in seconds */
  duration: number;

  /** Whether content is active */
  isActive: boolean;
}

/**
 * Default queue settings
 */
export const DEFAULT_QUEUE_SETTINGS: QueueSettings = {
  maxConcurrent: 1,
  maxRetries: 3,
  autoClearCompleted: true,
  clearCompletedDelay: 30000, // 30 seconds
};

/**
 * Helper to detect content type from MIME type
 */
export function getContentTypeFromMime(mimeType: string): UploadContentType {
  if (mimeType.startsWith('image/')) return 'image';
  if (mimeType.startsWith('video/')) return 'video';
  if (mimeType.startsWith('audio/')) return 'audio';
  return 'image'; // fallback
}

/**
 * Helper to format file size
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Generate UUID using crypto API
 */
export function generateId(): string {
  return crypto.randomUUID();
}
