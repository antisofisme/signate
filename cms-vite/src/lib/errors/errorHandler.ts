/**
 * Error Handler
 * Centralized error handling logic
 */

import { AxiosError } from 'axios';
import { APIErrorResponse, AppError, NetworkError, AuthenticationError } from './apiErrors';
import { getErrorMessage } from './errorMessages';

export function handleAPIError(error: unknown): AppError {
  // Axios error
  if (error instanceof AxiosError) {
    // Network error (no response)
    if (!error.response) {
      return new NetworkError('Tidak dapat terhubung ke server');
    }

    const statusCode = error.response.status;
    const data = error.response.data as any;

    // Extract error info from various response formats
    let message: string | undefined;
    let code: string | undefined;
    let details: Record<string, any> | undefined;

    // Format 1: Standard API response { error: { message, code, details } }
    if (data?.error) {
      message = data.error.message;
      code = data.error.code;
      details = data.error.details;
    }
    // Format 2: FastAPI HTTPException { detail: { message, code, details } }
    else if (data?.detail && typeof data.detail === 'object') {
      message = data.detail.message;
      code = data.detail.code;
      details = data.detail.details;
    }
    // Format 3: Simple string detail { detail: "error message" }
    else if (data?.detail && typeof data.detail === 'string') {
      message = data.detail;
      code = 'API_ERROR';
    }
    // Format 4: Direct message { message: "error message" }
    else if (data?.message) {
      message = data.message;
      code = data.code || 'API_ERROR';
      details = data.details;
    }

    // If we extracted error info, create appropriate error
    if (message) {
      // Map to specific error type
      if (statusCode === 401) {
        return new AuthenticationError(getErrorMessage(code || 'AUTHENTICATION_ERROR', message));
      }

      return new AppError(
        getErrorMessage(code || 'API_ERROR', message),
        code || 'API_ERROR',
        statusCode,
        details
      );
    }

    // Fallback for non-standard error response
    return new AppError(
      'Terjadi kesalahan pada server',
      'UNKNOWN_ERROR',
      statusCode
    );
  }

  // Already an AppError
  if (error instanceof AppError) {
    return error;
  }

  // Generic error
  if (error instanceof Error) {
    return new AppError(error.message, 'GENERIC_ERROR');
  }

  // Unknown error
  return new AppError('Terjadi kesalahan yang tidak diketahui', 'UNKNOWN_ERROR');
}

export function logError(error: AppError, context?: Record<string, any>): void {
  console.error('[Error]', {
    message: error.message,
    code: error.code,
    statusCode: error.statusCode,
    details: error.details,
    context,
    timestamp: new Date().toISOString(),
  });
}
