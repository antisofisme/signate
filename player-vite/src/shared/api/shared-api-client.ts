/**
 * Shared API Client
 * Lightweight wrapper for standardized backend API responses
 *
 * @features
 * - Auto-unwrapping of standardized responses
 * - Backward compatible with legacy format
 * - Type-safe with TypeScript generics
 * - Automatic JWT token injection
 * - Enhanced error handling with context
 * - Request tracing with unique IDs
 * - Debug mode for verbose logging
 */

import { config } from '@shared/config';
import { SharedLogger } from '@shared/logger';
import type { APIClient, APIResponse, RequestOptions, APIError } from './api-client.types';

/**
 * Shared API Client Class
 * Singleton pattern for centralized API communication
 */
class SharedAPIClientClass implements APIClient {
  /**
   * Execute fetch request with automatic response unwrapping
   */
  async request<T = unknown>(url: string, options: RequestOptions = {}): Promise<T> {
    const startTime = performance.now();
    const requestId = this.generateRequestId();

    // Default headers
    const defaultHeaders: HeadersInit = {
      'Content-Type': 'application/json',
    };

    // Add Authorization header if device token exists (unless skipped)
    if (!options.skipAuth) {
      const deviceToken = localStorage.getItem('device_token');
      if (deviceToken) {
        defaultHeaders.Authorization = `Bearer ${deviceToken}`;
      }
    }

    // Merge options with defaults
    const requestOptions: RequestInit = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...(options.headers || {}),
      },
    };

    // Remove custom skipAuth flag
    delete (requestOptions as RequestOptions).skipAuth;

    // Log outgoing request (debug mode)
    this.logRequest(requestId, url, requestOptions);

    try {
      const response = await fetch(url, requestOptions);
      const duration = Math.round(performance.now() - startTime);

      // Handle non-OK responses (4xx, 5xx)
      if (!response.ok) {
        await this.handleErrorResponse(response, requestId, duration, url);
      }

      // Parse JSON response
      const jsonData = await response.json();

      // Log successful response (debug mode)
      this.logResponse(requestId, response.status, duration, jsonData);

      // Auto-unwrap standardized API format
      const unwrappedData = this.unwrapResponse<T>(jsonData);

      return unwrappedData;
    } catch (error) {
      const duration = Math.round(performance.now() - startTime);

      // Enhance error with context
      const apiError = this.createAPIError(error as Error, requestId, url, duration);

      // Log error
      this.logError(requestId, apiError);

      throw apiError;
    }
  }

  /**
   * Convenience method for GET requests
   */
  async get<T = unknown>(url: string, options: RequestOptions = {}): Promise<T> {
    return this.request<T>(url, {
      ...options,
      method: 'GET',
    });
  }

  /**
   * Convenience method for POST requests
   */
  async post<T = unknown>(url: string, body?: unknown, options: RequestOptions = {}): Promise<T> {
    return this.request<T>(url, {
      ...options,
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  /**
   * Convenience method for PUT requests
   */
  async put<T = unknown>(url: string, body?: unknown, options: RequestOptions = {}): Promise<T> {
    return this.request<T>(url, {
      ...options,
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  /**
   * Convenience method for DELETE requests
   */
  async delete<T = unknown>(url: string, options: RequestOptions = {}): Promise<T> {
    return this.request<T>(url, {
      ...options,
      method: 'DELETE',
    });
  }

  /**
   * Unwrap standardized API response format
   */
  private unwrapResponse<T>(response: unknown): T {
    // Check if response matches new standardized format
    if (
      response &&
      typeof response === 'object' &&
      'success' in response &&
      'data' in response
    ) {
      // New format detected - return just the data field
      return (response as APIResponse<T>).data;
    }

    // Old format or unknown structure - return as-is
    return response as T;
  }

  /**
   * Handle HTTP error responses (4xx, 5xx)
   */
  private async handleErrorResponse(
    response: Response,
    requestId: string,
    duration: number,
    url: string
  ): Promise<never> {
    let errorData: unknown = null;
    let errorMessage = `HTTP ${response.status}: ${response.statusText}`;

    // Try to parse error response body
    try {
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        errorData = await response.json();

        // Extract error message from standardized error format
        if (errorData && typeof errorData === 'object') {
          if ('error' in errorData && typeof errorData.error === 'object' && errorData.error) {
            const error = errorData.error as { message?: string };
            if (error.message) {
              errorMessage = error.message;
            }
          } else if ('detail' in errorData) {
            // FastAPI validation error format
            errorMessage = String(errorData.detail);
          }
        }
      }
    } catch (parseError) {
      // Unable to parse error body - use status text
      SharedLogger.warn('[SharedAPIClient] Failed to parse error response:', parseError);
    }

    // Create enhanced error
    const error = new Error(errorMessage) as Error & Partial<APIError>;
    error.name = 'APIClientError';
    error.status = response.status;
    error.statusText = response.statusText;
    error.requestId = requestId;
    error.duration = duration;
    error.url = url;
    error.errorData = errorData;
    error.isNetworkError = false;

    throw error;
  }

  /**
   * Create enhanced API error from caught exception
   */
  private createAPIError(error: Error, requestId: string, url: string, duration: number): Error & APIError {
    // If already an APIClientError, return as-is
    if (error.name === 'APIClientError') {
      return error as Error & APIError;
    }

    // Create new enhanced error for network/parsing errors
    const apiError = new Error(error.message || 'Network request failed') as Error & APIError;
    apiError.name = 'APIClientError';
    apiError.requestId = requestId;
    apiError.duration = duration;
    apiError.url = url;
    apiError.isNetworkError = true;
    apiError.originalError = error;

    // Detect common error types
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      apiError.message = 'Network error: Unable to connect to server';
    } else if (error.name === 'SyntaxError') {
      apiError.message = 'Invalid JSON response from server';
    }

    return apiError;
  }

  /**
   * Generate unique request ID for tracing
   */
  private generateRequestId(): string {
    const timestamp = Date.now().toString(36);
    const random = Math.random().toString(36).substring(2, 9);
    return `${timestamp}-${random}`;
  }

  /**
   * Log outgoing request (debug mode only)
   */
  private logRequest(requestId: string, url: string, options: RequestInit): void {
    if (!this.isDebugMode()) return;

    SharedLogger.log(`[SharedAPIClient] → ${options.method || 'GET'} ${url}`, {
      requestId,
      headers: options.headers,
      bodyLength: options.body ? (options.body as string).length : 0,
    });
  }

  /**
   * Log successful response (debug mode only)
   */
  private logResponse(requestId: string, status: number, duration: number, data: unknown): void {
    if (!this.isDebugMode()) return;

    // Check if response was unwrapped
    const wasUnwrapped =
      data && typeof data === 'object' && 'success' in data && 'data' in data;

    SharedLogger.log(`[SharedAPIClient] ← ${status} (${duration}ms)`, {
      requestId,
      unwrapped: wasUnwrapped,
      dataType: Array.isArray(data) ? 'array' : typeof data,
    });
  }

  /**
   * Log error (always logged, regardless of debug mode)
   */
  private logError(requestId: string, error: Error & Partial<APIError>): void {
    SharedLogger.error(`[SharedAPIClient] ✗ Error (${error.duration || 0}ms)`, {
      requestId,
      message: error.message,
      status: error.status,
      isNetwork: error.isNetworkError,
      url: error.url,
    });
  }

  /**
   * Check if debug mode is enabled
   */
  private isDebugMode(): boolean {
    try {
      // Check config
      if (config.debug.apiDebug) {
        return true;
      }

      // Check localStorage
      if (localStorage.getItem('API_DEBUG') === 'true') {
        return true;
      }

      // Check URL parameter
      const urlParams = new URLSearchParams(window.location.search);
      if (urlParams.get('api_debug') === 'true') {
        return true;
      }
    } catch (e) {
      // localStorage might be disabled
    }

    return false;
  }
}

// Export singleton instance
export const SharedAPIClient = new SharedAPIClientClass();

// Helper functions for enabling/disabling debug mode
export function enableAPIDebug(): void {
  localStorage.setItem('API_DEBUG', 'true');
  SharedLogger.log('[SharedAPIClient] Debug mode enabled');
}

export function disableAPIDebug(): void {
  localStorage.removeItem('API_DEBUG');
  SharedLogger.log('[SharedAPIClient] Debug mode disabled');
}
