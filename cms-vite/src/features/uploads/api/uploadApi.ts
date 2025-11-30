/**
 * Upload Queue API Service
 *
 * Single-file upload with AbortController support for cancellation
 */

import { apiClient } from '@/lib/api/client';
import { API_ENDPOINTS } from '@/lib/api/endpoints';
import type { Content } from '@/features/contents/types/content';

/**
 * Progress callback type
 */
export type ProgressCallback = (progress: number, uploadedBytes: number) => void;

/**
 * Upload response type
 *
 * Note: The apiClient interceptor unwraps the response,
 * so we receive the Content directly, not wrapped in { success, data, message }
 */
export type SingleUploadResponse = Content;

/**
 * Upload a single file with progress tracking and cancellation support
 *
 * @param file - File to upload
 * @param options - Upload options (duration, is_active)
 * @param onProgress - Progress callback (progress: 0-100, uploadedBytes)
 * @param signal - AbortSignal for cancellation
 * @returns Promise with upload response
 */
export async function uploadSingleContent(
  file: File,
  options: { duration: number; is_active: boolean },
  onProgress?: ProgressCallback,
  signal?: AbortSignal
): Promise<SingleUploadResponse> {
  const formData = new FormData();

  // Append file
  formData.append('file', file);

  // Use filename as title (can be edited later)
  const title = file.name.replace(/\.[^/.]+$/, ''); // Remove extension
  formData.append('title', title);

  // Append options
  formData.append('duration', String(options.duration));
  formData.append('is_active', String(options.is_active));

  const response = await apiClient.post<SingleUploadResponse>(
    API_ENDPOINTS.CONTENT.UPLOAD,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 600000, // 10 minutes timeout for large file uploads
      signal, // AbortSignal for cancellation
      onUploadProgress: (event) => {
        if (onProgress && event.total) {
          const progress = Math.round((event.loaded * 100) / event.total);
          onProgress(progress, event.loaded);
        }
      },
    }
  );

  return response.data;
}

/**
 * Check if an error is due to cancellation
 */
export function isAbortError(error: unknown): boolean {
  if (error instanceof Error) {
    return error.name === 'AbortError' || error.name === 'CanceledError';
  }
  return false;
}

/**
 * Check if error is a permanent failure (should NOT retry)
 *
 * 400: Bad Request (validation, duplicate file)
 * 401: Unauthorized
 * 403: Forbidden
 * 413: Payload Too Large
 * 415: Unsupported Media Type
 */
export function isPermanentError(error: unknown): boolean {
  if (error instanceof Error && 'response' in error && error.response) {
    const response = error.response as { status?: number };
    const status = response.status;
    // 4xx errors (except 408 Request Timeout, 429 Too Many Requests)
    return status !== undefined && status >= 400 && status < 500 && status !== 408 && status !== 429;
  }
  return false;
}

/**
 * Get error message from various error types
 *
 * Handles:
 * - FastAPI format: { detail: "error message" }
 * - Standard format: { message: "error message" }
 * - Legacy format: { error: "error message" }
 */
export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    // Axios error with response
    if ('response' in error && error.response) {
      const response = error.response as {
        data?: {
          detail?: string;  // FastAPI format
          message?: string;
          error?: string
        }
      };

      // Try all possible error message fields
      const errorMessage =
        response.data?.detail ||    // FastAPI standard
        response.data?.message ||   // Common format
        response.data?.error;       // Legacy format

      if (errorMessage) {
        return errorMessage;
      }

      return error.message;
    }
    return error.message;
  }
  return 'Unknown error occurred';
}
