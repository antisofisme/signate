/**
 * API Response Types
 * Type definitions for standardized API responses
 */

export interface SuccessResponse<T = any> {
  success: true;
  data: T;
  message?: string;
  timestamp: string;
}

export interface ErrorResponse {
  success: false;
  error: {
    message: string;
    code: string;
    details?: Record<string, any>;
    status_code?: number;
  };
  timestamp: string;
}

export interface PaginatedResponse<T = any> {
  success: true;
  data: T[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
  timestamp: string;
}

export type APIResponse<T = any> = SuccessResponse<T> | ErrorResponse;
