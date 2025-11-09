/**
 * API Client Type Definitions
 */

export interface APIResponse<T = unknown> {
  success: boolean;
  data: T;
  meta?: {
    timestamp: string;
    version?: string;
  };
}

export interface APIError {
  message: string;
  status?: number;
  statusText?: string;
  requestId: string;
  duration: number;
  url?: string;
  isNetworkError: boolean;
  errorData?: unknown;
  originalError?: Error;
}

export interface RequestOptions extends RequestInit {
  skipAuth?: boolean;
}

export interface APIClient {
  request<T = unknown>(url: string, options?: RequestOptions): Promise<T>;
  get<T = unknown>(url: string, options?: RequestOptions): Promise<T>;
  post<T = unknown>(url: string, body?: unknown, options?: RequestOptions): Promise<T>;
  put<T = unknown>(url: string, body?: unknown, options?: RequestOptions): Promise<T>;
  delete<T = unknown>(url: string, options?: RequestOptions): Promise<T>;
}
