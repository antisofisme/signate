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

    // API error response
    const data = error.response.data as APIErrorResponse;

    if (data && data.error) {
      const { message, code, details } = data.error;
      const statusCode = error.response.status;

      // Map to specific error type
      if (statusCode === 401) {
        return new AuthenticationError(getErrorMessage(code, message));
      }

      return new AppError(
        getErrorMessage(code, message),
        code,
        statusCode,
        details
      );
    }

    // Fallback for non-standard error response
    return new AppError(
      'Terjadi kesalahan pada server',
      'UNKNOWN_ERROR',
      error.response.status
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
