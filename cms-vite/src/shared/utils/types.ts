/**
 * Shared Type Definitions
 *
 * Common types used across the CMS application
 */

import type { AxiosError } from 'axios';

// ============================================================================
// API Error Types
// ============================================================================

/**
 * Standard API error response from backend
 */
export interface ApiErrorResponse {
  detail: string;
  code?: string;
  errors?: Record<string, string[]>;
}

/**
 * Typed Axios error for API calls
 */
export type ApiError = AxiosError<ApiErrorResponse>;

/**
 * Extract error message from API error
 */
export function getApiErrorMessage(error: unknown, fallback = 'An error occurred'): string {
  if (!error) return fallback;

  // Axios error with response
  if (isApiError(error)) {
    return error.response?.data?.detail || error.message || fallback;
  }

  // Standard Error
  if (error instanceof Error) {
    return error.message || fallback;
  }

  // String error
  if (typeof error === 'string') {
    return error;
  }

  return fallback;
}

/**
 * Type guard for API error
 */
export function isApiError(error: unknown): error is ApiError {
  return (
    error !== null &&
    typeof error === 'object' &&
    'isAxiosError' in error &&
    (error as { isAxiosError: boolean }).isAxiosError === true
  );
}

// ============================================================================
// Pagination Types
// ============================================================================

/**
 * Paginated response from API
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

/**
 * Pagination filters
 */
export interface PaginationFilters {
  skip?: number;
  limit?: number;
}

// ============================================================================
// Common Entity Types
// ============================================================================

/**
 * Base entity with common fields
 */
export interface BaseEntity {
  id: number;
  created_at: string;
  updated_at?: string;
}

/**
 * Entity with soft delete
 */
export interface SoftDeleteEntity extends BaseEntity {
  is_deleted: boolean;
  deleted_at?: string;
}

// ============================================================================
// UI Types
// ============================================================================

/**
 * Sort direction
 */
export type SortDirection = 'asc' | 'desc';

/**
 * Sort configuration
 */
export interface SortConfig<T = string> {
  field: T;
  direction: SortDirection;
}

/**
 * Select option for dropdowns
 */
export interface SelectOption<T = string | number> {
  value: T;
  label: string;
  disabled?: boolean;
}

// ============================================================================
// Status Types
// ============================================================================

/**
 * Common status values
 */
export type Status = 'active' | 'inactive' | 'pending' | 'archived';

/**
 * Online status for devices
 */
export type OnlineStatus = 'online' | 'offline' | 'unknown';
